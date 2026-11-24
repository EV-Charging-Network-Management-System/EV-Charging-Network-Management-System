"""
Invoicing and Billing Endpoints.
Provides APIs for invoice generation, retrieval, payments, and revenue reporting.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.app.api.pagination import PageParam
from backend.app.api.deps import get_current_active_user, get_db
from backend.app.models.user import User
from backend.app.schemas.billing import (
    InvoiceResponse,
    PaymentResponse,
    PaymentCreate,
    RevenueReportResponse,
)
from backend.app.services.idempotency import IdempotencyKey, run_idempotent
from backend.app.services.billing_service import (
    generate_invoice_for_session,
    get_invoice_by_id,
    list_invoices,
    list_invoice_payments,
    process_invoice_payment,
    get_revenue_report,
)

router = APIRouter()


@router.post(
    "/generate/{session_id}",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate invoice for a completed charging session"
)
def generate_invoice(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate an immutable invoice snapshot for a completed charging session.
    Validates meter readings, resolves locked session pricing, and performs
    precise currency rounding (ROUND_HALF_UP).
    """
    return generate_invoice_for_session(
        session_id=session_id,
        current_user=current_user,
        db=db
    )


@router.get(
    "",
    response_model=List[InvoiceResponse],
    summary="List invoices with RBAC filtering"
)
def get_invoices(
    page: PageParam,
    status: Optional[str] = Query(None, description="Filter by status (UNPAID, PAID, VOID)"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List invoices based on user authorization:
    - CUSTOMER: View own invoices only.
    - OPERATOR: View invoices for managed charging stations.
    - ADMIN: View network-wide invoices.
    """
    return list_invoices(
        current_user=current_user,
        db=db,
        status_filter=status, page=page
    )


@router.get(
    "/reports/revenue",
    response_model=RevenueReportResponse,
    summary="Generate executive revenue and reconciliation report"
)
def get_revenue_summary(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Generate an executive revenue report clearly distinguishing billed revenue
    from confirmed collected payments.
    Accessible to Administrators and Station Operators.
    """
    return get_revenue_report(
        current_user=current_user,
        db=db
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    summary="Get invoice details by ID"
)
def get_invoice(
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve itemized invoice details including energy charges, taxes,
    session fees, and payment reconciliation status.
    """
    return get_invoice_by_id(
        invoice_id=invoice_id,
        current_user=current_user,
        db=db
    )


@router.get(
    "/{invoice_id}/payments",
    response_model=List[PaymentResponse],
    summary="List payment transaction attempts for an invoice"
)
def get_invoice_payments(
    page: PageParam,
    invoice_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Retrieve all payment attempts (SUCCESS, FAILED, REFUNDED) associated with an invoice.
    """
    return list_invoice_payments(
        invoice_id=invoice_id,
        current_user=current_user,
        db=db, page=page
    )


@router.post(
    "/{invoice_id}/payments",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit payment attempt for an invoice"
)
def pay_invoice(
    invoice_id: int,
    payload: PaymentCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
    idempotency_key: IdempotencyKey = None
):
    """
    Process a payment attempt against an unpaid invoice.
    Acquires an exclusive row-level lock on the invoice to serialize
    concurrent payments, prevent overpayment, and record idempotency keys.
    """
    return run_idempotent(
        db, current_user.user_id, f"invoice.payment:{invoice_id}", idempotency_key, payload,
        lambda: process_invoice_payment(
            invoice_id=invoice_id,
            payload=payload,
            current_user=current_user,
            db=db,
            commit=idempotency_key is None,
        ),
        lambda _: get_invoice_by_id(invoice_id, current_user, db),
    )
