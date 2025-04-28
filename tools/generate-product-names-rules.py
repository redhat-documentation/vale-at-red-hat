from collections import defaultdict
from oauth2client.service_account import ServiceAccountCredentials
from pathlib import Path
import gspread
import re
import shutil

# Setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Config
sheet_id = "1Q9sWlCu6jkQrHlapMflaWbP25RZsWFNzbsOdXbrpe6M"
sheet_name = "Components, portals, tools, and operators"

# Fetch sheet
sheet = client.open_by_key(sheet_id).worksheet(sheet_name)
json_data = sheet.get_all_records()

# Define explanatory phrases to remove
phrases_to_remove = [
    " Always use the full name to avoid confusion with open source community/project",
    "Red Hat Java OpenJDK trademark is OWNED BY ORACLE with a fair-use clause. Therefore",
    "we cannot use “Red Hat OpenJDK”. We MUST be very careful about how we use this!",
    " Always use the full name to avoid confusion with the primary VMware Tanzu project."
]

def should_exclude(text):
    return not text or text.strip() in ["", "-"] or text.strip().startswith(("Note:", "(Note:", "(Do not use"))

def clean_explanatory_text(text):
    text = re.sub(r'\s*\([^)]*\)\s*', ' ', text)
    text = re.sub(r'\+', r'\\+', text)
    for phrase in phrases_to_remove:
        text = text.replace(phrase, '')
    return re.sub(r'\s+', ' ', text).strip(' ,.;:')

def quote_if_needed(text):
    return f"'{text}'" if "," in text or ":" in text else text

def parse_unapproved_terms(bad_forms_text):
    if not bad_forms_text or bad_forms_text.strip() == "-":
        return []
    lines = [line.strip() for line in bad_forms_text.split('\n') if line and not line.startswith(("Note:", "(Note:"))]
    if not lines:
        return []
    terms_text = ' '.join(lines)
    terms, current_term, paren_level = [], "", 0
    for char in terms_text:
        if char == '(':
            paren_level += 1
        elif char == ')':
            paren_level -= 1
        if char == ',' and paren_level == 0:
            terms.append(current_term.strip())
            current_term = ""
        else:
            current_term += char
    if current_term.strip():
        terms.append(current_term.strip())
    return [clean_explanatory_text(term) for term in terms if not should_exclude(term)]

def get_group_key(name):
    if not name or not name.strip():
        return None
    first = name.strip()[0].upper()
    if first in "AB": return "AB"
    if first in "CD": return "CD"
    if first in "EFGH": return "EH"
    if first in "IJKL": return "IL"
    if first in "MNOPQ": return "MQ"
    if first in "R": return "R"
    if first in "ST": return "ST"
    if first in "UVW": return "UW"
    if first in "XYZ": return "XZ"
    return None

group_rules = {k: [] for k in ["AB", "CD", "EH", "IL", "MQ", "R", "ST", "UW", "XZ"]}

def vale_header():
    return [
        "---",
        "extends: substitution",
        "ignorecase: false",
        "level: error",
        "link: https://docs.google.com/spreadsheets/d/1DLS_lS3VKidgZIvcLmLp9BoiqptkvqHWfe1D5FD2kfk/edit?gid=1375785039#gid=1375785039",
        "message: \"Use the approved product name '%s' rather than '%s'.\"",
        "action:",
        "  name: replace",
        "# swap maps tokens in form of bad: good",
        "swap:"
    ]

replacement_groups = defaultdict(list)
for entry in json_data:
    name = entry.get("Name", "").strip()
    group = get_group_key(name)
    if name and name != "-" and group:
        bad_terms = parse_unapproved_terms(entry.get("Unapproved short forms\n& acronyms - DO NOT USE", ""))
        for bad in bad_terms:
            replacement_groups[(group, name)].append(bad)

for (group, replacement), bad_terms in replacement_groups.items():
    if not bad_terms:
        continue
    seen = set()
    unique_bad_terms = [t for t in bad_terms if t not in seen and not seen.add(t)]
    if unique_bad_terms:
        if len(unique_bad_terms) == 1:
            bad = quote_if_needed(unique_bad_terms[0])
        else:
            bad = quote_if_needed('|'.join(unique_bad_terms))
        good = quote_if_needed(replacement)
        group_rules[group].append(f"  {bad}: {good}")

# Write to files
dest_dir = Path("../.vale/styles/RedHatProductNames")
dest_dir.mkdir(parents=True, exist_ok=True)
for group, rules in group_rules.items():
    if rules:
        output_file = dest_dir / f"ProductNames{group}.yml"
        content = vale_header() + rules
        output_file.write_text("\n".join(content), encoding="utf-8")
