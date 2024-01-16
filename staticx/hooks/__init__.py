from __future__ import annotations
from .pyinstaller import process_pyinstaller_archive
from .glibc import process_glibc_prog
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..api import StaticxGenerator

hooks = [
    process_pyinstaller_archive,
    process_glibc_prog,
]


def run_hooks(sx: StaticxGenerator) -> None:
    for hook in hooks:
        hook(sx)
