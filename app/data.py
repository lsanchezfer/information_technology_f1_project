import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from psycopg2.extras import RealDictCursor

from db import get_connection, run_query
from queries import Q12_STANDINGS, Q12_UPDATE


def what_if_disqualified(race_id, driver_id, top_n=10):
    params = {"race_id": race_id, "driver_id": driver_id, "top_n": top_n}
    conn = get_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute(Q12_STANDINGS, params)
        before = [dict(r) for r in cur.fetchall()]
        cur.execute(Q12_UPDATE, params)
        updated = cur.rowcount
        cur.execute(Q12_STANDINGS, params)
        after = [dict(r) for r in cur.fetchall()]
        return before, after, updated
    finally:
        conn.rollback()          # undo the what-if change
        conn.close()