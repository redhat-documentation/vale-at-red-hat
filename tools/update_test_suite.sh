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

# This scripts creates and maintains a default test suite for each

for RULE in $(find .vale/styles/RedHat/ -name '*.yml' | cut -d/ -f 4 | cut -d. -f1 | sort)
do
    RULETESTDIR=".vale/fixtures/RedHat/$RULE"
    test -d $RULETESTDIR || mkdir "$RULETESTDIR"
    touch "$RULETESTDIR/testinvalid.adoc"
    touch "$RULETESTDIR/testvalid.adoc"
    cat <<EOF > "$RULETESTDIR/.vale.ini"
; Vale configuration file to test the \`$RULE\` rule
StylesPath = ../../../styles
MinAlertLevel = suggestion
[*.adoc]
RedHat.$RULE = YES
EOF
    
done
