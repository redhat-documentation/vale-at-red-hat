#!/bin/sh
# shellcheck disable=SC3043
#
# Copyright (c) 2021 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#
# Validates Vale rules by running them against test fixtures.
# - testvalid.adoc: Should produce NO alerts (false positive test)
# - testinvalid.adoc: Every line should produce an alert (detection test)

set -e

TOTAL=0
ERRORS_FILE=$(mktemp)
trap 'rm -f "$ERRORS_FILE"' EXIT

# Run vale and return the output
run_vale() {
    vale --config="$1/.vale.ini" --no-exit --output=line "$2"
}

# Count non-empty lines in output
count_lines() {
    echo "$1" | grep -c . || true
}

# Record an error
record_error() {
    echo "$1" >> "$ERRORS_FILE"
}

# Report false positives (alerts in testvalid.adoc)
check_false_positives() {
    local alerts="$1"
    local count="$2"

    if [ "$count" -gt 0 ]; then
        echo "$alerts" | while read -r line; do
            record_error "$line"
        done
        TOTAL=$((TOTAL + count))
    fi
}

# Test a RedHat style rule
# Expects every non-empty line in testinvalid.adoc to trigger an alert
test_redhat_rule() {
    local dir=".vale/fixtures/RedHat/$RULE"
    local valid_alerts
    local valid_count
    local invalid_alerts
    local invalid_count
    local expected_count

    valid_alerts="$(run_vale "$dir" "$dir/testvalid.adoc")"
    valid_count="$(count_lines "$valid_alerts")"
    invalid_alerts="$(run_vale "$dir" "$dir/testinvalid.adoc")"
    invalid_count="$(count_lines "$invalid_alerts")"
    expected_count="$(grep -c '.' "$dir/testinvalid.adoc" || true)"

    local missed=$((expected_count - invalid_count))

    check_false_positives "$valid_alerts" "$valid_count"

    if [ "$missed" -gt 0 ]; then
        # Report lines that should have triggered an alert but didn't
        grep -n '.' "$dir/testinvalid.adoc" | while read -r line; do
            linenum=$(echo "$line" | cut -d: -f1)
            if ! echo "$invalid_alerts" | grep -q ":$linenum:"; then
                record_error "$dir/testinvalid.adoc:$linenum"
            fi
        done
        TOTAL=$((TOTAL + missed))
    fi
}

# Test an AsciiDoc/OpenShiftAsciiDoc style rule
# Expects lines marked with "//vale-fixture" to trigger an alert
test_markup_rule() {
    local dir=".vale/fixtures/$RULE"
    local valid_alerts
    local valid_count
    local invalid_alerts
    local invalid_count
    local expected_count

    valid_alerts="$(run_vale "$dir" "$dir/testvalid.adoc")"
    valid_count="$(count_lines "$valid_alerts")"
    invalid_alerts="$(run_vale "$dir" "$dir/testinvalid.adoc")"
    invalid_count="$(count_lines "$invalid_alerts")"
    expected_count="$(grep -c "//vale-fixture" "$dir/testinvalid.adoc" || true)"

    local missed=$((expected_count - invalid_count))

    check_false_positives "$valid_alerts" "$valid_count"

    if [ "$missed" -ne 0 ]; then
        # Handle both missed detections and over-detections
        if [ "$missed" -lt 0 ]; then
            missed=$((missed * -1))
        fi
        grep -n "//vale-fixture" "$dir/testinvalid.adoc" | cut -d: -f1 | while read -r linenum; do
            record_error "$dir/testinvalid.adoc:$linenum"
        done
        TOTAL=$((TOTAL + missed))
    fi
}

# Run tests for AsciiDoc rules
for RULE in $(find .vale/styles/AsciiDoc -name '*.yml' | cut -d/ -f 3,4 | cut -d. -f1 | sort); do
    test_markup_rule
done

# Run tests for OpenShiftAsciiDoc rules
for RULE in $(find .vale/styles/OpenShiftAsciiDoc -name '*.yml' | cut -d/ -f 3,4 | cut -d. -f1 | sort); do
    test_markup_rule
done

# Run tests for RedHat rules
for RULE in $(find .vale/styles/RedHat/ -name '*.yml' | cut -d/ -f 4 | cut -d. -f1 | sort); do
    test_redhat_rule
done

if [ $TOTAL -gt 0 ]; then
    echo "$TOTAL tests to fix:"
    cat "$ERRORS_FILE"
else
    echo "All tests passed"
fi
exit $TOTAL
