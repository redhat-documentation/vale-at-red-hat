#!/bin/sh
#
# Copyright (c) 2021 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#
# Loop on each git repository found on location given as argument, or current directory
find "${1:-.}" -name .git -print | sed 's@/.git@@' | sort | uniq | while read directory; 
do 
    echo "Generating report on $directory"
    # Provide a full list of files to report on
    # Ignore files containing a space, content in German, /deprecated/ and /Internal/ directories
    FILE_LIST=$(find "${directory}" -type f -name '*.adoc' -print | sed '/ /d;/de-de\.adoc/d;/\/deprecated\//d;/\/Internal\//d;/\/internal-resources\//d'| sort | uniq)
    REPORT_BASENAME=vale-report-$(basename "${directory}")
    # Create file list
    echo "$FILE_LIST" > "${REPORT_BASENAME}-list.log"
    # Count words in the corpus
    # shellcheck disable=SC2002,SC2086
    cat $FILE_LIST | wc -w  > "${REPORT_BASENAME}-wordcount.log"
    # Create Vale report
    # shellcheck disable=SC2086
    vale --output=JSON --no-exit $FILE_LIST > "$REPORT_BASENAME.json"
    # A minimal analyze
    jq .[][].Severity "$REPORT_BASENAME.json" | sort | uniq -c | sort -nr > "$REPORT_BASENAME.severity"
    jq .[][].Check "$REPORT_BASENAME.json" | sort | uniq -c | sort -nr > "$REPORT_BASENAME.rules"
done
