#!/bin/bash
set -e

echo -e "\n\nTest StaticX against application using RPATH \$ORIGIN"

cd "$(dirname "${BASH_SOURCE[0]}")"

app="dist.rpath/bin/app"
outfile="dist.rpath/app.staticx"

# Build the application
scons -f SConstruct.rpath --quiet

# Ensure this test uses DT_RPATH and not DT_RUNPATH
if (readelf -d $app | grep -q '(RUNPATH)'); then
    echo "TEST ERROR: app uses DT_RUNPATH instead of DT_RPATH"
    exit 66
fi
if ! (readelf -d $app | grep -q '(RPATH)'); then
    echo "TEST ERROR: app is missing DT_RPATH"
    exit 66
fi

# Run the application normally
echo -e "\nApp run normally:"
$app

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile

# Run that executable
echo -e "\nRunning staticx executable"
$outfile
