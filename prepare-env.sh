#!/bin/bash

set -e

#DRY_RUN=echo
VENV=.pybuildenv

rm -rf $VENV

$DRY_RUN virtualenv --python=/usr/bin/python3.5 $VENV
$DRY_RUN source $VENV/bin/activate
$DRY_RUN pip3 install -r requirements.txt
