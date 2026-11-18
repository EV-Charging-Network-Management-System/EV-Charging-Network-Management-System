"""
Dynamic Pricing and Tariff Calculation Service.
Provides pure calculation engine, station demand calculation,
tariff resolution hierarchy, dynamic pricing rule evaluation, and conflict detection.
"""

from datetime import datetime, timezone, timedelta, time
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Tuple, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_

from backend.app.models.station import Station, Charger
from backend.app.models.tariff import Tariff, PricingRule
from backend.app.models.session import ChargingSession
from backend.app.models.reservation import Reservation
from backend.app.models.vehicle import ConnectorType
from backend.app.schemas.tariff import (
    PricingQuoteResponse,
    AppliedRuleInfo,
    StationDemandResponse
)


def normalize_datetime(dt: Optional[datetime]) -> datetime:
    """Ensure datetime is timezone-aware in UTC."""
    if dt is None:
        return datetime.now(timezone.utc)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def round_currency(val: Decimal) -> Decimal:
    """Round to 2 decimal places using standard financial ROUND_HALF_UP."""
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def check_tariff_overlap(
    station_id: int,
    connector_type_id: Optional[int],
    valid_from: datetime,
    valid_to: Optional[datetime],
    db: Session,
    exclude_tariff_id: Optional[int] = None
) -> bool:
    """
    Check if a tariff already exists for the given station and connector_type
    with an overlapping validity window.
    
    Two intervals [A_from, A_to] and [B_from, B_to] overlap if:
      (B_to IS NULL OR B_to > A_from) AND (A_to IS NULL OR B_from < A_to)
    """
    query = select(Tariff).where(
        Tariff.station_id == station_id,
        Tariff.connector_type_id == connector_type_id
    )
    if exclude_tariff_id is not None:
        query = query.where(Tariff.tariff_id != exclude_tariff_id)

    tariffs = db.execute(query).scalars().all()
    norm_from = normalize_datetime(valid_from)
    norm_to = normalize_datetime(valid_to) if valid_to is not None else None

    for t in tariffs:
        t_from = normalize_datetime(t.valid_from)
        t_to = normalize_datetime(t.valid_to) if t.valid_to is not None else None

        # Check overlap
        starts_before_existing_ends = (t_to is None) or (t_to > norm_from)
        ends_after_existing_starts = (norm_to is None) or (t_from < norm_to)

        if starts_before_existing_ends and ends_after_existing_starts:
            return True

    return False


def calculate_station_demand(
    station_id: int,
    start_at: datetime,
    end_at: datetime,
    db: Session
) -> Dict[str, Any]:
    """
    Calculate the dynamic demand percentage for a station during [start_at, end_at].
    
    demand_percentage = (occupied_chargers / total_online_chargers) * 100
    
    Occupied chargers:
      - Chargers currently in ACTIVE charging session
      - Chargers with overlapping CONFIRMED or PENDING reservations
    Avoids double-counting chargers that have both an active session and reservation.
    """
    norm_start = normalize_datetime(start_at)
    norm_end = normalize_datetime(end_at)

    # 1. Fetch chargers at station
    chargers = db.execute(
        select(Charger).where(Charger.station_id == station_id)
    ).scalars().all()

    online_chargers = [c for c in chargers if c.operational_status != "OUT_OF_SERVICE"]
    total_online = len(online_chargers)

    if total_online == 0:
        return {
            "station_id": station_id,
            "total_online_chargers": 0,
            "occupied_chargers": 0,
            "demand_percent": Decimal("0.00"),
            "as_of": norm_start
        }

    online_charger_ids = {c.charger_id for c in online_chargers}

    # 2. Find chargers with active sessions
    active_sessions = db.execute(
        select(ChargingSession.charger_id).where(
            ChargingSession.charger_id.in_(online_charger_ids),
            ChargingSession.status == "ACTIVE"
        )
    ).scalars().all()

    occupied_charger_ids = set(active_sessions)

    # 3. Find chargers with overlapping CONFIRMED or PENDING reservations
    # Overlap condition: res.start_at < norm_end AND res.end_at > norm_start
    overlapping_res = db.execute(
        select(Reservation.charger_id).where(
            Reservation.charger_id.in_(online_charger_ids),
            Reservation.status.in_(["CONFIRMED", "PENDING"]),
            Reservation.start_at < norm_end,
            Reservation.end_at > norm_start
        )
    ).scalars().all()

    # Avoid double-counting: set union
    occupied_charger_ids.update(overlapping_res)

    occupied_count = len(occupied_charger_ids)
    demand_pct = Decimal(str(round((occupied_count / total_online) * 100, 2))).quantize(Decimal("0.01"))

    return {
        "station_id": station_id,
        "total_online_chargers": total_online,
        "occupied_chargers": occupied_count,
        "demand_percent": demand_pct,
        "as_of": norm_start
    }


