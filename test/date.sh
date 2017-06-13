#!/bin/bash
set -e
outfile=./date.staticx

echo -e "\n\nTest StaticX against 'date'"

cd "$(dirname "${BASH_SOURCE[0]}")"


echo -e "\nRunning 'date':"
date

echo -e "\nMaking staticx executable:"
staticx $(which date) $outfile

echo -e "\nRunning staticx executable"
$outfile

if [ -n "$TEST_DOCKER_IMAGE" ]; then
    echo -e "\nRunning staticx executable under $TEST_DOCKER_IMAGE"
    scuba --image $TEST_DOCKER_IMAGE $outfile
fi
