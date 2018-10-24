#!/bin/bash

release_build_dir=/src
docker run --env RELEASE_BUILD_DIR=$release_build_dir --env LOC_UID=`id -u` --env LOC_GID=`id -g` --volume $HOME/.ssh/known_hosts:$release_build_dir/.ssh/known_hosts:ro --volume $SSH_AUTH_SOCK:/ssh-agent --volume\
       ${PWD}:/src -w /src --env SSH_AUTH_SOCK=/ssh-agent -ti braiins-os-builder docker/build-release-as-local-uid.sh $@