def select_applicable_tariff(
    station_id: int,
    connector_type_id: Optional[int],
    target_time: datetime,
    db: Session
) -> Optional[Tariff]:
    """
    Select the applicable tariff according to the hierarchy:
      1. Specific tariff for (station_id, connector_type_id) active at target_time
      2. If not found, station-wide tariff for (station_id, connector_type_id=NULL) active at target_time
    """
    norm_time = normalize_datetime(target_time)

    # First check connector-specific tariff if connector_type_id was requested
    if connector_type_id is not None:
        query = select(Tariff).where(
            Tariff.station_id == station_id,
            Tariff.connector_type_id == connector_type_id
        )
        candidates = db.execute(query).scalars().all()
        for t in candidates:
            t_from = normalize_datetime(t.valid_from)
            t_to = normalize_datetime(t.valid_to) if t.valid_to is not None else None
            if t_from <= norm_time and (t_to is None or t_to >= norm_time):
                return t

    # Fallback to station-wide default tariff (connector_type_id is NULL)
    query = select(Tariff).where(
        Tariff.station_id == station_id,
        Tariff.connector_type_id.is_(None)
    )
    candidates = db.execute(query).scalars().all()
    for t in candidates:
        t_from = normalize_datetime(t.valid_from)
        t_to = normalize_datetime(t.valid_to) if t.valid_to is not None else None
        if t_from <= norm_time and (t_to is None or t_to >= norm_time):
            return t

    return None


def evaluate_pricing_rules(
    tariff: Tariff,
    target_time: datetime,
    station_demand_percent: Decimal
) -> Tuple[Decimal, Optional[PricingRule]]:
    """
    Evaluate all active pricing rules for the selected tariff.
    
    Supports:
      - PEAK_HOUR: active if target_time.time() falls within [start_time, end_time]
      - OFF_PEAK: active if target_time.time() falls within [start_time, end_time]
      - HIGH_DEMAND: active if station_demand_percent >= demand_threshold_percent
      
    Priority resolution:
      - Highest priority rule wins (highest priority integer).
      - Collision detection: If multiple conflicting rules share the highest priority
        and have different multipliers, raise ValueError.
      - If no rule matches, multiplier = Decimal("1.000"), rule = None.
    """
    active_rules = [r for r in tariff.pricing_rules if r.is_active]
    if not active_rules:
        return Decimal("1.000"), None

    t_time = target_time.time()
    matching_rules: List[PricingRule] = []

    for rule in active_rules:
        rule_type = rule.rule_type.upper()
        if rule_type in ("PEAK_HOUR", "OFF_PEAK"):
            if rule.start_time is not None and rule.end_time is not None:
                if rule.start_time <= rule.end_time:
                    # Standard intra-day interval
                    if rule.start_time <= t_time <= rule.end_time:
                        matching_rules.append(rule)
                else:
                    # Overnight interval (e.g. 22:00 to 06:00)
                    if t_time >= rule.start_time or t_time <= rule.end_time:
                        matching_rules.append(rule)

        elif rule_type == "HIGH_DEMAND":
            if rule.demand_threshold_percent is not None:
                if station_demand_percent >= rule.demand_threshold_percent:
                    matching_rules.append(rule)

    if not matching_rules:
        return Decimal("1.000"), None

    # Find highest priority
    max_priority = max(r.priority for r in matching_rules)
    top_candidates = [r for r in matching_rules if r.priority == max_priority]

    if len(top_candidates) > 1:
        # Check for multiplier collision
        distinct_multipliers = {r.price_multiplier for r in top_candidates}
        if len(distinct_multipliers) > 1:
            conflict_types = [r.rule_type for r in top_candidates]
            raise ValueError(
                f"Pricing rule collision: Multiple rules ({', '.join(conflict_types)}) "
                f"share the same highest priority ({max_priority}) with different multipliers."
            )

    selected_rule = top_candidates[0]
    return selected_rule.price_multiplier, selected_rule


