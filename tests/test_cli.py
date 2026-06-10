import pytest

import pitwall
from pitwall.cli import build_app, main, parse_args


def test_version_prints_and_exits_zero(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    captured = capsys.readouterr()
    assert exc_info.value.code == 0
    assert captured.out.strip() == f"pitwall {pitwall.__version__}"


def test_version_does_not_build_app(monkeypatch):
    def mock_build_app(args):
        raise AssertionError("build_app should not be called")  # noqa: TRY003

    monkeypatch.setattr("pitwall.cli.build_app", mock_build_app)

    with pytest.raises(SystemExit):
        main(["--version"])


@pytest.mark.parametrize("value", ["4", "0", "-1"])
def test_refresh_interval_below_min_rejected(capsys, value):
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--refresh-interval", value])

    captured = capsys.readouterr()
    assert exc_info.value.code == 2
    assert "at least 5" in captured.err


def test_refresh_interval_default_and_min():
    args_min = parse_args(["--refresh-interval", "5"])
    assert args_min.refresh_interval == 5

    args_default = parse_args([])
    assert args_default.refresh_interval == 30


def test_build_app_plumbs_config(monkeypatch):
    # cli binds default_season at import; patch the cli-bound name, not the origin.
    monkeypatch.setattr("pitwall.cli.default_season", lambda now=None: 2026)
    args = parse_args(["--refresh-interval", "10"])

    app = build_app(args)

    assert app.config.refresh_interval_s == 10
    assert app.config.season == 2026


def test_main_runs_app_once(monkeypatch):
    run_calls = 0

    def mock_run(self):
        nonlocal run_calls
        run_calls += 1
        return 0

    # The interactive-terminal boundary is the one permitted mock here (SPEC AC-5).
    monkeypatch.setattr("pitwall.app.PitwallApp.run", mock_run)

    exit_code = main([])

    assert exit_code == 0
    assert run_calls == 1


def test_min_refresh_interval_single_source():
    """AC-1 (SPEC-03): cli must import the constant, not redefine it."""
    import inspect

    import pitwall.cli as cli_module
    import pitwall.config as config_module

    source = inspect.getsource(cli_module)
    assert "MIN_REFRESH_INTERVAL_S: int =" not in source
    assert cli_module.MIN_REFRESH_INTERVAL_S is config_module.MIN_REFRESH_INTERVAL_S
    assert "MIN_REFRESH_INTERVAL_S" in source.split("from pitwall.config import", 1)[-1].splitlines()[0]


def test_replay_flags_happy_path(tmp_path):
    # default values
    args = parse_args([])
    assert args.replay is None
    assert args.replay_speed == 60.0

    # valid --replay
    tmpdir = tmp_path / "replay_fixtures"
    tmpdir.mkdir()
    args = parse_args(["--replay", str(tmpdir)])
    assert args.replay == str(tmpdir)
    assert args.replay_speed == 60.0

    # valid --replay and --replay-speed
    args = parse_args(["--replay", str(tmpdir), "--replay-speed", "120.0"])
    assert args.replay == str(tmpdir)
    assert args.replay_speed == 120.0


def test_replay_flags_nonexistent_dir(capsys):
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--replay", "nonexistent_directory_12345"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "nonexistent_directory_12345" in captured.err


def test_replay_speed_out_of_bounds(capsys, tmp_path):
    tmpdir = tmp_path / "replay_fixtures"
    tmpdir.mkdir()
    # speed too low
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--replay", str(tmpdir), "--replay-speed", "0.5"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "0.5" in captured.err or "speed" in captured.err.lower()

    # speed too high
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--replay", str(tmpdir), "--replay-speed", "700"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "700" in captured.err or "speed" in captured.err.lower()


def test_replay_speed_without_replay(capsys):
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--replay-speed", "120"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "replay" in captured.err.lower()


def test_app_config_validation():
    from pitwall.config import AppConfig

    with pytest.raises(ValueError):
        AppConfig(season=2026, replay_speed=0.0)

    with pytest.raises(ValueError):
        AppConfig(season=2026, replay_speed=700.0)

    with pytest.raises(ValueError):
        AppConfig(season=2026, replay_speed=0.5)

    config_1 = AppConfig(season=2026, replay_speed=1.0)
    assert config_1.replay_speed == 1.0

    config_600 = AppConfig(season=2026, replay_speed=600.0)
    assert config_600.replay_speed == 600.0


def test_build_app_plumbs_replay_config(tmp_path, monkeypatch):
    monkeypatch.setattr("pitwall.cli.default_season", lambda now=None: 2026)
    tmpdir = tmp_path / "replay_fixtures"
    tmpdir.mkdir()
    args = parse_args(["--replay", str(tmpdir), "--replay-speed", "120"])
    app = build_app(args)
    assert app.config.replay_dir == str(tmpdir)
    assert app.config.replay_speed == 120.0


def test_live_flag_happy_path():
    # parse_args(["--live"]) -> args.live is True, replay fields defaulted
    args = parse_args(["--live"])
    assert args.live is True
    assert args.replay is None
    assert args.replay_speed == 60.0


def test_live_flag_mutual_exclusion(capsys, tmp_path):
    # ["--live", "--replay", "<dir>"] -> SystemExit with stderr containing cannot specify --live with --replay
    tmpdir = tmp_path / "replay_fixtures"
    tmpdir.mkdir()
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--live", "--replay", str(tmpdir)])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "cannot specify --live with --replay" in captured.err


def test_live_flag_speed_exclusion(capsys):
    # ["--live", "--replay-speed", "5"] -> the existing cannot specify --replay-speed without --replay
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--live", "--replay-speed", "5"])
    assert exc_info.value.code == 2
    captured = capsys.readouterr()
    assert "cannot specify --replay-speed without --replay" in captured.err


def test_build_app_propagates_live(monkeypatch):
    monkeypatch.setattr("pitwall.cli.default_season", lambda now=None: 2026)
    args = parse_args(["--live"])
    app = build_app(args)
    assert app.config.live is True


def test_app_openf1_transport_seam():
    # PitwallApp(...).openf1_transport is None by default and holds the injected transport when passed
    import httpx

    from pitwall.app import PitwallApp
    from pitwall.config import AppConfig

    config = AppConfig(season=2026, live=True)
    app_default = PitwallApp(config=config)
    assert hasattr(app_default, "openf1_transport")
    assert app_default.openf1_transport is None

    from conftest import wrap_transport

    mock_transport = wrap_transport(lambda req: httpx.Response(200))
    app_injected = PitwallApp(config=config, openf1_transport=mock_transport)
    assert app_injected.openf1_transport is mock_transport


def test_f15_import_grep():
    import re
    from pathlib import Path

    pattern = re.compile(r"^\s+(import|from)\s")
    matches = []

    # Repo-relative paths derived from Path(__file__)
    repo_root = Path(__file__).resolve().parent.parent
    app_py = repo_root / "src" / "pitwall" / "app.py"
    cli_py = repo_root / "src" / "pitwall" / "cli.py"

    for file_path in [app_py, cli_py]:
        in_type_checking = False
        with open(file_path, encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                # iter15 re-pin: `if TYPE_CHECKING:` imports never execute at
                # runtime, so they are not the F15 hazard (--version headless).
                if line.startswith("if TYPE_CHECKING:"):
                    in_type_checking = True
                    continue
                if in_type_checking:
                    if line.strip() and not line.startswith((" ", "\t")):
                        in_type_checking = False
                    else:
                        continue
                if pattern.match(line):
                    matches.append(f"{file_path.name}:{line_no}:{line.rstrip()}")

    assert len(matches) == 1, f"Expected exactly one match, got: {matches}"
    assert "from pitwall.app import PitwallApp" in matches[0]
