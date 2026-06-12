# Pitwall live surface audit — 2026-06-12

## Scope

Audit Pitwall now that GitHub is the live source of truth, with emphasis on:

- user onboarding: install, first run, CLI help, replay demo, live mode
- under-the-hood CLI quality: lazy imports, defaults, argument validation
- runtime correctness: OpenF1/Jolpica request paths, cache-first behavior, offline degradation
- repository efficiency: dependency footprint, packaging, CI, contributor gates
- Graphify-assisted architecture review

## Baseline

- GitHub source of truth at audit start: `origin/main` commit `4524e9b`
- Package version: `pitwall 0.3.0`
- Python: `3.13.13` via `uv`
- Graphify: `graphifyy` / `graphify 0.8.38`
- Graphify output: `graphify-out/`, 708 nodes and 2027 edges from `src/pitwall`

## Findings Fixed

| Area | Finding | Fix |
|---|---|---|
| CLI customer surface | `pitwall --help` was functional but sparse, omitted first-run examples, and duplicated defaults instead of importing all config defaults. | Added mode examples, key hints, clearer help text, `pathlib.Path` replay validation, and single-source default constants. |
| OpenF1 client | Query values were not percent-encoded. A normal ISO timestamp with `+00:00` would be emitted with a raw `+`, which URL parsers can treat as a space. | Added a regression and encoded query values while preserving OpenF1's operator-in-parameter-name format. |
| Public onboarding docs | Public docs could be clearer about Python 3.13 provisioning, clone usage, replay speed, and current verification gates. | Updated README and getting-started docs with the live GitHub/uv path and less brittle verification wording. |
| Local agent/contributor docs | Local ignored agent-environment docs had stale references to FastF1, WebSockets, PyPI publishing, pre-commit config, and a May scaffold branch as current. | Corrected the local files during the audit, but did not force-add them because `.gitignore` explicitly marks the agent environment local-only. |

## Runtime Audit Notes

- CLI import remains lazy for the heavy Textual app path; `pitwall --version` stays headless.
- Measured `pitwall.cli` import in the local `uv` environment at `0.1804s`.
- Jolpica live smoke fetched 22 races for the 2026 season.
- Runtime data layers already use bounded retry loops, typed parse boundaries, cache-first reads, and offline fixture seams.
- Python runtime dependencies remain lean: `textual` and `httpx`; storage uses stdlib `sqlite3`.
- Graphify callflow export still warns about edge endpoints missing from its generated graph; this appears to be a Graphify export limitation, not a Pitwall runtime finding.

## Verification During Fixes

- `node --test tests/integration/bootstrap-rsync-recipe.test.mjs tests/integration/check-gate-commands.test.mjs` — 17 passed
- `uv run pytest tests/test_cli.py -W error` — 23 passed
- `uv run pytest tests/test_openf1_client.py -W error` — 16 passed
- `uv run pitwall --version` — `pitwall 0.3.0`
- `uv run pitwall --help` — shows mode examples and defaults
- Jolpica smoke — 22 races for 2026

## Final Gate Results

Public product gates:

- `uv run pytest -W error` — 382 passed
- `uv run ruff check .` — passed
- `uv run ruff format --check .` — 75 files already formatted
- `uv run ty check` — passed
- `uv build` — wheel and sdist built
- `npm audit --audit-level=moderate` — 0 vulnerabilities
- `uvx --from git+https://github.com/Elessar617/Pitwall pitwall --version` — `pitwall 0.3.0`

Local ignored scaffold gates:

- `node scripts/check-gate-commands.mjs --strict` — `consistent`
- `npm test` — 0 failure(s)

## Residual Recommendations

- Keep PyPI release as an explicit roadmap item; do not advertise `uvx pitwall` before publication.
- Add a live-session operator checklist during a real race weekend, because mocked transports cannot prove OpenF1 live freshness.
- Consider broadening Python support to 3.12 only after a deliberate compatibility pass; the current docs are honest that 3.13+ is required and `uv` provisions it.
