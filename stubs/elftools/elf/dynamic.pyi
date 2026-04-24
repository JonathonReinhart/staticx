from collections.abc import Iterable
from .segments import Segment

class DynamicTag:
    # These attributes are conditionally present.See DynamicTag._HANDLED_TAGS.
    # There's no way to cleanly express this with Python typing.
    needed: str
    rpath: str
    runpath: str
    soname: str
    sunw_filter: str

class Dynamic:
    ...
    def iter_tags(self, type: str) -> Iterable[DynamicTag]:
        ...

class DynamicSegment(Segment, Dynamic):
    ...
