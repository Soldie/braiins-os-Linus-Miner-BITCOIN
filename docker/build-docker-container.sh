#!/bin/bash

set -e

DOCKERFILE_DIR=$(dirname "$0")
USER_UID=$(id -u)
USER_GID=$(id -g)

docker_dir=$(mktemp -d)
cp "./$DOCKERFILE_DIR/Dockerfile" "$docker_dir"
cp "./$DOCKERFILE_DIR/bashrc" "$docker_dir"
cp "./requirements.txt" "$docker_dir"

md5sum "./requirements.txt" > "$docker_dir/requirements.md5"

docker build --build-arg LOC_UID=$USER_UID --build-arg LOC_GID=$USER_GID \
    -t $USER/bos-builder "$docker_dir"

rm -fr "$docker_dir"
