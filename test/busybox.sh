#!/bin/bash
set -e
outfile=./busybox.staticx

cd "$(dirname "${BASH_SOURCE[0]}")"
echo -e "\n\nTest StaticX against 'busybox'"

infile=$(which busybox)

if [ ! -x $infile ]; then
    echo "Busybox not installed... skipping."
    exit 0
fi

echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $infile $outfile

echo -e "\nRunning staticx executable"
$outfile date

if [ -n "$TEST_DOCKER_IMAGE" ]; then
    echo -e "\nRunning staticx executable under $TEST_DOCKER_IMAGE"
    scuba --image $TEST_DOCKER_IMAGE $outfile date
fi
