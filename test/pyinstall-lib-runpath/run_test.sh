#!/bin/bash
set -e

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Verify StaticX rejects PyInstalled application with library using RUNPATH"

cd "$(dirname "${BASH_SOURCE[0]}")"
source ../funcs.sh

app="./dist/app"
outfile="./dist/app.staticx"

# Build the shared library
function make_shlib() {
    lib="$1"
    gcc -Wall -Werror -fPIC -c -o $lib.o $lib.c
    gcc -shared -Wl,-rpath=/bogus/absolute/path -Wl,--enable-new-dtags -o $lib.so $lib.o
    verify_uses_runpath $lib.so
}

make_shlib libfoo
make_shlib libbar

# Run the application normally
echo -e "\nPython app run normally:"
python3 app.py

# Build a PyInstaller "onefile" application
echo -e "\nBuilding PyInstaller 'one-file' application:"
pyinstaller app.spec

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

function check_output() {
    pat="$1"
    if ! (echo "$output" | grep -q "$pat"); then
        echo "FAIL: Unexpected output text (missing \"$pat\"):"
        echo "-----------------------------------------------------------------"
        echo "$output"
        echo "-----------------------------------------------------------------"
        exit 66
    fi
}
check_output "Unsupported PyInstaller input"
check_output "libfoo.so.*DT_RUNPATH"
check_output "libbar.so.*DT_RUNPATH"

echo "Success"
