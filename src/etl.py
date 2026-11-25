import argparse
import csv
import io
import sys
import time
from collections import Counter, OrderedDict
from datetime import datetime
from decimal import Decimal

import psycopg2
from psycopg2.extras import execute_values

from db import RAW_DIR, ROOT, get_connection

NULL_MARKER = "\\N"


RULES = OrderedDict([
    ("C1", "Source null marker '\\N' converted to NULL"),
    ("C2", "Empty string in qualifying Q2/Q3 converted to NULL"),
    ("C3", "Lap-time text 'm:ss.mmm' converted to integer milliseconds"),
    ("C4", "Fastest-lap rank 0 (code without meaning) converted to NULL"),
    ("C5", "Leading/trailing spaces removed from text values"),
    ("C6", "Nationality label harmonised: 'Argentinian' -> 'Argentine'"),
    ("C7", "Country label harmonised: 'United States' -> 'USA'"),
    ("C8", "Session date/time column pairs of races turned into race_sessions rows"),
    ("C9", "Redundant text column not loaded (same value already stored in milliseconds)"),
])
stats = Counter()      


# format cleaning
def txt(value, table):
    if value == NULL_MARKER:
        stats[("C1", table)] += 1
        return None
    stripped = value.strip()
    if stripped != value:
        stats[("C5", table)] += 1
    return stripped


def num(value, table, kind=int):
    v = txt(value, table)
    if v is None:
        return None
    return kind(v)


def ms(value, table):
    v = txt(value, table)
    if v is None:
        return None
    if v == "":
        stats[("C2", table)] += 1
        return None
    parts = v.split(":")
    seconds = Decimal(parts[-1])
    minutes = int(parts[-2]) if len(parts) >= 2 else 0
    hours = int(parts[-3]) if len(parts) == 3 else 0
    stats[("C3", table)] += 1
    return int((hours * 3600 + minutes * 60) * 1000 + seconds * 1000)


def read(name):
    with open(RAW_DIR / f"{name}.csv", newline="", encoding="utf-8") as f:
        yield from csv.DictReader(f)


def t_seasons():
    return [(int(r["year"]), txt(r["url"], "seasons")) for r in read("seasons")]


def t_circuits():
    out = []
    for r in read("circuits"):
        country = txt(r["country"], "circuits")
        if country == "United States":
            country = "USA"
            stats[("C7", "circuits")] += 1
        out.append((int(r["circuitId"]), txt(r["circuitRef"], "circuits"), txt(r["name"], "circuits"),
                    txt(r["location"], "circuits"), country,
                    num(r["lat"], "circuits", Decimal), num(r["lng"], "circuits", Decimal),
                    num(r["alt"], "circuits"), txt(r["url"], "circuits")))
    return out


def t_status():
    return [(int(r["statusId"]), txt(r["status"], "status")) for r in read("status")]


def t_drivers():
    out = []
    for r in read("drivers"):
        nat = txt(r["nationality"], "drivers")
        if nat == "Argentinian":
            nat = "Argentine"
            stats[("C6", "drivers")] += 1
        out.append((int(r["driverId"]), txt(r["driverRef"], "drivers"), num(r["number"], "drivers"),
                    txt(r["code"], "drivers"), txt(r["forename"], "drivers"), txt(r["surname"], "drivers"),
                    txt(r["dob"], "drivers"), nat, txt(r["url"], "drivers")))
    return out


def t_constructors():
    return [(int(r["constructorId"]), txt(r["constructorRef"], "constructors"), txt(r["name"], "constructors"),
             txt(r["nationality"], "constructors"), txt(r["url"], "constructors"))
            for r in read("constructors")]


SESSIONS = [("fp1", "FP1"), ("fp2", "FP2"), ("fp3", "FP3"), ("quali", "QUALIFYING"), ("sprint", "SPRINT")]


def t_races():
    races, sessions = [], []
    for r in read("races"):
        races.append((int(r["raceId"]), int(r["year"]), int(r["round"]), int(r["circuitId"]),
                      txt(r["name"], "races"), txt(r["date"], "races"), txt(r["time"], "races"),
                      txt(r["url"], "races")))
        for prefix, label in SESSIONS:
            d = txt(r[f"{prefix}_date"], "races")
            t = txt(r[f"{prefix}_time"], "races")
            if d is not None:                      
                sessions.append((int(r["raceId"]), label, d, t))
                stats[("C8", "race_sessions")] += 1
    return races, sessions


