"""Base-screen compose contract (Header / body hook / Footer)."""

from textual.widgets import Footer, Header, Static

from pitwall.app import PitwallApp
from pitwall.config import AppConfig
from pitwall.screens.base import PitwallScreen
from pitwall.screens.schedule import ScheduleScreen


class BodyProbeScreen(PitwallScreen):
    BODY_TEXT = "base body probe"


def test_base_declares_body_hook():
    assert issubclass(ScheduleScreen, PitwallScreen)
    assert callable(PitwallScreen.compose_body)
    assert isinstance(BodyProbeScreen.BODY_TEXT, str)
    assert BodyProbeScreen.BODY_TEXT


async def test_screen_composes_header_body_footer(injected_store):
    _conn, _client, store, _requests = injected_store
    app = PitwallApp(config=AppConfig(season=2026), store=store)
    async with app.run_test() as pilot:
        await app.workers.wait_for_complete()
        await pilot.pause()
        await app.push_screen(BodyProbeScreen())
        await pilot.pause()
        screen = app.screen
        assert screen.query_one(Header)
        assert screen.query_one(Footer)
        body = screen.query_one("#body", Static)
        assert not body.can_focus
