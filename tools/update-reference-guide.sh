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
    echo "Creating $PAGE"
    MESSAGE=$(grep "^message:" ".vale/styles/RedHat/$RULE.yml" | cut -d'"' -f2 | sed "s/%s/${RULE}/")
    LINK=$(grep "^link:" ".vale/styles/RedHat/$RULE.yml" | cut -d' ' -f2 | sed "s/'//g;s/\"//g")
    if [ ! -z "$LINK" ]
    then local ADDITIONAL=".Additional Resources

* link:${LINK}[]"
    fi

    cat <<EOF > "$PAGE"
:navtitle: $RULE
:keywords: reference, rule, $RULE

= $RULE

$MESSAGE

$ADDITIONAL

EOF
}

for RULE in $(find .vale/styles/RedHat/ -name '*.yml' | cut -d/ -f 4 | cut -d. -f1 | sort)
do
    PAGE="modules/reference-guide/pages/$RULE.adoc"
    if [ ! -f "$PAGE" ]
    then
        createPage
    fi
    NAVCONTENT="$NAVCONTENT
* xref:$RULE.adoc[]"
done

printf ".xref:reference-guide.adoc[Reference guide]\n%s" "$NAVCONTENT" > "modules/reference-guide/nav.adoc"
