import asyncio
import datetime
import json
from pathlib import Path

import httpx
import pytest

from pitwall.api.jolpica import JolpicaClient
from pitwall.cache.db import connect, init_schema
from pitwall.cache.store import SeasonStore


@pytest.fixture
def jolpica_payload():
    """Fixture that returns a function to load Jolpica JSON fixtures by name."""

    def _loader(name: str) -> dict:
        path = Path(__file__).parent / "fixtures" / "jolpica" / f"{name}.json"
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    return _loader


@pytest.fixture
def db_conn(tmp_path):
    """Fixture that yields an initialized sqlite3 connection.

    Ownership & Lifetime: The fixture manages the lifetime of the returned connection.
    Safety Tradeoff: Enforces teardown to prevent connection leaks across test execution boundaries.
    """
    db_file = tmp_path / "pitwall_test.db"
    conn = connect(str(db_file))
    init_schema(conn)
    yield conn
    conn.close()


SEASON = 2026
FIXED_NOW = datetime.datetime(2026, 6, 9, 14, 30, tzinfo=datetime.UTC)
EXCERPT_DIR = Path(__file__).parent / "fixtures" / "openf1" / "1285_11291_excerpt"


@pytest.fixture
def excerpt_dir():
    """Fixture returning the path to the OpenF1 excerpt directory."""
    return EXCERPT_DIR


def _season_payloads(loader, overrides=None):
    payloads = {
        "races": loader("races"),
        "driverstandings": loader("driverstandings"),
        "constructorstandings": loader("constructorstandings"),
        "results": loader("results"),
        "/drivers/": loader("drivers"),
        "/constructors/": loader("constructors"),
    }
    if overrides:
        payloads.update(overrides)
    return payloads


@pytest.fixture
def make_fixture_transport(jolpica_payload):
    """Single-source fixture-serving MockTransport builder with request recorder (SPEC-03 AC-3)."""

    def _make(recorder, overrides=None):
        payloads = _season_payloads(jolpica_payload, overrides)

        def handler(request: httpx.Request) -> httpx.Response:
            recorder.append(request)
            for key, payload in payloads.items():
                if key in request.url.path:
                    return httpx.Response(200, json=payload)
            return httpx.Response(404, json={"error": "unexpected path"})

        return httpx.MockTransport(handler)

    return _make


@pytest.fixture
def make_failing_transport():
    """Single-source all-500 MockTransport builder."""

    def _make(recorder):
        def handler(request: httpx.Request) -> httpx.Response:
            recorder.append(request)
            return httpx.Response(500, json={"error": "down"})

        return httpx.MockTransport(handler)

    return _make


@pytest.fixture
def make_gated_transport(jolpica_payload):
    """Async fixture-serving transport that holds every response until `gate` is set (SPEC-03 AC-6)."""

    def _make(recorder, gate):
        payloads = _season_payloads(jolpica_payload)

        async def handler(request: httpx.Request) -> httpx.Response:
            recorder.append(request)
            await gate.wait()
            for key, payload in payloads.items():
                if key in request.url.path:
                    return httpx.Response(200, json=payload)
            return httpx.Response(404, json={"error": "unexpected path"})

        return httpx.MockTransport(handler)

    return _make


@pytest.fixture
def injected_store(db_conn, make_fixture_transport):
    """Real SeasonStore on tmp SQLite + fixture transport (caller owns resources)."""
    requests: list[httpx.Request] = []
    client = JolpicaClient(transport=make_fixture_transport(requests))
    store = SeasonStore(db_conn, client, now=lambda: FIXED_NOW)
    yield db_conn, client, store, requests
    asyncio.run(client.aclose())


def wrap_transport(handler):
    """Single construction point for bespoke per-test transports (SPEC-03 AC-3).

    Test modules define their own handler semantics (scripted sequences,
    URL-shape asserts, error injection) but never construct MockTransport
    directly — the grep contract `MockTransport(` lives only in conftest.
    """
    return httpx.MockTransport(handler)


def notifications(app):
    """The ONE sanctioned reader of Textual's private notification store (audit F3).

    Textual 8.x exposes no public read API; when one lands, this is the only
    site to change.
    """
    return list(app._notifications)
