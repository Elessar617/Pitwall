import contextlib
import datetime
import sqlite3
from collections.abc import Iterator
from pathlib import Path
from typing import Any

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


def _fetchall(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> list[Any]:
    """Execute a read query and return all rows.

    Ownership: Cursor resource is explicitly closed in finally (PoT #7).
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        cursor.close()


def _fetchone(conn: sqlite3.Connection, sql: str, params: tuple[Any, ...] = ()) -> Any | None:
    """Execute a read query and return the first row, or None when no row matches.

    Ownership: Cursor resource is explicitly closed in finally (PoT #7).
    """
    cursor = conn.cursor()
    try:
        cursor.execute(sql, params)
        return cursor.fetchone()
    finally:
        cursor.close()


@contextlib.contextmanager
def _write_cursor(conn: sqlite3.Connection) -> Iterator[sqlite3.Cursor]:
    """Yield a cursor inside a 'with conn:' transaction block.

    Invariant: 'with conn:' commits on success and rolls back on error (semantics unchanged).
    Ownership: Cursor resource is explicitly closed in finally (PoT #7).
    """
    cursor = conn.cursor()
    try:
        with conn:
            yield cursor
    finally:
        cursor.close()


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


def set_refresh_log(
    conn: sqlite3.Connection, scope: str, fetched_at: datetime.datetime, record_count: int | None = None
) -> None:
    """Record a cache refresh event for a scope."""
    with _write_cursor(conn) as cursor:
        cursor.execute(
            """
            INSERT OR REPLACE INTO refresh_log (scope, fetched_at, record_count)
            VALUES (?, ?, ?)
            """,
            (scope, to_db_datetime(fetched_at), record_count),
        )


def get_refresh_log(conn: sqlite3.Connection, scope: str) -> datetime.datetime | None:
    """Retrieve the last cache refresh timestamp for a scope."""
    return get_refresh_log_metadata(conn, scope)[0]


def get_refresh_log_metadata(conn: sqlite3.Connection, scope: str) -> tuple[datetime.datetime | None, int | None]:
    """Retrieve the last cache refresh timestamp and record count for a scope."""
    row = _fetchone(
        conn,
        """
        SELECT fetched_at, record_count FROM refresh_log WHERE scope = ?
        """,
        (scope,),
    )
    if row is None:
        return None, None
    return from_db_datetime(row[0]), row[1]


# Invariant: entity-persistence functions live in pitwall.cache.entities and are
# re-exported here so existing `from pitwall.cache.db import ...` call sites keep
# working. This import must stay BELOW the serde/cursor helpers entities depends
# on, or the circular module initialization fails; hence the E402 suppression.
from pitwall.cache.entities import (  # noqa: E402
    get_constructor,
    get_driver,
    select_constructor_standings,
    select_constructors,
    select_driver_standings,
    select_drivers,
    select_race_results,
    select_races,
    upsert_constructor_standings,
    upsert_constructors,
    upsert_driver_standings,
    upsert_drivers,
    upsert_race_results,
    upsert_races,
)

__all__ = [
    "DEFAULT_DB_PATH",
    "connect",
    "from_db_date",
    "from_db_datetime",
    "get_constructor",
    "get_driver",
    "get_refresh_log",
    "get_refresh_log_metadata",
    "init_schema",
    "select_constructor_standings",
    "select_constructors",
    "select_driver_standings",
    "select_drivers",
    "select_race_results",
    "select_races",
    "set_refresh_log",
    "to_db_date",
    "to_db_datetime",
    "upsert_constructor_standings",
    "upsert_constructors",
    "upsert_driver_standings",
    "upsert_drivers",
    "upsert_race_results",
    "upsert_races",
]
