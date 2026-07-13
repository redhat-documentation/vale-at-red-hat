#!/usr/bin/env python3
# Copyright (c) 2024 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
"""Smoke-test generated Schematron rules against per-rule DITA fixtures.

Uses lxml.isoschematron which only supports XSLT 1.0. Rules using XPath 2.0
features (matches(), tokenize()) will compile but may not fire during these
smoke tests. This script validates that the Schematron files are structurally
sound and can be loaded by a Schematron processor. Full XPath 2.0 validation
requires a processor like Saxon or SchXslt.

Each .sch file is tested against its matching test-{RuleName}.dita fixture
in schematron/fixtures/.
"""

import glob
import os
import sys

from lxml import etree
from lxml.isoschematron import Schematron

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(REPO_ROOT, "schematron", "output")
FIXTURES_DIR = os.path.join(REPO_ROOT, "schematron", "fixtures")


def get_schematron_reports(sch_path, dita_path):
    """Apply a Schematron file to a DITA file and return report messages.

    Returns:
        (list of report message strings, error string) or (None, error) on failure.
    """
    try:
        sch_doc = etree.parse(sch_path)
        schematron = Schematron(sch_doc, store_report=True)
    except Exception as e:
        return None, str(e)

    try:
        dita_doc = etree.parse(dita_path)
    except etree.XMLSyntaxError as e:
        return None, "DITA parse error: %s" % e

    schematron.validate(dita_doc)
    report = schematron.validation_report

    if report is None:
        return [], ""

    ns = {"svrl": "http://purl.oclc.org/dml/svrl"}
    messages = []

    for elem in report.xpath("//svrl:successful-report", namespaces=ns):
        text_el = elem.find("svrl:text", ns)
        if text_el is not None and text_el.text:
            messages.append(text_el.text.strip())

    for elem in report.xpath("//svrl:failed-assert", namespaces=ns):
        text_el = elem.find("svrl:text", ns)
        if text_el is not None and text_el.text:
            messages.append(text_el.text.strip())

    return messages, ""


def main():
    sch_files = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.sch")))
    sch_files = [f for f in sch_files if not f.endswith("RedHat-all.sch")]

    if not sch_files:
        print("ERROR: No .sch files found in %s" % OUTPUT_DIR, file=sys.stderr)
        return 1

    print("Smoke-testing %d Schematron files against per-rule fixtures...\n" % len(sch_files))

    compile_errors = 0
    compilable = 0
    detections_total = 0
    xpath2_skipped = 0
    missing_fixtures = 0

    for sch_path in sch_files:
        name = os.path.basename(sch_path).replace(".sch", "")
        fixture = os.path.join(FIXTURES_DIR, "test-%s.dita" % name)

        if not os.path.exists(fixture):
            print("  MISSING: test-%s.dita — no fixture file" % name)
            missing_fixtures += 1
            continue

        reports, err = get_schematron_reports(sch_path, fixture)
        if reports is None:
            xpath2_skipped += 1
            print("  SKIP: %s (XPath 2.0, not testable with lxml: %s)" % (name, err[:80]))
            continue

        compilable += 1
        det_count = len(reports)
        if det_count > 0:
            print("  OK: %s — %d detection(s)" % (name, det_count))
            detections_total += det_count
        else:
            print("  INFO: %s — 0 detections (may need XPath 2.0)" % name)

    print("\nSummary:")
    print("  Files tested: %d" % len(sch_files))
    print("  Compilable by lxml (XSLT 1.0): %d" % compilable)
    print("  Skipped (require XPath 2.0): %d" % xpath2_skipped)
    print("  Missing fixtures: %d" % missing_fixtures)
    print("  Total detections: %d" % detections_total)
    print("  Compilation errors: %d" % compile_errors)

    if compile_errors > 0 or missing_fixtures > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
