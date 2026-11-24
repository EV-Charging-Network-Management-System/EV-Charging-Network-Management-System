"""
Payment Management Endpoints.
Provides APIs for inspecting transaction attempts and executing authorized refunds.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.pagination import PageParam
from backend.app.api.deps import get_current_active_user, get_db
from backend.app.models.user import User
from backend.app.schemas.billing import PaymentResponse, PaymentRefundRequest
from backend.app.services.billing_service import (
    list_all_payments,
    get_payment_by_id,
    refund_payment,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[PaymentResponse],
    summary="List payment records"
)
def get_payments(
    page: PageParam,
    status: Optional[str] = Query(None, description="Filter by payment status (PENDING, SUCCESS, FAILED, REFUNDED)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List payment transactions with RBAC filtering:
    - CUSTOMER: View own payment transactions.
    - OPERATOR: View transactions for managed stations.
    - ADMIN: View network-wide transactions.
    """
    return list_all_payments(
        current_user=current_user,
        db=db,
        status_filter=status, page=page
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    summary="Get payment details by ID"
)
def get_payment(
    payment_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve specific payment transaction details and audit log.
    """
    return get_payment_by_id(
        payment_id=payment_id,
        current_user=current_user,
        db=db
    )


@router.post(
    "/{payment_id}/refund",
    response_model=PaymentResponse,
    summary="Refund a confirmed payment transaction"
)
def process_refund(
    payment_id: int,
    payload: Optional[PaymentRefundRequest] = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Refund a previously confirmed (SUCCESS) payment transaction.
    Reconciles parent invoice status and prevents double-refunding.
    Restricted to Station Operators and Administrators.
    """
    reason = payload.reason if payload else "Customer requested refund"
    return refund_payment(
        payment_id=payment_id,
        reason=reason,
        current_user=current_user,
        db=db
    )

