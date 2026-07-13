#!/usr/bin/env bash
# Test Schematron rules against per-rule DITA fixtures using DITA-OT.
#
# Usage:
#   ./schematron/test.sh                  # test all rules
#   ./schematron/test.sh Contractions     # test a single rule
#   ./schematron/test.sh -l               # list available rules

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
OUTPUT_DIR="$SCRIPT_DIR/output"
FIXTURES_DIR="$SCRIPT_DIR/fixtures"
OUT_DIR="$REPO_ROOT/out"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

if ! command -v dita &>/dev/null; then
    echo -e "${RED}Error: dita command not found. Is DITA-OT on your PATH?${RESET}" >&2
    exit 1
fi

if [[ "${1:-}" == "-l" || "${1:-}" == "--list" ]]; then
    echo "Available rules:"
    for sch in "$OUTPUT_DIR"/*.sch; do
        name="$(basename "$sch" .sch)"
        [[ "$name" == "RedHat-all" ]] && continue
        fixture="$FIXTURES_DIR/test-${name}.dita"
        if [[ -f "$fixture" ]]; then
            echo "  $name"
        else
            echo "  $name  (no fixture)"
        fi
    done
    exit 0
fi

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
    echo "Usage: $0 [RULE_NAME | -l | -h]"
    echo
    echo "  (no args)    Test all rules against their fixtures"
    echo "  RULE_NAME    Test a single rule (e.g. Contractions)"
    echo "  -l, --list   List available rules"
    echo "  -h, --help   Show this help"
    exit 0
fi

passed=0
failed=0
skipped=0
total_findings=0

run_test() {
    local name="$1"
    local sch="$OUTPUT_DIR/${name}.sch"
    local fixture="$FIXTURES_DIR/test-${name}.dita"

    if [[ ! -f "$sch" ]]; then
        echo -e "  ${RED}ERROR${RESET}: $name — $sch not found"
        ((failed++)) || true
        return
    fi

    if [[ ! -f "$fixture" ]]; then
        echo -e "  ${YELLOW}SKIP${RESET}: $name — no fixture file"
        ((skipped++)) || true
        return
    fi

    # Clean previous output so the log is fresh
    rm -f "$OUT_DIR"/*.schematron.log "$OUT_DIR"/*.schematron.log.temp 2>/dev/null || true

    dita --input "$fixture" \
         --format html5 \
         -Dschematron.topic.validation.files="$sch" \
         -Dschematron.fail=false \
         -Dpolyglot.engine.WarnInterpreterOnly=false \
         1>/dev/null 2>/dev/null || true

    local logfile
    logfile="$(find "$OUT_DIR" -name '*.schematron.log' 2>/dev/null | head -1)"

    local findings=0
    if [[ -n "$logfile" && -f "$logfile" ]]; then
        findings="$(grep -cE '^\[(error|warn|info|fatal)\]' "$logfile" 2>/dev/null || echo 0)"
    fi

    if [[ "$findings" -gt 0 ]]; then
        echo -e "  ${RED}FAIL${RESET}: $name — $findings finding(s)"
        total_findings=$((total_findings + findings))
        ((passed++)) || true

        grep -E '^\[(error|warn|info|fatal)\]' "$logfile" | while IFS= read -r line; do
            echo -e "        ${CYAN}${line}${RESET}"
        done
    else
        echo -e "  ${GREEN}PASS${RESET}: $name — 0 findings"
        ((failed++)) || true
    fi
}

if [[ $# -gt 0 ]]; then
    echo -e "${BOLD}Testing rule: $1${RESET}"
    echo
    run_test "$1"
else
    echo -e "${BOLD}Testing all Schematron rules against fixtures...${RESET}"
    echo
    for sch in "$OUTPUT_DIR"/*.sch; do
        name="$(basename "$sch" .sch)"
        [[ "$name" == "RedHat-all" ]] && continue
        run_test "$name"
    done
fi

echo
echo -e "${BOLD}Results:${RESET} ${GREEN}${passed} passed${RESET}, ${RED}${failed} failed${RESET}, ${YELLOW}${skipped} skipped${RESET}, ${total_findings} total findings"

[[ "$failed" -eq 0 ]]
