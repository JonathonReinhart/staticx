#!/bin/bash
set -e

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Test StaticX sets STATICX_* vars"

cd "$(dirname "${BASH_SOURCE[0]}")"

app="$(which sh)"
outfile="./sh.staticx"

# Make a staticx executable from bash so we can test STATICX_ env vars
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS $app $outfile


# Verify STATICX_BUNDLE_DIR is set to "/tmp/staticx-*"
test_bundle_dir=$($outfile -c 'echo $STATICX_BUNDLE_DIR')
echo "STATICX_BUNDLE_DIR: $test_bundle_dir"
if [[ "$test_bundle_dir" != "/tmp/staticx-"* ]]; then
    echo "STATICX_BUNDLE_DIR looks wrong: \"$test_bundle_dir\""
    exit 1
fi

# Verify staticx respects $TMPDIR
export TMPDIR="/tmp/my/special/tmpdir"
mkdir -p $TMPDIR
test_bundle_dir=$($outfile -c 'echo $STATICX_BUNDLE_DIR')
echo "STATICX_BUNDLE_DIR: $test_bundle_dir"
if [[ "$test_bundle_dir" != "${TMPDIR}/staticx-"* ]]; then
    echo "STATICX_BUNDLE_DIR looks wrong: \"$test_bundle_dir\""
    exit 1
fi

# Verify STATICX_PROG_PATH is set to our application
test_prog_path=$($outfile -c 'echo $STATICX_PROG_PATH')
real_outfile="$(realpath $outfile)"
echo "STATICX_PROG_PATH: $test_prog_path"
if [[ "$test_prog_path" != "$real_outfile" ]]; then
    echo "STATICX_PROG_PATH incorrect: \"$test_prog_path\" != \"$real_outfile\""
    exit 1
fi
