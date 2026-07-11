"""Shared chassis screen: Header / body hook / Footer (SPEC-03 scope 4)."""

from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Header, Static

if TYPE_CHECKING:
    from pitwall.app import PitwallApp


class StoreNotInitializedError(RuntimeError):
    """Exception raised when the store is not initialized on the app."""

    def __init__(self) -> None:
        super().__init__("App store is not initialized")


class PitwallScreen(Screen):
    """Base screen composing the chassis around a subclass-provided body."""

    BODY_TEXT: str = ""

    @property
    def app(self) -> "PitwallApp":  # type: ignore[override]
        """The owning app, typed: every screen seam (config/store/clock/...) resolves."""
        return cast("PitwallApp", super().app)

    def compose_body(self) -> ComposeResult:
        """Body hook — placeholders keep the SPEC-02 contract Static."""
        yield Static(self.BODY_TEXT, id="body")

    def compose(self) -> ComposeResult:
        yield Header()
        yield from self.compose_body()
        yield Footer()
