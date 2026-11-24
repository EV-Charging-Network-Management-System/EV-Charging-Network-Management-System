"""Consistent optional pagination for list endpoints."""

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Query


@dataclass(frozen=True)
class Page:
    skip: Annotated[int, Query(ge=0)] = 0
    limit: Annotated[int | None, Query(ge=1, le=500)] = None

    def apply(self, query):
        return query.offset(self.skip).limit(self.limit)

    def slice(self, items):
        end = None if self.limit is None else self.skip + self.limit
        return items[self.skip:end]


PageParam = Annotated[Page, Depends()]
