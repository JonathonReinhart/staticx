#!/bin/bash
set -e

echo -e "\n\nTest StaticX in a broken NSS target environment"

cd "$(dirname "${BASH_SOURCE[0]}")"

app="build/app"
outfile="build/app.staticx"

# Build the application
scons --quiet

# Run the application normally
echo -e "\nApp run normally:"
$app

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile

# Run that executable
echo -e "\nRunning staticx executable"
$outfile

# Run it under Docker
if [ -n "$TEST_DOCKER_IMAGE" ]; then
    echo -e "\nRunning staticx executable under $TEST_DOCKER_IMAGE"
    docker run --rm -it \
        -v "$(pwd):$(pwd):ro" -w $(pwd) \
        -v "$(realpath ./bad_nsswitch.conf):/etc/nsswitch.conf:ro" \
        $TEST_DOCKER_IMAGE \
        $outfile
fi
