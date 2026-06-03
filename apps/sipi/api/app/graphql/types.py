import strawberry
from typing import List, Optional, Generic, TypeVar
from enum import Enum

T = TypeVar('T')

class PaginatedResult(Generic[T]):
    def __init__(self, items: List[T], total: int):
        self.items = items
        self.total = total

@strawberry.enum
class FilterOperator(Enum):
    EQ = "eq"
    NE = "ne"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    LIKE = "like"
    ILIKE = "ilike"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    BETWEEN = "between"

@strawberry.input
class FilterInput:
    field: str
    operator: FilterOperator = FilterOperator.EQ
    value: Optional[str] = None
    values: Optional[List[str]] = None

@strawberry.input
class SortInput:
    field: str
    direction: str = "asc"

@strawberry.input
class PaginationInput:
    limit: int = 20
    offset: int = 0