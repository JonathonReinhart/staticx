#!/bin/bash

# https://docs.pytest.org/en/latest/pythonpath.html#pytest-vs-python-m-pytest
# "Running pytest with python -m pytest [...] instead of pytest [...] yields
# nearly equivalent behaviour, except that the former call will add the current
# directory to sys.path."

exec python3 -m pytest -v "$@"
