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

# This scripts creates a default reference page for each rule and updates the Reference guide navigation.

createPage() {
    echo "Creating $PAGEFULLPATH"
    MESSAGE=$(grep "^message:" ".vale/styles/RedHat/$RULE.yml" | cut -d'"' -f2 | sed "s/%s/${RULE}/;s/'/\`/g")
    ADDITIONAL=''
    LINK=$(grep "^source:" ".vale/styles/RedHat/$RULE.yml" | cut -d' ' -f2 | sed "s/'//g;s/\"//g")
    if [ -n "$LINK" ]
    then ADDITIONAL=".Additional Resources

* link:${LINK}[]"
    fi

PAGECONTENT=":navtitle: $RULE
:keywords: reference, rule, $RULE

= $RULE

$MESSAGE

$ADDITIONAL

"
    # cat "$PAGECONTENT" > "$PAGEFULLPATH"

}

for RULE in $(find .vale/styles/RedHat/ -name '*.yml' | cut -d/ -f 4 | cut -d. -f1 | sort)
do
    # Page name: from CamelCase to lowercase
    PAGENAME=$(echo "$RULE" | tr '[:upper:]' '[:lower:]' )
    PAGEFULLPATH="modules/reference-guide/pages/$PAGENAME.adoc"
    if [ ! -f "$PAGEFULLPATH" ]
    then
        createPage
    fi
    NAVCONTENT="$NAVCONTENT
* xref:$PAGENAME.adoc[]"
done

printf ".xref:reference-guide.adoc[Reference guide]\n%s" "$NAVCONTENT" > "modules/reference-guide/nav.adoc"
