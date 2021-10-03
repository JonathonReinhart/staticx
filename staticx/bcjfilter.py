import platform
import lzma

# NOTE: This is also used by libxz/SConscript

class BCJFilter:
    __slots__ = ['arch']

    def __init__(self, arch):
        self.arch = arch

    def __repr__(self):
        return 'BCJFilter({})'.format(self.arch)

    def __str__(self):
        return self.arch

    @property
    def xz_dec_macro(self):
        """Get the XZ Embedded decoder macro name for this filter"""
        return 'XZ_DEC_' + self.arch

    @property
    def lzma_filter_id(self):
        """Get a Python lzma module filter id for this filter

        See https://docs.python.org/3/library/lzma.html#filter-chain-specs
        """
        return getattr(lzma, 'FILTER_' + self.arch)

    @classmethod
    def for_arch(cls, arch):
        """
        Get an appropriate BCJ filter for the given architecture.
        """
        if arch in ('i386', 'i686', 'x86_64'):
            return cls('X86')

        if arch == 'ia64':
            return cls('IA64')

        if arch.startswith('arm'):   # arm, armv8b, etc.
            return cls('ARM')

        # TODO: 'ARMTHUMB'

        if arch.startswith('ppc'):
            return cls('POWERPC')

        if arch.startswith('sparc'):
            return cls('SPARC')

        return None

    @classmethod
    def for_current_arch(cls):
        """
        Get an appropriate BCJ filter for the current architecture.
        """
        # It's possible that the code being compressed might not match that of the
        # current Python interpreter. In that case the problem becomes much more
        # complicated, as we have to inspect the files to make a determination.
        # This approach should be "good enough"; the worst case scenario is only a
        # slightly worse compression ratio.
        return cls.for_arch(platform.machine())
