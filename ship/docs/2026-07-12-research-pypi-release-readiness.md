<!-- wayfinder asset: resolves ticket #6 (PyPI release readiness) on map #2 (Future roadmap spec) - resolved 2026-07-12 -->

# Research: PyPI release readiness (`uvx pitwall`)

## Question
What stands between Pitwall and a PyPI release so a plain `uvx` invocation works?

## Findings

### (a) Name availability — `pitwall` is TAKEN
- https://pypi.org/project/pitwall/ exists: "Pitwall — the agentic AI companion to MultiViewer, the best app to watch motorsports", v0.2.2, released 2025-10-19, author Rob Spectre, MIT, alpha status. Verified via https://pypi.org/simple/pitwall/ (10 dist files, 0.1.0–0.2.2). It is **actively maintained and also motorsport-themed** — a squat/transfer request has no realistic chance and confusion risk is real.
- Alternatives verified free (HTTP 404 on the simple index, meaning unregistered):
  - `pitwall-f1` — https://pypi.org/simple/pitwall-f1/ → 404
  - `pitwall-tui` — https://pypi.org/simple/pitwall-tui/ → 404
- **uvx gotcha:** `uvx <name>` runs the console script matching the *package* name. With package `pitwall-f1` and only the existing script `pitwall = "pitwall.cli:main"` (pyproject.toml:12), users would need `uvx --from pitwall-f1 pitwall`. Fix: add a second entry `pitwall-f1 = "pitwall.cli:main"` so plain `uvx pitwall-f1` works (keep `pitwall` too — after `pip/uv tool install`, the short command still works).

### (b) Packaging metadata gaps (pyproject.toml, read this session)
Present: name, version 0.3.0, description, requires-python >=3.13, dependencies (textual, httpx), hatchling build backend, wheel packages config, one console script.
Missing (all standard for PyPI):
- `readme = "README.md"` — README.md exists; note its header uses `<img src="www/assets/logo.svg">` (repo-relative), which renders broken on PyPI — switch to an absolute raw.githubusercontent URL or drop the logo for the PyPI long description.
- `license = "MIT"` + `license-files = ["LICENSE"]` (LICENSE file exists, MIT, verified).
- `authors` / `maintainers`.
- `classifiers` — suggest: `Development Status :: 4 - Beta`, `Environment :: Console`, `Programming Language :: Python :: 3.13`, `Topic :: Terminals`, `Topic :: Games/Entertainment`, `Intended Audience :: End Users/Desktop`.
- `keywords` (f1, formula1, tui, textual, live-timing).
- `[project.urls]` — Homepage (https://elessar617.github.io/Pitwall/), Repository, Changelog.
- `requires-python = ">=3.13"` is unusually strict for a distributed tool; fine for uvx (uv fetches 3.13 automatically) but worth stating deliberately in docs.

### (c) Publish workflow
`.github/workflows/ci.yml` (read this session) already runs `uv build` as a smoke step but has no publish job. Two viable options, both supporting **trusted publishing** (OIDC, no long-lived token):

| Option | How | Fit |
|---|---|---|
| `uv publish` (recommended) | New `release.yml` on tag `v*`: `uv build` + `uv publish`, `permissions: id-token: write`, GitHub environment `pypi`. uv auto-detects the Actions OIDC environment and exchanges the token with PyPI ([uv packaging guide](https://docs.astral.sh/uv/guides/package/): "For publishing to PyPI from GitHub Actions or another Trusted Publisher, you don't need to set any credentials"). | Zero new tooling; uv is already the repo's toolchain and `uv build` is already exercised in CI. Astral ships a reference repo (astral-sh/trusted-publishing-examples). |
| `pypa/gh-action-pypi-publish` | Same trigger; build with `uv build`, upload with the PyPA action. | Battle-tested and PyPA-official, but adds a second publishing tool alongside uv for no gain here. |

Recommended shape: separate `release.yml` (not a job in ci.yml), trigger on published GitHub Release or `v*` tag, run the full test gate first, then build + `uv publish` inside `environment: pypi`. Also run the uv guide's install smoke: `uv run --with pitwall-f1 --no-project -- python -c "import pitwall"`.

### (d) Version / support policy for a 0.x TUI
- Stay on 0.x SemVer: 0.MINOR may break (keybindings, cache schema, CLI flags); 0.x.PATCH is fixes only. Current 0.3.0 already fits; drive version bumps via `uv version`.
- Declare in README/docs: only the latest 0.x release is supported; Python floor 3.13; no API stability promises until 1.0 (it's an app, not a library — the console script *is* the interface).
- Classifier `Development Status :: 4 - Beta` matches this posture.

## Release checklist
Agent-doable:
1. Decide + set `name = "pitwall-f1"`; add `pitwall-f1` console script alongside `pitwall`.
2. Add readme/license/authors/classifiers/keywords/urls to `[project]`; fix README logo URL for PyPI rendering.
3. Add `release.yml` (tag-triggered, gates → `uv build` → `uv publish`, `id-token: write`, `environment: pypi`).
4. Document version/support policy (ship/ or docs site).
5. Dry-run against TestPyPI if desired (separate trusted publisher registration there).

**Human-only steps:**
- Create/secure a PyPI account (2FA mandatory).
- Register a **pending trusted publisher** on PyPI for `pitwall-f1` naming repo `Elessar617/Pitwall`, workflow `release.yml`, environment `pypi` (per https://docs.pypi.org/trusted-publishers/adding-a-publisher/, linked from the uv guide) — this reserves the name at first publish; no token ever exists.
- Create the `pypi` GitHub environment (optionally with required reviewers).
- Push the release tag / publish the GitHub Release.

## Recommendation
Publish as **`pitwall-f1`** (over `pitwall-tui`: it says *what* the app is about, not what widget kit it uses, and the project already brands itself "for F1"). Use `uv publish` with trusted publishing in a new tag-triggered `release.yml`. Metadata work is ~30 lines of pyproject changes; the only irreducible human work is the PyPI account + pending-publisher registration + environment setup.

## Sources (fetched this session)
- https://pypi.org/project/pitwall/ — name taken, active competitor package
- https://pypi.org/simple/pitwall/ — dist file listing confirming releases
- https://pypi.org/simple/pitwall-f1/ and https://pypi.org/simple/pitwall-tui/ — 404, names free
- https://docs.astral.sh/uv/guides/package/ — uv build/publish + trusted publishing guidance
- Repo files: `pyproject.toml`, `.github/workflows/ci.yml`, `README.md`, `LICENSE` (all at /Users/gardnerwilson/workspace/github.com/elessar617/Pitwall/)