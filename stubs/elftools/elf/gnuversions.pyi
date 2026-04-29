from collections.abc import Iterable
from .sections import Section

class Version:
    name: str

class VersionAuxiliary:
    name: str

class GNUVersionSection(Section):
    def num_versions(self) -> int: ...
    def iter_versions(self) -> Iterable[tuple[Version, Iterable[VersionAuxiliary]]]: ...

class GNUVerNeedSection(GNUVersionSection):
    def has_indexes(self) -> bool: ...
    def iter_versions(self) -> Iterable[tuple[Version, Iterable[VersionAuxiliary]]]: ...
    def get_version(self, index: int) -> tuple[Version, VersionAuxiliary] | None: ...
