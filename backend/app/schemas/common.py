"""
Shared schemas and Health Check responses using Pydantic v2.
"""

from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    project: str
    version: str
    timestamp: str


class DatabaseHealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: str
    database_name: str
    version: str
    table_count: int
    driver: str


class APIResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(from_attributes=True)

    success: bool = True
    message: str = "Success"
    data: Optional[T] = None

