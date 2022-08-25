#!/bin/sh
#
# Copyright (c) 2021 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#

# Fail on errors
set -e
# Enable user to delete created files afterwards
umask 002
# Get Vale styles
# ./tools/get-vale-styles.sh
# Build Antora website
LIVERELOAD=true gulp
