#!/bin/bash
set -e

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Verify StaticX rejects PyInstalled application with library using RUNPATH"

cd "$(dirname "${BASH_SOURCE[0]}")"
source ../funcs.sh

app="./dist/app"
outfile="./dist/app.staticx"

# Build the shared library
gcc -Wall -Werror -fPIC -c -o libfoo.o libfoo.c
gcc -shared -Wl,-rpath=/bogus/absolute/path -Wl,--enable-new-dtags -o libfoo.so libfoo.o
verify_uses_runpath libfoo.so

# Run the application normally
echo -e "\nPython app run normally:"
python3 app.py

# Build a PyInstaller "onefile" application
echo -e "\nBuilding PyInstaller 'one-file' application:"
pyinstaller -F app.spec

# Run the PyInstalled application
echo -e "\nPyInstalled application run:"
$app

# Make a staticx executable from it
# This is an expected failure!
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS) [EXPECTED FAILURE]"

if output=$(staticx $STATICX_FLAGS $app $outfile); then
    echo "FAIL: Staticx permitted a problematic library using RUNPATH"
    exit 66
fi
if ! (echo "$output" | grep -q "Unsupported PyInstaller input"); then
    echo "FAIL: Unexpected output text:"
    echo "$output"
    exit 66
fi
echo "Success"
