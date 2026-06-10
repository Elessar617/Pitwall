from datetime import UTC, datetime

import pytest

from pitwall.errors import DataParseError


def test_parse_sessions_success():
    # AC-1: The mock record parses to Session(session_key=11291, meeting_key=1285, session_name="Race", date_start=datetime(2026, 5, 24, 19, 0, tzinfo=UTC), date_end=datetime(2026, 5, 24, 21, 0, tzinfo=UTC))
    from pitwall.openf1.models import Session, parse_sessions

    mock_record = {
        "session_key": 11291,
        "meeting_key": 1285,
        "session_name": "Race",
        "session_type": "Race",
        "date_start": "2026-05-24T19:00:00+00:00",
        "date_end": "2026-05-24T21:00:00+00:00",
        "circuit_short_name": "Montreal",
    }

    sessions = parse_sessions([mock_record])
    assert len(sessions) == 1
    session = sessions[0]

    assert isinstance(session, Session)
    assert session.session_key == 11291
    assert session.meeting_key == 1285
    assert session.session_name == "Race"
    assert session.date_start == datetime(2026, 5, 24, 19, 0, tzinfo=UTC)
    assert session.date_end == datetime(2026, 5, 24, 21, 0, tzinfo=UTC)

    # Extra keys ignored: Session has exactly those five fields
    # Let's inspect the fields of the Session dataclass
    import dataclasses

    fields = [f.name for f in dataclasses.fields(Session)]
    assert set(fields) == {"session_key", "meeting_key", "session_name", "date_start", "date_end"}


def test_parse_sessions_rejections():
    # AC-1 Rejections:
    from pitwall.openf1.models import parse_sessions

    # 1. non-list payload
    with pytest.raises(DataParseError):
        parse_sessions("not a list")

    with pytest.raises(DataParseError):
        parse_sessions({"session_key": 11291})

    # 2. missing session_key (names the field)
    with pytest.raises(DataParseError) as exc_info:
        parse_sessions(
            [
                {
                    "meeting_key": 1285,
                    "session_name": "Race",
                    "date_start": "2026-05-24T19:00:00+00:00",
                    "date_end": "2026-05-24T21:00:00+00:00",
                }
            ]
        )
    assert "session_key" in str(exc_info.value)

    # 3. boolean meeting_key
    with pytest.raises(DataParseError):
        parse_sessions(
            [
                {
                    "session_key": 11291,
                    "meeting_key": True,
                    "session_name": "Race",
                    "date_start": "2026-05-24T19:00:00+00:00",
                    "date_end": "2026-05-24T21:00:00+00:00",
                }
            ]
        )

    # 4. missing/empty date_start
    # Missing date_start
    with pytest.raises(DataParseError):
        parse_sessions(
            [
                {
                    "session_key": 11291,
                    "meeting_key": 1285,
                    "session_name": "Race",
                    "date_end": "2026-05-24T21:00:00+00:00",
                }
            ]
        )
    # Empty date_start
    with pytest.raises(DataParseError):
        parse_sessions(
            [
                {
                    "session_key": 11291,
                    "meeting_key": 1285,
                    "session_name": "Race",
                    "date_start": "",
                    "date_end": "2026-05-24T21:00:00+00:00",
                }
            ]
        )
    # None date_start
    with pytest.raises(DataParseError):
        parse_sessions(
            [
                {
                    "session_key": 11291,
                    "meeting_key": 1285,
                    "session_name": "Race",
                    "date_start": None,
                    "date_end": "2026-05-24T21:00:00+00:00",
                }
            ]
        )

    # 5. naive date_end parses as UTC
    sessions = parse_sessions(
        [
            {
                "session_key": 11291,
                "meeting_key": 1285,
                "session_name": "Race",
                "date_start": "2026-05-24T19:00:00+00:00",
                "date_end": "2026-05-24T21:00:00",
            }
        ]
    )
    assert sessions[0].date_end == datetime(2026, 5, 24, 21, 0, tzinfo=UTC)
