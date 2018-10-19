#!/bin/bash
# Purpose: custom script that prepares user environment and execute the release build

addgroup --gid=$LOC_GID build
adduser --system --home=$RELEASE_BUILD_DIR --no-create-home --uid=$LOC_UID --gid=$LOC_GID build

sudo -H -E -u build bash << EOF
./build-release.sh $@
EOF
