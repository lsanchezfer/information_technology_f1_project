L_SEASONS = "SELECT year FROM seasons WHERE year IN (SELECT DISTINCT year FROM races) ORDER BY year DESC"
L_SEASON_BOUNDS = "SELECT MIN(year) AS first, MAX(year) AS last FROM races"
L_CIRCUITS = """
SELECT c.circuit_id, c.name || ' (' || c.country || ')' AS label, COUNT(*) AS races
FROM circuits c JOIN races ra ON ra.circuit_id = c.circuit_id
WHERE EXISTS (SELECT 1 FROM lap_times lt WHERE lt.race_id = ra.race_id)
GROUP BY c.circuit_id, c.name, c.country
ORDER BY races DESC, label
"""
L_RACES_OF_SEASON = """
SELECT ra.race_id, ra.round, ra.name, ra.race_date
FROM races ra
WHERE ra.year = %(season)s
  AND EXISTS (SELECT 1 FROM lap_times lt WHERE lt.race_id = ra.race_id)
ORDER BY ra.round
"""
L_RACES_WITH_RESULTS = """
SELECT ra.race_id, ra.round, ra.name
FROM races ra
WHERE ra.year = %(season)s
  AND EXISTS (SELECT 1 FROM results r WHERE r.race_id = ra.race_id)
ORDER BY ra.round
"""
L_DRIVERS = """
SELECT d.driver_id, d.forename || ' ' || d.surname AS label, COUNT(*) AS starts
FROM drivers d JOIN results r ON r.driver_id = d.driver_id
GROUP BY d.driver_id, d.forename, d.surname
HAVING COUNT(*) >= %(min_starts)s
ORDER BY d.surname, d.forename
"""
L_DRIVER_SEARCH = """
SELECT d.driver_id, d.forename || ' ' || d.surname AS label,
       MIN(ra.year) AS first_season, MAX(ra.year) AS last_season, COUNT(*) AS starts
FROM drivers d
JOIN results r ON r.driver_id = d.driver_id
JOIN races ra  ON ra.race_id = r.race_id
WHERE (d.forename || ' ' || d.surname) ILIKE %(pattern)s
GROUP BY d.driver_id, d.forename, d.surname
ORDER BY starts DESC
LIMIT 50
"""
L_DRIVERS_OF_RACE = """
SELECT d.driver_id, d.forename || ' ' || d.surname AS label, r.position_order
FROM results r JOIN drivers d ON d.driver_id = r.driver_id
WHERE r.race_id = %(race_id)s
ORDER BY r.position_order
"""
L_CONSTRUCTORS_WITH_PITS = """
SELECT c.constructor_id, c.name
FROM constructors c
WHERE EXISTS (SELECT 1 FROM results r JOIN pit_stops p
                ON p.race_id = r.race_id AND p.driver_id = r.driver_id
              WHERE r.constructor_id = c.constructor_id)
ORDER BY c.name
"""
L_TABLE_COUNTS = """
SELECT 'lap_times' AS table_name, COUNT(*) AS n_rows FROM lap_times
UNION ALL SELECT 'driver_standings', COUNT(*) FROM driver_standings
UNION ALL SELECT 'results', COUNT(*) FROM results
UNION ALL SELECT 'constructor_standings', COUNT(*) FROM constructor_standings
UNION ALL SELECT 'constructor_results', COUNT(*) FROM constructor_results
UNION ALL SELECT 'pit_stops', COUNT(*) FROM pit_stops
UNION ALL SELECT 'qualifying', COUNT(*) FROM qualifying
UNION ALL SELECT 'races', COUNT(*) FROM races
UNION ALL SELECT 'drivers', COUNT(*) FROM drivers
UNION ALL SELECT 'race_sessions', COUNT(*) FROM race_sessions
UNION ALL SELECT 'sprint_results', COUNT(*) FROM sprint_results
UNION ALL SELECT 'constructors', COUNT(*) FROM constructors
UNION ALL SELECT 'status', COUNT(*) FROM status
UNION ALL SELECT 'circuits', COUNT(*) FROM circuits
UNION ALL SELECT 'seasons', COUNT(*) FROM seasons
ORDER BY n_rows DESC
"""

