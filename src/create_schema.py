from db import SQL_DIR, get_connection


def main():
    schema = (SQL_DIR / "02_schema.sql").read_text(encoding="utf-8")
    conn = get_connection()
    try:
        with conn:                      
            with conn.cursor() as cur:
                cur.execute(schema)
        print("Schema created (sql/02_schema.sql).")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
