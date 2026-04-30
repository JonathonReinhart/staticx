#!/bin/bash
if [ "${BASH_SOURCE[0]}" -ef "$0" ]
then
    echo "Usage: source ${BASH_SOURCE[0]}"
    exit 1
fi

echo -e "\nSetting up virtual environment..."
python3 -m venv venv || return $?
source venv/bin/activate || return $?

echo -e "\nInstalling dependencies..."
pip install --upgrade pip || return $?
pip install --group dev || return $?

echo -e "\nInstalling editable package..."
pip install -e . || return $?
