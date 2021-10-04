#!/bin/bash
set -e

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Test StaticX against application using RPATH \$ORIGIN"

cd "$(dirname "${BASH_SOURCE[0]}")"
source ../funcs.sh

app="dist.rpath/bin/app"
outfile="dist.rpath/app.staticx"

# Build the application
# Force use of RPATH, not RUNPATH
# https://stackoverflow.com/a/52020177/119527
scons --quiet name=rpath LINKFLAGS='-Wl,--disable-new-dtags'

verify_uses_rpath $app

# Run the application normally
echo -e "\nApp run normally:"
$app

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile

# Run that executable
echo -e "\nRunning staticx executable"
$outfile
