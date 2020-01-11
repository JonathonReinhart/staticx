#!/bin/bash
set -e
app=./date
outfile=./date.staticx

echo -e "\n\nTest StaticX against 'date'"

cd "$(dirname "${BASH_SOURCE[0]}")"


cp -p $(which date) $app

echo -e "\nRunning 'date':"
$app

echo -e "\nUnmarking executable:"
chmod -x $app

echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile

echo -e "\nRunning staticx executable"
$outfile

if [ -n "$TEST_DOCKER_IMAGE" ]; then
    echo -e "\nRunning staticx executable under $TEST_DOCKER_IMAGE"
    scuba --image $TEST_DOCKER_IMAGE $outfile
fi
