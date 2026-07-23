"""One-time migration from instance/restaurant.db to DATABASE_URL.

Run only after DATABASE_URL points to PostgreSQL:
    python migrate_sqlite_to_postgres.py
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, inspect, text

BASE_DIR = Path(__file__).resolve().parent
SQLITE_URL = f"sqlite:///{BASE_DIR / 'instance' / 'restaurant.db'}"
POSTGRES_URL = os.environ.get("DATABASE_URL", "")
if POSTGRES_URL.startswith("postgres://"):
    POSTGRES_URL = POSTGRES_URL.replace("postgres://", "postgresql://", 1)

if not POSTGRES_URL or POSTGRES_URL.startswith("sqlite"):
    raise SystemExit("กรุณาตั้ง DATABASE_URL ให้เป็น PostgreSQL ก่อน")

source = create_engine(SQLITE_URL)
target = create_engine(POSTGRES_URL, pool_pre_ping=True)

tables = [
    "users",
    "restaurant_settings",
    "menu_items",
    "reservations",
    "reviews",
    "gallery",
]

with source.connect() as src, target.begin() as dst:
    available = set(inspect(source).get_table_names())
    for table in tables:
        if table not in available:
            print(f"skip {table}: not found")
            continue
        rows = src.execute(text(f'SELECT * FROM "{table}"')).mappings().all()
        for row in rows:
            columns = list(row.keys())
            column_sql = ", ".join(f'"{c}"' for c in columns)
            value_sql = ", ".join(f':{c}' for c in columns)
            # Existing rows are kept; duplicate primary keys are skipped.
            statement = text(
                f'INSERT INTO "{table}" ({column_sql}) VALUES ({value_sql}) '
                'ON CONFLICT DO NOTHING'
            )
            dst.execute(statement, dict(row))
        print(f"{table}: {len(rows)} rows")

print("Migration complete. Verify the website before deleting the SQLite backup.")
