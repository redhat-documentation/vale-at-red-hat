#!/bin/sh
#
# Copyright (c) 2021 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#
# Fail on errors
set -e

Rule() {
    DIR=".vale/fixtures/RedHat/$RULE"
    VALIDALERTSCOUNT="$(vale --config="$DIR/.vale.ini" --no-exit --output=line "$DIR/testvalid.adoc" | wc -l)"
    INVALIDALERTS="$(vale --config="$DIR/.vale.ini" --no-exit --output=line "$DIR/testinvalid.adoc" | wc -l)"
    INVALIDLINES="$(grep -cve '.+' "$DIR/testinvalid.adoc" || true)"
    echo "$INVALIDLINES in .vale/fixtures/RedHat/$RULE/" 
    INVALIDGAP=$((INVALIDLINES - INVALIDALERTS))
    if [ "$VALIDALERTSCOUNT" -gt 0 ]
    then
        echo "ERROR: $VALIDALERTSCOUNT in .vale/fixtures/RedHat/$RULE/testvalid.adoc for .vale/styles/RedHat/$RULE.yml"
        TOTAL=$(( TOTAL + VALIDALERTSCOUNT ))
    fi
    if [ $INVALIDGAP -gt 0 ]
    then
        echo "ERROR: $INVALIDGAP in .vale/fixtures/RedHat/$RULE/testinvalid.adoc / .vale/styles/RedHat/$RULE.yml"
        TOTAL=$(( TOTAL + INVALIDGAP ))
    fi
}

RuleMarkup() {
    DIR=".vale/fixtures/$RULE"
    echo "$DIR"
    VALIDALERTSCOUNT="$(vale --config="$DIR/.vale.ini" --no-exit --output=line "$DIR/testvalid.adoc" | wc -l)"
    INVALIDALERTSCOUNT="$(vale --config="$DIR/.vale.ini" --no-exit --output=line "$DIR/testinvalid.adoc" | wc -l)"
    INVALIDLINES="$(grep -c "//vale-fixture" "$DIR/testinvalid.adoc" || true)"
    INVALIDGAP=$((INVALIDLINES - INVALIDALERTSCOUNT))
    if [ "$VALIDALERTSCOUNT" -gt 0 ]
    then
        echo "$VALIDALERTSCOUNT ERROR(s) in $DIR/testvalid.adoc for .vale/styles/$RULE.yml"
        TOTAL=$(( TOTAL + VALIDALERTSCOUNT ))
    fi
    if [ $INVALIDGAP -eq 0 ]
    then
        true #no errors
    else
        #handle error count or "//vale-fixture" string count mismatches
        TOTAL=$(( TOTAL + INVALIDGAP ))
        if [ $TOTAL -lt 0 ]
        then
            TOTAL=$((TOTAL * -1))
        fi
        echo "$TOTAL ERROR(s) in $DIR/testinvalid.adoc / .vale/styles/$DIR.yml"
    fi
}

# This scripts runs the  suite for each rule in the `AsciiDoc` style.
TOTAL=0
for RULE in $(find .vale/styles/AsciiDoc -name '*.yml' | cut -d/ -f 3,4 | cut -d. -f1 | sort)
do
    RuleMarkup
done

# This scripts runs the  suite for each rule in the `OpenShiftAsciiDoc` style.
TOTAL=0
for RULE in $(find .vale/styles/OpenShiftAsciiDoc -name '*.yml' | cut -d/ -f 3,4 | cut -d. -f1 | sort)
do
    RuleMarkup
done

# This scripts runs the  suite for each rule in the `RedHat` style.
TOTAL=0
for RULE in $(find .vale/styles/RedHat/ -name '*.yml' | cut -d/ -f 4 | cut -d. -f1 | sort)
do  
    Rule
done

echo "$TOTAL tests to fix"
exit $TOTAL