"""
Connector Types Endpoints.
Allows querying available EV connector standards (CCS-2, Type 2, CHAdeMO, GB/T, etc.).
"""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.models.vehicle import ConnectorType
from backend.app.schemas.vehicle import ConnectorTypeResponse

router = APIRouter()


@router.get(
    "",
    response_model=List[ConnectorTypeResponse],
    summary="List available connector types"
)
def list_connector_types(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[ConnectorType]:
    """
    Retrieve all standardized EV connector types supported by the network.
    """
    connectors = db.query(ConnectorType).order_by(ConnectorType.connector_type_id.asc()).all()
    return connectors

