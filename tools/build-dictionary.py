#!/usr/bin/env python3
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
# Usage: tools/build-dictionary.py [wordlist] [output.dic]
#
# The wordlist is a plain text file with one word per line.
# No hunspell flags needed — the script detects plural forms
# automatically and generates the appropriate /S, /P, /SP flags.
# Lowercase words automatically get a Title Case counterpart.

import os
import sys


def pluralize(word):
    """Generate the plural form of a word using the same rules as en_US-RedHat.aff."""
    if not word:
        return None
    last = word[-1]
    if len(word) >= 2:
        last2 = word[-2:]
    else:
        last2 = ""

    # consonant + y → ies
    if word.endswith("y") and len(word) >= 2 and word[-2] not in "aeiouAEIOU":
        return word[:-1] + "ies"
    # vowel + y → ys
    if word.endswith("y") and len(word) >= 2 and word[-2] in "aeiouAEIOU":
        return word + "s"
    # ends in s, x, z → es
    if last in "sxzSXZ":
        return word + "es"
    # ends in sh, ch → es
    if last2 in ("sh", "ch", "SH", "CH", "Sh", "Ch"):
        return word + "es"
    # ends in other h → s
    if last in "hH":
        return word + "s"
    # everything else → s
    return word + "s"


def make_possessive(word):
    """Generate the possessive form of a word."""
    if word.endswith("s") or word.endswith("S"):
        return word + "'"
    return word + "'s"


def title_case(word):
    """Capitalize first letter, keep rest unchanged."""
    if not word:
        return word
    return word[0].upper() + word[1:]


def detect_base_form(word, all_words_lower):
    """Check if a word is a plural form of another word in the set.

    Returns the base form if found, None otherwise.
    """
    w = word.lower()

    # Try: word ends in 'ies' → base is word[:-3] + 'y' (consonant+y rule)
    if w.endswith("ies") and len(w) > 3:
        base = w[:-3] + "y"
        if base in all_words_lower and len(base) >= 2 and base[-2] not in "aeiou":
            return base

    # Try: word ends in 'es' → base is word[:-2] (s/x/z/sh/ch rule)
    if w.endswith("es") and len(w) > 2:
        base = w[:-2]
        if base in all_words_lower:
            last = base[-1] if base else ""
            last2 = base[-2:] if len(base) >= 2 else ""
            if last in "sxz" or last2 in ("sh", "ch"):
                return base

    # Try: word ends in 's' → base is word[:-1] (general rule)
    if w.endswith("s") and not w.endswith("ss") and len(w) > 1:
        base = w[:-1]
        if base in all_words_lower:
            # Make sure the base would actually pluralize to this word
            if pluralize(base) == w:
                return base

    return None


def main():
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dict_dir = os.path.join(repo_root, ".vale", "styles", "config", "dictionaries")

    wordlist_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(dict_dir, "wordlist.txt")
    dic_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(dict_dir, "en_US-RedHat.dic")

    if not os.path.isfile(wordlist_path):
        print(f"Error: wordlist not found: {wordlist_path}", file=sys.stderr)
        sys.exit(1)

    # Read and clean wordlist
    words = set()
    with open(wordlist_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            words.add(line)

    # Build lowercase lookup for plural detection
    words_lower = {w.lower() for w in words}

    # Detect plurals: find words that are plural forms of other words
    plural_bases = {}  # base_lower -> set of original-case base forms
    plural_forms = set()  # words identified as plurals (to exclude)

    for word in sorted(words):
        base = detect_base_form(word, words_lower)
        if base:
            # Find the original-case version of the base
            base_originals = [w for w in words if w.lower() == base]
            if base_originals:
                for bo in base_originals:
                    plural_bases.setdefault(bo, set()).add(word)
                plural_forms.add(word)

    # Build output entries
    entries = set()

    for word in words:
        if word in plural_forms:
            # Skip — will be covered by base/S
            continue

        flags = set()

        # Check if this word has plural forms in the list
        if word in plural_bases:
            flags.add("S")

        # Add possessive for proper nouns (capitalized words)
        if word[0].isupper():
            flags.add("P")

        # Build the entry
        if flags:
            flag_str = "/" + "".join(sorted(flags, key="SP".index))
        else:
            flag_str = ""

        entries.add(f"{word}{flag_str}")

        # Auto-generate Title Case for lowercase-starting words
        if word[0].islower():
            titled = title_case(word)
            # Title case version gets P (possessive) since it's capitalized
            if "S" in flags:
                entries.add(f"{titled}/SP")
            else:
                entries.add(f"{titled}/P")

    # Sort with C locale ordering (uppercase before lowercase)
    sorted_entries = sorted(entries, key=lambda x: x.encode("utf-8"))

    # Write output
    with open(dic_path, "w") as f:
        f.write(f"{len(sorted_entries)}\n")
        for entry in sorted_entries:
            f.write(f"{entry}\n")

    print(f"Generated {len(sorted_entries)} entries in {dic_path}")
    if plural_bases:
        plural_count = sum(len(v) for v in plural_bases.values())
        print(f"  Consolidated {plural_count} plural forms into {len(plural_bases)} base entries with /S flag")


if __name__ == "__main__":
    main()
