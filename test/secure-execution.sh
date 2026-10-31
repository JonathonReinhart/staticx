#!/bin/bash
# Test that StaticX refuses to run as setuid, setgid, or under AT_SECURE.
# This test must be run as root so it can create setuid/setgid files and test capabilities.
#
# Usage:
#   sudo ./test/secure-execution.sh
#
set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (e.g. sudo $0)" >&2
    exit 1
fi

export PATH="$PATH:/sbin:/usr/sbin"
cd "$(dirname "${BASH_SOURCE[0]}")"

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Test StaticX secure execution prevention (setuid, setgid, AT_SECURE)"

# Find staticx executable
STATICX="$(command -v staticx || true)"
if [ -z "$STATICX" ] && [ -x "../venv/bin/staticx" ]; then
    STATICX="$(pwd)/../venv/bin/staticx"
fi

if [ -z "$STATICX" ]; then
    echo "Error: staticx not found in PATH or in ../venv/bin/staticx" >&2
    exit 1
fi

TMPDIR="$(mktemp -d /tmp/staticx-sec-test.XXXXXX)"
chmod 755 "$TMPDIR"
cleanup() {
    rm -rf "$TMPDIR"
}
trap cleanup EXIT INT TERM

TEST_BIN="$TMPDIR/id.staticx"
INFILE="$(command -v id)"

echo -e "\nBuilding test staticx binary..."
"$STATICX" $STATICX_FLAGS "$INFILE" "$TEST_BIN"
chmod 755 "$TEST_BIN"

# Helper to execute as an unprivileged user ('nobody') and verify the expected error
run_test() {
    local desc="$1"
    local expected_msg="$2"
    local prefix="staticx [$(basename "$TEST_BIN")]: "
    local expected="${prefix}${expected_msg}"

    echo -e "\nRunning test: $desc"
    set +e
    output=$(su -s /bin/sh nobody -c "$TEST_BIN" 2>&1)
    status=$?
    set -e

    if [ "$status" -ne 2 ]; then
        echo "TEST FAILED: Expected exit code 2, got $status"
        echo "Output was: $output"
        exit 1
    fi

    if [[ "$output" != *"$expected"* ]]; then
        echo "TEST FAILED: Output did not contain expected message: '$expected'"
        echo "Output was: $output"
        exit 1
    fi

    echo "PASSED: $desc"
}

# Test setuid execution
chown root:root "$TEST_BIN"
chmod 4755 "$TEST_BIN"
run_test "Setuid root binary" "Running as setuid/setgid is unsupported for security reasons."

# Test setgid execution
# We assign the binary to group 'bin' and run as 'nobody'
chown nobody:bin "$TEST_BIN"
chmod 2755 "$TEST_BIN"
run_test "Setgid binary" "Running as setuid/setgid is unsupported for security reasons."

# Test AT_SECURE execution via Linux file capabilities
if command -v setcap >/dev/null 2>&1; then
    chown nobody:nogroup "$TEST_BIN"
    chmod 755 "$TEST_BIN"
    setcap cap_net_raw+p "$TEST_BIN"
    run_test "File capabilities (AT_SECURE)" "Binary was launched in secure mode (AT_SECURE)."
else
    echo -e "\nSkipping AT_SECURE test: 'setcap' not found."
fi

echo -e "\nAll secure execution tests passed successfully!"
