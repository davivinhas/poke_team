from typing import Generic, List, Optional, TypeVar

T = TypeVar("T")


class CursorPage(Generic[T]):
    def __init__(
        self,
        items: List[T],
        next_cursor: Optional[str],
    ):
        self.items = items
        self.next_cursor = next_cursor