def t_results():
    out = []
    for r in read("results"):
        rank = num(r["rank"], "results")
        if rank == 0:
            rank = None
            stats[("C4", "results")] += 1
        if r["time"] != NULL_MARKER:
            stats[("C9", "results.time")] += 1
        out.append((int(r["resultId"]), int(r["raceId"]), int(r["driverId"]), int(r["constructorId"]),
                    num(r["number"], "results"), int(r["grid"]), num(r["position"], "results"),
                    txt(r["positionText"], "results"), int(r["positionOrder"]),
                    Decimal(r["points"]), int(r["laps"]), num(r["milliseconds"], "results"),
                    num(r["fastestLap"], "results"), rank, ms(r["fastestLapTime"], "results"),
                    num(r["fastestLapSpeed"], "results", Decimal), int(r["statusId"])))
    return out


def t_sprint_results():
    out = []
    for r in read("sprint_results"):
        if r["time"] != NULL_MARKER:
            stats[("C9", "sprint_results.time")] += 1
        out.append((int(r["resultId"]), int(r["raceId"]), int(r["driverId"]), int(r["constructorId"]),
                    int(r["number"]), int(r["grid"]), num(r["position"], "sprint_results"),
                    txt(r["positionText"], "sprint_results"), int(r["positionOrder"]),
                    Decimal(r["points"]), int(r["laps"]), num(r["milliseconds"], "sprint_results"),
                    num(r["fastestLap"], "sprint_results"), ms(r["fastestLapTime"], "sprint_results"),
                    int(r["statusId"])))
    return out


def t_qualifying():
    return [(int(r["qualifyId"]), int(r["raceId"]), int(r["driverId"]), int(r["constructorId"]),
             int(r["number"]), int(r["position"]),
             ms(r["q1"], "qualifying"), ms(r["q2"], "qualifying"), ms(r["q3"], "qualifying"))
            for r in read("qualifying")]


def t_pit_stops():
    out = []
    for r in read("pit_stops"):
        stats[("C9", "pit_stops.duration")] += 1
        out.append((int(r["raceId"]), int(r["driverId"]), int(r["stop"]), int(r["lap"]),
                    txt(r["time"], "pit_stops"), int(r["milliseconds"])))
    return out


def t_lap_times():
    out = []
    for r in read("lap_times"):
        stats[("C9", "lap_times.time")] += 1
        out.append((int(r["raceId"]), int(r["driverId"]), int(r["lap"]),
                    int(r["position"]), int(r["milliseconds"])))
    return out


def t_driver_standings():
    return [(int(r["driverStandingsId"]), int(r["raceId"]), int(r["driverId"]), Decimal(r["points"]),
             int(r["position"]), txt(r["positionText"], "driver_standings"), int(r["wins"]))
            for r in read("driver_standings")]


def t_constructor_standings():
    return [(int(r["constructorStandingsId"]), int(r["raceId"]), int(r["constructorId"]), Decimal(r["points"]),
             int(r["position"]), txt(r["positionText"], "constructor_standings"), int(r["wins"]))
            for r in read("constructor_standings")]


def t_constructor_results():
    return [(int(r["constructorResultsId"]), int(r["raceId"]), int(r["constructorId"]), Decimal(r["points"]),
             txt(r["status"], "constructor_results"))
            for r in read("constructor_results")]

# Data loading
COLUMNS = OrderedDict([
    ("seasons", "year, url"),
    ("circuits", "circuit_id, circuit_ref, name, location, country, lat, lng, alt, url"),
    ("status", "status_id, status"),
    ("drivers", "driver_id, driver_ref, number, code, forename, surname, dob, nationality, url"),
    ("constructors", "constructor_id, constructor_ref, name, nationality, url"),
    ("races", "race_id, year, round, circuit_id, name, race_date, race_time, url"),
    ("race_sessions", "race_id, session_type, session_date, session_time"),
    ("results", "result_id, race_id, driver_id, constructor_id, car_number, grid, position, position_text, "
                "position_order, points, laps, race_time_ms, fastest_lap, fastest_lap_rank, "
                "fastest_lap_time_ms, fastest_lap_speed, status_id"),
    ("sprint_results", "sprint_result_id, race_id, driver_id, constructor_id, car_number, grid, position, "
                       "position_text, position_order, points, laps, race_time_ms, fastest_lap, "
                       "fastest_lap_time_ms, status_id"),
    ("qualifying", "qualify_id, race_id, driver_id, constructor_id, car_number, position, q1_ms, q2_ms, q3_ms"),
    ("pit_stops", "race_id, driver_id, stop, lap, time_of_day, duration_ms"),
    ("lap_times", "race_id, driver_id, lap, position, lap_time_ms"),
    ("driver_standings", "driver_standings_id, race_id, driver_id, points, position, position_text, wins"),
    ("constructor_standings", "constructor_standings_id, race_id, constructor_id, points, position, "
                              "position_text, wins"),
    ("constructor_results", "constructor_results_id, race_id, constructor_id, points, status"),
])


