#!/bin/bash
set -e

echo -e "\n\nTest StaticX against application using RUNPATH \$ORIGIN"

cd "$(dirname "${BASH_SOURCE[0]}")"

app="dist.runpath/bin/app"
outfile="dist.runpath/app.staticx"

# Build the application
# Force use of RUNPATH, not RPATH
# https://stackoverflow.com/a/52020177/119527
scons --quiet name=runpath LINKFLAGS='-Wl,--enable-new-dtags'

# Ensure this test uses DT_RUNPATH and not DT_RPATH
if (readelf -d $app | grep -q '(RPATH)'); then
    echo "TEST ERROR: app uses DT_RPATH instead of DT_RUNPATH"
    exit 66
fi
if ! (readelf -d $app | grep -q '(RUNPATH)'); then
    echo "TEST ERROR: app is missing DT_RUNPATH"
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
