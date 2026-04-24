# entry_offset, data_length, uncompressed_length, compression_flag, typecode
_TocEntry = tuple[int, int, int, int, str]

class CArchiveReader:
    toc: dict[str, _TocEntry]

    def __init__(self, filename: str):
        ...

    # PyInstaller 5.10+
    # See #236, #237
    def extract(self, name: str) -> bytes:
        ...
