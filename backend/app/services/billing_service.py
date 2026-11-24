"""
Billing and Invoicing Service.
Handles transactional invoice generation, financial rounding (ROUND_HALF_UP),
payment processing via simulated gateway, reconciliation, and revenue reporting.
"""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import select, func, and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from backend.app.api.pagination import Page
from backend.app.models.billing import Invoice, Payment
from backend.app.models.session import ChargingSession
from backend.app.models.station import Station, Charger
from backend.app.models.tariff import Tariff
from backend.app.models.user import User
from backend.app.models.workflow import AdminAuditEvent
from backend.app.schemas.billing import (
    InvoiceResponse,
    InvoiceCustomerInfo,
    InvoiceStationInfo,
    PaymentResponse,
    PaymentCreate,
    RevenueReportResponse,
    DailyRevenue,
    MonthlyRevenue,
    StationRevenue,
    PaymentMethodBreakdown,
)
from backend.app.services.pricing_service import evaluate_pricing_rules, normalize_datetime


def quantize_currency(value: Any) -> Decimal:
    """Quantize financial values to 2 decimal places using ROUND_HALF_UP."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def quantize_energy(value: Any) -> Decimal:
    """Quantize energy metering to 3 decimal places using ROUND_HALF_UP."""
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return value.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def format_invoice_response(invoice: Invoice) -> InvoiceResponse:
    """Format an Invoice ORM object into a comprehensive InvoiceResponse schema."""
    customer_info = None
    station_info = None

    if invoice.session and invoice.session.user:
        customer_info = InvoiceCustomerInfo(
            user_id=invoice.session.user.user_id,
            full_name=invoice.session.user.full_name,
            email=invoice.session.user.email,
            phone=invoice.session.user.phone,
        )

    if invoice.session and invoice.session.charger:
        charger = invoice.session.charger
        station = charger.station
        if station:
            station_info = InvoiceStationInfo(
                station_id=station.station_id,
                station_name=station.station_name,
                charger_id=charger.charger_id,
                charger_code=charger.charger_code,
                address=station.address,
                city=station.city,
            )

    payments_list = [PaymentResponse.model_validate(p) for p in (invoice.payments or [])]
    successful_payments = sum((p.amount for p in (invoice.payments or []) if p.status == "SUCCESS"), Decimal("0.00"))
    balance_due = max(Decimal("0.00"), invoice.total_amount - successful_payments)

    return InvoiceResponse(
        invoice_id=invoice.invoice_id,
        invoice_number=f"INV-{invoice.invoice_id:06d}",
        session_id=invoice.session_id,
        energy_kwh=invoice.energy_kwh,
        price_per_kwh=invoice.price_per_kwh,
        session_fee=invoice.session_fee,
        tax_rate_percent=invoice.tax_rate_percent,
        energy_charge=invoice.energy_charge,
        tax_amount=invoice.tax_amount,
        total_amount=invoice.total_amount,
        status=invoice.status,
        issued_at=invoice.issued_at,
        customer=customer_info,
        station=station_info,
        amount_paid=quantize_currency(successful_payments),
        balance_due=quantize_currency(balance_due),
        payments=payments_list,
    )


def generate_invoice_for_session(
    session_id: int,
    current_user: User | None,
    db: Session
) -> InvoiceResponse:
    """
    Generate an immutable invoice snapshot for a completed charging session.
    Acquires a row-level lock on the charging session and strictly validates
    final meter readings and locked tariff rates.
    """
    # 1. Row-level lock on ChargingSession
    session_obj = db.execute(
        select(ChargingSession)
        .where(ChargingSession.session_id == session_id)
        .with_for_update(of=ChargingSession)
    ).scalar_one_or_none()

    if not session_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Charging session #{session_id} not found."
        )

    # 2. Authorization Verification
    if current_user is not None and current_user.role == "CUSTOMER" and session_obj.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: You can only generate invoices for your own charging sessions."
        )
    elif current_user is not None and current_user.role == "OPERATOR":
        if (
            session_obj.charger
            and session_obj.charger.station
            and session_obj.charger.station.operator_id != current_user.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only generate invoices for sessions at stations you manage."
            )

    # 3. Session Status Validation (Must be completed/billable)
    if session_obj.status == "ACTIVE":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot generate invoice: Charging session #{session_id} is currently ACTIVE. The session must be COMPLETED or INTERRUPTED with final meter readings."
        )

    # 4. Final Meter Reading Validation
    if session_obj.meter_end_kwh is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing final meter reading: Final meter reading (meter_end_kwh) is required to generate an invoice."
        )

    if session_obj.meter_end_kwh < session_obj.meter_start_kwh:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid meter reading: Final meter reading cannot be lower than starting meter reading."
        )

    # 5. Check Duplicate Invoice
    existing_invoice = db.execute(
        select(Invoice).where(Invoice.session_id == session_id)
    ).scalars().first()

    if existing_invoice:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate invoice rejected: An invoice has already been generated for charging session #{session_id} (Invoice #{existing_invoice.invoice_id})."
        )

    # 6. Retrieve Locked Pricing Snapshot Values
    if session_obj.applied_rate_per_kwh is not None:
        price_per_kwh = quantize_currency(Decimal(str(session_obj.applied_rate_per_kwh)))
        session_fee = quantize_currency(Decimal(str(session_obj.locked_session_fee or "0.00")))
        tax_rate_percent = Decimal(str(session_obj.locked_tax_rate_percent or "0.00"))
    else:
        # Resolve from the session's assigned historical Tariff record
        tariff = session_obj.tariff or db.get(Tariff, session_obj.tariff_id)
        if not tariff:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing locked pricing: No tariff associated with session #{session_id}."
            )

        # Ensure the session's tariff was valid at session.started_at
        started_at = normalize_datetime(session_obj.started_at)
        t_valid_from = normalize_datetime(tariff.valid_from)
        t_valid_to = normalize_datetime(tariff.valid_to) if tariff.valid_to else None
        if started_at < t_valid_from or (t_valid_to and started_at > t_valid_to):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Missing locked pricing: Assigned tariff #{tariff.tariff_id} was not active when session #{session_id} started ({started_at.isoformat()}). Historical accepted rate cannot be determined."
            )

        # Evaluate applicable pricing rules at the session start timestamp
        rule_multiplier, active_rule = evaluate_pricing_rules(
            tariff=tariff,
            target_time=started_at,
            station_demand_percent=Decimal("0.00")
        )
        price_per_kwh = quantize_currency(tariff.base_price_per_kwh * rule_multiplier)
        session_fee = quantize_currency(tariff.session_fee)
        tax_rate_percent = tariff.tax_rate_percent

    # 7. Financial Formula Calculations (ROUND_HALF_UP)
    # energy_kwh = meter_end_kwh - meter_start_kwh
    energy_kwh = quantize_energy(session_obj.meter_end_kwh - session_obj.meter_start_kwh)

    # energy_charge = energy_kwh * price_per_kwh
    energy_charge = quantize_currency(energy_kwh * price_per_kwh)

    # subtotal = energy_charge + session_fee
    subtotal = quantize_currency(energy_charge + session_fee)

    # tax_amount = subtotal * tax_rate_percent / 100
    tax_amount = quantize_currency(subtotal * tax_rate_percent / Decimal("100"))

    # total_amount = subtotal + tax_amount
    total_amount = quantize_currency(subtotal + tax_amount)

    # 8. Create and Persist Invoice Transactionally
    invoice = Invoice(
        session_id=session_id,
        energy_kwh=energy_kwh,
        price_per_kwh=price_per_kwh,
        session_fee=session_fee,
        tax_rate_percent=tax_rate_percent,
        energy_charge=energy_charge,
        tax_amount=tax_amount,
        total_amount=total_amount,
        status="UNPAID",
        issued_at=datetime.now(timezone.utc),
    )

    db.add(invoice)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Duplicate invoice rejected: An invoice for session #{session_id} was created concurrently."
        )

    db.refresh(invoice)
    return format_invoice_response(invoice)


def get_invoice_by_id(
    invoice_id: int,
    current_user: User,
    db: Session
) -> InvoiceResponse:
    """Retrieve detailed invoice snapshot by ID with strict RBAC access control."""
    invoice = db.get(Invoice, invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )

    # RBAC Authorization
    if current_user.role == "CUSTOMER":
        if not invoice.session or invoice.session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only view your own invoices."
            )
    elif current_user.role == "OPERATOR":
        if (
            not invoice.session
            or not invoice.session.charger
            or not invoice.session.charger.station
            or invoice.session.charger.station.operator_id != current_user.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only view invoices for stations under your management."
            )

    return format_invoice_response(invoice)


def list_invoices(
    current_user: User,
    db: Session,
    status_filter: Optional[str] = None,
    page: Page = Page(),
) -> List[InvoiceResponse]:
    """List invoices filtered by user role and optional payment status."""
    stmt = select(Invoice).join(ChargingSession, Invoice.session_id == ChargingSession.session_id)

    if current_user.role == "CUSTOMER":
        stmt = stmt.where(ChargingSession.user_id == current_user.user_id)
    elif current_user.role == "OPERATOR":
        stmt = stmt.join(Charger, ChargingSession.charger_id == Charger.charger_id).join(
            Station, Charger.station_id == Station.station_id
        ).where(Station.operator_id == current_user.user_id)

    if status_filter:
        stmt = stmt.where(Invoice.status == status_filter.upper())

    stmt = page.apply(stmt.order_by(Invoice.issued_at.desc(), Invoice.invoice_id.desc()))
    invoices = db.execute(stmt).scalars().all()

    return [format_invoice_response(inv) for inv in invoices]


def list_invoice_payments(
    invoice_id: int,
    current_user: User,
    db: Session,
    page: Page = Page(),
) -> List[PaymentResponse]:
    """Retrieve payment audit history for a specific invoice."""
    # Enforces invoice access rules
    get_invoice_by_id(invoice_id, current_user, db)

    payments = db.execute(
        page.apply(select(Payment).where(Payment.invoice_id == invoice_id)
                   .order_by(Payment.created_at.asc(), Payment.payment_id.asc()))
    ).scalars().all()

    return [PaymentResponse.model_validate(p) for p in payments]


# ============================================================================
# PAYMENT PROVIDER ABSTRACTION & SIMULATED GATEWAY ADAPTER
# ============================================================================

class PaymentGateway(ABC):
    """Abstract interface for payment gateway integration."""

    @abstractmethod
    def process_transaction(
        self,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        transaction_reference: str,
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        """Process or simulate a payment attempt."""
        pass


class DemoPaymentGateway(PaymentGateway):
    """
    Simulated payment provider for academic and demonstration purposes.
    The server determines simulated success or failure based on gateway criteria.
    """

    def process_transaction(
        self,
        invoice: Invoice,
        amount: Decimal,
        payment_method: str,
        transaction_reference: str,
        simulate_failure: bool = False
    ) -> Dict[str, Any]:
        ref_upper = transaction_reference.upper()

        # Simulated failure triggers: explicit flag or test reference conventions
        if simulate_failure or "-FAIL" in ref_upper or "DECLINE" in ref_upper:
            return {
                "success": False,
                "status": "FAILED",
                "error_code": "SIMULATED_DECLINE",
                "error_message": "Payment simulation: Transaction was declined by the simulated card issuer / bank.",
                "paid_at": None,
            }

        # Successful simulation
        return {
            "success": True,
            "status": "SUCCESS",
            "paid_at": datetime.now(timezone.utc),
            "error_code": None,
            "error_message": None,
        }


# ============================================================================
# PAYMENT RECONCILIATION & TRANSACTION MANAGEMENT
# ============================================================================

def process_invoice_payment(
    invoice_id: int,
    payload: PaymentCreate,
    current_user: User,
    db: Session,
    *,
    commit: bool = True,
) -> PaymentResponse:
    """
    Process and reconcile an invoice payment attempt.
    Acquires an exclusive row-level lock on the invoice (SELECT FOR UPDATE)
    to serialize concurrent payment attempts and prevent overpayment.
    """
    # 1. Exclusive row-level lock on the target Invoice
    invoice = db.execute(
        select(Invoice)
        .where(Invoice.invoice_id == invoice_id)
        .with_for_update(of=Invoice)
    ).scalar_one_or_none()

    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice #{invoice_id} not found."
        )

    # 2. Authorization Verification
    if current_user.role == "CUSTOMER":
        if not invoice.session or invoice.session.user_id != current_user.user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only pay your own invoices."
            )
    elif current_user.role == "OPERATOR":
        if (
            not invoice.session
            or not invoice.session.charger
            or not invoice.session.charger.station
            or invoice.session.charger.station.operator_id != current_user.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You cannot process payments for stations you do not manage."
            )

    # 3. Check Invoice Status (Overpayment Prevention)
    if invoice.status == "PAID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Overpayment prevented: Invoice #{invoice_id} has already been paid in full."
        )
    if invoice.status == "VOID":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot accept payment: Invoice #{invoice_id} is marked VOID."
        )

    # 4. Calculate Current Confirmed Payments and Remaining Balance
    existing_payments = db.execute(
        select(Payment)
        .where(Payment.invoice_id == invoice_id)
    ).scalars().all()

    total_confirmed = sum(p.amount for p in existing_payments if p.status == "SUCCESS")
    remaining_balance = quantize_currency(invoice.total_amount - total_confirmed)

    if remaining_balance <= Decimal("0.00"):
        invoice.status = "PAID"
        if commit:
            db.commit()
        else:
            db.flush()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Overpayment prevented: Invoice #{invoice_id} has no remaining balance."
        )

    # 5. Determine Payment Amount
    if payload.amount is not None:
        pay_amount = quantize_currency(payload.amount)
        if pay_amount <= Decimal("0.00"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Payment amount must be greater than zero."
            )
        if pay_amount > remaining_balance:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Overpayment prevented: Submitted amount ₹{pay_amount} exceeds remaining invoice balance of ₹{remaining_balance}."
            )
    else:
        # Default to full outstanding balance
        pay_amount = remaining_balance

    # 6. Idempotency Key & Transaction Reference Verification
    if payload.transaction_reference:
        txn_ref = payload.transaction_reference.strip()
        existing_ref = db.execute(
            select(Payment).where(Payment.transaction_reference == txn_ref)
        ).scalar_one_or_none()

        if existing_ref:
            if existing_ref.status == "SUCCESS":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Duplicate transaction reference: Reference '{txn_ref}' has already been processed successfully."
                )
            elif existing_ref.status == "FAILED":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Duplicate transaction reference: Reference '{txn_ref}' was previously recorded as FAILED. Please submit a new reference to retry."
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Transaction reference '{txn_ref}' already exists with status {existing_ref.status}."
                )
    else:
        txn_ref = f"DEMO-TXN-{uuid.uuid4().hex[:10].upper()}"

    # 7. Execute Gateway Provider
    gateway = DemoPaymentGateway()
    gw_result = gateway.process_transaction(
        invoice=invoice,
        amount=pay_amount,
        payment_method=payload.payment_method,
        transaction_reference=txn_ref,
        simulate_failure=payload.simulate_failure,
    )

    # 8. Record Payment Attempt
    payment = Payment(
        invoice_id=invoice_id,
        amount=pay_amount,
        payment_method=payload.payment_method,
        transaction_reference=txn_ref,
        status=gw_result["status"],
        created_at=datetime.now(timezone.utc),
        paid_at=gw_result.get("paid_at"),
    )
    db.add(payment)

    # 9. Reconcile Invoice Status
    if gw_result["status"] == "SUCCESS":
        new_confirmed = total_confirmed + pay_amount
        if new_confirmed >= invoice.total_amount:
            invoice.status = "PAID"
    else:
        # Ensure invoice remains UNPAID on failed attempts
        if invoice.status != "PAID":
            invoice.status = "UNPAID"

    try:
        if commit:
            db.commit()
        else:
            db.flush()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Transaction conflict: Could not complete payment recording due to a concurrent database conflict."
        )

    db.refresh(payment)
    return PaymentResponse.model_validate(payment)


def get_payment_by_id(
    payment_id: int,
    current_user: User,
    db: Session
) -> PaymentResponse:
    """Retrieve detailed payment record by ID with RBAC check."""
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment #{payment_id} not found."
        )

    # Verify authorization through parent invoice
    if payment.invoice:
        get_invoice_by_id(payment.invoice_id, current_user, db)

    return PaymentResponse.model_validate(payment)


def list_all_payments(
    current_user: User,
    db: Session,
    status_filter: Optional[str] = None,
    page: Page = Page(),
) -> List[PaymentResponse]:
    """List payments with role-based visibility."""
    stmt = select(Payment).join(Invoice, Payment.invoice_id == Invoice.invoice_id).join(
        ChargingSession, Invoice.session_id == ChargingSession.session_id
    )

    if current_user.role == "CUSTOMER":
        stmt = stmt.where(ChargingSession.user_id == current_user.user_id)
    elif current_user.role == "OPERATOR":
        stmt = stmt.join(Charger, ChargingSession.charger_id == Charger.charger_id).join(
            Station, Charger.station_id == Station.station_id
        ).where(Station.operator_id == current_user.user_id)

    if status_filter:
        stmt = stmt.where(Payment.status == status_filter.upper())

    stmt = page.apply(stmt.order_by(Payment.created_at.desc(), Payment.payment_id.desc()))
    payments = db.execute(stmt).scalars().all()

    return [PaymentResponse.model_validate(p) for p in payments]


# ============================================================================
# REFUND PROCESSING (TASK 6)
# ============================================================================

def refund_payment(
    payment_id: int,
    reason: Optional[str],
    current_user: User,
    db: Session
) -> PaymentResponse:
    """
    Execute a refund for a previously successful payment.
    Enforces that only SUCCESS payments can be refunded, prevents duplicate
    refunds, and updates invoice reconciliation state transactionally.
    """
    if current_user.role not in ("ADMIN", "OPERATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Only Station Operators and Administrators can process payment refunds."
        )

    # 1. Row-level lock on Payment
    payment = db.execute(
        select(Payment)
        .where(Payment.payment_id == payment_id)
        .with_for_update(of=Payment)
    ).scalar_one_or_none()

    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Payment #{payment_id} not found."
        )

    # 2. Operator Station Authorization
    if current_user.role == "OPERATOR":
        if (
            payment.invoice
            and payment.invoice.session
            and payment.invoice.session.charger
            and payment.invoice.session.charger.station
            and payment.invoice.session.charger.station.operator_id != current_user.user_id
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: You can only refund payments for stations you manage."
            )

    # 3. Status Validation
    if payment.status == "REFUNDED":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payment #{payment_id} has already been refunded."
        )
    if payment.status != "SUCCESS":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot refund payment with status '{payment.status}'. Only successful payments can be refunded."
        )

    # 4. Row-level lock on Invoice
    invoice = db.execute(
        select(Invoice)
        .where(Invoice.invoice_id == payment.invoice_id)
        .with_for_update(of=Invoice)
    ).scalar_one()

    # 5. Transition Payment Status to REFUNDED
    payment.status = "REFUNDED"

    # 6. Reconcile Invoice Status
    all_payments = db.execute(
        select(Payment).where(Payment.invoice_id == invoice.invoice_id)
    ).scalars().all()

    remaining_confirmed = sum(
        p.amount for p in all_payments if p.status == "SUCCESS" and p.payment_id != payment_id
    )

    if remaining_confirmed < invoice.total_amount:
        invoice.status = "UNPAID"

    db.add(AdminAuditEvent(
        actor_id=current_user.user_id, action="payment.refunded", resource_id=payment_id, details={"invoice_id": invoice.invoice_id, "amount": str(payment.amount)},
    ))
    db.commit()
    db.refresh(payment)
    return PaymentResponse.model_validate(payment)


# ============================================================================
# REVENUE & RECONCILIATION REPORTING (TASK 8)
# ============================================================================

def get_revenue_report(
    current_user: User,
    db: Session
) -> RevenueReportResponse:
    """
    Generate an executive revenue report clearly distinguishing billed revenue
    from confirmed collected revenue.
    """
    if current_user.role not in ("ADMIN", "OPERATOR"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Revenue reports are restricted to Operators and Administrators."
        )

    # Filter base query by operator if not admin
    inv_stmt = select(Invoice).join(ChargingSession, Invoice.session_id == ChargingSession.session_id)
    pay_stmt = select(Payment).join(Invoice, Payment.invoice_id == Invoice.invoice_id).join(
        ChargingSession, Invoice.session_id == ChargingSession.session_id
    )

    if current_user.role == "OPERATOR":
        inv_stmt = inv_stmt.join(Charger, ChargingSession.charger_id == Charger.charger_id).join(
            Station, Charger.station_id == Station.station_id
        ).where(Station.operator_id == current_user.user_id)

        pay_stmt = pay_stmt.join(Charger, ChargingSession.charger_id == Charger.charger_id).join(
            Station, Charger.station_id == Station.station_id
        ).where(Station.operator_id == current_user.user_id)

    invoices = db.execute(inv_stmt).scalars().all()
    payments = db.execute(pay_stmt).scalars().all()

    # Billed revenue (exclude VOID)
    active_invoices = [inv for inv in invoices if inv.status != "VOID"]
    total_billed = sum((inv.total_amount for inv in active_invoices), Decimal("0.00"))

    # Confirmed collected revenue (only SUCCESS payments)
    success_payments = [p for p in payments if p.status == "SUCCESS"]
    total_collected = sum((p.amount for p in success_payments), Decimal("0.00"))

    # Outstanding balance
    outstanding = max(Decimal("0.00"), total_billed - total_collected)

    failed_count = sum(1 for p in payments if p.status == "FAILED")
    refunded_count = sum(1 for p in payments if p.status == "REFUNDED")

    # Daily aggregation
    daily_map: Dict[str, Dict[str, Any]] = {}
    for inv in active_invoices:
        d_str = inv.issued_at.strftime("%Y-%m-%d") if inv.issued_at else "Unknown"
        if d_str not in daily_map:
            daily_map[d_str] = {"amount": Decimal("0.00"), "count": 0}
        daily_map[d_str]["amount"] += inv.total_amount
        daily_map[d_str]["count"] += 1

    daily_revenue = [
        DailyRevenue(date=k, amount=quantize_currency(v["amount"]), invoice_count=v["count"])
        for k, v in sorted(daily_map.items())
    ]

    # Monthly aggregation
    monthly_map: Dict[str, Dict[str, Any]] = {}
    for inv in active_invoices:
        m_str = inv.issued_at.strftime("%Y-%m") if inv.issued_at else "Unknown"
        if m_str not in monthly_map:
            monthly_map[m_str] = {"amount": Decimal("0.00"), "count": 0}
        monthly_map[m_str]["amount"] += inv.total_amount
        monthly_map[m_str]["count"] += 1

    monthly_revenue = [
        MonthlyRevenue(month=k, amount=quantize_currency(v["amount"]), invoice_count=v["count"])
        for k, v in sorted(monthly_map.items())
    ]

    # Station-wise revenue
    station_map: Dict[int, Dict[str, Any]] = {}
    for inv in active_invoices:
        st = None
        if inv.session and inv.session.charger and inv.session.charger.station:
            st = inv.session.charger.station

        st_id = st.station_id if st else 0
        st_name = st.station_name if st else "Unassigned"
        st_city = st.city if st else "Unknown"

        if st_id not in station_map:
            station_map[st_id] = {
                "name": st_name,
                "city": st_city,
                "billed": Decimal("0.00"),
                "collected": Decimal("0.00"),
                "count": 0,
            }
        station_map[st_id]["billed"] += inv.total_amount
        station_map[st_id]["count"] += 1

    for p in success_payments:
        inv = p.invoice
        st = None
        if inv and inv.session and inv.session.charger and inv.session.charger.station:
            st = inv.session.charger.station
        st_id = st.station_id if st else 0
        if st_id in station_map:
            station_map[st_id]["collected"] += p.amount

    station_wise = [
        StationRevenue(
            station_id=k,
            station_name=v["name"],
            city=v["city"],
            total_billed=quantize_currency(v["billed"]),
            total_collected=quantize_currency(v["collected"]),
            session_count=v["count"],
        )
        for k, v in station_map.items()
    ]

    # Payment method breakdown
    method_map: Dict[str, Dict[str, Any]] = {}
    for p in success_payments:
        m = p.payment_method
        if m not in method_map:
            method_map[m] = {"amount": Decimal("0.00"), "count": 0}
        method_map[m]["amount"] += p.amount
        method_map[m]["count"] += 1

    payment_method_breakdown = [
        PaymentMethodBreakdown(
            payment_method=k,
            total_collected=quantize_currency(v["amount"]),
            transaction_count=v["count"],
        )
        for k, v in sorted(method_map.items())
    ]

    return RevenueReportResponse(
        total_billed_revenue=quantize_currency(total_billed),
        total_collected_revenue=quantize_currency(total_collected),
        outstanding_invoice_amount=quantize_currency(outstanding),
        failed_payment_count=failed_count,
        refunded_payment_count=refunded_count,
        daily_revenue=daily_revenue,
        monthly_revenue=monthly_revenue,
        station_wise_revenue=station_wise,
        payment_method_breakdown=payment_method_breakdown,
        note="Billed revenue represents total invoiced charges; collected revenue represents confirmed payments minus refunds.",
    )
