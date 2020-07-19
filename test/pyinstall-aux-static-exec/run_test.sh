#!/bin/bash
set -e

CCFLAGS="-Wall -Werror -Os -s"
CCFLAGS_STATIC="$CCFLAGS -static -DSTATIC=1"

outfile=./dist/app.staticx

# Only run if PyInstaller is installed
# By gracefully failing here, we can control which versions of Python this test
# runs under in requirements.txt
pyinstaller --version 2>/dev/null || { echo "PyInstaller not installed"; exit 0; }


echo -e "\n\nTest StaticX against PyInstalled application which includes a statically-linked aux app"

cd "$(dirname "${BASH_SOURCE[0]}")"


# Build our auxiliary app
echo "Building aux app with gcc"
gcc $CCFLAGS_STATIC -o aux-glibc-static  aux.c

if [ -x "$(command -v musl-gcc)" ]; then
    echo "Building aux app with musl-gcc"
    musl-gcc $CCFLAGS_STATIC -o aux-musl-static  aux.c
fi


# Run the application normally
echo -e "\nPython app run normally:"
python app.py

# Build a PyInstaller "onefile" application
echo -e "\nBuilding PyInstaller 'one-file' application:"
pyinstaller -F app.spec

# Run the PyInstalled application
echo -e "\nPyInstalled application run:"
./dist/app

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS ./dist/app $outfile

# Run that executable
echo -e "\nRunning staticx executable"
$outfile

# Run it under an old distro
if [ -n "$TEST_DOCKER_IMAGE" ]; then
    echo -e "\nRunning staticx executable under $TEST_DOCKER_IMAGE"
    scuba --image $TEST_DOCKER_IMAGE $outfile
fi
