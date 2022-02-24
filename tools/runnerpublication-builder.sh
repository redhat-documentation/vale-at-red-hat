#!/bin/sh
#
# Copyright (c) 2022 Red Hat, Inc.
# This program and the accompanying materials are made
# available under the terms of the Eclipse Public License 2.0
# which is available at https://www.eclipse.org/legal/epl-2.0/
#
# SPDX-License-Identifier: EPL-2.0
#

# Detect available runner
if command -v podman > /dev/null
  then RUNNER=podman
elif command -v docker > /dev/null
  then RUNNER=docker
else echo "No installation of podman or docker found in the PATH" ; exit 1
fi

# Fail on errors
set -e

if [ -z "$IMAGE" ]
then
  IMAGE="quay.io/antoraformodulardocs/antora-for-modular-docs:main"
  echo "Pulling $IMAGE. To use a different container image, set the IMAGE environment variable"
  ${RUNNER} pull -q ${IMAGE}
fi

# Display commands
set -x

${RUNNER} run --rm -ti \
  --name "${PWD##*/}" \
  -v "$PWD:/projects:z" -w /projects \
  --entrypoint="./tools/publication-builder.sh" \
  -p 4000:4000 -p 35729:35729 \
  "quay.io/antoraformodulardocs/antora-for-modular-docs"

