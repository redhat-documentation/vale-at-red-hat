// 
// Copyright(c) 2021 Red Hat, Inc.
// This program and the accompanying materials are made
// available under the terms of the Eclipse Public License 2.0
// which is available at https://www.eclipse.org/legal/epl-2.0/
// 
//  SPDX - License - Identifier: EPL - 2.0
// 
'use strict'

const connect = require('gulp-connect')
const util = require('util');
const exec = util.promisify(require('child_process').exec);
const fs = require('fs')
const generator = require('@antora/site-generator')
const { reload: livereload } = process.env.LIVERELOAD === 'true' ? require('gulp-connect') : {}
const { parallel, series, src, watch } = require('gulp')
const yaml = require('js-yaml')

const playbookFilename = 'antora-playbook.yml'
const playbook = yaml.load(fs.readFileSync(playbookFilename, 'utf8'))
const outputDir = (playbook.output || {}).dir || './build'
const serverConfig = { name: 'Preview Site', livereload, host: '0.0.0.0', port: 4000, root: outputDir }
const antoraArgs = ['--playbook', playbookFilename]
const watchPatterns = playbook.content.sources.filter((source) => !source.url.includes(':')).reduce((accum, source) => {
    accum.push(`.vale/**/*`)
    accum.push(`./antora-playbook.yml`)
    accum.push(`./antora.yml`)
    accum.push(`./gulpfile.js`)
    accum.push(`./modules/**/*`)
    accum.push(`./supplemental-ui/**/*`)
    return accum
}, [])

// Antora for modular docs functions

// Generate Antora website
function generate_html(done) {
    generator(antoraArgs, process.env)
        .then(() => done())
        .catch((err) => {
            console.log(err)
            done()
        })
}

// Run web server
async function serve(done) {
    connect.server(serverConfig, function () {
        this.server.on('close', done)
        watch(watchPatterns, series(
            generate_reference_guide,
            generate_vale_rule_tests,
            generate_html,
            validate_language_changes,
            validate_links,
            validate_shell_scripts,
            validate_vale_rules,
        ))
        if (livereload) watch(this.root).on('change', (filepath) => src(filepath, { read: false }).pipe(livereload()))
    })
}

async function validate_language_changes() {
    // Report links errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/validate-language-changes.sh 2>&1')
        console.log(stdout, stderr);
    }
    catch (error) {
        console.log(error.stdout, error.stderr);
        return;
    }
}

async function validate_links() {
    // Report links errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('htmltest 2>&1')
        console.log(stdout, stderr);
    }
    catch (error) {
        console.log(error.stdout, error.stderr);
        return;
    }
}

async function validate_shell_scripts() {
    // Report shellcheck errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/validate-shell-scripts.sh 2>&1')
        console.log(stdout, stderr);
    }
    catch (error) {
        console.log(error.stdout, error.stderr);
        return;
    }
}

// Functions specific to this repository

// Validate vale rules
async function validate_vale_rules() {
    // Report errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/validate-vale-rules.sh')
        console.log(stdout, stderr);
    }
    catch (error) {
        console.log(error.stdout, error.stderr);
        return;
    }
}


// Generate reference guide
async function generate_reference_guide() {
    // Report errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/generate-reference-guide.sh')
        console.log(stdout, stderr);
    }
    catch (error) {
        console.log(error.stdout, error.stderr);
        return;
    }
}

// Generate vale rules tests
async function generate_vale_rule_tests() {
    // Report links errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/generate-vale-rule-tests.sh')
        console.log(stdout, stderr);
    }
    catch (error) {
        console.log(error.stdout, error.stderr);
        return;
    }
}

exports.default = series(
    parallel(
        generate_reference_guide,
        generate_vale_rule_tests
    ),
    generate_html,
    serve,
    parallel(
        validate_language_changes,
        validate_links,
        validate_shell_scripts,
        validate_vale_rules,
    )
);
