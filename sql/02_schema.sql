DROP TABLE IF EXISTS lap_times             CASCADE;
DROP TABLE IF EXISTS pit_stops             CASCADE;
DROP TABLE IF EXISTS qualifying            CASCADE;
DROP TABLE IF EXISTS sprint_results        CASCADE;
DROP TABLE IF EXISTS results               CASCADE;
DROP TABLE IF EXISTS driver_standings      CASCADE;
DROP TABLE IF EXISTS constructor_standings CASCADE;
DROP TABLE IF EXISTS constructor_results   CASCADE;
DROP TABLE IF EXISTS race_sessions         CASCADE;
DROP TABLE IF EXISTS races                 CASCADE;
DROP TABLE IF EXISTS constructors          CASCADE;
DROP TABLE IF EXISTS drivers               CASCADE;
DROP TABLE IF EXISTS status                CASCADE;
DROP TABLE IF EXISTS circuits              CASCADE;
DROP TABLE IF EXISTS seasons               CASCADE;



CREATE TABLE seasons (
    year        SMALLINT     PRIMARY KEY
                             CHECK (year BETWEEN 1950 AND 2100),
    url         VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE circuits (
    circuit_id  INTEGER       PRIMARY KEY,
    circuit_ref VARCHAR(30)   NOT NULL UNIQUE,
    name        VARCHAR(80)   NOT NULL UNIQUE,
    location    VARCHAR(50),
    country     VARCHAR(40),
    lat         NUMERIC(8,5)  CHECK (lat BETWEEN -90 AND 90),
    lng         NUMERIC(8,5)  CHECK (lng BETWEEN -180 AND 180),
    alt         SMALLINT      CHECK (alt BETWEEN -500 AND 5000),  
    url         VARCHAR(255)
);

CREATE TABLE status (
    status_id   INTEGER      PRIMARY KEY,
    status      VARCHAR(40)  NOT NULL UNIQUE
);

CREATE TABLE drivers (
    driver_id   INTEGER      PRIMARY KEY,
    driver_ref  VARCHAR(40)  NOT NULL UNIQUE,
    number      SMALLINT     CHECK (number BETWEEN 0 AND 99),   
    code        CHAR(3)      CHECK (code ~ '^[A-Z]{3}$'),     
    forename    VARCHAR(40)  NOT NULL,
    surname     VARCHAR(40)  NOT NULL,
    dob         DATE         CHECK (dob >= DATE '1890-01-01'),
    nationality VARCHAR(30),
    url         VARCHAR(255),
    UNIQUE (forename, surname, dob)
);

CREATE TABLE constructors (
    constructor_id  INTEGER      PRIMARY KEY,
    constructor_ref VARCHAR(40)  NOT NULL UNIQUE,
    name            VARCHAR(60)  NOT NULL UNIQUE,
    nationality     VARCHAR(30),
    url             VARCHAR(255)                 
);





CREATE TABLE races (
    race_id     INTEGER      PRIMARY KEY,
    year        SMALLINT     NOT NULL REFERENCES seasons (year),
    round       SMALLINT     NOT NULL CHECK (round BETWEEN 1 AND 30),
    circuit_id  INTEGER      NOT NULL REFERENCES circuits (circuit_id),
    name        VARCHAR(60)  NOT NULL,
    race_date   DATE         NOT NULL,
    race_time   TIME,                           
    url         VARCHAR(255),
    UNIQUE (year, round),
    CHECK (EXTRACT(YEAR FROM race_date) = year)
);


CREATE TABLE race_sessions (
    race_id      INTEGER     NOT NULL REFERENCES races (race_id) ON DELETE CASCADE,
    session_type VARCHAR(10) NOT NULL
                 CHECK (session_type IN ('FP1', 'FP2', 'FP3', 'QUALIFYING', 'SPRINT')),
    session_date DATE        NOT NULL,
    session_time TIME,
    PRIMARY KEY (race_id, session_type)
);






CREATE TABLE results (
    result_id           INTEGER      PRIMARY KEY,
    race_id             INTEGER      NOT NULL REFERENCES races (race_id),
    driver_id           INTEGER      NOT NULL REFERENCES drivers (driver_id),
    constructor_id      INTEGER      NOT NULL REFERENCES constructors (constructor_id),
    car_number          SMALLINT     CHECK (car_number >= 0),
    grid                SMALLINT     NOT NULL CHECK (grid >= 0),      
    position            SMALLINT     CHECK (position > 0),              
    position_text       VARCHAR(3)   NOT NULL
                        CHECK (position_text ~ '^[0-9]+$' OR position_text IN ('R','D','E','W','F','N')),
    position_order      SMALLINT     NOT NULL CHECK (position_order > 0),
    points              NUMERIC(5,2) NOT NULL CHECK (points >= 0),
    laps                SMALLINT     NOT NULL CHECK (laps >= 0),
    race_time_ms        INTEGER      CHECK (race_time_ms > 0),
    fastest_lap         SMALLINT     CHECK (fastest_lap > 0),
    fastest_lap_rank    SMALLINT     CHECK (fastest_lap_rank > 0),
    fastest_lap_time_ms INTEGER      CHECK (fastest_lap_time_ms > 0),
    fastest_lap_speed   NUMERIC(6,3) CHECK (fastest_lap_speed > 0),     
    status_id           INTEGER      NOT NULL REFERENCES status (status_id)
);

CREATE TABLE sprint_results (
    sprint_result_id    INTEGER      PRIMARY KEY,
    race_id             INTEGER      NOT NULL REFERENCES races (race_id),
    driver_id           INTEGER      NOT NULL REFERENCES drivers (driver_id),
    constructor_id      INTEGER      NOT NULL REFERENCES constructors (constructor_id),
    car_number          SMALLINT     NOT NULL CHECK (car_number >= 0),
    grid                SMALLINT     NOT NULL CHECK (grid >= 0),
    position            SMALLINT     CHECK (position > 0),
    position_text       VARCHAR(3)   NOT NULL
                        CHECK (position_text ~ '^[0-9]+$' OR position_text IN ('R','D','E','W','F','N')),
    position_order      SMALLINT     NOT NULL CHECK (position_order > 0),
    points              NUMERIC(5,2) NOT NULL CHECK (points >= 0),
    laps                SMALLINT     NOT NULL CHECK (laps >= 0),
    race_time_ms        INTEGER      CHECK (race_time_ms > 0),
    fastest_lap         SMALLINT     CHECK (fastest_lap > 0),
    fastest_lap_time_ms INTEGER      CHECK (fastest_lap_time_ms > 0),
    status_id           INTEGER      NOT NULL REFERENCES status (status_id),
    UNIQUE (race_id, driver_id)
);

CREATE TABLE qualifying (
    qualify_id      INTEGER   PRIMARY KEY,
    race_id         INTEGER   NOT NULL REFERENCES races (race_id),
    driver_id       INTEGER   NOT NULL REFERENCES drivers (driver_id),
    constructor_id  INTEGER   NOT NULL REFERENCES constructors (constructor_id),
    car_number      SMALLINT  NOT NULL CHECK (car_number >= 0),
    position        SMALLINT  NOT NULL CHECK (position > 0),
    q1_ms           INTEGER   CHECK (q1_ms > 0),
    q2_ms           INTEGER   CHECK (q2_ms > 0),
    q3_ms           INTEGER   CHECK (q3_ms > 0),
    UNIQUE (race_id, driver_id),
    CHECK (q3_ms IS NULL OR q2_ms IS NOT NULL)    
);

CREATE TABLE pit_stops (
    race_id      INTEGER  NOT NULL REFERENCES races (race_id),
    driver_id    INTEGER  NOT NULL REFERENCES drivers (driver_id),
    stop         SMALLINT NOT NULL CHECK (stop BETWEEN 1 AND 99),
    lap          SMALLINT NOT NULL CHECK (lap > 0),
    time_of_day  TIME     NOT NULL,                
    duration_ms  INTEGER  NOT NULL CHECK (duration_ms > 0),
    PRIMARY KEY (race_id, driver_id, stop)
);

CREATE TABLE lap_times (
    race_id      INTEGER  NOT NULL REFERENCES races (race_id),
    driver_id    INTEGER  NOT NULL REFERENCES drivers (driver_id),
    lap          SMALLINT NOT NULL CHECK (lap > 0),
    position     SMALLINT NOT NULL CHECK (position > 0),
    lap_time_ms  INTEGER  NOT NULL CHECK (lap_time_ms > 0),
    PRIMARY KEY (race_id, driver_id, lap)
);








CREATE TABLE driver_standings (
    driver_standings_id INTEGER      PRIMARY KEY,
    race_id             INTEGER      NOT NULL REFERENCES races (race_id),
    driver_id           INTEGER      NOT NULL REFERENCES drivers (driver_id),
    points              NUMERIC(6,2) NOT NULL CHECK (points >= 0),
    position            SMALLINT     NOT NULL CHECK (position > 0),
    position_text       VARCHAR(3)   NOT NULL CHECK (position_text ~ '^[0-9]+$' OR position_text = 'D'),
    wins                SMALLINT     NOT NULL CHECK (wins >= 0),
    UNIQUE (race_id, driver_id)
);

CREATE TABLE constructor_standings (
    constructor_standings_id INTEGER      PRIMARY KEY,
    race_id                  INTEGER      NOT NULL REFERENCES races (race_id),
    constructor_id           INTEGER      NOT NULL REFERENCES constructors (constructor_id),
    points                   NUMERIC(6,2) NOT NULL CHECK (points >= 0),
    position                 SMALLINT     NOT NULL CHECK (position > 0),
    position_text            VARCHAR(3)   NOT NULL CHECK (position_text ~ '^[0-9]+$' OR position_text = 'E'),
    wins                     SMALLINT     NOT NULL CHECK (wins >= 0),
    UNIQUE (race_id, constructor_id)
);

CREATE TABLE constructor_results (
    constructor_results_id INTEGER      PRIMARY KEY,
    race_id                INTEGER      NOT NULL REFERENCES races (race_id),
    constructor_id         INTEGER      NOT NULL REFERENCES constructors (constructor_id),
    points                 NUMERIC(5,2) NOT NULL CHECK (points >= 0),
    status                 CHAR(1)      CHECK (status = 'D'),  
    UNIQUE (race_id, constructor_id)
);


CREATE INDEX idx_races_circuit        ON races (circuit_id);
CREATE INDEX idx_results_race         ON results (race_id);
CREATE INDEX idx_results_driver       ON results (driver_id);
CREATE INDEX idx_results_constructor  ON results (constructor_id);
CREATE INDEX idx_results_status       ON results (status_id);
CREATE INDEX idx_qualifying_driver    ON qualifying (driver_id);
CREATE INDEX idx_pit_stops_driver     ON pit_stops (driver_id);
CREATE INDEX idx_lap_times_driver     ON lap_times (driver_id);
CREATE INDEX idx_dstand_driver        ON driver_standings (driver_id);
CREATE INDEX idx_cstand_constructor   ON constructor_standings (constructor_id);
