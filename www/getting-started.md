# Getting started

Pitwall is a Python app built on [Textual](https://textual.textualize.io/). It
is not on PyPI yet — run it straight from GitHub.

## Run it

=== "uvx (no install)"

    ```console
    $ uvx --from git+https://github.com/Elessar617/Pitwall pitwall
    ```

=== "Clone + uv"

    ```console
    $ git clone https://github.com/Elessar617/Pitwall
    $ cd Pitwall
    $ uv run pitwall
    ```

Requires Python 3.13+ (uv provisions it for you) and a terminal with Unicode
support — the track map is drawn in braille characters.

## Three ways to watch

**Season mode (default).** Live season data — schedule, standings, results,
profiles — fetched from the Jolpica F1 API and cached locally, so it degrades
gracefully offline.

```console
$ pitwall
```

**Replay mode.** Play back a recorded session window. A 60-second excerpt of
the 2026 Canadian Grand Prix ships in the repo — this is the fastest way to see
the live timing tower, the track map, and the strategy game without waiting for
a race weekend:

```console
$ pitwall --replay tests/fixtures/openf1/1285_11291_excerpt
```

Add `--replay-speed 10` to slow the playback down (default is ×60).

**Live mode.** Follow an in-progress session from the OpenF1 live API:

```console
$ pitwall --live
```

Outside a session you'll get an honest status line instead of a spinner — for
example `Live unavailable — latest session (Race) ended 15:00 UTC.`

!!! note "Data freshness"
    OpenF1's location telemetry can lag a session by days, so the track map may
    legitimately sit out a live race even while timing flows. The replay mode
    is the reliable demo.

## First keys

Press <span class="pitwall-key">l</span> for live timing,
<span class="pitwall-key">g</span> for the strategy game,
<span class="pitwall-key">q</span> to quit — the full map is on the
[keyboard reference](reference/keys.md).
