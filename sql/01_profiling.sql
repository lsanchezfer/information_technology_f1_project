-- CHECK: 1. Row count of every file
SELECT 'seasons' AS file, COUNT(*) AS n_rows FROM staging.seasons
UNION ALL SELECT 'circuits', COUNT(*) FROM staging.circuits
UNION ALL SELECT 'status', COUNT(*) FROM staging.status
UNION ALL SELECT 'drivers', COUNT(*) FROM staging.drivers
UNION ALL SELECT 'constructors', COUNT(*) FROM staging.constructors
UNION ALL SELECT 'races', COUNT(*) FROM staging.races
UNION ALL SELECT 'results', COUNT(*) FROM staging.results
UNION ALL SELECT 'sprint_results', COUNT(*) FROM staging.sprint_results
UNION ALL SELECT 'qualifying', COUNT(*) FROM staging.qualifying
UNION ALL SELECT 'pit_stops', COUNT(*) FROM staging.pit_stops
UNION ALL SELECT 'lap_times', COUNT(*) FROM staging.lap_times
UNION ALL SELECT 'driver_standings', COUNT(*) FROM staging.driver_standings
UNION ALL SELECT 'constructor_standings', COUNT(*) FROM staging.constructor_standings
UNION ALL SELECT 'constructor_results', COUNT(*) FROM staging.constructor_results
ORDER BY n_rows DESC;

-- CHECK: 2. Candidate keys (duplicated_values = 0 means unique)
SELECT 'circuits(circuit_id)' AS candidate_key, COUNT(*) - COUNT(DISTINCT circuit_id) AS duplicated_values FROM staging.circuits
UNION ALL SELECT 'circuits(circuit_ref)', COUNT(*) - COUNT(DISTINCT circuit_ref) FROM staging.circuits
UNION ALL SELECT 'drivers(driver_id)', COUNT(*) - COUNT(DISTINCT driver_id) FROM staging.drivers
UNION ALL SELECT 'drivers(driver_ref)', COUNT(*) - COUNT(DISTINCT driver_ref) FROM staging.drivers
UNION ALL SELECT 'drivers(code) non-null', COUNT(*) FILTER (WHERE code <> '\N') - COUNT(DISTINCT code) FILTER (WHERE code <> '\N') FROM staging.drivers
UNION ALL SELECT 'drivers(number) non-null', COUNT(*) FILTER (WHERE number <> '\N') - COUNT(DISTINCT number) FILTER (WHERE number <> '\N') FROM staging.drivers
UNION ALL SELECT 'constructors(constructor_id)', COUNT(*) - COUNT(DISTINCT constructor_id) FROM staging.constructors
UNION ALL SELECT 'constructors(constructor_ref)', COUNT(*) - COUNT(DISTINCT constructor_ref) FROM staging.constructors
UNION ALL SELECT 'constructors(name)', COUNT(*) - COUNT(DISTINCT name) FROM staging.constructors
UNION ALL SELECT 'status(status)', COUNT(*) - COUNT(DISTINCT status) FROM staging.status
UNION ALL SELECT 'races(race_id)', COUNT(*) - COUNT(DISTINCT race_id) FROM staging.races
UNION ALL SELECT 'races(year, round)', COUNT(*) - COUNT(DISTINCT (year, round)) FROM staging.races
UNION ALL SELECT 'results(result_id)', COUNT(*) - COUNT(DISTINCT result_id) FROM staging.results
UNION ALL SELECT 'results(race_id, driver_id)', COUNT(*) - COUNT(DISTINCT (race_id, driver_id)) FROM staging.results
UNION ALL SELECT 'results(race_id, position_order)', COUNT(*) - COUNT(DISTINCT (race_id, position_order)) FROM staging.results
UNION ALL SELECT 'sprint_results(race_id, driver_id)', COUNT(*) - COUNT(DISTINCT (race_id, driver_id)) FROM staging.sprint_results
UNION ALL SELECT 'qualifying(qualify_id)', COUNT(*) - COUNT(DISTINCT qualify_id) FROM staging.qualifying
UNION ALL SELECT 'qualifying(race_id, driver_id)', COUNT(*) - COUNT(DISTINCT (race_id, driver_id)) FROM staging.qualifying
UNION ALL SELECT 'pit_stops(race_id, driver_id, stop)', COUNT(*) - COUNT(DISTINCT (race_id, driver_id, stop)) FROM staging.pit_stops
UNION ALL SELECT 'lap_times(race_id, driver_id, lap)', COUNT(*) - COUNT(DISTINCT (race_id, driver_id, lap)) FROM staging.lap_times
UNION ALL SELECT 'driver_standings(race_id, driver_id)', COUNT(*) - COUNT(DISTINCT (race_id, driver_id)) FROM staging.driver_standings
UNION ALL SELECT 'constructor_standings(race_id, constructor_id)', COUNT(*) - COUNT(DISTINCT (race_id, constructor_id)) FROM staging.constructor_standings
UNION ALL SELECT 'constructor_results(race_id, constructor_id)', COUNT(*) - COUNT(DISTINCT (race_id, constructor_id)) FROM staging.constructor_results
ORDER BY duplicated_values DESC, candidate_key;

