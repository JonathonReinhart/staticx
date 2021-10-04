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
