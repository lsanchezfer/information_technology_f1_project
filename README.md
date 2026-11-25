# Project B - Formula 1 World Championship database

Information Technology, Project B. Members: **Laura Sánchez** and **Raúl Pérez**

We turned the **Formula 1 World Championship (1950-2024)** dataset into a PostgreSQL database:

- 15 tables with primary keys, foreign keys, NOT NULL, UNIQUE and CHECK constraints;
- a Python ETL that loads 701,793 rows in a single transaction;
- 12 hand-written SQL queries;
- a Streamlit app with one chart per query.

The dataset comes from Kaggle (Rohan Rao), built from the Ergast Developer API.

---

## Requirements

- **Python 3.10 or newer**
- **PostgreSQL 16** (pgAdmin is optional but useful)
- The 14 CSV files of the dataset. They are **not** in this repository; step 3 below downloads them.

## Setup (once per computer)

All commands are run from the project folder, in PowerShell or the VS Code terminal. On macOS/Linux write `python3` instead of `py`.

### 1. Virtual environment and libraries

```powershell
py -m venv venv                    # macOS/Linux: python3 -m venv venv
venv\Scripts\activate              # macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
```

When the environment is active, the terminal line starts with `(venv)`.

> If Windows says running scripts is disabled, run this once and try again:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

### 2. Database and password

1. In pgAdmin (or `psql`), create an empty database called **`f1`**.
2. Copy `password.txt.example` to `password.txt` and write your PostgreSQL password in it.
   `password.txt` is ignored by git and never uploaded.

By default the app connects to `localhost:5432`, database `f1`, user `postgres`. You can change these with the
environment variables `PGHOST`, `PGPORT`, `PGDATABASE` and `PGUSER`.

### 3. Raw data

```powershell
py scripts/download_data.py
```

This puts the 14 CSV files in `data/raw/`. It uses `kagglehub`; if that fails, download the zip from
[Kaggle](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020) and extract the CSV
files into `data/raw/`.

### 4. Create the tables and load the data

```powershell
py src/create_schema.py        # creates the 15 tables, constraints and indexes
py src/etl.py                  # loads all the CSV files in one transaction (~10 s)
```

## Run the app

```powershell
venv\Scripts\activate
py -m streamlit run app/streamlit_app.py
```

The app opens at <http://localhost:8501>. Stop it with **Ctrl+C** in the terminal.

Once the data is loaded, these two commands are all you need each time. The app reads from PostgreSQL, not from
the CSV files.

> Use `py -m streamlit` rather than `streamlit` on its own. It makes sure the app runs with the Python of the
> virtual environment. Otherwise you can get errors like `No module named 'matplotlib'`.

### Pages of the app

| Page | Queries | What you can change |
|---|---|---|
| Overview | - | - (row counts of every table) |
| Drivers | Q01, Q04, Q05, Q07 | driver search, minimum races, youngest/oldest, minimum streak |
| Countries | Q02, Q03 | nationality, country |
| Races | Q06, Q08 | range of seasons, minimum cases |
| Seasons & teams | Q09, Q10, Q11 | range of seasons, minimum starts |
| What-if (transaction) | Q12 | season, race and driver to disqualify (UPDATE + ROLLBACK) |

Every filter is sent to PostgreSQL as a bound parameter (`%(name)s`), so typing quotes or SQL in the search box
does nothing harmful.

## Other scripts (optional)

These scripts regenerate the documents of the report. The app does not need them.

```powershell
py src/profile_raw.py          # data profile in SQL        -> docs/profile_results.md
py src/etl.py --demo-rollback > docs/rollback_demo.txt   # forces an error: the whole load is rolled back
py src/run_queries.py          # runs the 12 queries        -> docs/query_results.md, docs/img/
py src/index_benchmark.py      # EXPLAIN ANALYZE with/without indexes -> docs/index_benchmark.md
```

To check the constraints after the load, open `sql/03_verify_constraints.sql` in pgAdmin.

## Project structure

```
app/
  streamlit_app.py      the application (pages, filters, layout)
  queries.py            all the SQL used by the app (bound parameters only)
  charts.py             one matplotlib chart per query (only draws, no calculations)
  data.py               connection to the database + the what-if transaction (Q12)
.streamlit/config.toml  colours of the app
src/
  db.py                 connection settings (reads password.txt)
  profile_raw.py        loads the CSV files as text and profiles them in SQL
  create_schema.py      runs sql/02_schema.sql
  etl.py                reads, cleans and inserts the data in one transaction
  run_queries.py        runs all queries and saves results and charts
  index_benchmark.py    measures the effect of the indexes
sql/
  01_profiling.sql      the 12 profiling checks
  02_schema.sql         tables and constraints
  03_verify_constraints.sql
  04_queries.sql        the 12 queries with example values (to run in pgAdmin)
  05_transaction_dml.sql  Q12 by hand: UPDATE inside BEGIN ... ROLLBACK
scripts/download_data.py  downloads the raw CSV files
docs/
  profile_results.md    output of profile_raw.py
  etl_log.md            output of etl.py (rows loaded, rows changed by each cleaning rule)
  rollback_demo.txt     output of etl.py --demo-rollback
  query_results.md      output of run_queries.py
  index_benchmark.md    output of index_benchmark.py
  img/                  ER diagram, relational model and the 12 charts
EFFORT_LOG.md           what each member did
```

## Rules we followed

- **All analysis happens in SQL.** Python only reads the files, converts formats and sends queries. We don't use
  pandas anywhere.
- **psycopg2 with hand-written SQL**, and every user value is a bound parameter.
- **The load is a single transaction.** Missing values stay NULL, and each cleaning rule is counted in
  `docs/etl_log.md`.

## Troubleshooting

| Error | Fix |
|---|---|
| `No module named 'matplotlib'` (or `psycopg2`, `streamlit`) | Activate the venv, run `pip install -r requirements.txt`, and start the app with `py -m streamlit run ...` |
| `Cannot connect to PostgreSQL` | Check that PostgreSQL is running, that the database `f1` exists and that `password.txt` has the right password |
| `FileNotFoundError: data/raw/...csv` | Run `py scripts/download_data.py` or copy the CSV files into `data/raw/` |
| The app opens but the tables are empty | Run `py src/create_schema.py` and then `py src/etl.py` |

## Data licence

Dataset: [Formula 1 World Championship (1950-2024)](https://www.kaggle.com/datasets/rohanrao/formula-1-world-championship-1950-2020)
on Kaggle, licence **CC0: Public Domain**. Original source: Ergast Developer API.
