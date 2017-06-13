#!/bin/bash
set -e

# Only run if PyInstaller is installed
# By gracefully failing here, we can control which versions of Python this test
# runs under in requirements.txt
pyinstaller --version 2>/dev/null || { echo "PyInstaller not installed"; exit 0; }


echo -e "\n\nTest StaticX against PyInstalled application"

cd "$(dirname "${BASH_SOURCE[0]}")"

# Run the application normally
echo -e "\nPython app run normally:"
python app.py

# Build a PyInstaller "onefile" application
echo -e "\nBuilding PyInstaller 'onfile' application:"
pyinstaller -F app.py

# Run the PyInstalled application
echo -e "\nPyInstalled application run:"
./dist/app

# Make a staticx executable from it
echo -e "\nMaking staticx executable:"
staticx ./dist/app ./dist/app.staticx

# Run that executable
echo -e "\nRunning staticx executable"
./dist/app.staticx

# Run it under an old distro
echo -e "\nRunning staticx executable under CentOS 5"
scuba --image centos:5 ./dist/app.staticx
