#!/usr/bin/env python3
# Copyright (c) 2024 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
"""Generate ISO Schematron rules from Red Hat Vale style YAML files."""

import os
import re
import sys

import yaml
from lxml import etree

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VALE_STYLES_DIR = os.path.join(REPO_ROOT, ".vale", "styles", "RedHat")
OUTPUT_DIR = os.path.join(REPO_ROOT, "schematron", "output")

SCH_NS = "http://purl.oclc.org/dml/schematron"
SCH = "{%s}" % SCH_NS
NSMAP = {"sch": SCH_NS}

SKIP_RULES = {"Spelling", "Using", "ReadabilityGrade"}

LEVEL_TO_ROLE = {
    "error": "error",
    "warning": "warning",
    "suggestion": "info",
}

CODE_EXCLUSIONS = [
    "codeblock", "codeph", "filepath", "systemoutput",
    "cmdname", "option", "varname", "apiname",
]

RULES_TO_GENERATE = [
    "Abbreviations", "CaseSensitiveTerms", "Conjunctions",
    "ConsciousLanguage", "Contractions", "Definitions",
    "DoNotUseTerms", "Ellipses", "EmDash", "HeadingPunctuation",
    "Headings", "Hyphens", "ObviousTerms", "OxfordComma",
    "PassiveVoice", "ProductCentricWriting", "RepeatedWords",
    "SelfReferentialText", "SentenceLength", "SessionId",
    "SimpleWords", "Slash", "SmartQuotes", "Spacing",
    "Symbols", "TermsErrors", "TermsSuggestions", "TermsWarnings",
]

def handle_existence(rule_name, data):
    """Generate Schematron for a Vale 'existence' rule.

    Existence rules flag text matching any token in the tokens list.
    If a 'raw' field is present (e.g., PassiveVoice), each token is
    prefixed with the raw pattern to form a compound match.
    """
    level = data.get("level", "warning")
    role = LEVEL_TO_ROLE.get(level, "warning")
    message_template = data.get("message", "Found '%s'.")
    scope = data.get("scope")
    ignorecase = data.get("ignorecase", False)
    tokens = data.get("tokens", [])
    raw_prefix = data.get("raw", [])

    schema = make_schema_element(rule_name, rule_name, "existence", level)
    context = build_scope_context(scope)

    pattern = etree.SubElement(schema, SCH + "pattern")
    pattern.set("id", "RedHat-%s" % rule_name)

    rule_el = etree.SubElement(pattern, SCH + "rule")
    rule_el.set("context", context)

    prefix = ""
    if raw_prefix:
        if isinstance(raw_prefix, list):
            prefix = raw_prefix[0]
        else:
            prefix = str(raw_prefix)

    flags = "'i'" if ignorecase else ""

    for token in tokens:
        token_str = str(token)
        if prefix:
            full_pattern = prefix + token_str
        else:
            full_pattern = token_str

        converted, warnings = convert_regex_to_xpath(full_pattern)

        for w in warnings:
            rule_el.append(etree.Comment(" %s " % w))

        report = etree.SubElement(rule_el, SCH + "report")

        escaped = xml_escape_regex(converted)
        if flags:
            test = "matches(., '%s', %s)" % (escaped, flags)
        else:
            test = "matches(., '%s')" % escaped

        report.set("test", test)
        report.set("role", role)

        try:
            msg = message_template % token_str
        except TypeError:
            msg = message_template
        report.text = msg

    write_schematron_file(rule_name, schema)


