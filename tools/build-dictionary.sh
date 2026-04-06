#!/bin/sh
#
# Copyright (c) 2021 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#
# Builds en_US-RedHat.dic from wordlist.txt.
#
# Usage: tools/build-dictionary.sh [wordlist] [output.dic]
#
# The wordlist is a plain text file with one word per line, optional
# affix flags (/S, /P, /SP), comments (#), and blank lines.
# Lowercase words automatically get a Title Case counterpart in the
# output dictionary.

set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DICT_DIR="$REPO_ROOT/.vale/styles/config/dictionaries"

WORDLIST="${1:-$DICT_DIR/wordlist.txt}"
DIC_FILE="${2:-$DICT_DIR/en_US-RedHat.dic}"

if [ ! -f "$WORDLIST" ]; then
    echo "Error: wordlist not found: $WORDLIST" >&2
    exit 1
fi

TMP_FILE="$(mktemp)"
trap 'rm -f "$TMP_FILE"' EXIT

# Process wordlist:
# - Strip comment lines and blank lines
# - For lowercase-starting words, also emit a Title Case version
awk '
/^[[:space:]]*#/ { next }
/^[[:space:]]*$/ { next }
{
    # Trim whitespace
    gsub(/^[[:space:]]+|[[:space:]]+$/, "")
    if ($0 == "") next

    print $0

    # Split word from flags at first /
    slash = index($0, "/")
    if (slash > 0) {
        word = substr($0, 1, slash - 1)
        flags = substr($0, slash)
    } else {
        word = $0
        flags = ""
    }

    # Auto-generate Title Case for lowercase-starting words
    first = substr(word, 1, 1)
    if (first >= "a" && first <= "z") {
        print toupper(first) substr(word, 2) flags
    }
}
' "$WORDLIST" | LC_ALL=C sort -u > "$TMP_FILE"

# Prepend word count and write final dic
COUNT=$(wc -l < "$TMP_FILE")
{
    echo "$COUNT"
    cat "$TMP_FILE"
} > "$DIC_FILE"

echo "Generated $COUNT entries in $DIC_FILE"
