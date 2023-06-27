#!/bin/bash
set -e

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Test StaticX bootloader forwards signals"

cd "$(dirname "${BASH_SOURCE[0]}")"

app="build/app"
outfile="build/app.staticx"

# Build the application
scons --quiet

# Test the application normally
echo -e "\nApp run normally:"
./test_signals.py $app

# Make a staticx executable from it
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile

# Test the staticx executable
echo -e "\nRunning staticx executable"
./test_signals.py $outfile

