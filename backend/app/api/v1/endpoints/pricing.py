"""
Dynamic Pricing Quote & Demand Calculation Endpoints.
Pure calculation engine that performs read-only pricing simulations without altering database state.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user
from backend.app.models.user import User
from backend.app.models.station import Station
from backend.app.schemas.tariff import (
    PricingQuoteRequest,
    PricingQuoteResponse,
    StationDemandResponse
)
from backend.app.services.pricing_service import (
    calculate_price_quote,
    calculate_station_demand,
    normalize_datetime
)

router = APIRouter()


@router.post(
    "/quote",
    response_model=PricingQuoteResponse,
    summary="Calculate dynamic pricing quote"
)
def get_pricing_quote(
    payload: PricingQuoteRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PricingQuoteResponse:
    """
    Simulate and calculate an itemized pricing quote for a charging session.
    
    Evaluates:
      1. Applicable base tariff (connector-specific vs station-wide)
      2. Station demand percentage (online vs active/reserved chargers)
      3. Dynamic pricing rules (PEAK_HOUR, OFF_PEAK, HIGH_DEMAND)
      4. Priority resolution and multiplier collision detection
      5. Complete math breakdown: energy charge, session fee, taxes, total
      
    This is a pure calculation endpoint: no database mutations or reservations are created.
    """
    try:
        quote = calculate_price_quote(
            station_id=payload.station_id,
            connector_type_id=payload.connector_type_id,
            estimated_energy_kwh=payload.estimated_energy_kwh,
            start_at=payload.start_at,
            end_at=payload.end_at,
            db=db
        )
        return quote
    except LookupError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValueError as e:
        err_msg = str(e)
        if "collision" in err_msg.lower():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=err_msg
            )
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=err_msg
        )


@router.get(
    "/demand",
    response_model=StationDemandResponse,
    summary="Get station demand percentage"
)
def get_station_demand(
    station_id: int = Query(..., description="Target charging station ID"),
    start_at: Optional[datetime] = Query(None, description="Start of window (defaults to now)"),
    end_at: Optional[datetime] = Query(None, description="End of window (defaults to start_at + 1h)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> StationDemandResponse:
    """
    Inspect real-time or projected station utilization and demand percentage.
    """
    station = db.get(Station, station_id)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Station with ID {station_id} not found."
        )

    norm_start = normalize_datetime(start_at)
    norm_end = normalize_datetime(end_at) if end_at is not None else norm_start + timedelta(hours=1)
    if norm_end <= norm_start:
        norm_end = norm_start + timedelta(hours=1)

    demand_info = calculate_station_demand(station_id, norm_start, norm_end, db)
    return StationDemandResponse(**demand_info)

