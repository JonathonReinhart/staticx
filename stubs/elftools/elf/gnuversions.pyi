from typing import Iterable, Optional, Tuple
from .sections import Section

class Version:
    name: str

class VersionAuxiliary:
    name: str

class GNUVersionSection(Section):
    def num_versions(self) -> int:
        ...
    def iter_versions(self) -> Iterable[Tuple[Version, Iterable[VersionAuxiliary]]]:
        ...


class GNUVerNeedSection(GNUVersionSection):
    def has_indexes(self) -> bool:
        ...
    def iter_versions(self) -> Iterable[Tuple[Version, Iterable[VersionAuxiliary]]]:
        ...
    def get_version(self, index: int) -> Optional[Tuple[Version, VersionAuxiliary]]:
        ...