def calculate_price_quote(
    station_id: int,
    connector_type_id: Optional[int],
    estimated_energy_kwh: Decimal,
    start_at: Optional[datetime],
    end_at: Optional[datetime],
    db: Session
) -> PricingQuoteResponse:
    """
    Calculate an itemized pricing quote for a charging session without modifying state.
    """
    norm_start = normalize_datetime(start_at)
    norm_end = normalize_datetime(end_at) if end_at is not None else norm_start + timedelta(hours=1)

    if norm_end <= norm_start:
        norm_end = norm_start + timedelta(hours=1)

    # 1. Validate station exists
    station = db.get(Station, station_id)
    if not station:
        raise ValueError(f"Station with ID {station_id} does not exist.")

    # 2. Validate connector type if provided
    connector_name: Optional[str] = None
    if connector_type_id is not None:
        connector = db.get(ConnectorType, connector_type_id)
        if not connector:
            raise ValueError(f"ConnectorType with ID {connector_type_id} does not exist.")
        connector_name = connector.type_name

    # 3. Calculate station demand
    demand_info = calculate_station_demand(station_id, norm_start, norm_end, db)
    demand_pct = demand_info["demand_percent"]

    # 4. Resolve applicable tariff
    tariff = select_applicable_tariff(station_id, connector_type_id, norm_start, db)
    if not tariff:
        desc = f"connector type ID {connector_type_id}" if connector_type_id else "station default"
        raise LookupError(
            f"No active tariff found for station '{station.station_name}' (ID: {station_id}) "
            f"and {desc} at requested time {norm_start.isoformat()}."
        )

    # 5. Evaluate dynamic pricing rules
    multiplier, applied_rule = evaluate_pricing_rules(tariff, norm_start, demand_pct)

    # 6. Math breakdown
    base_price = tariff.base_price_per_kwh
    effective_rate = round_currency(base_price * multiplier)
    energy_charge = round_currency(estimated_energy_kwh * effective_rate)
    session_fee = round_currency(tariff.session_fee)
    subtotal = round_currency(energy_charge + session_fee)
    tax_rate = tariff.tax_rate_percent
    tax_amount = round_currency(subtotal * (tax_rate / Decimal("100")))
    total_amount = round_currency(subtotal + tax_amount)

    applied_info: Optional[AppliedRuleInfo] = None
    if applied_rule is not None:
        applied_info = AppliedRuleInfo(
            rule_id=applied_rule.rule_id,
            rule_type=applied_rule.rule_type,
            price_multiplier=applied_rule.price_multiplier,
            priority=applied_rule.priority,
            description=f"{applied_rule.rule_type} multiplier {applied_rule.price_multiplier}x applied (priority {applied_rule.priority})"
        )

    return PricingQuoteResponse(
        station_id=station.station_id,
        station_name=station.station_name,
        tariff_id=tariff.tariff_id,
        connector_type_id=tariff.connector_type_id,
        connector_type_name=connector_name or (tariff.connector_type.type_name if tariff.connector_type else None),
        base_price_per_kwh=base_price,
        multiplier=multiplier,
        effective_rate_per_kwh=effective_rate,
        estimated_energy_kwh=estimated_energy_kwh,
        energy_charge=energy_charge,
        session_fee=session_fee,
        subtotal=subtotal,
        tax_rate_percent=tax_rate,
        tax_amount=tax_amount,
        total_amount=total_amount,
        currency="INR",
        station_demand_percent=demand_pct,
        applied_rule=applied_info,
        calculation_timestamp=datetime.now(timezone.utc)
    )
