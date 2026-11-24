"""
Pricing Rules Management Endpoints.
Implements CRUD, querying, validation, and station ownership access control for dynamic pricing rules.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import select

from backend.app.api.pagination import PageParam
from backend.app.core.database import get_db
from backend.app.api.deps import get_current_active_user, require_operator_or_admin
from backend.app.models.user import User
from backend.app.models.tariff import Tariff, PricingRule
from backend.app.schemas.tariff import (
    PricingRuleCreate,
    PricingRuleUpdate,
    PricingRuleResponse
)

router = APIRouter()


@router.get(
    "",
    response_model=List[PricingRuleResponse],
    summary="List pricing rules with optional filters"
)
def list_pricing_rules(
    page: PageParam,
    tariff_id: Optional[int] = Query(None, description="Filter by parent tariff ID"),
    rule_type: Optional[str] = Query(None, description="Filter by rule type (PEAK_HOUR, OFF_PEAK, HIGH_DEMAND)"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive rules"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> List[PricingRule]:
    """
    List dynamic pricing rules across tariffs.
    Filterable by parent tariff, rule type, and active status.
    """
    query = select(PricingRule)

    if tariff_id is not None:
        query = query.where(PricingRule.tariff_id == tariff_id)
    if rule_type:
        query = query.where(PricingRule.rule_type == rule_type.strip().upper())
    if is_active is not None:
        query = query.where(PricingRule.is_active == is_active)

    rules = db.execute(page.apply(query.order_by(PricingRule.priority.desc(), PricingRule.rule_id.asc()))).scalars().all()
    return rules


@router.post(
    "",
    response_model=PricingRuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dynamic pricing rule"
)
def create_pricing_rule(
    payload: PricingRuleCreate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> PricingRule:
    """
    Attach a new dynamic pricing rule to an existing tariff.
    Operators can only configure rules for stations they operate. Admins can configure for any.
    Validates rule type, active hours, thresholds, and priority.
    """
    tariff = db.get(Tariff, payload.tariff_id)
    if not tariff:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent Tariff with ID {payload.tariff_id} not found."
        )

    # Ownership check
    if current_user.role == "OPERATOR" and tariff.station.operator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only configure pricing rules for stations you operate."
        )

    rule = PricingRule(
        tariff_id=payload.tariff_id,
        rule_type=payload.rule_type.upper(),
        start_time=payload.start_time,
        end_time=payload.end_time,
        demand_threshold_percent=payload.demand_threshold_percent,
        price_multiplier=payload.price_multiplier,
        priority=payload.priority,
        is_active=payload.is_active
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)

    return rule


@router.get(
    "/{rule_id}",
    response_model=PricingRuleResponse,
    summary="Get pricing rule details"
)
def get_pricing_rule(
    rule_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> PricingRule:
    """
    Retrieve pricing rule details by ID.
    """
    rule = db.get(PricingRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with ID {rule_id} not found."
        )
    return rule


@router.patch(
    "/{rule_id}",
    response_model=PricingRuleResponse,
    summary="Update pricing rule"
)
def update_pricing_rule(
    rule_id: int,
    payload: PricingRuleUpdate,
    current_user: User = Depends(require_operator_or_admin),
    db: Session = Depends(get_db)
) -> PricingRule:
    """
    Update pricing rule multiplier, priority, schedule, threshold, or active status.
    Operators can only update rules for their own stations. Admins can update any.
    """
    rule = db.get(PricingRule, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with ID {rule_id} not found."
        )

    if current_user.role == "OPERATOR" and rule.tariff.station.operator_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only update pricing rules for stations you operate."
        )

    if payload.price_multiplier is not None:
        rule.price_multiplier = payload.price_multiplier
    if payload.priority is not None:
        rule.priority = payload.priority
    if payload.is_active is not None:
        rule.is_active = payload.is_active
    if payload.start_time is not None:
        rule.start_time = payload.start_time
    if payload.end_time is not None:
        rule.end_time = payload.end_time
    if payload.demand_threshold_percent is not None:
        rule.demand_threshold_percent = payload.demand_threshold_percent

    db.commit()
    db.refresh(rule)
    return rule

