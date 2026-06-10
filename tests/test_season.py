"""Worker-layer tests for load_season + SeasonSnapshot (SPEC-02 AC-9..11 at the worker seam)."""

import datetime

import httpx
import pytest

from pitwall.api.jolpica import JolpicaClient
from pitwall.cache.store import SeasonStore, Source, StoreResult
from pitwall.errors import JolpicaHttpError
from pitwall.workers.season import SeasonSnapshot, load_season

SEASON = 2026
FIXED_NOW = datetime.datetime(2026, 6, 9, 14, 30, tzinfo=datetime.UTC)


def make_store(db_conn, transport):
    client = JolpicaClient(transport=transport)
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    return client, store


async def test_load_season_returns_snapshot(db_conn, make_fixture_transport):
    requests: list[httpx.Request] = []
    client, store = make_store(db_conn, make_fixture_transport(requests))

    snapshot = await load_season(store, SEASON)

    assert isinstance(snapshot, SeasonSnapshot)
    assert isinstance(snapshot.schedule, StoreResult)
    assert snapshot.schedule.source == Source.NETWORK
    assert snapshot.driver_standings.source == Source.NETWORK
    assert snapshot.constructor_standings.source == Source.NETWORK
    assert len(requests) == 3
    assert snapshot.oldest_fetched_at == FIXED_NOW
    assert snapshot.has_stale is False
    await client.aclose()


async def test_snapshot_is_frozen(db_conn, make_fixture_transport):
    requests: list[httpx.Request] = []
    client, store = make_store(db_conn, make_fixture_transport(requests))
    snapshot = await load_season(store, SEASON)

    with pytest.raises(Exception, match=r"frozen|cannot assign"):
        snapshot.schedule = snapshot.driver_standings  # ty: ignore[invalid-assignment] - intentional frozen check

    await client.aclose()


async def test_load_season_propagates_jolpica_error(db_conn, make_failing_transport):
    failures: list[httpx.Request] = []
    client, store = make_store(db_conn, make_failing_transport(failures))

    with pytest.raises(JolpicaHttpError):
        await load_season(store, SEASON)
    await client.aclose()


async def test_snapshot_has_stale(db_conn, jolpica_payload, make_failing_transport):
    """Pre-seed all three scopes stale via public cache functions; failing transport => STALE_CACHE."""
    from pitwall.cache.db import (
        set_refresh_log,
        upsert_constructor_standings,
        upsert_driver_standings,
        upsert_races,
    )
    from pitwall.models import (
        parse_constructor_standings,
        parse_driver_standings,
        parse_races,
    )

    races = parse_races(jolpica_payload("races"))
    drivers = parse_driver_standings(jolpica_payload("driverstandings"))
    constructors = parse_constructor_standings(jolpica_payload("constructorstandings"))
    old_fetched = datetime.datetime(2026, 6, 7, 8, 0, tzinfo=datetime.UTC)

    upsert_races(db_conn, races, season=SEASON)
    set_refresh_log(db_conn, f"schedule:{SEASON}", old_fetched, record_count=len(races))
    upsert_driver_standings(db_conn, SEASON, drivers)
    set_refresh_log(db_conn, f"driver_standings:{SEASON}", old_fetched, record_count=len(drivers))
    upsert_constructor_standings(db_conn, SEASON, constructors)
    set_refresh_log(db_conn, f"constructor_standings:{SEASON}", old_fetched, record_count=len(constructors))

    failures: list[httpx.Request] = []
    client, store = make_store(db_conn, make_failing_transport(failures))

    snapshot = await load_season(store, SEASON)

    assert snapshot.schedule.source == Source.STALE_CACHE
    assert snapshot.has_stale is True
    assert snapshot.oldest_fetched_at == old_fetched
    await client.aclose()


def test_oldest_fetched_at_is_minimum():
    early = datetime.datetime(2026, 6, 9, 10, 0, tzinfo=datetime.UTC)
    late = datetime.datetime(2026, 6, 9, 12, 0, tzinfo=datetime.UTC)
    snapshot = SeasonSnapshot(
        schedule=StoreResult(data=[], fetched_at=late, source=Source.CACHE),
        driver_standings=StoreResult(data=[], fetched_at=early, source=Source.CACHE),
        constructor_standings=StoreResult(data=[], fetched_at=late, source=Source.CACHE),
    )

    assert snapshot.oldest_fetched_at == early
    assert snapshot.has_stale is False
