#!/usr/bin/python

#Import functions from ssg_lib.py
from ssg_lib import *


#Compares SSG glossary entries to Vale rules fixtures and outputs anything in the SSG that is not covered by the Vale fixtures. Writes the results as Vale swap terms in the form "bad: good" to the file ssg_utils/missing_ssg_terms.json. 
def main():

    #initialize some variables
    git_repo = git.Repo(os.path.abspath(os.getcwd()), search_parent_directories=True)
    git_root = git_repo.git.rev_parse("--show-toplevel")
    rules_dir = git_root + '/.vale/styles/RedHat'
    fixtures_dir = git_root + '/.vale/fixtures/RedHat'
    temp_dir = git_root + '/tools/ssg_utils/temp'
    ssg_zip_url = 'https://github.com/redhat-documentation/supplementary-style-guide/archive/refs/heads/main.zip'
    adoc_dir = git_root + '/modules/reference-guide/partials'
    adoc_ref_files = ["ref_error_terms.adoc", "ref_suggestion_terms.adoc", "ref_usage_terms.adoc"]

    #grab the ssg source from github and unzip it to /temp
    get_ssg_source(temp_dir, ssg_zip_url)

    #scans ssg *.adoc files in terms and creates a list of incorrect word usages
    get_ssg_terms(temp_dir)

    #get the current vale rules terms
    get_vale_rule_terms(temp_dir, rules_dir)

    #get the current vale rules test fixture terms
    get_vale_fixture_terms(temp_dir, fixtures_dir)

    #check for new SSG entries that are potentially not included in the vale rules
    check_new_ssg_entries(temp_dir, rules_dir, git_root)

    #remove the temp folder
    clean_up(temp_dir)

if __name__ == "__main__":
    main()