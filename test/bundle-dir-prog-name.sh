#!/bin/bash
set -e

echo -e "\n\n--------------------------------------------------------------------------------"
echo -e "Test StaticX --bundle-dir and --prog-name options."

cd "$(dirname "${BASH_SOURCE[0]}")"

app="$(which sh)"
outfile="./sh.staticx"

# The values we're going to be testing for.
bundle_dir=$(mktemp --dry-run --tmpdir -d systemd-private-60ce0209a865480b817f3623184c43e2-dmesg.service-XXXXXX)
prog_name="tmp"

# Make a staticx executable from bash so we can check the STATICX_ env vars to know the bundle directory and program path.
echo -e "\nMaking staticx executable (\$STATICX_FLAGS=$STATICX_FLAGS):"
staticx $STATICX_FLAGS --bundle-dir $bundle_dir --prog-name $prog_name $app $outfile

# Verify STATICX_BUNDLE_DIR matches the `--bundle-dir` option.
test_bundle_dir=$($outfile -c 'echo $STATICX_BUNDLE_DIR')
echo "STATICX_BUNDLE_DIR: $test_bundle_dir"
if [[ "$test_bundle_dir" != "$bundle_dir" ]]; then
    echo "STATICX_BUNDLE_DIR does not match --bundle-dir: \"$test_bundle_dir\" != \"$bundle_dir\""
    exit 1
fi

# Verify that the program is renamed to `--prog-name` when specified.
test_prog_name=$($outfile -c 'echo $0')
echo "The program name is: $test_prog_name"
if [[ "$test_prog_name" != "$prog_name" ]]; then
    echo "The program name does not match --prog-name: \"$test_prog_name\" != \"$prog_name\""
    exit 1
fi