L_NATIONALITIES = """
SELECT d.nationality, COUNT(DISTINCT d.driver_id) AS drivers
FROM drivers d JOIN results r ON r.driver_id = d.driver_id
WHERE d.nationality IS NOT NULL
GROUP BY d.nationality
ORDER BY d.nationality
"""
L_CIRCUIT_COUNTRIES = """
SELECT c.country, COUNT(*) AS races
FROM circuits c JOIN races ra ON ra.circuit_id = c.circuit_id
WHERE c.country IS NOT NULL
GROUP BY c.country
ORDER BY c.country
"""

# The 12 queries
Q01 = """
WITH q AS (                        -- every qualifying session: who, for which team, where
    SELECT race_id, constructor_id, driver_id, position
    FROM qualifying
)
SELECT d2.forename || ' ' || d2.surname                         AS teammate,
       STRING_AGG(DISTINCT c.name, ', ')                        AS teams,
       MIN(ra.year)                                             AS from_season,
       MAX(ra.year)                                             AS to_season,
       COUNT(*)                                                 AS sessions,
       COUNT(*) FILTER (WHERE a.position < b.position)          AS times_ahead,
       ROUND(100.0 * COUNT(*) FILTER (WHERE a.position < b.position) / COUNT(*), 1)
                                                                AS pct_ahead
FROM q a
JOIN q b             ON b.race_id = a.race_id                   -- same session
                    AND b.constructor_id = a.constructor_id     -- same team
                    AND b.driver_id <> a.driver_id              -- the other driver
JOIN races ra        ON ra.race_id = a.race_id
JOIN constructors c  ON c.constructor_id = a.constructor_id
JOIN drivers d2      ON d2.driver_id = b.driver_id
WHERE a.driver_id = %(driver_id)s
GROUP BY d2.driver_id, d2.forename, d2.surname
HAVING COUNT(*) >= %(min_sessions)s
ORDER BY from_season, sessions DESC
"""

Q02 = """
WITH per_season AS (               -- points and podiums of each driver of that nationality, per season
    SELECT d.driver_id,
           d.forename || ' ' || d.surname             AS driver,
           ra.year,
           SUM(r.points)                              AS points,
           COUNT(*) FILTER (WHERE r.position <= 3)    AS podiums
    FROM results r
    JOIN races   ra ON ra.race_id  = r.race_id
    JOIN drivers d  ON d.driver_id = r.driver_id
    WHERE d.nationality = %(nationality)s
    GROUP BY d.driver_id, d.forename, d.surname, ra.year
),
cumulative AS (                    -- running total of career points
    SELECT driver_id, driver, year, podiums,
           SUM(points) OVER (PARTITION BY driver_id ORDER BY year) AS career_points
    FROM per_season
)
SELECT driver,
       MIN(year)                                   AS first_season,
       MAX(year)                                   AS last_season,
       MAX(career_points)                          AS career_points,
       SUM(podiums)                                AS podiums,
       ARRAY_AGG(year          ORDER BY year)      AS seasons,
       ARRAY_AGG(career_points ORDER BY year)      AS points_so_far
FROM cumulative
GROUP BY driver_id, driver
HAVING MAX(career_points) >= %(min_points)s
ORDER BY career_points DESC
LIMIT %(top_n)s
"""

Q03 = """
WITH wins AS (                     -- wins of each driver at each circuit of the country
    SELECT ra.circuit_id,
           d.forename || ' ' || d.surname AS driver,
           COUNT(*)                       AS wins
    FROM races ra
    JOIN circuits c ON c.circuit_id = ra.circuit_id
    JOIN results  r ON r.race_id = ra.race_id AND r.position = 1
    JOIN drivers  d ON d.driver_id = r.driver_id
    WHERE c.country = %(country)s
    GROUP BY ra.circuit_id, d.driver_id, d.forename, d.surname
),
ranked AS (                        -- 1 = the driver with most wins at that circuit (ties share 1)
    SELECT circuit_id, driver, wins,
           RANK() OVER (PARTITION BY circuit_id ORDER BY wins DESC) AS rank_at_circuit
    FROM wins
)
SELECT c.name                       AS circuit,
       c.location,
       COUNT(*)                     AS races,
       MIN(ra.year)                 AS first_race,
       MAX(ra.year)                 AS last_race,
       (SELECT STRING_AGG(rk.driver || ' (' || rk.wins || ')', ', ')
        FROM ranked rk
        WHERE rk.circuit_id = c.circuit_id AND rk.rank_at_circuit = 1) AS top_winner
FROM races ra
JOIN circuits c ON c.circuit_id = ra.circuit_id
WHERE c.country = %(country)s
  AND EXISTS (SELECT 1 FROM results r WHERE r.race_id = ra.race_id)
GROUP BY c.circuit_id, c.name, c.location
ORDER BY races DESC
"""

