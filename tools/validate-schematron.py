#!/usr/bin/env python3
# Copyright (c) 2024 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
"""Validate generated Schematron files for well-formedness and structure."""

import glob
import os
import sys

from lxml import etree

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(REPO_ROOT, "schematron", "output")

SCH_NS = "http://purl.oclc.org/dsdl/schematron"


def validate_schematron(filepath):
    """Validate a single .sch file.

    Checks:
    1. XML well-formedness
    2. Root element is sch:schema with correct namespace
    3. queryBinding is xslt2
    4. Contains at least one sch:pattern

    Note: lxml.isoschematron only supports XSLT 1.0, so it cannot compile
    our xslt2/XPath 2.0 rules. We validate structure instead.

    Returns:
        (valid, error_message) tuple.
    """
    filename = os.path.basename(filepath)

    try:
        doc = etree.parse(filepath)
    except etree.XMLSyntaxError as e:
        return False, "XML parse error in %s: %s" % (filename, e)

    root = doc.getroot()

    if root.tag != "{%s}schema" % SCH_NS:
        return False, "%s: root element is not sch:schema" % filename

    qb = root.get("queryBinding", "")
    if qb != "xslt2":
        return False, "%s: queryBinding is '%s', expected 'xslt2'" % (filename, qb)

    patterns = root.findall("{%s}pattern" % SCH_NS)
    includes = root.findall("{%s}include" % SCH_NS)

    if not patterns and not includes:
        return False, "%s: no sch:pattern or sch:include elements found" % filename

    for pat in patterns:
        rules = pat.findall("{%s}rule" % SCH_NS)
        if not rules:
            return False, "%s: pattern '%s' has no sch:rule" % (filename, pat.get("id", "?"))

        for rule_el in rules:
            ctx = rule_el.get("context", "")
            if not ctx:
                return False, "%s: sch:rule has no context attribute" % filename

            reports = rule_el.findall("{%s}report" % SCH_NS)
            asserts = rule_el.findall("{%s}assert" % SCH_NS)
            if not reports and not asserts:
                return False, "%s: sch:rule has no report or assert children" % filename

    return True, ""


def main():
    sch_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.sch")))

    if not sch_files:
        print("ERROR: No .sch files found in %s" % OUTPUT_DIR, file=sys.stderr)
        return 1

    print("Validating %d Schematron files..." % len(sch_files))

    errors = []
    for filepath in sch_files:
        valid, error_msg = validate_schematron(filepath)
        name = os.path.basename(filepath)
        if valid:
            print("  OK: %s" % name)
        else:
            print("  FAIL: %s" % name)
            errors.append(error_msg)

    if errors:
        print("\n%d validation errors:" % len(errors))
        for err in errors:
            print("  %s" % err)
        return 1

    print("\nAll %d files valid." % len(sch_files))
    return 0


if __name__ == "__main__":
    sys.exit(main())
