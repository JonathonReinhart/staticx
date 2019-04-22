#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

# Run test against system executable
./date.sh

# Test environment variables
./staticx-env-vars.sh

# Run test against app built with PyInstaller
pyinstall/run_test.sh

# Run test against app built with PyInstaller and uses CFFI
pyinstall-cffi/run_test.sh