Q04 = """
SELECT d.forename || ' ' || d.surname             AS driver,
       COUNT(*)                                   AS races,
       SUM(r.points)                              AS points,
       COUNT(*) FILTER (WHERE r.position <= 3)    AS podiums,
       MIN(r.position)                            AS best_finish
FROM results r
JOIN drivers d ON d.driver_id = r.driver_id
WHERE NOT EXISTS (                                -- the driver never won a race
    SELECT 1 FROM results w
    WHERE w.driver_id = r.driver_id AND w.position = 1
)
GROUP BY d.driver_id, d.forename, d.surname
HAVING COUNT(*) >= %(min_races)s
ORDER BY points DESC
LIMIT %(top_n)s
"""

Q05 = """
WITH wins AS (                     -- number every win of a driver: 1 = his first win
    SELECT r.driver_id, ra.year, ra.name AS race, ra.race_date,
           ROW_NUMBER() OVER (PARTITION BY r.driver_id ORDER BY ra.race_date) AS win_number
    FROM results r
    JOIN races ra ON ra.race_id = r.race_id
    WHERE r.position = 1
)
SELECT d.forename || ' ' || d.surname                          AS driver,
       w.year,
       w.race,
       ROUND((w.race_date - d.dob) / 365.25, 2)                AS age_at_first_win
FROM wins w
JOIN drivers d ON d.driver_id = w.driver_id
WHERE w.win_number = 1
  AND d.dob IS NOT NULL
  AND w.year BETWEEN %(year_from)s AND %(year_to)s
ORDER BY CASE WHEN %(oldest)s THEN -(w.race_date - d.dob) ELSE (w.race_date - d.dob) END
LIMIT %(top_n)s
"""

Q06 = """
SELECT d.forename || ' ' || d.surname           AS driver,
       ra.year,
       ra.name                                  AS race,
       r.grid                                   AS started,
       r.grid - 1                               AS places_gained,
       RANK() OVER (ORDER BY r.grid DESC)       AS comeback_rank
FROM results r
JOIN races   ra ON ra.race_id  = r.race_id
JOIN drivers d  ON d.driver_id = r.driver_id
WHERE r.position = 1                            -- won the race
  AND r.grid > 0                                -- 0 = pit-lane start, grid unknown
  AND ra.year BETWEEN %(year_from)s AND %(year_to)s
ORDER BY r.grid DESC, ra.year
LIMIT %(top_n)s
"""

Q07 = """
WITH race_order AS (               -- number every race in history: 1, 2, 3 ...
    SELECT race_id, ROW_NUMBER() OVER (ORDER BY year, round) AS race_no
    FROM races
    WHERE race_id IN (SELECT race_id FROM results)
),
wins AS (                          -- race number minus win number stays the same while the streak lasts
    SELECT r.driver_id, ra.year, ro.race_no,
           ro.race_no - ROW_NUMBER() OVER (PARTITION BY r.driver_id ORDER BY ro.race_no) AS streak_id
    FROM results r
    JOIN race_order ro ON ro.race_id = r.race_id
    JOIN races      ra ON ra.race_id = r.race_id
    WHERE r.position = 1
)
SELECT d.forename || ' ' || d.surname   AS driver,
       COUNT(*)                         AS consecutive_wins,
       MIN(w.year)                      AS from_season,
       MAX(w.year)                      AS to_season
FROM wins w
JOIN drivers d ON d.driver_id = w.driver_id
GROUP BY d.driver_id, d.forename, d.surname, w.streak_id
HAVING COUNT(*) >= %(min_streak)s
ORDER BY consecutive_wins DESC, from_season
LIMIT %(top_n)s
"""

