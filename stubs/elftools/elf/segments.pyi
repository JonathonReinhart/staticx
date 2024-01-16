from typing import Any
from .sections import Section

class Segment:
    def data(self) -> bytes:
        ...
    def __getitem__(self, name: str) -> Any:
        ...
    def section_in_segment(self, section: Section) -> bool:
        ...

class InterpSegment(Segment):
    def get_interp_name(self) -> str:
        ...
