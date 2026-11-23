"""Load sample records and turn their disabled credentials into Argon2 hashes."""

import argparse
import secrets
from pathlib import Path

from sqlalchemy import text

from backend.app.core.database import engine
from backend.app.core.security import get_password_hash

SEED = Path(__file__).with_name("EV_Charging_Insert_Dummy_Data.sql")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--confirm-demo-database", action="store_true", required=True)
    args = parser.parse_args()
    if not args.confirm_demo_database:
        parser.error("Choose the demo database explicitly.")
    with engine.begin() as connection:
        connection.exec_driver_sql("LOCK TABLE users IN SHARE ROW EXCLUSIVE MODE")
        if not connection.execute(text("SELECT EXISTS (SELECT FROM users)")).scalar_one():
            sql = SEED.read_text(encoding="utf-8").split("BEGIN;", 1)[1].split("COMMIT;", 1)[0]
            connection.exec_driver_sql(sql)
        users = connection.execute(text(
            "SELECT email, role FROM users WHERE password_hash IN "
            "('demo_placeholder_1', 'demo_placeholder_2', 'demo_placeholder_3', "
            "'demo_placeholder_4', 'demo_placeholder_5') ORDER BY user_id"
        )).all()
        credentials = []
        for email, role in users:
            password = secrets.token_urlsafe(20)
            connection.execute(text("UPDATE users SET password_hash = :hash WHERE email = :email"),
                               {"hash": get_password_hash(password), "email": email})
            credentials.append((role, email, password))
    for role, email, password in credentials:
        print(f"{role} {email} {password}")
    if not credentials:
        print("No uninitialized demo users found.")


if __name__ == "__main__":
    main()