Q08 = """
WITH stops AS (                    -- number of real pit stops of each driver in each race
    SELECT p.race_id, p.driver_id, COUNT(*) AS n_stops
    FROM pit_stops p
    WHERE p.duration_ms <= 60000                  -- longer ones are red-flag stoppages
    GROUP BY p.race_id, p.driver_id
)
SELECT s.n_stops,
       COUNT(*)                                                   AS finishers,
       ROUND(AVG(r.position), 2)                                  AS avg_finish,
       COUNT(*) FILTER (WHERE r.position = 1)                     AS wins,
       ROUND(100.0 * COUNT(*) FILTER (WHERE r.position <= 3) / COUNT(*), 1) AS pct_podium
FROM stops s
JOIN results r  ON r.race_id = s.race_id AND r.driver_id = s.driver_id
JOIN races   ra ON ra.race_id = s.race_id
WHERE r.position IS NOT NULL                      -- classified finishers only
  AND ra.year BETWEEN %(year_from)s AND %(year_to)s
GROUP BY s.n_stops
HAVING COUNT(*) >= %(min_cases)s
ORDER BY s.n_stops
"""

Q09 = """
WITH final_race AS (               -- last race of each season with standings
    SELECT ra.year, MAX(ra.round) AS last_round
    FROM races ra
    WHERE EXISTS (SELECT 1 FROM driver_standings ds WHERE ds.race_id = ra.race_id)
    GROUP BY ra.year
),
final_table AS (                   -- final classification, with the next driver's points on the same row
    SELECT ra.year, ds.position, ds.points,
           d.forename || ' ' || d.surname                                         AS driver,
           LEAD(d.forename || ' ' || d.surname) OVER (PARTITION BY ra.year ORDER BY ds.position) AS runner_up,
           LEAD(ds.points) OVER (PARTITION BY ra.year ORDER BY ds.position)       AS runner_up_points
    FROM driver_standings ds
    JOIN races      ra ON ra.race_id = ds.race_id
    JOIN final_race f  ON f.year = ra.year AND f.last_round = ra.round
    JOIN drivers    d  ON d.driver_id = ds.driver_id
)
SELECT year,
       driver                       AS champion,
       points,
       runner_up,
       runner_up_points,
       points - runner_up_points    AS margin
FROM final_table
WHERE position = 1
  AND year BETWEEN %(year_from)s AND %(year_to)s
ORDER BY year
"""

Q10 = """
WITH classified AS (               -- every start labelled: accident, other reason, mechanical, or not retired
    SELECT r.constructor_id,
           CASE
               WHEN r.position_text <> 'R' THEN 'not retired'
               WHEN s.status IN ('Accident', 'Collision', 'Collision damage', 'Damage',
                                 'Debris', 'Fatal accident', 'Spun off') THEN 'accident'
               WHEN s.status IN ('Retired', 'Physical', 'Illness', 'Injured', 'Injury', 'Eye injury',
                                 'Driver unwell', 'Not restarted', 'Safety concerns', 'Withdrew',
                                 'Out of fuel', 'Refuelling', 'Fuel rig') THEN 'other'
               ELSE 'mechanical'
           END AS outcome
    FROM results r
    JOIN races  ra ON ra.race_id  = r.race_id
    JOIN status s  ON s.status_id = r.status_id
    WHERE ra.year BETWEEN %(year_from)s AND %(year_to)s
)
SELECT c.name                                                                     AS team,
       COUNT(*)                                                                   AS starts,
       COUNT(*) FILTER (WHERE outcome = 'mechanical')                             AS mechanical,
       COUNT(*) FILTER (WHERE outcome = 'accident')                               AS accidents,
       ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'mechanical') / COUNT(*), 1) AS pct_mechanical,
       ROUND(100.0 * COUNT(*) FILTER (WHERE outcome = 'accident')   / COUNT(*), 1) AS pct_accident
FROM classified cl
JOIN constructors c ON c.constructor_id = cl.constructor_id
GROUP BY c.constructor_id, c.name
HAVING COUNT(*) >= %(min_starts)s
ORDER BY pct_mechanical DESC
LIMIT %(top_n)s
"""

