#!/usr/bin/python

# Get a list of error terms from the Vale rules and generate a correspoding asiidoc reference.

import glob
import os
import re
import shutil
import wget, zipfile
import git
import yaml
import json
import sys

def main():

    try: 
        #initialize some variables
        git_repo = git.Repo(os.path.abspath(os.getcwd()), search_parent_directories=True)
        git_root = git_repo.git.rev_parse("--show-toplevel")
        rules_dir = git_root + '/.vale/styles/RedHat'
        temp_dir = git_root + '/tools/temp'
        ssg_zip_url = 'https://github.com/redhat-documentation/supplementary-style-guide/archive/refs/heads/master.zip'
        terms_files = ["TermsErrors.yml", "TermsSuggestions.yml", "TermsWarnings.yml"]
        adoc_dir = git_root + '/modules/reference-guide/partials'
        adoc_ref_files = ["ref_error_terms.adoc", "ref_suggestion_terms.adoc", "ref_usage_terms.adoc"]

        #grab the ssg source from github and unzip it to /temp
        get_ssg_source(temp_dir, ssg_zip_url)

        #scans ssg *.adoc files in terms and creates a list of each incorrect word usage type
        get_ssg_terms(temp_dir)

        #get the current vale rules terms
        get_vale_rule_terms(terms_files, temp_dir, rules_dir)

        #write the output asciidoc reference tables
        write_ref_tables(temp_dir, adoc_dir, "error")
        write_ref_tables(temp_dir, adoc_dir, "suggestion")

        #remove the temp folder                
        clean_up(temp_dir)

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

