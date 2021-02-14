import typing as T

M = T.TypeVar("M")


class PaginationData:
    page_size: int
    page: int
    total_items: int
    has_next_page: bool


class Pagination(T.Generic[M]):
    items: T.List[M]
    meta: PaginationData
