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
    INVALIDGAP=$(($INVALIDLINES - $INVALIDALERTS))
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

# This scripts runs the  suite for each rule in the `RedHat` style.
TOTAL=0
for RULE in $(find .vale/styles/RedHat/ -name '*.yml' | cut -d/ -f 4 | cut -d. -f1 | sort)
do  
    Rule
done

echo "$TOTAL tests to fix"
exit $TOTAL