#!/usr/bin/env python3
import argparse
import glob
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent.resolve()
PYTHON_CODE = (
    "*.py",
    "SConstruct",
    "docs",
    "site_scons",
    "staticx",
    "stubs",
    "test",
    "unittest",
)


def _format_python(fix: bool) -> bool:
    args = ["ruff", "format"]
    for pat in PYTHON_CODE:
        args += glob.glob(pat, root_dir=PROJECT_DIR)

    if not fix:
        # check only
        args += [
            "--check",
            "--diff",
        ]

    status = subprocess.run(args).returncode

    if status == 0:
        return True
    if status == 1:
        return False
    raise Exception(f"Unexpected exit status: {status}")


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Modify files to fix formatting",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()

    ok = True

    print(f"\n{'Fixing' if args.fix else 'Checking'} Python code formatting...")
    ok &= _format_python(args.fix)

    if not ok:
        print("\nTo fix, rerun with --fix")
        raise SystemExit(1)


if __name__ == "__main__":
    main()
