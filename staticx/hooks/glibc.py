from ..assets import copy_asset_to_tempfile
from ..errors import InternalError
from ..elf import open_elf, get_shobj_deps, patch_elf
from ..utils import make_executable
from elftools.elf.gnuversions import GNUVerNeedSection
import logging

LIBNSSFIX = 'libnssfix.so'

def process_glibc_prog(sx):
    if not is_linked_against_glibc(sx.orig_prog):
        return

    try:
        nssfix = copy_asset_to_tempfile(LIBNSSFIX, debug=sx.debug,
                prefix='libnssfix-', suffix='.so')
    except KeyError:
        raise InternalError("GLIBC binary detected but libnssfix.so not available")

    # Make the user program depend on libnssfix.so
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
        sx.sxar.add_fileobj(LIBNSSFIX, nssfix)
        for libpath in get_shobj_deps(nssfix.name):
            sx.add_library(libpath, exist_ok=True)


def is_linked_against_glibc(prog):
    with open_elf(prog) as elf:
        sec = elf.get_single_section(GNUVerNeedSection)
        if not sec:
            return False
        for verneed, vernaux_iter in sec.iter_versions():
            if not verneed.name.startswith('libc.so'):
                continue
            for vernaux in vernaux_iter:
                if vernaux.name.startswith('GLIBC_'):
                    logging.debug("Program linked with GLIBC: Found {} {}".format(
                        verneed.name, vernaux.name))
                    return True
    return False
