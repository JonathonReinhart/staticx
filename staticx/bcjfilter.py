import platform

# NOTE: This is also used by libxz/SConscript


def get_bcj_filter_arch() -> str | None:
    """
    Get an appropriate BCJ filter for the current architecture.

    Returns just the architecture part of the BCJ filter name.
    This can be prepended with FILTER_ for a Python lzma module constant,
    or XZ_DEC_ for an XZ Embedded decoder macro.
    """
    # It's possible that the code being compressed might not match that of the
    # current Python interpreter. In that case the problem becomes much more
    # complicated, as we have to inspect the files to make a determination.
    # This approach should be "good enough"; the worst case scenario is only a
    # slightly worse compression ratio.

    match platform.machine():
        case "i386" | "i686" | "x86_64":
            return "X86"
        case "ia64":
            return "IA64"
        case m if m.startswith("arm"):  # arm, armv8b, etc.
            return "ARM"
        case m if m.startswith("ppc"):
            return "POWERPC"
        case m if m.startswith("sparc"):
            return "SPARC"
        case _:
            return None