-- CHECK: 3. Same driver twice in a race, per season
SELECT ra.year, COUNT(*) AS duplicated_pairs
FROM (SELECT race_id, driver_id FROM staging.results
      GROUP BY race_id, driver_id HAVING COUNT(*) > 1) d
JOIN staging.races ra ON ra.race_id = d.race_id
GROUP BY ra.year ORDER BY ra.year;

-- CHECK: 4. Driver codes reused by different drivers
SELECT code, STRING_AGG(driver_ref, ', ' ORDER BY driver_id::int) AS drivers
FROM staging.drivers WHERE code <> '\N'
GROUP BY code HAVING COUNT(*) > 1 ORDER BY code;

-- CHECK: 5. Referential integrity - orphan rows per foreign key
SELECT 'races.circuit_id -> circuits' AS fk, COUNT(*) AS orphans FROM staging.races r WHERE NOT EXISTS (SELECT 1 FROM staging.circuits c WHERE c.circuit_id = r.circuit_id)
UNION ALL SELECT 'races.year -> seasons', COUNT(*) FROM staging.races r WHERE NOT EXISTS (SELECT 1 FROM staging.seasons s WHERE s.year = r.year)
UNION ALL SELECT 'results.race_id -> races', COUNT(*) FROM staging.results x WHERE NOT EXISTS (SELECT 1 FROM staging.races r WHERE r.race_id = x.race_id)
UNION ALL SELECT 'results.driver_id -> drivers', COUNT(*) FROM staging.results x WHERE NOT EXISTS (SELECT 1 FROM staging.drivers d WHERE d.driver_id = x.driver_id)
UNION ALL SELECT 'results.constructor_id -> constructors', COUNT(*) FROM staging.results x WHERE NOT EXISTS (SELECT 1 FROM staging.constructors c WHERE c.constructor_id = x.constructor_id)
UNION ALL SELECT 'results.status_id -> status', COUNT(*) FROM staging.results x WHERE NOT EXISTS (SELECT 1 FROM staging.status s WHERE s.status_id = x.status_id)
UNION ALL SELECT 'qualifying.(race,driver) -> results', COUNT(*) FROM staging.qualifying x WHERE NOT EXISTS (SELECT 1 FROM staging.results r WHERE r.race_id = x.race_id AND r.driver_id = x.driver_id)
UNION ALL SELECT 'lap_times.(race,driver) -> results', COUNT(*) FROM staging.lap_times x WHERE NOT EXISTS (SELECT 1 FROM staging.results r WHERE r.race_id = x.race_id AND r.driver_id = x.driver_id)
UNION ALL SELECT 'pit_stops.(race,driver) -> results', COUNT(*) FROM staging.pit_stops x WHERE NOT EXISTS (SELECT 1 FROM staging.results r WHERE r.race_id = x.race_id AND r.driver_id = x.driver_id)
UNION ALL SELECT 'driver_standings.driver_id -> drivers', COUNT(*) FROM staging.driver_standings x WHERE NOT EXISTS (SELECT 1 FROM staging.drivers d WHERE d.driver_id = x.driver_id)
UNION ALL SELECT 'constructor_standings.constructor_id -> constructors', COUNT(*) FROM staging.constructor_standings x WHERE NOT EXISTS (SELECT 1 FROM staging.constructors c WHERE c.constructor_id = x.constructor_id)
UNION ALL SELECT 'constructor_results.constructor_id -> constructors', COUNT(*) FROM staging.constructor_results x WHERE NOT EXISTS (SELECT 1 FROM staging.constructors c WHERE c.constructor_id = x.constructor_id)
UNION ALL SELECT 'sprint_results.race_id -> races', COUNT(*) FROM staging.sprint_results x WHERE NOT EXISTS (SELECT 1 FROM staging.races r WHERE r.race_id = x.race_id);

