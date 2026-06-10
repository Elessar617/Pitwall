import argparse
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pitwall.app import PitwallApp
import os

from pitwall import __version__
from pitwall.config import MAX_REPLAY_SPEED, MIN_REFRESH_INTERVAL_S, MIN_REPLAY_SPEED, AppConfig, default_season


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments for the pitwall application.

    Raises:
        SystemExit: If version is requested or invalid arguments are passed.
    """
    parser = argparse.ArgumentParser(prog="pitwall")
    parser.add_argument(
        "--version",
        action="version",
        version=f"pitwall {__version__}",
    )
    parser.add_argument(
        "--refresh-interval",
        type=int,
        default=30,
        help="Refresh interval in seconds (minimum 5).",
    )
    parser.add_argument(
        "--replay",
        type=str,
        default=None,
        help="Directory containing OpenF1 session replay fixtures.",
    )
    parser.add_argument(
        "--replay-speed",
        type=float,
        default=None,
        help="Replay speed multiplier (1.0 to 600.0, default 60.0).",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Follow the current live session via OpenF1.",
    )

    args = parser.parse_args(argv)

    # Invariant: Refresh interval must be at least 5 seconds.
    if args.refresh_interval < MIN_REFRESH_INTERVAL_S:
        parser.error(f"refresh-interval must be at least {MIN_REFRESH_INTERVAL_S}")

    if args.live and args.replay is not None:
        parser.error("cannot specify --live with --replay")

    if args.replay is not None and not os.path.isdir(args.replay):
        parser.error(f"replay directory does not exist: {args.replay}")

    if args.replay_speed is not None and args.replay is None:
        parser.error("cannot specify --replay-speed without --replay")

    if args.replay_speed is None:
        args.replay_speed = 60.0

    if args.replay_speed < MIN_REPLAY_SPEED or args.replay_speed > MAX_REPLAY_SPEED:
        parser.error(f"replay-speed must be between {MIN_REPLAY_SPEED} and {MAX_REPLAY_SPEED}")

    return args


def build_app(args: argparse.Namespace) -> "PitwallApp":
    """Construct and configure the PitwallApp instance.

    The app import is lazy so --version stays headless (SPEC-02 AC-1).
    """
    from pitwall.app import PitwallApp

    config = AppConfig(
        season=default_season(),
        refresh_interval_s=args.refresh_interval,
        replay_dir=args.replay,
        replay_speed=args.replay_speed,
        live=args.live,
    )
    return PitwallApp(config=config)


def main(argv: list[str] | None = None) -> int:
    """Run the command line interface."""
    args = parse_args(argv)
    app = build_app(args)
    res = app.run()
    return 0 if res is None else int(res)