def insert(cur, table, rows):
    if table == "lap_times":
        buf = io.StringIO()
        csv.writer(buf, lineterminator="\n").writerows(rows)
        buf.seek(0)
        cur.copy_expert(f"COPY lap_times ({COLUMNS[table]}) FROM STDIN WITH (FORMAT csv)", buf)
    else:
        execute_values(cur, f"INSERT INTO {table} ({COLUMNS[table]}) VALUES %s", rows, page_size=2000)


def write_log(source_rows, loaded, seconds):
    lines = ["# ETL log (generated by src/etl.py)\n",
             f"Run {datetime.now():%Y-%m-%d %H:%M}, one transaction, {seconds:.1f} s.\n",
             "## Rows per table: source file vs table (counted with SELECT COUNT(*))\n",
             "| table | rows prepared from the CSV | rows in the table | ok |", "|---|---|---|---|"]
    for t in COLUMNS:
        lines.append(f"| {t} | {source_rows[t]} | {loaded[t]} | {'yes' if source_rows[t] == loaded[t] else 'NO'} |")
    lines += ["", "## Cleaning rules and values affected\n",
              "| rule | description | table / column | values affected |", "|---|---|---|---|"]
    for rule, desc in RULES.items():
        hits = sorted((t, n) for (r, t), n in stats.items() if r == rule)
        if not hits:
            lines.append(f"| {rule} | {desc} | - | 0 |")
        for t, n in hits:
            lines.append(f"| {rule} | {desc} | {t} | {n} |")
    (ROOT / "docs" / "etl_log.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo-rollback", action="store_true",
                    help="insert a broken row at the end to show that the whole load is rolled back")
    args = ap.parse_args()

    start = time.time()
    print("Reading and cleaning the CSV files ...")
    races, sessions = t_races()
    data = OrderedDict([
        ("seasons", t_seasons()), ("circuits", t_circuits()), ("status", t_status()),
        ("drivers", t_drivers()), ("constructors", t_constructors()),
        ("races", races), ("race_sessions", sessions),
        ("results", t_results()), ("sprint_results", t_sprint_results()),
        ("qualifying", t_qualifying()), ("pit_stops", t_pit_stops()), ("lap_times", t_lap_times()),
        ("driver_standings", t_driver_standings()),
        ("constructor_standings", t_constructor_standings()),
        ("constructor_results", t_constructor_results()),
    ])

    conn = get_connection()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM lap_times")
        before = cur.fetchone()[0]

        cur.execute("TRUNCATE " + ", ".join(reversed(list(COLUMNS))))
        for table, rows in data.items():
            insert(cur, table, rows)
            print(f"  {table:<22} {len(rows):>8} rows inserted")

        if args.demo_rollback:
            print("DEMO: inserting a lap time for race 999999, which does not exist ...")
            cur.execute("INSERT INTO lap_times (race_id, driver_id, lap, position, lap_time_ms) "
                        "VALUES (%s, %s, %s, %s, %s)", (999999, 1, 1, 1, 90000))

        loaded = {}
        for table in COLUMNS:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            loaded[table] = cur.fetchone()[0]
        source_rows = {t: len(r) for t, r in data.items()}
        if loaded != source_rows:
            raise RuntimeError(f"Row counts differ: {loaded} vs {source_rows}")

        conn.commit()
        write_log(source_rows, loaded, time.time() - start)
        print(f"COMMIT - load finished in {time.time() - start:.1f} s. Log in docs/etl_log.md")
    except (psycopg2.Error, RuntimeError, ValueError) as e:
        conn.rollback()
        print("ERROR -> ROLLBACK. Nothing from this load was saved.")
        print("  ", type(e).__name__, getattr(getattr(e, "diag", None), "message_primary", None) or e)
        detail = getattr(getattr(e, "diag", None), "message_detail", None)
        if detail:
            print("  ", detail)
        with conn.cursor() as c2:
            c2.execute("SELECT COUNT(*) FROM lap_times")
            print(f"   lap_times rows before the load: {before}, after the rollback: {c2.fetchone()[0]}")
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())