Q11 = """
WITH per_season AS (               -- age of every driver on the day of every race, summarised per season
    SELECT ra.year,
           COUNT(DISTINCT r.driver_id)                            AS drivers,
           ROUND(AVG((ra.race_date - d.dob) / 365.25), 2)         AS avg_age,
           ROUND(MIN((ra.race_date - d.dob) / 365.25), 2)         AS youngest,
           ROUND(MAX((ra.race_date - d.dob) / 365.25), 2)         AS oldest
    FROM results r
    JOIN races   ra ON ra.race_id  = r.race_id
    JOIN drivers d  ON d.driver_id = r.driver_id
    WHERE d.dob IS NOT NULL
    GROUP BY ra.year
)
SELECT year, drivers, avg_age, youngest, oldest,
       avg_age - LAG(avg_age) OVER (ORDER BY year)   AS change_vs_previous
FROM per_season
WHERE year BETWEEN %(year_from)s AND %(year_to)s
ORDER BY year
"""

# Query 12 transaction
Q12_STANDINGS = """
WITH season_points AS (
    SELECT r.driver_id, r.points
    FROM results r JOIN races ra ON ra.race_id = r.race_id
    WHERE ra.year = (SELECT year FROM races WHERE race_id = %(race_id)s)
    UNION ALL
    SELECT s.driver_id, s.points
    FROM sprint_results s JOIN races ra ON ra.race_id = s.race_id
    WHERE ra.year = (SELECT year FROM races WHERE race_id = %(race_id)s)
)
SELECT RANK() OVER (ORDER BY SUM(sp.points) DESC)   AS position,
       d.forename || ' ' || d.surname               AS driver,
       SUM(sp.points)                               AS points
FROM season_points sp
JOIN drivers d ON d.driver_id = sp.driver_id
GROUP BY d.driver_id, d.forename, d.surname
ORDER BY points DESC, driver
LIMIT %(top_n)s
"""
Q12_UPDATE = """
UPDATE results
SET points        = 0,
    position      = NULL,
    position_text = 'D',
    status_id     = (SELECT status_id FROM status WHERE status = 'Disqualified')
WHERE race_id = %(race_id)s
  AND driver_id = %(driver_id)s
"""

