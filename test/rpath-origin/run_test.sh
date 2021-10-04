#!/bin/bash
set -e

cd "$(dirname "${BASH_SOURCE[0]}")"

./run_test-rpath.sh
./run_test-runpath.sh
