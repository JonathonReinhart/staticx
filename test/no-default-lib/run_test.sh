#!/bin/bash
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Verify StaticX can't link against target system libs"

app="./app"
outfile="./app.staticx"
libname="libcrypt.so"

# Build the application
gcc -Wall -Werror -DLIBNAME="\"$libname\"" -o $app app.c -ldl || exit $?

# Run the application normally
echo -e "\nApp run normally:"
$app $libname 0 || exit $?

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile || exit $?

# Run that executable
echo -e "\nRunning staticx executable"
$outfile $libname 1 || exit $?


### Docker
libname="libcrack.so"

if [ -n "$TEST_DOCKER_IMAGE" ]; then
    echo -e "\nVerifying target library is loadable under $TEST_DOCKER_IMAGE"
    scuba --image $TEST_DOCKER_IMAGE /bin/bash -c "ldd /usr/sbin/cracklib-check | grep libcrack.so"

    echo -e "\nRunning staticx executable under $TEST_DOCKER_IMAGE"
    scuba --image $TEST_DOCKER_IMAGE $outfile $libname 1
fi
