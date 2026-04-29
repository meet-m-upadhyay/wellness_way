"""
Seed v2_pairing_rules table from config/pairing_rules_seed.json.

Usage:
    cd backend
    python scripts/seed/seed_pairing_rules.py

Idempotent: ON CONFLICT (cuisine, item) DO UPDATE.
"""

import json
import os
import sys
import uuid

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import text
from app.database.connection import get_session_local

SEED_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "app", "services", "meal_engine", "config", "pairing_rules_seed.json"
)


def main():
    with open(SEED_FILE, "r") as f:
        data = json.load(f)

    SessionLocal = get_session_local()
    session = SessionLocal()

    count = 0
    try:
        for cuisine, rules in data.items():
            for rule in rules:
                session.execute(
                    text("""
                        INSERT INTO v2_pairing_rules (id, cuisine, item, preferred, acceptable, incompatible)
                        VALUES (:id, :cuisine, :item, :preferred, :acceptable, :incompatible)
                        ON CONFLICT (cuisine, item) DO UPDATE SET
                            preferred = :preferred,
                            acceptable = :acceptable,
                            incompatible = :incompatible
                    """),
                    {
                        "id": str(uuid.uuid4()),
                        "cuisine": cuisine,
                        "item": rule["item"],
                        "preferred": rule["preferred"],
                        "acceptable": rule["acceptable"],
                        "incompatible": rule["incompatible"],
                    },
                )
                count += 1

        session.commit()
        print(f"Seeded {count} pairing rules")

        # Summary
        result = session.execute(text("SELECT cuisine, COUNT(*) FROM v2_pairing_rules GROUP BY cuisine"))
        for cuisine, c in result:
            print(f"  {cuisine}: {c} rules")

    except Exception as e:
        session.rollback()
        print(f"ERROR: {e}")
        raise
    finally:
        session.close()


if __name__ == "__main__":
    main()
