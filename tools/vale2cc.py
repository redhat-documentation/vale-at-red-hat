#!/usr/bin/env python
"""
This script takes Vale's JSON output from stdin, and converts it to a format
that GitLab will accept to generate & display code quality reports.
"""

import json, sys, hashlib, linecache

# This maps between Vale's severity output and what GitLab will accept.
severity_map = {
    "suggestion": "info",
    "warning": "minor",
    "error": "critical"
}

vale_json = json.load(sys.stdin)
output = []

for filename in vale_json:
    issues = vale_json[filename]

    for issue in issues:
        description = issue["Message"]

        if issue["Link"]:
            description += f" See: {issue['Link']}"

        line_no = issue["Line"]
        column = issue["Span"]
        severity = issue["Severity"]

        raw_line = linecache.getline(filename, line_no).strip()

        # The fingerprint is a hash used by GitLab to keep track of each issue
        # detected by Vale, in order to compare the source/target branch
        # during reporting.
        fingerprint_raw = f"{filename}:{raw_line}:{description}:{column[0]}:{column[1]}"
        fingerprint_encoded = hashlib.sha1(fingerprint_raw.encode()).hexdigest()

        output.append({
            "description": description,
            "fingerprint": fingerprint_encoded,
            "severity": issue["Severity"],
            "location": {
                "path": filename,
                "positions": {
                    "begin": {
                        "line": line_no,
                        "column": column[0]
                    },
                    "end": {
                        "line": line_no,
                        "column": column[1]
                    }
                }
            }
        })

print(json.dumps(output))