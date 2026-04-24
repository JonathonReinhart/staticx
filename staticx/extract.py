from tempfile import NamedTemporaryFile
import tarfile
import os

from .constants import ARCHIVE_SECTION
from .elf import elf_dump_section
from .errors import ArchiveError


def open_archive(archive: str) -> tarfile.TarFile:
    f = NamedTemporaryFile(prefix='staticx-archive-', suffix='.tar')
    elf_dump_section(archive, ARCHIVE_SECTION, f.name)

    size = os.stat(f.name).st_size
    if size == 0:
        raise ArchiveError(f"{archive} does not appear to contain a staticx archive section")
    return tarfile.open(fileobj=f, mode='r', format=tarfile.GNU_FORMAT)


def main() -> None:
    import argparse
    ap = argparse.ArgumentParser(
            description='StaticX archive extractor/browser')
    ap.add_argument('archive',
            help="StaticX-generated executable (archive) to extract")
    ap.add_argument('outdir', nargs='?',
            help="Optional output directory into which archive is to be extracted")
    ap.add_argument('-v', '--verbose', action='store_true',
            help="Verbose output")
    args = ap.parse_args()

    try:
        ar = open_archive(args.archive)
    except ArchiveError as e:
        raise SystemExit(str(e))

    with ar:
        if args.outdir:
            ar.extractall(path=args.outdir)
        else:
            ar.list(verbose=args.verbose)

if __name__ == '__main__':
    main()
