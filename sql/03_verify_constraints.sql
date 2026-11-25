SELECT rel.relname AS table_name,
       COUNT(*) FILTER (WHERE con.contype = 'p') AS primary_keys,
       COUNT(*) FILTER (WHERE con.contype = 'f') AS foreign_keys,
       COUNT(*) FILTER (WHERE con.contype = 'u') AS uniques,
       COUNT(*) FILTER (WHERE con.contype = 'c') AS checks,
       BOOL_AND(con.convalidated)                AS all_validated
FROM pg_constraint con
JOIN pg_class rel     ON rel.oid = con.conrelid
JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE nsp.nspname = 'public'
GROUP BY rel.relname
ORDER BY rel.relname;


SELECT table_name, COUNT(*) FILTER (WHERE is_nullable = 'NO') AS not_null_columns,
       COUNT(*) AS total_columns
FROM information_schema.columns
WHERE table_schema = 'public'
GROUP BY table_name
ORDER BY table_name;


SELECT rel.relname AS table_name, con.conname AS constraint_name,
       CASE con.contype WHEN 'p' THEN 'PRIMARY KEY' WHEN 'f' THEN 'FOREIGN KEY'
                        WHEN 'u' THEN 'UNIQUE' WHEN 'c' THEN 'CHECK' END AS type,
       pg_get_constraintdef(con.oid) AS definition
FROM pg_constraint con
JOIN pg_class rel     ON rel.oid = con.conrelid
JOIN pg_namespace nsp ON nsp.oid = rel.relnamespace
WHERE nsp.nspname = 'public'
ORDER BY rel.relname, type, con.conname;


BEGIN;
-- INSERT INTO lap_times VALUES (999999, 1, 1, 1, 90000);           -- foreign key
-- INSERT INTO drivers (driver_id, driver_ref, forename, surname)
--        VALUES (1, 'dup', 'A', 'B');                                -- primary key
-- INSERT INTO status VALUES (9999, 'Finished');                     -- unique
-- UPDATE results SET points = -1 WHERE result_id = 1;               -- check
-- UPDATE races SET race_date = NULL WHERE race_id = 1;              -- not null
ROLLBACK;
