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

# Type handlers will be implemented in subsequent tasks
TYPE_HANDLERS = {}


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
