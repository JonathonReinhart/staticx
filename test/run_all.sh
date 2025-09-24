#!/bin/bash
set -e
cd "$(dirname "${BASH_SOURCE[0]}")"

# Run test against system executable
./date.sh
./busybox.sh

# Test environment variables
./staticx-env-vars.sh

# Test --bundle-dir and --prog-name options
./bundle-dir-prog-name.sh

# Run test an executable linked against musl-libc
musl/run_test.sh

# Run test against app built with PyInstaller
pyinstall/run_test.sh

# Run test against app built with PyInstaller and uses CFFI
pyinstall-cffi/run_test.sh

# Run test against app built with PyInstaller and includes a helper app
pyinstall-aux-static-exec/run_test.sh

# Test against a PyInstaller app that uses unsupported RUNPATH
pyinstall-lib-runpath/run_test.sh

# Verify that target system libs can't be loaded
no-default-lib/run_test.sh

# Run test against broken NSS
nss-isolated/run_test.sh

echo "All tests successful!"
