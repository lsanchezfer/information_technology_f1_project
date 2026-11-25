import os
from pathlib import Path

import psycopg2
from psycopg2.extras import RealDictCursor

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"
SQL_DIR = ROOT / "sql"


def _read_password():
    path = ROOT / "password.txt"
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return f.read().strip()
    return os.environ.get("PGPASSWORD")


def get_connection():
    return psycopg2.connect(
        host=os.environ.get("PGHOST", "localhost"),
        port=int(os.environ.get("PGPORT", 5432)),
        dbname=os.environ.get("PGDATABASE", "f1"),
        user=os.environ.get("PGUSER", "postgres"),
        password=_read_password(),
    )


def run_query(sql_text, params=None):
    conn = get_connection()
    try:
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql_text, params or {})
                return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()