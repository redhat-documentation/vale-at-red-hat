#!/usr/bin/python

# Various Python functions for parsing the Red Hat Supplementary Style Guide glossary
# https://github.com/redhat-documentation/supplementary-style-guide

import glob
import os
import re
import shutil
import wget, zipfile
import git
import yaml
import json
import sys

def clean_up(temp_dir):
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)

def get_ssg_source(temp_dir, ssg_zip_url):
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir, exist_ok=True)
    os.chdir(temp_dir)
    r = wget.download(ssg_zip_url)
    with zipfile.ZipFile('supplementary-style-guide-main.zip', 'r') as zip_ref:
        zip_ref.extractall(temp_dir + '/')

def get_vale_rule_terms(temp_dir, rules_dir):
    os.chdir(rules_dir)
    with open("vale_terms.json", "w+", encoding='utf-8') as out_file:
        #set up the list of dicts
        vale_terms_list = []
        for file in os.listdir(rules_dir):
            if file.endswith('.yml'):
                with open(file, 'r+', encoding='utf-8') as f:
                    yaml_data = yaml.safe_load(f)
                    for key, value in yaml_data.items():
                        if 'swap' in key:
                            for key, value in yaml_data['swap'].items():
                                #print(f"{key}: {value}")
                                #set up the vale term dict
                                vale_term_dict = {}
                                vale_term_dict["term"] = {}
                                vale_term_dict["term"]["correct_term"] = {}                                
                                vale_term_dict["term"]["incorrect_term_regex"] = {}
                                vale_term_dict["term"]["rule_file"] = {}
                                #write the vale terms into the dict
                                vale_term_dict["term"]["incorrect_term_regex"] = str(key)
                                vale_term_dict["term"]["correct_term"] = str(value)
                                vale_term_dict["term"]["rule_file"] = str(file)               
                                #append to the list
                                vale_terms_list.append(vale_term_dict)
        #serialize the json 
        vale_terms_json = json.dumps(vale_terms_list, indent = 4)
        out_file.write(vale_terms_json)
    shutil.move("./vale_terms.json", temp_dir + "/vale_terms.json")

def get_vale_fixture_terms(temp_dir, fixtures_dir):
    os.chdir(fixtures_dir)
    with open("fixture_terms.json", "w+", encoding='utf-8') as out_file:
        vale_fixtures_list = []
        for file in glob.glob("**/*.adoc", recursive=True):
            with open(file, 'r+', encoding='utf-8') as w:
                lines = w.read().splitlines()
                for line in lines:
                    #append to the list
                    vale_fixtures_list.append(line)
        #serialize the json 
        fixtures_json = json.dumps(vale_fixtures_list, indent = 4)
        out_file.write(fixtures_json)
    shutil.move("./fixture_terms.json", temp_dir + "/fixture_terms.json")

def get_ssg_terms(temp_dir):
    os.chdir(temp_dir)
    with open("ssg_terms.json", "w+", encoding='utf-8') as out_file:
        #set up the list of dicts
        ssg_terms_list = []
        for file in glob.glob("**/*.adoc", recursive=True):
            #file_folder = os.path.dirname(file)
            with open(file, 'r+', encoding='utf-8') as w:
                data = w.read()
                data = re.findall(r'\[\[(.*)\]\]\n(====) (.*) \(.*\)\n\*Description\*: (.*)\n\n\*Use it\*: yes\n\n\*Incorrect forms\*: (.*)', data)
                for word_usage in data:
                    #set up the term dict
                    ssg_term_dict = {}
                    ssg_term_dict["term"] = {}
                    ssg_term_dict["term"]["correct_term"] = {}
                    ssg_term_dict["term"]["word_id"] = {}
                    ssg_term_dict["term"]["incorrect_forms"] = {}
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
                    incorrect_forms = re.sub(r'^.*xref.*$', '', incorrect_forms)
                    #clean regex special characters hack - this needs to be handled correctly
                    incorrect_forms = re.sub(r'\/', ' ', incorrect_forms)
                    incorrect_forms = re.sub(r'\^', '', incorrect_forms)
                    incorrect_forms = re.sub(r'\(', '\\(', incorrect_forms)
                    incorrect_forms = re.sub(r'\)', '\\)', incorrect_forms)
                    #write the terms into the dict
                    ssg_term_dict["term"]["word_id"] = word_id
                    ssg_term_dict["term"]["correct_term"] = correct_form
                    ssg_term_dict["term"]["incorrect_forms"] = incorrect_forms
                    #append to the list
                    ssg_terms_list.append(ssg_term_dict)
        #serialize the json 
        ssg_terms_json = json.dumps(ssg_terms_list, indent = 4)
        #print(ssg_terms_json)  
        out_file.write(ssg_terms_json)

