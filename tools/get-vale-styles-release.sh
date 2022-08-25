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

umask 002

# Get fresh Vale styles from GitHub release zip
cd "$HOME"
wget -q --timestamping -O ".vale.ini" https://raw.githubusercontent.com/redhat-documentation/vale-at-red-hat/main/.vale.ini
mkdir -p .vale/styles
cd .vale/styles || exit
rm -rf RedHat 
wget -q --timestamping https://github.com/redhat-documentation/vale-at-red-hat/releases/latest/download/RedHat.zip
unzip -q RedHat.zip
rm RedHat.zip
echo "vale-at-red-hat style installed to .vale/styles. Go lint!"
