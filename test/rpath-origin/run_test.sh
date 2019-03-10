#!/bin/bash
set -e

echo -e "\n\nTest StaticX against application using RPATH \$ORIGIN"

cd "$(dirname "${BASH_SOURCE[0]}")"

app="dist/bin/app"
outfile="dist/app.staticx"

# Build the application
scons --quiet

# Run the application normally
echo -e "\nApp run normally:"
$app

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile

# Run that executable
echo -e "\nRunning staticx executable"
$outfile
