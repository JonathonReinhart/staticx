# Contributing Guide
*This file is incomplete. Feel free to open an issue if there is missing
information you desire.*

## Dev environment

1. Download and install [SCons](https://scons.org/pages/download.html).
2. Download and install
   [docker-ce](https://docs.docker.com/engine/install/debian/#install-using-the-repository)
   (for running integration tests).
<!-- Specific python version? -->
3. Download and install python3 and pip
4. Run `source ./dev_bootstrap.sh` — This will:
   * Set up a Python virtual environment (using `venv`) and activate it.
   * Install the development packages from `requirements.txt`.
   * Install the local staticx package in *editable mode*.

## Build and test

1. Run `scons` to build the bootloader.
   * NOTE: When built this way, the bootloader version will be `<unknown>`.
2. Run `./run_unit_tests.sh` to run unit tests.
3. Run `./run_integration_tests.sh` to run integration tests.
4. Run `./static_analysis.sh` to run static analysis.

See docs/installation for more details on building.

## Code Format
Staticx is compliant with the [Black](https://black.readthedocs.io/)
code style. Code format in PRs is verified by a GitHub action.

To check code formatting:
```
$ ./code_format.py
```

To fix code formatting:
```
$ ./code_format.py --fix
```
