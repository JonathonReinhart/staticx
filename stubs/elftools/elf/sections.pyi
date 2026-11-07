from typing import Any

class Section:
    name: str
    header: Any

    @property
    def compressed(self) -> int: ...
    @property
    def data_size(self) -> int: ...
    def data(self) -> bytes: ...
