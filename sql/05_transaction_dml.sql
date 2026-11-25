-- Q12 by hand: what if Max Verstappen (driver 830) had been disqualified
-- from the 2021 Abu Dhabi Grand Prix (race 1073)?
BEGIN;

-- 1. Standings recomputed from the stored results (race + sprint points)
WITH season_points AS (
    SELECT r.driver_id, r.points FROM results r JOIN races ra ON ra.race_id = r.race_id
    WHERE ra.year = (SELECT year FROM races WHERE race_id = 1073)
    UNION ALL
    SELECT s.driver_id, s.points FROM sprint_results s JOIN races ra ON ra.race_id = s.race_id
    WHERE ra.year = (SELECT year FROM races WHERE race_id = 1073)
)
SELECT RANK() OVER (ORDER BY SUM(sp.points) DESC) AS position,
       d.forename || ' ' || d.surname AS driver, SUM(sp.points) AS points
FROM season_points sp JOIN drivers d ON d.driver_id = sp.driver_id
GROUP BY d.driver_id, d.forename, d.surname
ORDER BY points DESC LIMIT 5;

-- 2. The change (1 row)
UPDATE results
SET points = 0, position = NULL, position_text = 'D',
    status_id = (SELECT status_id FROM status WHERE status = 'Disqualified')
WHERE race_id = 1073 AND driver_id = 830;

-- 3. Same query again, inside the same transaction: Hamilton is now first
WITH season_points AS (
    SELECT r.driver_id, r.points FROM results r JOIN races ra ON ra.race_id = r.race_id
    WHERE ra.year = (SELECT year FROM races WHERE race_id = 1073)
    UNION ALL
    SELECT s.driver_id, s.points FROM sprint_results s JOIN races ra ON ra.race_id = s.race_id
    WHERE ra.year = (SELECT year FROM races WHERE race_id = 1073)
)
SELECT RANK() OVER (ORDER BY SUM(sp.points) DESC) AS position,
       d.forename || ' ' || d.surname AS driver, SUM(sp.points) AS points
FROM season_points sp JOIN drivers d ON d.driver_id = sp.driver_id
GROUP BY d.driver_id, d.forename, d.surname
ORDER BY points DESC LIMIT 5;

-- 4. Undo. After this, the stored result is unchanged:
ROLLBACK;
SELECT position, position_text, points FROM results WHERE race_id = 1073 AND driver_id = 830;
