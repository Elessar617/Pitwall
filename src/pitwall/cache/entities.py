"""Entity persistence layer for the season cache.

Upsert/select/get functions for races, drivers, constructors, standings, and
race results. Connection management, schema DDL, datetime serde, and the
refresh log live in ``pitwall.cache.db``, which re-exports this module's
public functions so existing ``from pitwall.cache.db import ...`` call sites
keep working.
"""

import json
import sqlite3
from typing import Any

from pitwall.cache.db import (
    _fetchall,
    _fetchone,
    _required_datetime,
    _write_cursor,
    from_db_date,
    from_db_datetime,
    to_db_date,
    to_db_datetime,
)
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


def _driver_from_row(r: Any, offset: int = 0) -> Driver:
    """Construct a Driver from 8 consecutive row columns starting at offset."""
    return Driver(
        driver_id=r[offset],
        permanent_number=r[offset + 1],
        code=r[offset + 2],
        url=r[offset + 3],
        given_name=r[offset + 4],
        family_name=r[offset + 5],
        date_of_birth=from_db_date(r[offset + 6]),
        nationality=r[offset + 7],
    )


def _constructor_from_row(r: Any, offset: int = 0) -> Constructor:
    """Construct a Constructor from 4 consecutive row columns starting at offset."""
    return Constructor(
        constructor_id=r[offset],
        url=r[offset + 1],
        name=r[offset + 2],
        nationality=r[offset + 3],
    )


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
    with _write_cursor(conn) as cursor:
        _upsert_races_cursor(cursor, races, season)


def select_races(conn: sqlite3.Connection, season: int) -> list[Race]:
    """Retrieve schedule of races for the specified season, ordered by round.

    PoT #7: Fetch results are consumed entirely.
    """
    rows = _fetchall(
        conn,
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
    with _write_cursor(conn) as cursor:
        _upsert_drivers_cursor(cursor, drivers, season)


def select_drivers(conn: sqlite3.Connection, season: int | None = None) -> list[Driver]:
    """Retrieve driver profiles, optionally filtered by season, sorted alphabetically by driver_id."""
    if season is not None:
        rows = _fetchall(
            conn,
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
        rows = _fetchall(
            conn,
            """
            SELECT driver_id, permanent_number, code, url, given_name, family_name, date_of_birth, nationality
            FROM drivers
            ORDER BY driver_id ASC
            """,
        )
    return [_driver_from_row(r) for r in rows]


def get_driver(conn: sqlite3.Connection, driver_id: str) -> Driver | None:
    """Lookup a single driver profile by driver_id."""
    row = _fetchone(
        conn,
        """
        SELECT driver_id, permanent_number, code, url, given_name, family_name, date_of_birth, nationality
        FROM drivers
        WHERE driver_id = ?
        """,
        (driver_id,),
    )
    if row is None:
        return None
    return _driver_from_row(row)


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
    with _write_cursor(conn) as cursor:
        _upsert_constructors_cursor(cursor, constructors, season)


def select_constructors(conn: sqlite3.Connection, season: int | None = None) -> list[Constructor]:
    """Retrieve constructor profiles, optionally filtered by season, sorted by constructor_id."""
    if season is not None:
        rows = _fetchall(
            conn,
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
        rows = _fetchall(
            conn,
            """
            SELECT constructor_id, url, name, nationality
            FROM constructors
            ORDER BY constructor_id ASC
            """,
        )
    return [_constructor_from_row(r) for r in rows]


def get_constructor(conn: sqlite3.Connection, constructor_id: str) -> Constructor | None:
    """Lookup a single constructor profile by constructor_id."""
    row = _fetchone(
        conn,
        """
        SELECT constructor_id, url, name, nationality
        FROM constructors
        WHERE constructor_id = ?
        """,
        (constructor_id,),
    )
    if row is None:
        return None
    return _constructor_from_row(row)


def upsert_driver_standings(conn: sqlite3.Connection, season: int, standings: list[DriverStanding]) -> None:
    """Upsert driver standings and dependencies into the database.

    Invariant: Pre-seed nested driver and constructor profiles to prevent referential integrity failures.
    Restructuring: Restructured so profile seeds and standings replacements run inside a single 'with conn:' transaction.
    """
    drivers = [s.driver for s in standings]
    constructors = []
    for s in standings:
        constructors.extend(s.constructors)

    with _write_cursor(conn) as cursor:
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


def select_driver_standings(conn: sqlite3.Connection, season: int) -> list[DriverStanding]:
    """Retrieve driver standings for the season, ordered by position."""
    rows = _fetchall(
        conn,
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

    standings = []
    for r in rows:
        driver = _driver_from_row(r, offset=5)
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

    with _write_cursor(conn) as cursor:
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


def select_constructor_standings(conn: sqlite3.Connection, season: int) -> list[ConstructorStanding]:
    """Retrieve constructor standings for the season, ordered by position."""
    rows = _fetchall(
        conn,
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
    return [
        ConstructorStanding(
            position=r[0],
            position_text=r[1],
            points=r[2],
            wins=r[3],
            constructor=_constructor_from_row(r, offset=4),
        )
        for r in rows
    ]


def upsert_race_results(conn: sqlite3.Connection, season: int, round: int, results: list[RaceResult]) -> None:  # noqa: A002
    """Upsert race results and dependencies into the database.

    Invariant: Pre-seed nested driver and constructor profiles to prevent referential integrity failures.
    Restructuring: Restructured so profile seeds and results replacements run inside a single 'with conn:' transaction.
    """
    drivers = [r.driver for r in results]
    constructors = [r.constructor for r in results]

    with _write_cursor(conn) as cursor:
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


def select_race_results(conn: sqlite3.Connection, season: int, round: int) -> list[RaceResult]:  # noqa: A002
    """Retrieve race results for the season and round, ordered by result_order."""
    rows = _fetchall(
        conn,
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

    results = []
    for r in rows:
        driver = _driver_from_row(r, offset=12)
        constructor = _constructor_from_row(r, offset=20)

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