def clean_up(temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def clean_old_build(temp_dir):
    files = glob.glob(temp_dir + "/*")
    for f in files:
        os.remove(f)

def get_ssg_source(temp_dir, ssg_zip_url):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    os.chdir(temp_dir)
    r = wget.download(ssg_zip_url)
    with zipfile.ZipFile('supplementary-style-guide-master.zip', 'r') as zip_ref:
        zip_ref.extractall(temp_dir + '/')

def get_vale_rule_terms(terms_files, temp_dir, rules_dir):
    os.chdir(rules_dir)
    with open("vale_terms.json", "w+", encoding='utf-8') as out_file:
        #set up the list of dicts
        vale_terms_list = []
        for i in terms_files:
            with open(i, 'r+', encoding='utf-8') as f:
                yaml_data = yaml.safe_load(f)
                for key, value in yaml_data['swap'].items():
                    #print(f"{key}: {value}")
                    #set up the vale term dict
                    vale_term_dict = {}
                    vale_term_dict["vale_term"] = {}
                    vale_term_dict["vale_term"]["incorrect_term_regex"] = {}
                    vale_term_dict["vale_term"]["correct_term"] = {}
                    vale_term_dict["vale_term"]["rule_file"] = {}
                    #write the vale terms into the dict
                    vale_term_dict["vale_term"]["incorrect_term_regex"] = str(key)
                    vale_term_dict["vale_term"]["correct_term"] = str(value)
                    vale_term_dict["vale_term"]["rule_file"] = str(i)               
                    #append to the list
                    vale_terms_list.append(vale_term_dict)
        #serialize the json 
        vale_terms_json = json.dumps(vale_terms_list, indent = 4)
        out_file.write(vale_terms_json)
    shutil.move("./vale_terms.json", temp_dir + "/vale_terms.json")

def get_ssg_terms(temp_dir):
    os.chdir(temp_dir)
    with open("ssg_terms.json", "w+", encoding='utf-8') as out_file:
        #set up the list of dicts
        ssg_terms_list = []
        for in_file in glob.glob("**/*.adoc", recursive=True):
            #in_file_folder = os.path.dirname(in_file)
            with open(in_file, 'r+', encoding='utf-8') as w:
                data = w.read()
                data = re.findall(r'\[\[(.*)\]\]\n(====) (.*) \(.*\)\n\*Description\*: (.*)\n\n\*Use it\*: yes\n\n\*Incorrect forms\*: (.*)', data)
                for word_usage in data:
                    #set up the term dict
                    ssg_term_dict = {}
                    ssg_term_dict["ssg_term"] = {}
                    ssg_term_dict["ssg_term"]["word_id"] = {}
                    ssg_term_dict["ssg_term"]["correct_term"] = {}
                    ssg_term_dict["ssg_term"]["incorrect_forms"] = {}
                    #process the terms
                    word_id = word_usage[0]
                    correct_form = word_usage[2]
                    incorrect_forms = re.sub(r', ', '|', word_usage[4])
                    #clean out yes/no image refs
                    incorrect_forms = re.sub(r'image:images\/yes\.png\[yes\] ', '', incorrect_forms)
                    incorrect_forms = re.sub(r'image:images\/no\.png\[no\] ', '', incorrect_forms) 
                    correct_form = re.sub(r'image:images\/yes\.png\[yes\] ', '', correct_form)
                    correct_form = re.sub(r'image:images\/no\.png\[no\] ', '', correct_form)
                    #clean out other items
                    incorrect_forms = re.sub(r' \(capitalized\)', '', incorrect_forms)
                    incorrect_forms = re.sub(r', and so on', '', incorrect_forms)
                    incorrect_forms = re.sub(r' \(without trademark symbol\)', '', incorrect_forms)
                    incorrect_forms = re.sub(r' \(unless at the start of a sentence\).', '', incorrect_forms)
                    #clean regex special characters hack - this needs to be handled correctly
                    incorrect_forms = re.sub(r'\/', ' ', incorrect_forms)
                    incorrect_forms = re.sub(r'\^', '', incorrect_forms)
                    incorrect_forms = re.sub(r'\(', '\(', incorrect_forms)
                    incorrect_forms = re.sub(r'\)', '\)', incorrect_forms)
                    #write the terms into the dict
                    ssg_term_dict["ssg_term"]["word_id"] = word_id
                    ssg_term_dict["ssg_term"]["correct_term"] = correct_form
                    ssg_term_dict["ssg_term"]["incorrect_forms"] = incorrect_forms
                    #append to the list
                    ssg_terms_list.append(ssg_term_dict)
        #serialize the json 
        ssg_terms_json = json.dumps(ssg_terms_list, indent = 4)
        #print(ssg_terms_json)  
        out_file.write(ssg_terms_json)

def write_ref_tables(temp_dir, adoc_dir, error_type):
    if error_type == "error":
        rule_filename = "TermsErrors.yml"
        adoc_file = "ref_error_terms.adoc"
    #no warning terms in SSG?
    elif error_type == "warning":
        rule_filename = "TermsWarning.yml"
        adoc_file = "ref_warning_terms.adoc"
    elif error_type == "suggestion":
        rule_filename = "TermsSuggestions.yml"
        adoc_file = "ref_suggestion_terms.adoc"

    os.chdir(temp_dir)
    #invoke json.loads() on the contents of the file, not the file path
    with open("./ssg_terms.json", 'r') as s:
        ssg_contents = json.loads(s.read())
    with open("./vale_terms.json", 'r') as j:
        vale_contents = json.loads(j.read())
    #start writing
    os.chdir(adoc_dir)
    with open(adoc_file, 'w+', encoding='utf-8') as w:
        w.seek(0)
        #clean the previous version
        w.truncate()
        #start writing
        w.write(":_module-type: REFERENCE" + "\n")
        w.write("[id=\"ssg_vale_" + error_type + "_reference\"]" + "\n")
        w.write("= Vale " + error_type + " rule guidance" + "\n")
        w.write("\n")
        w.write("The following table lists incorrect terminology and the approved usage as outlined in the Red Hat Supplementary Style Guide." + "\n")
        w.write("\n")
        w.write(".Supplementary Style Guide terminology guidance" + "\n")
        w.write("[options=\"header\"]" + "\n")
        w.write("|====" + "\n")
        w.write("|Incorrect term|Correct term" + "\n")

        #for every line in the vale rules file, if a correspoding entry exists in ssg file, write a table row
        for line in vale_contents:
            correct_vale_term = line["vale_term"]["correct_term"]
            rule_file = line["vale_term"]["rule_file"]
            if rule_file == rule_filename:
                for line in ssg_contents:
                    if correct_vale_term == line["ssg_term"]["correct_term"]:
                        word_id = line["ssg_term"]["word_id"]
                        correct = line["ssg_term"]["correct_term"]
                        incorrect = line["ssg_term"]["incorrect_forms"]
                        #re.sub pipe char
                        incorrect = re.sub(r'\|', ' OR ', incorrect)
                        correct = re.sub(r'\|', ' OR ', correct)
                        w.write("\n")
                        w.write("|" + incorrect + "|" + "link:https://redhat-documentation.github.io/supplementary-style-guide/#" + word_id + "[" + correct + "]" + "\n")
        #close it out
        w.write("|====" + "\n")
        w.write("\n")

if __name__ == "__main__":
    main()
