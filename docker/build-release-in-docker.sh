#!/bin/bash

set -e

RELEASE_BUILD_DIR=/src
DOCKER_SSH_AUTH_SOCK=/ssh-agent
USER_NAME=build

if [ $# -eq 0 ]; then
    echo "Warning: Missing build release parameters!"
    echo "Running only braiins OS build environment..."
else
    ARGS="./build-release.sh $@"
fi

docker run -it --rm \
    -v $HOME/.ssh/known_hosts:/home/$USER_NAME/.ssh/known_hosts:ro \
    -v $SSH_AUTH_SOCK:$DOCKER_SSH_AUTH_SOCK -e SSH_AUTH_SOCK=$DOCKER_SSH_AUTH_SOCK \
    -v $PWD:$RELEASE_BUILD_DIR -w $RELEASE_BUILD_DIR \
    -e RELEASE_BUILD_DIR=$RELEASE_BUILD_DIR \
    $USER/bos-builder $ARGS