-- CHECK: 6. Value ranges of dates and numbers
SELECT 'races.date' AS col, MIN(date) AS min_value, MAX(date) AS max_value FROM staging.races
UNION ALL SELECT 'races.year', MIN(year), MAX(year) FROM staging.races
UNION ALL SELECT 'drivers.dob', MIN(dob), MAX(dob) FROM staging.drivers
UNION ALL SELECT 'circuits.lat', MIN(lat::numeric)::text, MAX(lat::numeric)::text FROM staging.circuits
UNION ALL SELECT 'circuits.lng', MIN(lng::numeric)::text, MAX(lng::numeric)::text FROM staging.circuits
UNION ALL SELECT 'circuits.alt (m)', MIN(alt::int)::text, MAX(alt::int)::text FROM staging.circuits
UNION ALL SELECT 'drivers.number', MIN(number::int)::text, MAX(number::int)::text FROM staging.drivers WHERE number <> '\N'
UNION ALL SELECT 'results.number (car)', MIN(number::int)::text, MAX(number::int)::text FROM staging.results WHERE number <> '\N'
UNION ALL SELECT 'results.grid', MIN(grid::int)::text, MAX(grid::int)::text FROM staging.results
UNION ALL SELECT 'results.points', MIN(points::numeric)::text, MAX(points::numeric)::text FROM staging.results
UNION ALL SELECT 'results.laps', MIN(laps::int)::text, MAX(laps::int)::text FROM staging.results
UNION ALL SELECT 'results.milliseconds', MIN(milliseconds::int)::text, MAX(milliseconds::int)::text FROM staging.results WHERE milliseconds <> '\N'
UNION ALL SELECT 'results.rank', MIN(rank::int)::text, MAX(rank::int)::text FROM staging.results WHERE rank <> '\N'
UNION ALL SELECT 'results.fastest_lap_speed (km/h)', MIN(fastest_lap_speed::numeric)::text, MAX(fastest_lap_speed::numeric)::text FROM staging.results WHERE fastest_lap_speed <> '\N'
UNION ALL SELECT 'lap_times.milliseconds', MIN(milliseconds::int)::text, MAX(milliseconds::int)::text FROM staging.lap_times
UNION ALL SELECT 'lap_times.position', MIN(position::int)::text, MAX(position::int)::text FROM staging.lap_times
UNION ALL SELECT 'pit_stops.milliseconds', MIN(milliseconds::int)::text, MAX(milliseconds::int)::text FROM staging.pit_stops
UNION ALL SELECT 'pit_stops.stop', MIN(stop::int)::text, MAX(stop::int)::text FROM staging.pit_stops
UNION ALL SELECT 'driver_standings.points', MIN(points::numeric)::text, MAX(points::numeric)::text FROM staging.driver_standings
UNION ALL SELECT 'constructor_standings.points', MIN(points::numeric)::text, MAX(points::numeric)::text FROM staging.constructor_standings;

