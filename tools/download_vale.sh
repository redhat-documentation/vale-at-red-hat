#!/bin/sh
#
# Copyright (c) 2021 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#
set -e

# Download latest vale release
gh release download --repo 'errata-ai/vale' --pattern '*Linux*.tar.gz'
tar -xf vale*
./vale -v

# Download latest vale configuration from vale-at-red-hat
curl -Os https://raw.githubusercontent.com/redhat-documentation/vale-at-red-hat/master/.vale.ini

# Download latest `RedHat` style
mkdir .vale/styles || true
cd .vale/styles
gh release download --repo 'redhat-documentation/vale-at-red-hat' --pattern 'RedHat.zip'
unzip RedHat.zip
