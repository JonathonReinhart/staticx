from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from elftools.elf.gnuversions import GNUVerNeedSection

from ..assets import copy_asset_to_tempfile
from ..elf import get_shobj_deps, open_elf, patch_elf
from ..errors import InternalError
from ..utils import make_executable

if TYPE_CHECKING:
    from ..api import StaticxGenerator

LIBNSSFIX = "libnssfix.so"


def process_glibc_prog(sx: StaticxGenerator) -> None:
    if not is_linked_against_glibc(sx.orig_prog):
        return

    try:
        nssfix = copy_asset_to_tempfile(
            LIBNSSFIX, debug=sx.debug, prefix="libnssfix-", suffix=".so"
        )
    except KeyError:
        raise InternalError("GLIBC binary detected but libnssfix.so not available")

    # Make the user program depend on libnssfix.so
    assert sx.tmpprog
    patch_elf(sx.tmpprog, add_needed=LIBNSSFIX)

    # Add libnssfix.so and its dependencies to the archive.
    # These include the configured libnss_*.so "service" libs and their
    # dependencies.
    #
    # TODO: Ideally staticx.api.generate_archive() would handle this for us,
    # since we added the dependency on libnssfix to the user program above.
    # Even though dependency discovery runs after this hook, it necessarily
    # operates on the *original* executable and not the copied/modified one,
    # (see dfa201b07e) so it doesn't see changes made here.
    with nssfix:
        # Silence "you do not have execution permission" warning from ldd
        make_executable(nssfix.name)

        # TODO: Don't use sxar
        assert sx.sxar
        sx.sxar.add_fileobj(LIBNSSFIX, nssfix)
        for libpath in get_shobj_deps(nssfix.name):
            sx.add_library(libpath, exist_ok=True)


def is_linked_against_glibc(prog: str) -> bool:
    with open_elf(prog) as elf:
        sec = elf.get_single_section(GNUVerNeedSection)
        if not sec:
            return False
        assert isinstance(sec, GNUVerNeedSection)
        for verneed, vernaux_iter in sec.iter_versions():
            if not verneed.name.startswith("libc.so"):
                continue
            for vernaux in vernaux_iter:
                if vernaux.name.startswith("GLIBC_"):
                    logging.debug(
                        f"Program linked with GLIBC: Found {verneed.name} {vernaux.name}"
                    )
                    return True
    return False