-- CHECK: 7. Formats of time strings (rows that do not follow the usual pattern)
SELECT 'races.time  (hh:mm:ss)' AS col, COUNT(*) FILTER (WHERE time <> '\N' AND time !~ '^\d\d:\d\d:\d\d$') AS off_pattern FROM staging.races
UNION ALL SELECT 'qualifying.q1 (m:ss.mmm)', COUNT(*) FILTER (WHERE q1 <> '\N' AND q1 !~ '^\d+:\d\d\.\d{3}$') FROM staging.qualifying
UNION ALL SELECT 'qualifying.q2 (m:ss.mmm)', COUNT(*) FILTER (WHERE q2 <> '\N' AND q2 !~ '^\d+:\d\d\.\d{3}$') FROM staging.qualifying
UNION ALL SELECT 'qualifying.q3 (m:ss.mmm)', COUNT(*) FILTER (WHERE q3 <> '\N' AND q3 !~ '^\d+:\d\d\.\d{3}$') FROM staging.qualifying
UNION ALL SELECT 'results.fastest_lap_time (m:ss.mmm)', COUNT(*) FILTER (WHERE fastest_lap_time <> '\N' AND fastest_lap_time !~ '^\d+:\d\d\.\d{3}$') FROM staging.results
UNION ALL SELECT 'lap_times.time (m:ss.mmm)', COUNT(*) FILTER (WHERE time !~ '^\d+:\d\d\.\d{3}$') FROM staging.lap_times
UNION ALL SELECT 'pit_stops.duration (ss.mmm)', COUNT(*) FILTER (WHERE duration !~ '^\d+\.\d{3}$') FROM staging.pit_stops
UNION ALL SELECT 'pit_stops.time (hh:mm:ss)', COUNT(*) FILTER (WHERE time !~ '^\d\d:\d\d:\d\d$') FROM staging.pit_stops;

-- CHECK: 8. Times with an unusual format
SELECT 'qualifying.q2 = empty string' AS finding, COUNT(*) AS n_rows FROM staging.qualifying WHERE q2 = ''
UNION ALL SELECT 'qualifying.q3 = empty string', COUNT(*) FROM staging.qualifying WHERE q3 = ''
UNION ALL SELECT 'lap_times.time like h:mm:ss.mmm (laps over 1 hour, red flags)', COUNT(*) FROM staging.lap_times WHERE time ~ '^\d+:\d+:\d\d\.\d{3}$'
UNION ALL SELECT 'pit_stops.duration like m:ss.mmm (stops over 1 minute)', COUNT(*) FROM staging.pit_stops WHERE duration ~ '^\d+:\d\d\.\d{3}$'
UNION ALL SELECT 'lap_times: milliseconds disagree with time text', COUNT(*) FROM staging.lap_times
     WHERE time ~ '^\d+:\d\d\.\d{3}$'
       AND milliseconds::int <> split_part(time, ':', 1)::int * 60000 + ROUND(split_part(time, ':', 2)::numeric * 1000)::int;

-- CHECK: 9. Codes in position_text (letters instead of a position)
SELECT 'results' AS file, position_text AS code, COUNT(*) AS n_rows,
       CASE position_text WHEN 'R' THEN 'retired' WHEN 'D' THEN 'disqualified'
            WHEN 'E' THEN 'excluded' WHEN 'W' THEN 'withdrawn'
            WHEN 'F' THEN 'failed to qualify' WHEN 'N' THEN 'not classified' END AS meaning
FROM staging.results WHERE position_text !~ '^\d+$' GROUP BY position_text
UNION ALL
SELECT 'driver_standings', position_text, COUNT(*), NULL FROM staging.driver_standings WHERE position_text !~ '^\d+$' GROUP BY position_text
UNION ALL
SELECT 'sprint_results', position_text, COUNT(*), NULL FROM staging.sprint_results WHERE position_text !~ '^\d+$' GROUP BY position_text
UNION ALL
SELECT 'constructor_standings', position_text, COUNT(*), 'excluded' FROM staging.constructor_standings WHERE position_text !~ '^\d+$' GROUP BY position_text
UNION ALL
SELECT 'constructor_results.status', status, COUNT(*), NULL FROM staging.constructor_results GROUP BY status
ORDER BY 1, 3 DESC;

