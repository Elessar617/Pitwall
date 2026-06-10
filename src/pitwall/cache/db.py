import contextlib
import datetime
import json
import sqlite3
from pathlib import Path

from pitwall.models import (
    Circuit,
    Constructor,
    ConstructorStanding,
    Driver,
    DriverStanding,
    FastestLap,
    Race,
    RaceResult,
)

DEFAULT_DB_PATH = "data/pitwall.db"


def to_db_datetime(dt: datetime.datetime | None) -> str | None:
    """Serialize a timezone-aware UTC datetime to ISO-8601 string format.

    Invariant: The input datetime must be tz-aware or coerced to UTC timezone to ensure consistency.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.UTC)
    return dt.isoformat()


def _required_datetime(value: str) -> datetime.datetime:
    """A NOT NULL datetime column: decoding never yields None (schema invariant)."""
    decoded = from_db_datetime(value)
    if decoded is None:
        raise sqlite3.DataError("NOT NULL datetime column decoded to None")  # noqa: TRY003
    return decoded


def from_db_datetime(val: str | None) -> datetime.datetime | None:
    """Deserialize an ISO-8601 string format back to a timezone-aware UTC datetime.

    Failure Mode: Returns None if database field is null. Coerces output to UTC offset.
    """
    if val is None:
        return None
    dt = datetime.datetime.fromisoformat(val)
    return dt.replace(tzinfo=datetime.UTC) if dt.tzinfo is None else dt.astimezone(datetime.UTC)


def to_db_date(d: datetime.date | None) -> str | None:
    """Serialize a date object to ISO-8601 format."""
    if d is None:
        return None
    return d.isoformat()


def from_db_date(val: str | None) -> datetime.date | None:
    """Deserialize an ISO-8601 date string back to a date object."""
    if val is None:
        return None
    return datetime.date.fromisoformat(val)


def connect(path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Create a database connection and enable foreign keys.

    Ownership & Concurrency: The caller owns the lifetime of the returned connection.
    Safety Tradeoff: Enforces immediate schema constraints but requires thread-safety management externally.
    """
    # Invariant: Ensure the parent directories exist before creating the DB file.
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_schema(conn: sqlite3.Connection) -> None:
    """Initialize the schema idempotently (DDL version 1).

    Invariant: Re-running this function on an initialized connection has no side effects.
    Failure Mode: User version is locked to 1. Schema errors fail loudly if migration is needed.
    """
    # Ownership: Database writes are wrapped in a transaction block.
    with conn:
        conn.execute("PRAGMA foreign_keys = ON;")

        # Race schedule schema: PK is (season, round) to ensure single entry per event.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS races (
                season INTEGER,
                round INTEGER,
                url TEXT NOT NULL,
                race_name TEXT NOT NULL,
                circuit_id TEXT NOT NULL,
                circuit_url TEXT NOT NULL,
                circuit_name TEXT NOT NULL,
                lat REAL NOT NULL,
                long REAL NOT NULL,
                locality TEXT NOT NULL,
                country TEXT NOT NULL,
                start TEXT NOT NULL,
                fp1 TEXT,
                fp2 TEXT,
                fp3 TEXT,
                qualifying TEXT,
                sprint TEXT,
                sprint_qualifying TEXT,
                PRIMARY KEY (season, round)
            );
        """)

        # Driver profile schema: PK is driver_id.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS drivers (
                driver_id TEXT PRIMARY KEY,
                permanent_number INTEGER,
                code TEXT,
                url TEXT,
                given_name TEXT NOT NULL,
                family_name TEXT NOT NULL,
                date_of_birth TEXT,
                nationality TEXT
            );
        """)

        # Constructor profile schema: PK is constructor_id.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS constructors (
                constructor_id TEXT PRIMARY KEY,
                url TEXT NOT NULL,
                name TEXT NOT NULL,
                nationality TEXT NOT NULL
            );
        """)

        # Driver standings schema: PK is (season, driver_id).
        # Safety Tradeoff: constructor_ids is stored as JSON-array to map one-to-many relationship without helper tables.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS driver_standings (
                season INTEGER,
                driver_id TEXT,
                position INTEGER NOT NULL,
                position_text TEXT NOT NULL,
                points REAL NOT NULL,
                wins INTEGER NOT NULL,
                constructor_ids TEXT NOT NULL,
                PRIMARY KEY (season, driver_id),
                FOREIGN KEY (driver_id) REFERENCES drivers(driver_id)
            );
        """)

        # Constructor standings schema: PK is (season, constructor_id).
        conn.execute("""
            CREATE TABLE IF NOT EXISTS constructor_standings (
                season INTEGER,
                constructor_id TEXT,
                position INTEGER NOT NULL,
                position_text TEXT NOT NULL,
                points REAL NOT NULL,
                wins INTEGER NOT NULL,
                PRIMARY KEY (season, constructor_id),
                FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id)
            );
        """)

        # Race result schema: PK is (season, round, driver_id).
        # Invariant: result_order enforces list order preservation when querying results.
        conn.execute("""
            CREATE TABLE IF NOT EXISTS race_results (
                season INTEGER,
                round INTEGER,
                driver_id TEXT,
                constructor_id TEXT NOT NULL,
                number INTEGER NOT NULL,
                position INTEGER,
                position_text TEXT NOT NULL,
                points REAL NOT NULL,
                grid INTEGER NOT NULL,
                laps INTEGER NOT NULL,
                status TEXT NOT NULL,
                time_millis INTEGER,
                time_str TEXT,
                fastest_lap_rank INTEGER,
                fastest_lap_lap INTEGER,
                fastest_lap_time TEXT,
                result_order INTEGER NOT NULL,
                PRIMARY KEY (season, round, driver_id),
                FOREIGN KEY (driver_id) REFERENCES drivers(driver_id),
                FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id)
            );
        """)

        # Season-scoped driver mapping schema
        conn.execute("""
            CREATE TABLE IF NOT EXISTS season_drivers (
                season INTEGER,
                driver_id TEXT,
                PRIMARY KEY (season, driver_id),
                FOREIGN KEY (driver_id) REFERENCES drivers(driver_id) ON DELETE CASCADE
            );
        """)

        # Season-scoped constructor mapping schema
        conn.execute("""
            CREATE TABLE IF NOT EXISTS season_constructors (
                season INTEGER,
                constructor_id TEXT,
                PRIMARY KEY (season, constructor_id),
                FOREIGN KEY (constructor_id) REFERENCES constructors(constructor_id) ON DELETE CASCADE
            );
        """)

        # Cache metadata refresh log. PK is scope key (e.g. schedule:2026).
        conn.execute("""
            CREATE TABLE IF NOT EXISTS refresh_log (
                scope TEXT PRIMARY KEY,
                fetched_at TEXT NOT NULL,
                record_count INTEGER
            );
        """)
        # Invariant: Support pre-release in-place updates by adding record_count to existing database tables.
        with contextlib.suppress(sqlite3.OperationalError):
            conn.execute("ALTER TABLE refresh_log ADD COLUMN record_count INTEGER;")

        conn.execute("PRAGMA user_version = 1;")


