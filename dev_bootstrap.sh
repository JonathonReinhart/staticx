#!/bin/bash
if [ "${BASH_SOURCE[0]}" -ef "$0" ]
then
    echo "Usage: source ${BASH_SOURCE[0]}"
    exit 1
fi

python3 -m venv venv || return $?
source venv/bin/activate || return $?
pip install -r requirements.txt || return $?
pip install -e . || return $?
