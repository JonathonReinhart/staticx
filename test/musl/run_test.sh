#!/bin/bash
set -e

CCFLAGS="-Wall -Werror -Os -s"

outfile=./app.staticx

echo -e "\n\nTest StaticX against a musl-libc-linked executable"

cd "$(dirname "${BASH_SOURCE[0]}")"


# Build our app
if [ -x "$(command -v musl-gcc)" ]; then
    echo "Building aux app with musl-gcc"
    musl-gcc $CCFLAGS -o app app.c
else
    echo "musl-gcc not installed"
    exit 0
fi

# Run the application normally
echo -e "\napp run normally:"
./app

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
STATICX_LDD="musl-ldd" staticx $STATICX_FLAGS ./app $outfile

# Run that executable
echo -e "\nRunning staticx executable"
$outfile

# Run it under an old distro
if [ -n "$TEST_DOCKER_IMAGE" ]; then
    echo -e "\nRunning staticx executable under $TEST_DOCKER_IMAGE"
    scuba --image $TEST_DOCKER_IMAGE $outfile
fi
