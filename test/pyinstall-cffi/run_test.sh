#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
source ../funcs.sh

verify_pyinstaller
python3 -c 'import cffi' 2>/dev/null || { echo "CFFI not installed"; exit 0; }

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Test StaticX against PyInstalled application using CFFI"

outfile=./dist/app.staticx

# Run the application normally
echo -e "\nPython app run normally:"
python3 app.py

# Build a PyInstaller "onefile" application
echo -e "\nBuilding PyInstaller 'onfile' application:"
pyinstaller -F app.py

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