def handle_substitution(rule_name, data):
    """Generate Schematron for a Vale 'substitution' rule.

    Substitution rules have a swap map of {bad_pattern: replacement}.
    Each swap entry becomes a sch:report that flags the bad pattern
    and suggests the replacement in its message.
    """
    level = data.get("level", "warning")
    role = LEVEL_TO_ROLE.get(level, "warning")
    message_template = data.get("message", "Use '%s' rather than '%s'.")
    scope = data.get("scope")
    ignorecase = data.get("ignorecase", True)
    swap = data.get("swap", {})
    nonword = data.get("nonword", False)

    schema = make_schema_element(rule_name, rule_name, "substitution", level)
    context = build_scope_context(scope)

    pat = etree.SubElement(schema, SCH + "pattern")
    pat.set("id", "RedHat-%s" % rule_name)

    rule_el = etree.SubElement(pat, SCH + "rule")
    rule_el.set("context", context)

    flags = "'i'" if ignorecase else ""

    for bad_pattern, replacement in swap.items():
        bad_str = str(bad_pattern)
        repl_str = str(replacement)

        converted, warnings = convert_regex_to_xpath(bad_str)

        for w in warnings:
            rule_el.append(etree.Comment(" %s " % w))

        report = etree.SubElement(rule_el, SCH + "report")

        escaped = xml_escape_regex(converted)
        if flags:
            test = "matches(., '%s', %s)" % (escaped, flags)
        else:
            test = "matches(., '%s')" % escaped

        report.set("test", test)
        report.set("role", role)

        try:
            msg = message_template % (repl_str, bad_str)
        except TypeError:
            try:
                msg = message_template % repl_str
            except TypeError:
                msg = message_template
        report.text = msg

    write_schematron_file(rule_name, schema)


def handle_conditional(rule_name, data):
    """Generate Schematron for a Vale 'conditional' rule.

    Checks that if 'first' pattern appears, 'second' pattern must also
    appear in the same scope. Used by Definitions.yml for acronyms.
    """
    level = data.get("level", "warning")
    role = LEVEL_TO_ROLE.get(level, "warning")
    exceptions = data.get("exceptions", [])

    schema = make_schema_element(rule_name, rule_name, "conditional", level)

    schema.append(etree.Comment(
        " Fidelity: Partial — scoped per topic, not per document. "
    ))

    pat = etree.SubElement(schema, SCH + "pattern")
    pat.set("id", "RedHat-%s" % rule_name)

    rule_el = etree.SubElement(pat, SCH + "rule")
    rule_el.set("context", "//*[contains(@class, ' topic/topic ') or self::topic]")

    report = etree.SubElement(rule_el, SCH + "report")
    report.set(
        "test",
        "some $text in .//text()[matches(., '\\b[A-Z]{3,5}s?\\b')] satisfies "
        "(let $words := tokenize($text, '\\s+') return "
        "some $w in $words satisfies "
        "(matches($w, '^[A-Z]{3,5}s?$') and "
        "not(contains(string(.), concat('(', $w, ')')))))"
    )
    report.set("role", role)
    report.text = (
        "Define acronyms and abbreviations on first occurrence "
        "if they are likely to be unfamiliar."
    )

    if exceptions:
        rule_el.append(etree.Comment(
            " %d well-known acronyms are exempted in the Vale rule " % len(exceptions)
        ))

    write_schematron_file(rule_name, schema)


def handle_capitalization(rule_name, data):
    """Generate Schematron for a Vale 'capitalization' rule.

    Simplified: checks for title-case words after the first word in headings.
    """
    level = data.get("level", "warning")
    role = LEVEL_TO_ROLE.get(level, "warning")
    exceptions = data.get("exceptions", [])

    schema = make_schema_element(rule_name, rule_name, "capitalization", level)

    schema.append(etree.Comment(
        " Fidelity: Simplified — checks for title-case words after the first word. "
    ))
    schema.append(etree.Comment(
        " %d proper nouns / tech terms are exempted in the Vale rule. " % len(exceptions)
    ))

    excl = exclusion_predicates()
    pat = etree.SubElement(schema, SCH + "pattern")
    pat.set("id", "RedHat-%s" % rule_name)

    rule_el = etree.SubElement(pat, SCH + "rule")
    rule_el.set("context", "//title%s | //searchtitle%s" % (excl, excl))

    report = etree.SubElement(rule_el, SCH + "report")
    report.set(
        "test",
        "matches(., '^[A-Z][a-z].*\\s[A-Z][A-Z]') or "
        "matches(., '^[A-Z][^a-z]')"
    )
    report.set("role", role)
    report.text = "Use sentence-style capitalization in headings."

    write_schematron_file(rule_name, schema)


