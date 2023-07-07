# Functions for use by other test scripts

# Ensure the input file uses DT_RPATH and not DT_RUNPATH
function verify_uses_rpath() {
    local app="$1"

    if (readelf -d $app | grep -q '(RUNPATH)'); then
        echo "TEST ERROR: $app uses DT_RUNPATH instead of DT_RPATH"
        exit 66
    fi
    if ! (readelf -d $app | grep -q '(RPATH)'); then
        echo "TEST ERROR: $app is missing DT_RPATH"
        exit 66
    fi
}

# Ensure the input file uses DT_RUNPATH and not DT_RPATH
function verify_uses_runpath() {
    local app="$1"

    if (readelf -d $app | grep -q '(RPATH)'); then
        echo "TEST ERROR: $app uses DT_RPATH instead of DT_RUNPATH"
        exit 66
    fi
    if ! (readelf -d $app | grep -q '(RUNPATH)'); then
        echo "TEST ERROR: $app is missing DT_RUNPATH"
        exit 66
    fi
}

# Check to see if PyInstaller is installed.
# If not, then fail gracefully. By doing so, we can control which versions of
# Python this test runs under in requirements.txt.
function verify_pyinstaller() {
    pyinstaller --version >/dev/null 2>/dev/null || {
        echo "PyInstaller not installed"
        exit 0
    }

    # If "pyinstaller" is in $PATH, but PyInstaller is not in sys.path,
    # then we need to abort because this is not expected.
    python3 -m PyInstaller --version >/dev/null 2>/dev/null || {
        echo "PyInstaller installed, but not in this (virtual?) environment!"
        exit 66
    }
}
