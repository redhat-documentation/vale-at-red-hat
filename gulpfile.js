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

const playbookFilename = 'antora-playbook-for-development.yml'
const playbook = yaml.load(fs.readFileSync(playbookFilename, 'utf8'))
const outputDir = (playbook.output || {}).dir || './build/site'
const serverConfig = { name: 'Preview Site', livereload, host: '0.0.0.0', port: 4000, root: outputDir }
const antoraArgs = ['--playbook', playbookFilename]
const watchPatterns = playbook.content.sources.filter((source) => !source.url.includes(':')).reduce((accum, source) => {
    accum.push(`./antora.yml`)
    accum.push(`./modules/**/*`)
    accum.push(`.vale/**/*`)
    return accum
}, [])

function generate_html(done) {
    generator(antoraArgs, process.env)
        .then(() => done())
        .catch((err) => {
            console.log(err)
            done()
        })
}

async function generate_reference_guide() {
    // Report errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/generate_reference_guide.sh')
        console.log(stdout);
        console.error(stderr);
    }
    catch (error) {
        console.log(error.stdout);
        console.log(error.stderr);
        return;
    }
}

async function generate_vale_rule_tests() {
    // Report links errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/generate_vale_rule_tests.sh')
        console.log(stdout);
        console.error(stderr);
    }
    catch (error) {
        console.log(error.stdout);
        console.log(error.stderr);
        return;
    }
}

async function serve(done) {
    connect.server(serverConfig, function () {
        this.server.on('close', done)
        watch(watchPatterns, series(generate_reference_guide, generate_vale_rule_tests, generate_html, test_html, test_vale_rules))
        if (livereload) watch(this.root).on('change', (filepath) => src(filepath, { read: false }).pipe(livereload()))
    })
}

async function test_vale_rules() {
    // Report errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('./tools/test_vale_rules.sh')
        console.log(stdout);
        console.error(stderr);
    }
    catch (error) {
        console.log(error.stdout);
        console.log(error.stderr);
        return;
    }
}

async function test_html() {
    // Report errors but don't make gulp fail.
    try {
        const { stdout, stderr } = await exec('htmltest')
        console.log(stdout);
        console.error(stderr);
    }
    catch (error) {
        console.log(error.stdout);
        console.log(error.stderr);
        return;
    }
}

exports.default = series(
    parallel(generate_reference_guide, generate_vale_rule_tests),
    generate_html,
    serve,
    parallel(test_vale_rules, test_html)
);