QUERIES = [
    dict(id="Q01", author="Laura Sánchez", title="A driver against each of his teammates",
         question="In qualifying, how often did a chosen driver (Fernando Alonso by default) start ahead of each of his teammates over his whole career?",
         sql=Q01, defaults=dict(driver_id=4, min_sessions=5),
         features="CTE used twice in a self-join, 4 joins, conditional aggregation with FILTER, GROUP BY with HAVING",
         why="Teammates drive the same car, so this is the fairest way to compare a driver with the people he raced against."),
    dict(id="Q02", author="Laura Sánchez", title="Drivers of one nationality: career points",
         question="How did the career points of the drivers of a nationality (Spanish by default) build up, season after season?",
         sql=Q02, defaults=dict(nationality="Spanish", min_points=1, top_n=8),
         features="Two CTEs, GROUP BY, running total with SUM() OVER (PARTITION BY ... ORDER BY), HAVING, ARRAY_AGG",
         why="It shows how much of a country's history in Formula 1 depends on one or two drivers (for Spain, Alonso and Sainz). Points systems changed over time, so totals of different eras are not directly comparable."),
    dict(id="Q03", author="Laura Sánchez", title="Grands Prix held in one country",
         question="Which circuits of a country (Spain by default) hosted Grands Prix, how many, in which years, and who won the most at each one?",
         sql=Q03, defaults=dict(country="Spain"),
         features="Two CTEs, RANK() OVER (PARTITION BY), correlated subquery with STRING_AGG, EXISTS",
         why="It tells the story of a country's Grands Prix: from the street circuits of Pedralbes and Montjuic to the permanent track of Barcelona-Catalunya."),
    dict(id="Q04", author="Laura Sánchez", title="Most points without ever winning",
         question="Which drivers scored the most points in their career without winning a single race?",
         sql=Q04, defaults=dict(min_races=20, top_n=15),
         features="Correlated NOT EXISTS subquery, JOIN, GROUP BY with HAVING, FILTER",
         why="It highlights consistent drivers who never got the car or the luck to win (Nico Hulkenberg leads the list)."),
    dict(id="Q05", author="Laura Sánchez", title="Youngest (or oldest) first-time winners",
         question="Which drivers were the youngest (or the oldest) when they won their first Grand Prix?",
         sql=Q05, defaults=dict(year_from=1950, year_to=2024, oldest=False, top_n=15),
         features="CTE with ROW_NUMBER() OVER (PARTITION BY), date arithmetic, CASE in ORDER BY",
         why="It shows how much the age of winners varies: Max Verstappen won his first race at 18, while Luigi Fagioli was 53 (use the oldest option)."),
    dict(id="Q06", author="Laura Sánchez", title="Greatest comebacks to a win",
         question="Which race wins came from furthest back on the starting grid?",
         sql=Q06, defaults=dict(year_from=1950, year_to=2024, top_n=15),
         features="3-table JOIN, RANK() OVER, filtering on the grid position",
         why="Winning from the back is rare and usually tells of a chaotic race (John Watson won from 22nd in 1983)."),
    dict(id="Q07", author="Raúl Pérez", title="Longest winning streaks",
         question="What are the longest runs of consecutive race wins by the same driver?",
         sql=Q07, defaults=dict(min_streak=4, top_n=15),
         features="Two chained CTEs, two ROW_NUMBER() OVER (one with PARTITION BY), IN subquery, GROUP BY with HAVING",
         why="Long streaks mark the most dominant periods in the sport (Max Verstappen won 10 in a row in 2023)."),
    dict(id="Q08", author="Raúl Pérez", title="Does stopping more often pay off?",
         question="What is the average finishing position, the number of wins and the podium rate of drivers according to how many pit stops they made?",
         sql=Q08, defaults=dict(year_from=2011, year_to=2024, min_cases=20),
         features="CTE with GROUP BY, 3-table JOIN, AVG and FILTER, GROUP BY with HAVING",
         why="It tests a common strategy question with real data: since 2011, one-stop races end on average higher up than three-stop races."),
    dict(id="Q09", author="Raúl Pérez", title="Championship winning margins",
         question="By how many points did each champion beat the runner-up, season by season?",
         sql=Q09, defaults=dict(year_from=1950, year_to=2024),
         features="Two CTEs, correlated EXISTS subquery, LEAD() OVER (PARTITION BY ... ORDER BY)",
         why="Small margins mark the closest title fights; very large ones mark dominant seasons."),
    dict(id="Q10", author="Raúl Pérez", title="Team reliability: breakdowns versus accidents",
         question="Which teams retired most often because of mechanical failures, and how does that compare with retirements caused by accidents?",
         sql=Q10, defaults=dict(year_from=2000, year_to=2024, min_starts=100, top_n=15),
         features="CTE with CASE to classify each retirement, JOIN, FILTER, GROUP BY with HAVING",
         why="Mechanical retirements measure how reliable a car was, separately from driver mistakes and crashes."),
    dict(id="Q11", author="Raúl Pérez", title="Average age of the grid",
         question="How old were the drivers on the grid, on average, season by season, and who were the youngest and oldest?",
         sql=Q11, defaults=dict(year_from=1950, year_to=2024),
         features="CTE with date arithmetic and aggregates, LAG() OVER (ORDER BY year)",
         why="It shows how Formula 1 got younger: the average age fell from 39 in 1950 to about 28 in the 2020s, and in 2015 a 17-year-old (Max Verstappen) raced."),
    dict(id="Q12", author="Raúl Pérez", title="What-if disqualification (UPDATE inside a transaction)",
         question="How would the season standings change if a driver had been disqualified from one race? (The change is rolled back.)",
         sql=Q12_UPDATE.strip() + ";\n-- then, in the same transaction:\n" + Q12_STANDINGS.strip() + ";\n-- ROLLBACK",
         defaults=dict(race_id=1073, driver_id=830, top_n=5),
         features="UPDATE with a scalar subquery inside an explicit transaction, CTE with UNION ALL, RANK; ROLLBACK",
         why="It shows how much a single result weighs in a title fight, without altering the stored data."),
]

QUERY_BY_ID = {q["id"]: q for q in QUERIES}
