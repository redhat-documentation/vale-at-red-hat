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
# - testinvalid.adoc: Marked examples should produce the expected alerts

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

# Test an AILanguage rule.
# Each //vale-fixture marker identifies an alert on the following line.
# Validate the line and rule ID as well as the total number of alerts.
test_ailanguage_rule() {
    local dir=".vale/fixtures/$RULE"
    local rule_name
    local valid_alerts
    local valid_count
    local invalid_alerts
    local invalid_count
    local expected_count
    local expected_line
    local line_count
    local marker_lines

    rule_name="${RULE#*/}"
    valid_alerts="$(run_vale "$dir" "$dir/testvalid.adoc")"
    valid_count="$(count_lines "$valid_alerts")"
    invalid_alerts="$(run_vale "$dir" "$dir/testinvalid.adoc")"
    invalid_count="$(count_lines "$invalid_alerts")"
    expected_count="$(grep -c '^//vale-fixture$' "$dir/testinvalid.adoc" || true)"

    check_false_positives "$valid_alerts" "$valid_count"

    if [ "$expected_count" -eq 0 ]; then
        record_error "$dir/testinvalid.adoc (no //vale-fixture markers)"
        TOTAL=$((TOTAL + 1))
    fi

    marker_lines="$(grep -n '^//vale-fixture$' "$dir/testinvalid.adoc" | cut -d: -f1)"
    while IFS= read -r expected_line; do
        [ -n "$expected_line" ] || continue
        expected_line=$((expected_line + 1))
        line_count="$(printf '%s\n' "$invalid_alerts" |
            grep -F ":$expected_line:" |
            grep -F -c "AILanguage.$rule_name" || true)"

        if [ "$line_count" -ne 1 ]; then
            record_error "$dir/testinvalid.adoc:$expected_line (expected AILanguage.$rule_name once, found $line_count)"
            TOTAL=$((TOTAL + 1))
        fi
    done <<EOF
$marker_lines
EOF

    if [ "$invalid_count" -ne "$expected_count" ]; then
        record_error "$dir/testinvalid.adoc (expected $expected_count total alerts, found $invalid_count)"
        TOTAL=$((TOTAL + 1))
    fi
}

# Test an AILanguage document-level occurrence rule.
# An absence rule has no meaningful source location, so validate the rule ID
# and require exactly one alert for the complete invalid fixture.
test_ailanguage_document_rule() {
    local dir=".vale/fixtures/$RULE"
    local rule_name
    local valid_alerts
    local valid_count
    local invalid_alerts
    local invalid_count
    local rule_count

    rule_name="${RULE#*/}"
    valid_alerts="$(run_vale "$dir" "$dir/testvalid.adoc")"
    valid_count="$(count_lines "$valid_alerts")"
    invalid_alerts="$(run_vale "$dir" "$dir/testinvalid.adoc")"
    invalid_count="$(count_lines "$invalid_alerts")"
    rule_count="$(printf '%s\n' "$invalid_alerts" |
        grep -F -c "AILanguage.$rule_name" || true)"

    check_false_positives "$valid_alerts" "$valid_count"

    if [ "$invalid_count" -ne 1 ] || [ "$rule_count" -ne 1 ]; then
        record_error "$dir/testinvalid.adoc (expected AILanguage.$rule_name once, found $rule_count of $invalid_count total alerts)"
        TOTAL=$((TOTAL + 1))
    fi
}

# The complete AILanguage style must remain quiet on representative Red Hat
# concept, procedure, reference, and general technical content.
test_ailanguage_corpus() {
    local dir=".vale/fixtures/AILanguage/corpus"
    local file
    local alerts
    local count

    for file in "$dir"/*.adoc; do
        alerts="$(run_vale "$dir" "$file")"
        count="$(count_lines "$alerts")"
        check_false_positives "$alerts" "$count"
    done
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

# Run tests for AILanguage rules and the representative technical corpus.
for RULE in $(find .vale/styles/AILanguage -maxdepth 1 -name '*.yml' | cut -d/ -f 3,4 | cut -d. -f1 | sort); do
    if grep -q '^extends: occurrence$' ".vale/styles/$RULE.yml" &&
        grep -q '^scope: raw$' ".vale/styles/$RULE.yml"; then
        test_ailanguage_document_rule
    else
        test_ailanguage_rule
    fi
done
test_ailanguage_corpus

if [ $TOTAL -gt 0 ]; then
    echo "$TOTAL tests to fix:"
    cat "$ERRORS_FILE"
else
    echo "All tests passed"
fi
exit $TOTAL
