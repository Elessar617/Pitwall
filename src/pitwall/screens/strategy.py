"""Strategy mini-game screen (SPEC-12 D6-D7): wizard, race prompts, scoring."""

import asyncio
from collections import deque
from pathlib import Path

import rich.text
from textual import work
from textual.app import ComposeResult
from textual.widgets import Static

from pitwall.errors import DataParseError
from pitwall.game.model import Decision, StrategyPlan
from pitwall.game.score import GAME_START, GameState, actual_outcome, advance, render_score, score_plan
from pitwall.game.wizard import PlanDraft, draft_plan, draft_press, new_draft, render_draft, render_plan
from pitwall.openf1.errors import ReplayDataError
from pitwall.openf1.replay import TICK_INTERVAL_S, ReplayEngine, ReplaySession, load_session, merge_events
from pitwall.screens.base import PitwallScreen
from pitwall.screens.live_timing import format_speed

NO_REPLAY_TEXT = "Strategy game requires a replay — start pitwall with --replay <fixtures-dir>."
LOADING_TEXT = "Strategy — loading replay…"
COMMIT_TEXT = "Strategy — commit a plan to start the race."
LOAD_FAILED_TEXT = "Strategy game unavailable — failed to load replay data."
NO_EVENTS_TEXT = "Strategy game unavailable — replay data contains no events."


class StrategyScreen(PitwallScreen):
    """Plan → race → score, riding the replay engine (commit gates the run)."""

    def __init__(self) -> None:
        super().__init__()
        self._session: ReplaySession | None = None
        self._events: tuple = ()
        self._draft: PlanDraft | None = None
        self._plan: StrategyPlan | None = None
        self._acronym = ""
        self._state: GameState = GAME_START
        self._pending: deque = deque()
        self._decisions: list[Decision] = []
        self._racing = False

    def compose_body(self) -> ComposeResult:
        status = Static(NO_REPLAY_TEXT, id="game-status")
        yield status
        for name in ("form", "plan", "prompt", "event", "score"):
            widget = Static("", id=f"game-{name}")
            widget.display = False
            yield widget

    def on_mount(self) -> None:
        if self.app.config.replay_dir is None:
            return
        self.query_one("#game-status", Static).update(LOADING_TEXT)
        self._setup_worker()

    @work(exclusive=True, group="strategy-game")
    async def _setup_worker(self) -> None:
        status = self.query_one("#game-status", Static)
        replay_dir = self.app.config.replay_dir
        try:
            if replay_dir is None:
                # Invariant: the setup worker starts only when replay_dir is set.
                return
            session = await asyncio.to_thread(load_session, Path(replay_dir))
        except (ReplayDataError, DataParseError, OSError):
            status.update(LOAD_FAILED_TEXT)
            self.app.notify("Strategy replay data failed to load.", severity="error")
            return
        events = tuple(merge_events(session))
        if not events:
            status.update(NO_EVENTS_TEXT)
            return
        self._session = session
        self._events = events
        drivers = tuple(sorted((d.driver_number, d.name_acronym) for d in session.drivers))
        self._draft = new_draft(drivers)
        status.update(COMMIT_TEXT)
        form = self.query_one("#game-form", Static)
        form.update(rich.text.Text(render_draft(self._draft)))
        form.display = True

    def on_key(self, event) -> None:
        if self._racing:
            self._race_key(event.key)
            return
        # Once committed the wizard is dead: post-race keys are no-ops (AC-9f).
        if self._plan is not None or self._draft is None:
            return
        if event.key not in ("up", "down", "enter", "backspace") and not event.key.isdigit():
            return
        self._draft = draft_press(self._draft, event.key)
        plan = draft_plan(self._draft)
        if plan is not None:
            self._commit(plan)
        else:
            self.query_one("#game-form", Static).update(rich.text.Text(render_draft(self._draft)))

    def _commit(self, plan: StrategyPlan) -> None:
        self._plan = plan
        draft = self._draft
        if draft is None:
            # Invariant: _commit only follows a committed draft.
            return
        self._acronym = dict(draft.drivers)[plan.driver_number]
        self.query_one("#game-form", Static).display = False
        plan_widget = self.query_one("#game-plan", Static)
        plan_widget.update(rich.text.Text(render_plan(plan, self._acronym)))
        plan_widget.display = True
        self.query_one("#game-status", Static).update(
            rich.text.Text(f"Game {format_speed(self.app.config.replay_speed)} · {self._acronym} · starting…")
        )
        self._racing = True
        self._race_worker()

    def _render_window_prompt(self) -> None:
        """The visible prompt is ALWAYS the queue head (decision-display pairing)."""
        head = self._pending[0]
        widget = self.query_one("#game-prompt", Static)
        widget.update(f"Pit window — planned stop at lap {head.planned_lap}: [1] pit now · [2] stay out")
        widget.display = True

    def _race_key(self, key: str) -> None:
        if key not in ("1", "2") or not self._pending:
            return
        prompt = self._pending.popleft()
        choice = "pit" if key == "1" else "stay"
        self._decisions.append(Decision(prompt.planned_lap, choice))
        if self._pending:
            # Another window awaits: surface it so the next keypress targets
            # what the player sees.
            self._render_window_prompt()
            return
        verb = "pit now" if choice == "pit" else "stay out"
        self.query_one("#game-prompt", Static).update(f"Decision recorded — {verb} (planned lap {prompt.planned_lap}).")

    @work(exclusive=True, group="strategy-game")
    async def _race_worker(self) -> None:
        plan = self._plan
        session = self._session
        if plan is None or session is None:
            # Invariant: the worker starts only from _commit (plan set) after
            # a successful setup (session set); quiet return contains misuse.
            return
        status = self.query_one("#game-status", Static)
        speed = format_speed(self.app.config.replay_speed)
        engine = ReplayEngine(
            events=list(self._events),
            speed=self.app.config.replay_speed,
            tick_interval_s=TICK_INTERVAL_S,
            start_at=session.replay_start,
            sleep=self.app.replay_sleep,
        )
        async for tick in engine.ticks():
            self._state, prompts = advance(self._state, tuple(tick.events), plan)
            for prompt in prompts:
                if prompt.kind == "window":
                    self._pending.append(prompt)
                    self._render_window_prompt()
                else:
                    where = (
                        f"(planned lap {prompt.planned_lap})."
                        if prompt.planned_lap is not None
                        else "(no planned stop nearby)."
                    )
                    widget = self.query_one("#game-event", Static)
                    widget.update(rich.text.Text(f"{self._acronym} pitted — lap {prompt.lap} {where}"))
                    widget.display = True
            status.update(rich.text.Text(f"Game {speed} · {self._acronym} · {tick.playhead:%H:%M:%S} UTC"))
        outcome = actual_outcome(session.stints, self._state, plan.driver_number)
        breakdown = score_plan(plan, outcome, decisions=tuple(self._decisions), prompts_total=len(self._state.prompted))
        score_widget = self.query_one("#game-score", Static)
        score_widget.update(rich.text.Text(render_score(plan, outcome, breakdown)))
        score_widget.display = True
        status.update(rich.text.Text(f"Game over · {self._acronym} · final score {breakdown.total}"))
        self._racing = False

    def on_screen_suspend(self) -> None:
        # Navigating away abandons the run (accepted v1, R7) — cancel the group.
        self.workers.cancel_group(self, "strategy-game")

    def on_unmount(self) -> None:
        self.workers.cancel_group(self, "strategy-game")
