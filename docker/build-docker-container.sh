#!/bin/bash

DOCKERFILE_DIR=`dirname $0`
docker build -t braiins-os-builder $DOCKERFILE_DIR