def handle_occurrence(rule_name, data):
    """Generate Schematron for a Vale 'occurrence' rule.

    Counts word tokens and flags when count exceeds max.
    """
    level = data.get("level", "warning")
    role = LEVEL_TO_ROLE.get(level, "warning")
    message = data.get("message", "Consider shortening this text.")
    max_count = data.get("max", 32)
    scope = data.get("scope")

    schema = make_schema_element(rule_name, rule_name, "occurrence", level)

    schema.append(etree.Comment(
        " Uses XPath 2.0 tokenize() for word counting. "
    ))

    context = build_scope_context(scope)
    pat = etree.SubElement(schema, SCH + "pattern")
    pat.set("id", "RedHat-%s" % rule_name)

    rule_el = etree.SubElement(pat, SCH + "rule")
    rule_el.set("context", context)

    report = etree.SubElement(rule_el, SCH + "report")
    report.set(
        "test",
        "count(tokenize(normalize-space(.), '\\s+')) > %d" % max_count,
    )
    report.set("role", role)
    report.text = message

    write_schematron_file(rule_name, schema)


def handle_repetition(rule_name, data):
    """Generate Schematron for a Vale 'repetition' rule.

    Detects consecutive duplicate words.
    """
    level = data.get("level", "warning")
    role = LEVEL_TO_ROLE.get(level, "warning")

    schema = make_schema_element(rule_name, rule_name, "repetition", level)
    context = build_scope_context(data.get("scope"))

    pat = etree.SubElement(schema, SCH + "pattern")
    pat.set("id", "RedHat-%s" % rule_name)

    rule_el = etree.SubElement(pat, SCH + "rule")
    rule_el.set("context", context)

    report = etree.SubElement(rule_el, SCH + "report")
    report.set("test", r"matches(., '(\b\w+\b)\s+\1\b')")
    report.set("role", role)
    report.text = "A word is repeated consecutively."

    write_schematron_file(rule_name, schema)


TYPE_HANDLERS = {
    "existence": handle_existence,
    "substitution": handle_substitution,
    "conditional": handle_conditional,
    "capitalization": handle_capitalization,
    "occurrence": handle_occurrence,
    "repetition": handle_repetition,
}


def exclusion_predicates():
    """XPath predicates to exclude code-bearing DITA elements."""
    return "".join(
        "[not(ancestor-or-self::%s)]" % el for el in CODE_EXCLUSIONS
    )


def build_scope_context(scope):
    """Convert a Vale scope to a DITA XPath context expression.

    Args:
        scope: Vale scope string, e.g. "heading", "sentence", "raw",
               "~heading", or comma-separated like "sentence, heading".
    Returns:
        XPath context string for use in sch:rule/@context.
    """
    excl = exclusion_predicates()

    sentence_elements = [
        "p", "li", "shortdesc", "abstract", "entry", "dd", "note", "lq",
    ]
    heading_elements = ["title", "searchtitle"]

    scope_map = {
        "heading": " | ".join(
            "//%s%s" % (el, excl) for el in heading_elements
        ),
        "sentence": " | ".join(
            "//%s%s" % (el, excl) for el in sentence_elements
        ),
        "paragraph": " | ".join(
            "//%s%s" % (el, excl) for el in sentence_elements
        ),
        "raw": "//*[text()]",
    }

    if scope is None:
        return scope_map["sentence"]

    if isinstance(scope, list):
        scope_str = ", ".join(str(s) for s in scope)
    else:
        scope_str = str(scope)

    parts = [s.strip() for s in scope_str.split(",")]

    if len(parts) == 1:
        s = parts[0]
        if s.startswith("~"):
            negated = s[1:]
            if negated == "heading":
                return scope_map["sentence"]
            return scope_map.get(negated, scope_map["sentence"])
        return scope_map.get(s, scope_map["sentence"])

    # Union of multiple scopes
    contexts = set()
    for s in parts:
        s = s.strip()
        ctx = scope_map.get(s, "")
        if ctx:
            for part in ctx.split(" | "):
                contexts.add(part.strip())
    return " | ".join(sorted(contexts))


def convert_regex_to_xpath(pattern):
    """Convert a Vale regex pattern to an XPath 2.0 compatible regex.

    Strips unsupported constructs (negative lookbehind/lookahead) and
    escapes XML special characters.

    Returns:
        (converted_pattern, warnings) where warnings is a list of strings
        describing what was stripped.
    """
    warnings = []
    result = pattern

    # Strip negative lookbehind (?<!...)
    lookbehind_re = r"\(\?<![^)]*\)"
    if re.search(lookbehind_re, result):
        warnings.append("Stripped negative lookbehind (?<!...) — may cause false positives")
        result = re.sub(lookbehind_re, "", result)

    # Strip negative lookahead (?!...)
    lookahead_re = r"\(\?![^)]*\)"
    if re.search(lookahead_re, result):
        warnings.append("Stripped negative lookahead (?!...) — may cause false positives")
        result = re.sub(lookahead_re, "", result)

    # Escape backslash-escaped special chars that are XML-sensitive
    # (The regex itself stays in XPath string form; XML escaping happens at serialization)

    return result, warnings


