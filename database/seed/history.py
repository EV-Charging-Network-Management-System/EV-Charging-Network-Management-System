"""Add repeatable sample charging history to an explicitly chosen demo database."""

import argparse
import hashlib
import random
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from backend.app.core.database import SessionLocal
from backend.app.models.billing import Invoice, Payment
from backend.app.models.session import ChargingSession
from backend.app.models.station import Charger, Station
from backend.app.models.tariff import Tariff
from backend.app.models.user import User
from backend.app.models.vehicle import Vehicle, VehicleConnectorType
from backend.app.models.workflow import IdempotentOperation
from backend.app.services.pricing_service import round_currency

DEMO_EMAILS = ("ananya.demo@example.com", "karan.demo@example.com", "arjun.demo@example.com")
BATCH = hashlib.sha256(b"ev-demo-history-v1").hexdigest()


def generate_history() -> int:
    generator = random.Random(73024)
    midnight = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    with SessionLocal.begin() as db:
        options = db.execute(
            select(Vehicle, Charger, Station)
            .join(User, User.user_id == Vehicle.owner_user_id)
            .join(VehicleConnectorType, VehicleConnectorType.vehicle_id == Vehicle.vehicle_id)
            .join(Charger, Charger.connector_type_id == VehicleConnectorType.connector_type_id)
            .join(Station, Station.station_id == Charger.station_id)
            .where(User.email.in_(DEMO_EMAILS), Charger.operational_status == "ONLINE", Station.status == "ACTIVE")
            .order_by(Vehicle.vehicle_id, Charger.charger_id)
        ).all()
        if not options:
            raise RuntimeError("Load the demo station and vehicle data first.")
        seed_user_id = options[0].Vehicle.owner_user_id
        marker = db.scalar(insert(IdempotentOperation).values(
            user_id=seed_user_id, operation="seed.history", key_hash=BATCH, request_hash=BATCH,
            response={"days": 90},
        ).on_conflict_do_nothing().returning(IdempotentOperation.user_id))
        if marker is None:
            return 0

        tariffs = {}
        for tariff in db.scalars(select(Tariff).order_by(Tariff.valid_from, Tariff.tariff_id)):
            tariffs[tariff.station_id, tariff.connector_type_id] = tariff
        options = [
            (vehicle, charger, tariff)
            for vehicle, charger, station in options
            if (tariff := tariffs.get((station.station_id, charger.connector_type_id))
                or tariffs.get((station.station_id, None))) is not None
        ]
        if not options:
            raise RuntimeError("No compatible demo charger has a tariff.")

        for day in range(90, 0, -1):
            for hour in (3, 6, 10, 14):
                vehicle, charger, tariff = generator.choice(options)
                start = midnight - timedelta(days=day) + timedelta(hours=hour, minutes=generator.randrange(0, 30))
                finish = start + timedelta(minutes=generator.randrange(20, 71))
                energy = (Decimal(charger.power_kw) * Decimal(generator.randrange(20, 43)) / 60).quantize(Decimal("0.001"))
                if vehicle.battery_capacity_kwh:
                    energy = min(energy, vehicle.battery_capacity_kwh)
                session = ChargingSession(
                    user_id=vehicle.owner_user_id, vehicle_id=vehicle.vehicle_id, charger_id=charger.charger_id,
                    tariff_id=tariff.tariff_id, started_at=start, ended_at=finish, status="COMPLETED",
                    meter_start_kwh=Decimal(0), meter_end_kwh=energy,
                    locked_base_price_per_kwh=tariff.base_price_per_kwh, applied_rate_per_kwh=tariff.base_price_per_kwh,
                    locked_session_fee=tariff.session_fee, locked_tax_rate_percent=tariff.tax_rate_percent,
                    applied_multiplier=Decimal(1), applied_rule_type="STANDARD",
                )
                posted = round_currency(energy * tariff.base_price_per_kwh)
                subtotal = posted + tariff.session_fee
                tax = round_currency(subtotal * tariff.tax_rate_percent / 100)
                paid = generator.random() < 0.85
                invoice = Invoice(
                    session=session, energy_kwh=energy, price_per_kwh=tariff.base_price_per_kwh,
                    session_fee=tariff.session_fee, tax_rate_percent=tariff.tax_rate_percent,
                    energy_charge=posted, tax_amount=tax, total_amount=subtotal+tax,
                    status="PAID" if paid else "UNPAID", issued_at=finish,
                )
                db.add(invoice)
                if paid:
                    db.add(Payment(invoice=invoice, amount=invoice.total_amount, status="SUCCESS",
                                   payment_method="DEMO", created_at=finish, paid_at=finish))
        return 360


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-demo-database", action="store_true", required=True)
    parser.parse_args()
    print(f"Generated {generate_history()} synthetic sessions.")


if __name__ == "__main__":
    main()
