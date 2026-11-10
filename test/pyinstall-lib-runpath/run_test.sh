#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"
source ../funcs.sh

verify_pyinstaller

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Verify StaticX rejects PyInstalled application with library using RUNPATH"

app="./dist/app"
outfile="./dist/app.staticx"

# Build the shared library
function make_shlib() {
    lib="$1"
    deps="$2"
    set -x
    gcc -Wall -Werror -fPIC -c -o $lib.o $lib.c
    gcc -shared -Wl,-rpath=/bogus/absolute/path -Wl,--enable-new-dtags $deps -o $lib.so $lib.o
    set +x
    verify_uses_runpath $lib.so
}

# Build libbar.so (leaf node)
gcc -Wall -Werror -fPIC -c -o libbar.o libbar.c
gcc -shared -o libbar.so libbar.o

# Move libbar to a temporary home
templibdir="my/temporary/home"
mkdir -p $templibdir
mv libbar.so $templibdir/

# Build libfoo.so (depends on libbar.so)
gcc -Wall -Werror -fPIC -c -o libfoo.o libfoo.c
gcc -shared \
    -Wl,-rpath=$(realpath $templibdir) -Wl,--enable-new-dtags \
    -L $templibdir \
    -lbar \
    -o libfoo.so libfoo.o -lbar

##################

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
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS)"
staticx $STATICX_FLAGS $app $outfile

$outfile

echo "TODO Remove temp home"
rm -r $templibdir

$outfile

echo "Success"