def write_ref_tables(temp_dir, adoc_dir):
    os.chdir(temp_dir)
    #invoke json.loads() on the contents of the file, not the file path
    with open("./ssg_terms.json", 'r') as s:
        ssg_contents = json.loads(s.read())
    with open("./vale_terms.json", 'r') as j:
        vale_contents = json.loads(j.read())
    #start writing
    os.chdir(adoc_dir)
    with open('/home/aireilly/vale-at-red-hat/modules/reference-guide/partials/ref_error_terms.adoc', 'w+', encoding='utf-8') as w:
        w.seek(0)
        #clean the previous version
        w.truncate()
        #start writing
        w.write(":_module-type: REFERENCE" + "\n")
        w.write("[id=\"ssg_vale_" + "error" + "_reference\"]" + "\n")
        w.write("= Vale " + "error" + " rules" + "\n")
        w.write("\n")
        #Add scope escaping for generated terms
        w.write("pass:[<!-- vale RedHat.CaseSensitiveTerms = NO -->]" + "\n")
        w.write("pass:[<!-- vale RedHat.TermsErrors = NO -->]" + "\n")
        w.write("\n")
        w.write(".Supplementary Style Guide terminology guidance" + "\n")
        w.write("[options=\"header\"]" + "\n")
        w.write("|====" + "\n")
        w.write("|Incorrect term|Correct term" + "\n")

        #for every line in the vale rules file, if a correspoding entry exists in ssg file, write a table row
        for line in vale_contents:
            correct_vale_term = line["term"]["correct_term"]
            rule_file = line["term"]["rule_file"]
            for line in ssg_contents:
                if correct_vale_term == line["term"]["correct_term"]:
                    word_id = line["term"]["word_id"]
                    correct = line["term"]["correct_term"]
                    incorrect = line["term"]["incorrect_forms"]
                    #re.sub pipe char
                    incorrect = re.sub(r'\|', ' \\| ', incorrect)
                    correct = re.sub(r'\|', ' \\| ', correct)
                    #re.sub escaped brackets
                    incorrect = re.sub(r'\\\(', '(', incorrect)
                    incorrect = re.sub(r'\\\)', ')', incorrect)
                    correct = re.sub(r'\\\(', '(', correct)
                    correct = re.sub(r'\\\)', ')', correct)
                    #handle noun, adj, verb
                    if bool(re.search('(-adj)$', word_id)):
                        grammar_type = ' (as an adjective)'
                    elif bool(re.search('(-n)$', word_id)):
                        grammar_type = ' (as a noun)'
                    elif bool(re.search('(-v)$', word_id)):
                        grammar_type = ' (as a verb)'
                    else:
                        grammar_type = ''

                    w.write("\n")
                    w.write("|" + incorrect + "|" + "link:https://redhat-documentation.github.io/supplementary-style-guide/#" + word_id + "[" + correct + grammar_type + "]" + "\n")
        w.write("|====" + "\n")
        w.write("\n")

def check_new_ssg_entries(temp_dir, adoc_dir, git_root):
    os.chdir(temp_dir)
    with open("missing_terms.json", "w+", encoding='utf-8') as out_file:
        with open("./ssg_terms.json", 'r') as s:
            ssg_contents = json.loads(s.read())
        with open("./fixture_terms.json", 'r') as j:
            fixture_contents = json.loads(j.read())
        #compare terms from the Vale fixtures and SSG JSON files
        ssg_terms_list = []
        terms_diff = []
        missing_terms = []
        for i in ssg_contents:
            ssg_terms_list.append(i["term"]["correct_term"])
        terms_diff = [x for x in ssg_terms_list if x not in fixture_contents]
        for i in terms_diff:
            for j in ssg_contents:
                if i == j["term"]["correct_term"]:
                    missing_term = (j["term"]["incorrect_forms"] + ': ' + i)
                    missing_terms.append(missing_term)
        #serialize the json 
        missing_terms_json = json.dumps(missing_terms, indent = 4)
        out_file.write(missing_terms_json)
        shutil.move("./missing_terms.json", git_root + "/tools/ssg_utils/missing_ssg_terms.json")