-- CHECK: 10. Codes without a meaning and inconsistent labels
SELECT 'results.rank = 0 (no fastest-lap rank)' AS finding, COUNT(*) AS n_rows FROM staging.results WHERE rank = '0'
UNION ALL SELECT 'results.grid = 0 (pit-lane start / no grid slot)', COUNT(*) FROM staging.results WHERE grid = '0'
UNION ALL SELECT 'drivers.nationality with trailing space', COUNT(*) FROM staging.drivers WHERE nationality <> TRIM(nationality)
UNION ALL SELECT 'drivers.nationality ''Argentinian'' vs ''Argentine''', COUNT(*) FROM staging.drivers WHERE TRIM(nationality) = 'Argentinian'
UNION ALL SELECT 'circuits.country ''United States'' vs ''USA''', COUNT(*) FROM staging.circuits WHERE country = 'United States'
UNION ALL SELECT 'status values never used', COUNT(*) FROM staging.status s WHERE NOT EXISTS (SELECT 1 FROM staging.results r WHERE r.status_id = s.status_id) AND NOT EXISTS (SELECT 1 FROM staging.sprint_results r WHERE r.status_id = s.status_id)
UNION ALL SELECT 'constructors without any result', COUNT(*) FROM staging.constructors c WHERE NOT EXISTS (SELECT 1 FROM staging.results r WHERE r.constructor_id = c.constructor_id)
UNION ALL SELECT 'constructors sharing the same url', COUNT(*) - COUNT(DISTINCT url) FROM staging.constructors;

-- CHECK: 11. Unexpected values (kept, documented, not changed)
SELECT 'results: fastest_lap greater than laps completed' AS finding, COUNT(*) AS n_rows FROM staging.results WHERE fastest_lap <> '\N' AND fastest_lap::int > laps::int
UNION ALL SELECT 'results: position differs from position_order', COUNT(*) FROM staging.results WHERE position <> '\N' AND position <> position_order
UNION ALL SELECT 'results: position NULL but position_text numeric', COUNT(*) FROM staging.results WHERE position = '\N' AND position_text ~ '^\d+$'
UNION ALL SELECT 'results: duplicated (race_id, position_order)', COUNT(*) - COUNT(DISTINCT (race_id, position_order)) FROM staging.results
UNION ALL SELECT 'pit_stops: stop number above 10', COUNT(*) FROM staging.pit_stops WHERE stop::int > 10
UNION ALL SELECT 'pit_stops: longer than 60 s (red-flag stoppages)', COUNT(*) FROM staging.pit_stops WHERE milliseconds::int > 60000
UNION ALL SELECT 'races: no start time (mostly before 2005)', COUNT(*) FROM staging.races WHERE time = '\N'
UNION ALL SELECT 'results: race time under 30 min (2024 Belgian GP stores gaps, not totals)', COUNT(*) FROM staging.results WHERE milliseconds <> '\N' AND milliseconds::int < 1800000
UNION ALL SELECT 'circuits: altitude below sea level', COUNT(*) FROM staging.circuits WHERE alt::int < 0
ORDER BY n_rows DESC;

-- CHECK: 12. First and last season with data in each file
SELECT 'results' AS file, MIN(ra.year) AS first_season, MAX(ra.year) AS last_season FROM staging.results x JOIN staging.races ra USING (race_id)
UNION ALL SELECT 'qualifying', MIN(ra.year), MAX(ra.year) FROM staging.qualifying x JOIN staging.races ra USING (race_id)
UNION ALL SELECT 'lap_times', MIN(ra.year), MAX(ra.year) FROM staging.lap_times x JOIN staging.races ra USING (race_id)
UNION ALL SELECT 'pit_stops', MIN(ra.year), MAX(ra.year) FROM staging.pit_stops x JOIN staging.races ra USING (race_id)
UNION ALL SELECT 'sprint_results', MIN(ra.year), MAX(ra.year) FROM staging.sprint_results x JOIN staging.races ra USING (race_id)
UNION ALL SELECT 'constructor_standings', MIN(ra.year), MAX(ra.year) FROM staging.constructor_standings x JOIN staging.races ra USING (race_id);