def xml_escape_regex(pattern):
    """Escape XML special chars and double single quotes for XPath string literals.

    Args:
        pattern: The regex pattern to escape.
    Returns:
        Escaped pattern safe for use in XPath string literals.
    """
    # Double single quotes for XPath string literal escaping
    result = pattern.replace("'", "''")

    # XML special characters are handled by lxml during serialization,
    # but we need to ensure they're properly escaped in the context of XPath strings
    # The lxml library will handle <, >, & when we serialize the XML

    return result


def parse_vale_rule(filepath):
    """Parse a Vale YAML rule file and return its fields as a dict."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def make_schema_element(title, source_comment, extends_type, level):
    """Create the root sch:schema element with metadata."""
    schema = etree.Element(SCH + "schema", nsmap=NSMAP)
    schema.set("queryBinding", "xslt2")
    schema.set("schemaVersion", "iso")

    title_el = etree.SubElement(schema, SCH + "title")
    title_el.text = "RedHat: %s" % title

    schema.append(etree.Comment(
        " Generated from .vale/styles/RedHat/%s.yml " % title
    ))
    schema.append(etree.Comment(
        " Vale extension type: %s " % extends_type
    ))
    schema.append(etree.Comment(" Level: %s " % level))

    return schema


def write_schematron_file(rule_name, schema_element):
    """Write a sch:schema element to a .sch file."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, "%s.sch" % rule_name)
    tree = etree.ElementTree(schema_element)
    tree.write(
        filepath,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
    )


def write_combined_schematron(rule_names):
    """Write RedHat-all.sch that includes all individual .sch files."""
    schema = etree.Element(SCH + "schema", nsmap=NSMAP)
    schema.set("queryBinding", "xslt2")
    schema.set("schemaVersion", "iso")

    title_el = etree.SubElement(schema, SCH + "title")
    title_el.text = "RedHat: All rules"

    schema.append(etree.Comment(" Combined Schematron — includes all individual rule files "))

    for name in sorted(rule_names):
        inc = etree.SubElement(schema, SCH + "include")
        inc.set("href", "%s.sch" % name)

    write_schematron_file("RedHat-all", schema)


def generate_rule(rule_name):
    """Generate a Schematron rule from a Vale YAML file.

    Args:
        rule_name: Name of the rule (e.g., 'Abbreviations')
    Returns:
        rule_name on success, None on skip/failure
    """
    if rule_name in SKIP_RULES:
        print("Skipping %s (in SKIP_RULES)" % rule_name)
        return None

    vale_file = os.path.join(VALE_STYLES_DIR, "%s.yml" % rule_name)
    if not os.path.exists(vale_file):
        print("Warning: %s not found" % vale_file, file=sys.stderr)
        return None

    try:
        rule_data = parse_vale_rule(vale_file)
        extends = rule_data.get("extends", "")

        # Dispatch to type handler (will be implemented in Tasks 2-4)
        handler = TYPE_HANDLERS.get(extends)
        if handler:
            handler(rule_name, rule_data)
            return rule_name
        else:
            print("Warning: No handler for type '%s' (rule: %s)" % (extends, rule_name), file=sys.stderr)
            return None

    except Exception as e:
        print("Error generating %s: %s" % (rule_name, e), file=sys.stderr)
        return None


def main():
    """Main entry point: generate all Schematron rules."""
    print("Generating Schematron rules from Vale YAML files...")
    print("Vale styles dir: %s" % VALE_STYLES_DIR)
    print("Output dir: %s" % OUTPUT_DIR)
    print()

    generated = []
    for rule_name in RULES_TO_GENERATE:
        result = generate_rule(rule_name)
        if result:
            generated.append(result)

    if generated:
        print()
        print("Writing combined schema...")
        write_combined_schematron(generated)
        print()
        print("Generated %d rules:" % len(generated))
        for name in sorted(generated):
            print("  - %s.sch" % name)
        print()
        print("Combined schema: RedHat-all.sch")
    else:
        print("No rules generated (no type handlers implemented yet)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
