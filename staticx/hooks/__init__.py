from __future__ import annotations

from typing import TYPE_CHECKING

from .glibc import process_glibc_prog
from .pyinstaller import process_pyinstaller_archive

if TYPE_CHECKING:
    from ..api import StaticxGenerator

hooks = [
    process_pyinstaller_archive,
    process_glibc_prog,
]


def run_hooks(sx: StaticxGenerator) -> None:
    for hook in hooks:
        hook(sx)
