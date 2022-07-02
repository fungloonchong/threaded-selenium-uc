#!/bin/bash

basePath=$(dirname $(readlink -f ${BASH_SOURCE}))
cd "${basePath}"

python3 -m venv . && \
source ./bin/activate && \
pip3 install -r requirements.txt && \
python3 main.py