def _upsert_races_cursor(cursor: sqlite3.Cursor, races: list[Race], season: int | None = None) -> None:
    """Internal helper to upsert races using an active cursor.

    Loop Bound: Constrained by length of races parameter.
    Invariant: Restructured to run within a shared transaction without executing commits.
    """
    if season is not None:
        # Invariant: Replace the entire season schedule scope by deleting old races first.
        cursor.execute("DELETE FROM races WHERE season = ?", (season,))
    elif races:
        # Invariant: If season is not explicitly specified, derive it from the races payload
        # and replace the schedule scope for all seasons present in the payload.
        seasons = {r.season for r in races}
        for s in seasons:
            cursor.execute("DELETE FROM races WHERE season = ?", (s,))
    for r in races:
        cursor.execute(
            """
            INSERT OR REPLACE INTO races (
                season, round, url, race_name,
                circuit_id, circuit_url, circuit_name, lat, long, locality, country,
                start, fp1, fp2, fp3, qualifying, sprint, sprint_qualifying
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                r.season,
                r.round,
                r.url,
                r.race_name,
                r.circuit.circuit_id,
                r.circuit.url,
                r.circuit.circuit_name,
                r.circuit.lat,
                r.circuit.long,
                r.circuit.locality,
                r.circuit.country,
                to_db_datetime(r.start),
                to_db_datetime(r.fp1),
                to_db_datetime(r.fp2),
                to_db_datetime(r.fp3),
                to_db_datetime(r.qualifying),
                to_db_datetime(r.sprint),
                to_db_datetime(r.sprint_qualifying),
            ),
        )


def upsert_races(conn: sqlite3.Connection, races: list[Race], season: int | None = None) -> None:
    """Upsert a list of races into the races table.

    Loop Bound: Constrained by length of races parameter.
    Ownership: Cursor resource is explicitly closed in finally.
    """
    cursor = conn.cursor()
    try:
        with conn:
            _upsert_races_cursor(cursor, races, season)
    finally:
        # PoT #7: Explicit cursor resource cleanup.
        cursor.close()


def select_races(conn: sqlite3.Connection, season: int) -> list[Race]:
    """Retrieve schedule of races for the specified season, ordered by round.

    PoT #7: Fetch results are consumed entirely.
    """
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT season, round, url, race_name,
                   circuit_id, circuit_url, circuit_name, lat, long, locality, country,
                   start, fp1, fp2, fp3, qualifying, sprint, sprint_qualifying
            FROM races
            WHERE season = ?
            ORDER BY round ASC
            """,
            (season,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    races = []
    # Loop Bound: Constrained by database row count (PoT #2).
    for row in rows:
        circuit = Circuit(
            circuit_id=row[4],
            url=row[5],
            circuit_name=row[6],
            lat=row[7],
            long=row[8],
            locality=row[9],
            country=row[10],
        )
        race = Race(
            season=row[0],
            round=row[1],
            url=row[2],
            race_name=row[3],
            circuit=circuit,
            start=_required_datetime(row[11]),
            fp1=from_db_datetime(row[12]),
            fp2=from_db_datetime(row[13]),
            fp3=from_db_datetime(row[14]),
            qualifying=from_db_datetime(row[15]),
            sprint=from_db_datetime(row[16]),
            sprint_qualifying=from_db_datetime(row[17]),
        )
        races.append(race)
    return races


def _upsert_drivers_cursor(cursor: sqlite3.Cursor, drivers: list[Driver], season: int | None = None) -> None:
    """Internal helper to upsert drivers using an active cursor.

    Loop Bound: Constrained by length of drivers parameter.
    Invariant: Restructured to run within a shared transaction without executing commits.
    """
    if season is not None:
        # Invariant: Replace the entire season roster scope by deleting old memberships first.
        cursor.execute("DELETE FROM season_drivers WHERE season = ?", (season,))

    for d in drivers:
        # Invariant: Use ON CONFLICT DO UPDATE on global drivers table
        # to avoid triggering ON DELETE CASCADE membership wipes in season_drivers.
        cursor.execute(
            """
            INSERT INTO drivers (
                driver_id, permanent_number, code, url, given_name, family_name, date_of_birth, nationality
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(driver_id) DO UPDATE SET
                permanent_number = excluded.permanent_number,
                code = excluded.code,
                url = excluded.url,
                given_name = excluded.given_name,
                family_name = excluded.family_name,
                date_of_birth = excluded.date_of_birth,
                nationality = excluded.nationality
            """,
            (
                d.driver_id,
                d.permanent_number,
                d.code,
                d.url,
                d.given_name,
                d.family_name,
                to_db_date(d.date_of_birth),
                d.nationality,
            ),
        )
        if season is not None:
            cursor.execute(
                """
                INSERT OR IGNORE INTO season_drivers (season, driver_id)
                VALUES (?, ?)
                """,
                (season, d.driver_id),
            )


def upsert_drivers(conn: sqlite3.Connection, drivers: list[Driver], season: int | None = None) -> None:
    """Upsert driver profiles into the drivers table.

    Loop Bound: Constrained by length of drivers parameter.
    Ownership: Cursor resource is explicitly closed in finally.
    """
    cursor = conn.cursor()
    try:
        with conn:
            _upsert_drivers_cursor(cursor, drivers, season)
    finally:
        cursor.close()


def select_drivers(conn: sqlite3.Connection, season: int | None = None) -> list[Driver]:
    """Retrieve driver profiles, optionally filtered by season, sorted alphabetically by driver_id."""
    cursor = conn.cursor()
    try:
        if season is not None:
            cursor.execute(
                """
                SELECT d.driver_id, d.permanent_number, d.code, d.url, d.given_name, d.family_name, d.date_of_birth, d.nationality
                FROM drivers d
                JOIN season_drivers sd ON d.driver_id = sd.driver_id
                WHERE sd.season = ?
                ORDER BY d.driver_id ASC
                """,
                (season,),
            )
        else:
            cursor.execute(
                """
                SELECT driver_id, permanent_number, code, url, given_name, family_name, date_of_birth, nationality
                FROM drivers
                ORDER BY driver_id ASC
                """
            )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    drivers = []
    for r in rows:
        drivers.append(
            Driver(
                driver_id=r[0],
                permanent_number=r[1],
                code=r[2],
                url=r[3],
                given_name=r[4],
                family_name=r[5],
                date_of_birth=from_db_date(r[6]),
                nationality=r[7],
            )
        )
    return drivers


def get_driver(conn: sqlite3.Connection, driver_id: str) -> Driver | None:
    """Lookup a single driver profile by driver_id."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT driver_id, permanent_number, code, url, given_name, family_name, date_of_birth, nationality
            FROM drivers
            WHERE driver_id = ?
            """,
            (driver_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return Driver(
        driver_id=row[0],
        permanent_number=row[1],
        code=row[2],
        url=row[3],
        given_name=row[4],
        family_name=row[5],
        date_of_birth=from_db_date(row[6]),
        nationality=row[7],
    )


def _upsert_constructors_cursor(
    cursor: sqlite3.Cursor, constructors: list[Constructor], season: int | None = None
) -> None:
    """Internal helper to upsert constructors using an active cursor.

    Loop Bound: Constrained by length of constructors parameter.
    Invariant: Restructured to run within a shared transaction without executing commits.
    """
    if season is not None:
        # Invariant: Replace the entire season constructor roster scope by deleting old memberships first.
        cursor.execute("DELETE FROM season_constructors WHERE season = ?", (season,))

    for c in constructors:
        # Invariant: Use ON CONFLICT DO UPDATE on global constructors table
        # to avoid triggering ON DELETE CASCADE membership wipes in season_constructors.
        cursor.execute(
            """
            INSERT INTO constructors (
                constructor_id, url, name, nationality
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT(constructor_id) DO UPDATE SET
                url = excluded.url,
                name = excluded.name,
                nationality = excluded.nationality
            """,
            (
                c.constructor_id,
                c.url,
                c.name,
                c.nationality,
            ),
        )
        if season is not None:
            cursor.execute(
                """
                INSERT OR IGNORE INTO season_constructors (season, constructor_id)
                VALUES (?, ?)
                """,
                (season, c.constructor_id),
            )


def upsert_constructors(conn: sqlite3.Connection, constructors: list[Constructor], season: int | None = None) -> None:
    """Upsert constructor profiles into the constructors table.

    Loop Bound: Constrained by length of constructors parameter.
    Ownership: Cursor resource is explicitly closed in finally.
    """
    cursor = conn.cursor()
    try:
        with conn:
            _upsert_constructors_cursor(cursor, constructors, season)
    finally:
        cursor.close()


def select_constructors(conn: sqlite3.Connection, season: int | None = None) -> list[Constructor]:
    """Retrieve constructor profiles, optionally filtered by season, sorted by constructor_id."""
    cursor = conn.cursor()
    try:
        if season is not None:
            cursor.execute(
                """
                SELECT c.constructor_id, c.url, c.name, c.nationality
                FROM constructors c
                JOIN season_constructors sc ON c.constructor_id = sc.constructor_id
                WHERE sc.season = ?
                ORDER BY c.constructor_id ASC
                """,
                (season,),
            )
        else:
            cursor.execute(
                """
                SELECT constructor_id, url, name, nationality
                FROM constructors
                ORDER BY constructor_id ASC
                """
            )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    constructors = []
    for r in rows:
        constructors.append(
            Constructor(
                constructor_id=r[0],
                url=r[1],
                name=r[2],
                nationality=r[3],
            )
        )
    return constructors


def get_constructor(conn: sqlite3.Connection, constructor_id: str) -> Constructor | None:
    """Lookup a single constructor profile by constructor_id."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT constructor_id, url, name, nationality
            FROM constructors
            WHERE constructor_id = ?
            """,
            (constructor_id,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return Constructor(
        constructor_id=row[0],
        url=row[1],
        name=row[2],
        nationality=row[3],
    )


def upsert_driver_standings(conn: sqlite3.Connection, season: int, standings: list[DriverStanding]) -> None:
    """Upsert driver standings and dependencies into the database.

    Invariant: Pre-seed nested driver and constructor profiles to prevent referential integrity failures.
    Restructuring: Restructured so profile seeds and standings replacements run inside a single 'with conn:' transaction.
    """
    drivers = [s.driver for s in standings]
    constructors = []
    for s in standings:
        constructors.extend(s.constructors)

    cursor = conn.cursor()
    try:
        with conn:
            _upsert_drivers_cursor(cursor, drivers)
            _upsert_constructors_cursor(cursor, constructors)

            # Invariant: Replace driver standings scope for the season by deleting old standings.
            cursor.execute("DELETE FROM driver_standings WHERE season = ?", (season,))

            for s in standings:
                c_ids = [c.constructor_id for c in s.constructors]
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO driver_standings (
                        season, driver_id, position, position_text, points, wins, constructor_ids
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        season,
                        s.driver.driver_id,
                        s.position,
                        s.position_text,
                        s.points,
                        s.wins,
                        json.dumps(c_ids),
                    ),
                )
    finally:
        cursor.close()


def select_driver_standings(conn: sqlite3.Connection, season: int) -> list[DriverStanding]:
    """Retrieve driver standings for the season, ordered by position."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT ds.position, ds.position_text, ds.points, ds.wins, ds.constructor_ids,
                   d.driver_id, d.permanent_number, d.code, d.url, d.given_name, d.family_name, d.date_of_birth, d.nationality
            FROM driver_standings ds
            JOIN drivers d ON ds.driver_id = d.driver_id
            WHERE ds.season = ?
            ORDER BY ds.position ASC
            """,
            (season,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    standings = []
    for r in rows:
        driver = Driver(
            driver_id=r[5],
            permanent_number=r[6],
            code=r[7],
            url=r[8],
            given_name=r[9],
            family_name=r[10],
            date_of_birth=from_db_date(r[11]),
            nationality=r[12],
        )
        c_ids = json.loads(r[4])
        constructors = []
        for c_id in c_ids:
            c = get_constructor(conn, c_id)
            if c is not None:
                constructors.append(c)

        standings.append(
            DriverStanding(
                position=r[0],
                position_text=r[1],
                points=r[2],
                wins=r[3],
                driver=driver,
                constructors=constructors,
            )
        )
    return standings


def upsert_constructor_standings(conn: sqlite3.Connection, season: int, standings: list[ConstructorStanding]) -> None:
    """Upsert constructor standings and dependencies into the database.

    Invariant: Pre-seed nested constructor profiles to prevent referential integrity failures.
    Restructuring: Restructured so profile seeds and standings replacements run inside a single 'with conn:' transaction.
    """
    constructors = [s.constructor for s in standings]

    cursor = conn.cursor()
    try:
        with conn:
            _upsert_constructors_cursor(cursor, constructors)

            # Invariant: Replace constructor standings scope for the season by deleting old standings.
            cursor.execute("DELETE FROM constructor_standings WHERE season = ?", (season,))

            for s in standings:
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO constructor_standings (
                        season, constructor_id, position, position_text, points, wins
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        season,
                        s.constructor.constructor_id,
                        s.position,
                        s.position_text,
                        s.points,
                        s.wins,
                    ),
                )
    finally:
        cursor.close()


def select_constructor_standings(conn: sqlite3.Connection, season: int) -> list[ConstructorStanding]:
    """Retrieve constructor standings for the season, ordered by position."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT cs.position, cs.position_text, cs.points, cs.wins,
                   c.constructor_id, c.url, c.name, c.nationality
            FROM constructor_standings cs
            JOIN constructors c ON cs.constructor_id = c.constructor_id
            WHERE cs.season = ?
            ORDER BY cs.position ASC
            """,
            (season,),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    standings = []
    for r in rows:
        constructor = Constructor(
            constructor_id=r[4],
            url=r[5],
            name=r[6],
            nationality=r[7],
        )
        standings.append(
            ConstructorStanding(
                position=r[0],
                position_text=r[1],
                points=r[2],
                wins=r[3],
                constructor=constructor,
            )
        )
    return standings


def upsert_race_results(conn: sqlite3.Connection, season: int, round: int, results: list[RaceResult]) -> None:  # noqa: A002
    """Upsert race results and dependencies into the database.

    Invariant: Pre-seed nested driver and constructor profiles to prevent referential integrity failures.
    Restructuring: Restructured so profile seeds and results replacements run inside a single 'with conn:' transaction.
    """
    drivers = [r.driver for r in results]
    constructors = [r.constructor for r in results]

    cursor = conn.cursor()
    try:
        with conn:
            _upsert_drivers_cursor(cursor, drivers)
            _upsert_constructors_cursor(cursor, constructors)

            # Invariant: Replace race results scope for this season and round by deleting old results.
            cursor.execute("DELETE FROM race_results WHERE season = ? AND round = ?", (season, round))

            for idx, r in enumerate(results):
                fl_rank = r.fastest_lap.rank if r.fastest_lap is not None else None
                fl_lap = r.fastest_lap.lap if r.fastest_lap is not None else None
                fl_time = r.fastest_lap.time if r.fastest_lap is not None else None
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO race_results (
                        season, round, driver_id, constructor_id, number, position, position_text, points,
                        grid, laps, status, time_millis, time_str,
                        fastest_lap_rank, fastest_lap_lap, fastest_lap_time, result_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        season,
                        round,
                        r.driver.driver_id,
                        r.constructor.constructor_id,
                        r.number,
                        r.position,
                        r.position_text,
                        r.points,
                        r.grid,
                        r.laps,
                        r.status,
                        r.time_millis,
                        r.time_str,
                        fl_rank,
                        fl_lap,
                        fl_time,
                        idx,
                    ),
                )
    finally:
        cursor.close()


def select_race_results(conn: sqlite3.Connection, season: int, round: int) -> list[RaceResult]:  # noqa: A002
    """Retrieve race results for the season and round, ordered by result_order."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT rr.number, rr.position, rr.position_text, rr.points,
                   rr.grid, rr.laps, rr.status, rr.time_millis, rr.time_str,
                   rr.fastest_lap_rank, rr.fastest_lap_lap, rr.fastest_lap_time,
                   d.driver_id, d.permanent_number, d.code, d.url, d.given_name, d.family_name, d.date_of_birth, d.nationality,
                   c.constructor_id, c.url, c.name, c.nationality
            FROM race_results rr
            JOIN drivers d ON rr.driver_id = d.driver_id
            JOIN constructors c ON rr.constructor_id = c.constructor_id
            WHERE rr.season = ? AND rr.round = ?
            ORDER BY rr.result_order ASC
            """,
            (season, round),
        )
        rows = cursor.fetchall()
    finally:
        cursor.close()

    results = []
    for r in rows:
        driver = Driver(
            driver_id=r[12],
            permanent_number=r[13],
            code=r[14],
            url=r[15],
            given_name=r[16],
            family_name=r[17],
            date_of_birth=from_db_date(r[18]),
            nationality=r[19],
        )
        constructor = Constructor(
            constructor_id=r[20],
            url=r[21],
            name=r[22],
            nationality=r[23],
        )

        fl = None
        if r[10] is not None:  # fastest_lap_lap
            fl = FastestLap(
                rank=r[9],
                lap=r[10],
                time=r[11],
            )

        results.append(
            RaceResult(
                number=r[0],
                position=r[1],
                position_text=r[2],
                points=r[3],
                driver=driver,
                constructor=constructor,
                grid=r[4],
                laps=r[5],
                status=r[6],
                time_millis=r[7],
                time_str=r[8],
                fastest_lap=fl,
            )
        )
    return results


def set_refresh_log(
    conn: sqlite3.Connection, scope: str, fetched_at: datetime.datetime, record_count: int | None = None
) -> None:
    """Record a cache refresh event for a scope."""
    cursor = conn.cursor()
    try:
        with conn:
            cursor.execute(
                """
                INSERT OR REPLACE INTO refresh_log (scope, fetched_at, record_count)
                VALUES (?, ?, ?)
                """,
                (scope, to_db_datetime(fetched_at), record_count),
            )
    finally:
        cursor.close()


def get_refresh_log(conn: sqlite3.Connection, scope: str) -> datetime.datetime | None:
    """Retrieve the last cache refresh timestamp for a scope."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT fetched_at FROM refresh_log WHERE scope = ?
            """,
            (scope,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None
    return from_db_datetime(row[0])


def get_refresh_log_metadata(conn: sqlite3.Connection, scope: str) -> tuple[datetime.datetime | None, int | None]:
    """Retrieve the last cache refresh timestamp and record count for a scope."""
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT fetched_at, record_count FROM refresh_log WHERE scope = ?
            """,
            (scope,),
        )
        row = cursor.fetchone()
    finally:
        cursor.close()

    if row is None:
        return None, None
    return from_db_datetime(row[0]), row[1]
