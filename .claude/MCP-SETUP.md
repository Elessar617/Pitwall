# MCP & Plugin Setup

This document covers post-clone setup for the agent infrastructure: installing the recommended Claude Code plugins, registering the baseline MCP servers, providing credentials where needed, and verifying everything works.

The four hooks in `.claude/hooks/` work out of the box once the repo is cloned. MCP servers and plugins require explicit setup.

> **Important architectural note (May 2026):** In modern Claude Code, MCP servers are **not** configured in `.claude/settings.json` — the `mcpServers` field there is silently ignored by the schema validator. Register MCP servers via the `claude mcp add` CLI command (writes to `~/.claude.json`) or via a project-root `.mcp.json` file. This document uses `claude mcp add` throughout.

---

## 1. Plugin installation

This repo benefits from two community plugins. Install them after cloning:

```bash
# Add the official Claude Code plugin marketplace (one-time)
/plugin marketplace add anthropics/claude-plugins-official

# Install the recommended plugins
/plugin install obra/superpowers
/plugin install affaan-m/everything-claude-code
```

**`obra/superpowers`** — by Jesse Vincent. Provides ~20 battle-tested skills (TDD workflows, debugging patterns, brainstorming, plan-writing, plan-execution). The skills here overlap with this repo's project-specific skills; they coexist (project skills win where they cover the same ground).

**`affaan-m/everything-claude-code`** — Anthropic hackathon winner. Comprehensive Claude Code setup with security scanning, hook patterns, and config conventions. Useful as a reference for further extending `.claude/hooks/`.

To verify installation:
```bash
/plugin list
```
Both should appear.

---

## 2. MCP server installation

The baseline MCP servers below are recommended for any project derived from this scaffold. Run each command from anywhere; Claude Code records them in `~/.claude.json` keyed by scope.

### Scopes
- `--scope local` — this machine, this project only (default). Use for project-specific paths.
- `--scope user` — this machine, all projects. Use for identity-bound or generally-useful servers.
- `--scope project` — committed to the repo via `.mcp.json` (shared with collaborators). Use when the team should get the same config.

### 2.1 Credential-free servers (install in any order)

**filesystem** (project-local; sandboxed file ops scoped to the repo):
```bash
claude mcp add filesystem -s local -- npx -y @modelcontextprotocol/server-filesystem "$(pwd)"
```

**git** (project-local; needs the *git repository root*, which may be a parent directory if this project is a subfolder of a larger repo — check with `git rev-parse --show-toplevel`):
```bash
claude mcp add git -s local -- uvx mcp-server-git --repository "$(git rev-parse --show-toplevel)"
```

**fetch** (user-global; credential-free web fetch):
```bash
claude mcp add fetch -s user -- uvx mcp-server-fetch
```

> **Note:** `mcp-server-git` and `mcp-server-fetch` are Python packages (run via `uvx`, the `uv` package runner from Astral). Install `uv` first if you don't have it: `curl -LsSf https://astral.sh/uv/install.sh | sh`. The packages named `@modelcontextprotocol/server-git` and `@modelcontextprotocol/server-fetch` do *not* exist on npm — earlier versions of this scaffold documented them as `npx` installs, which never worked.

### 2.2 OAuth-based servers (HTTP transport, no token management)

**github** (official remote MCP server hosted by GitHub):
```bash
claude mcp add github -s user --transport http https://api.githubcopilot.com/mcp/
```

**sentry** (official remote MCP server hosted by Sentry):
```bash
claude mcp add sentry -s user --transport http https://mcp.sentry.dev/mcp
```

After registering these, `claude mcp list` will show them as **"Needs authentication"**. Complete the OAuth flow by running `/mcp` inside a Claude Code session — pick the server, and the CLI will open a browser for you to authorize. Tokens are stored securely by Claude Code; no manual PAT management.

These remote-HTTP+OAuth servers are strictly preferable to legacy stdio + Personal Access Token configurations: no secrets in your config files, server-side rate-limiting, and authentication revocable in one click.

### 2.3 Servers needing an API key

**brave-search** (web search via Brave Search API; requires a paid API key from [api-dashboard.search.brave.com](https://api-dashboard.search.brave.com/)):
```bash
claude mcp add brave-search -s user -e BRAVE_API_KEY=<your-real-key> -- npx -y @brave/brave-search-mcp-server
```

If you want to register the server now and add the key later, install with a placeholder, then re-register once you have a real key:
```bash
# Placeholder install (server registers but queries will fail until key is set):
claude mcp add brave-search -s user -e BRAVE_API_KEY=PLACEHOLDER -- npx -y @brave/brave-search-mcp-server

# When the real key is available:
claude mcp remove brave-search -s user
claude mcp add brave-search -s user -e BRAVE_API_KEY=<your-real-key> -- npx -y @brave/brave-search-mcp-server
```

> **CLI quirk:** the `claude mcp add` command's `-e` flag is variadic — it eats subsequent arguments. **Always put the server name *before* any `-e` flags.** Pattern: `claude mcp add <name> [-s scope] [-e KEY=val ...] -- <command> [args]`.

### 2.4 Legacy GitHub stdio MCP (Personal Access Token)

If you cannot use the OAuth-based remote GitHub MCP (Section 2.2) — for example, you're behind a network policy that blocks the HTTP transport, or you need to operate fully offline against a self-hosted GitHub Enterprise — you can fall back to the legacy stdio server with a GitHub Personal Access Token (PAT). Prefer Section 2.2 in all other cases.

#### Create the token

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)** or **Fine-grained tokens** → **Generate new token**.
3. **Recommended scopes for read-only first use:**
   - `repo` (read access to repos you'll work with) — or use a fine-grained token scoped to specific repos
   - `read:org` (if you need org info)
   - `read:user` (basic user info)
4. **Do NOT grant write scopes (`workflow`, `delete_repo`, etc.) until you've used the read-only setup for at least one full work session and are comfortable.**
5. Copy the token immediately — GitHub will not show it again.

#### Register the server with the token

```bash
claude mcp add github-stdio -s user -e GITHUB_PERSONAL_ACCESS_TOKEN=<your-token> -- npx -y @modelcontextprotocol/server-github
```

For convenience, you can put the token in your shell profile (`~/.zshrc` / `~/.bash_profile`) as `GITHUB_TOKEN` and reference it at install time:
```bash
claude mcp add github-stdio -s user -e GITHUB_PERSONAL_ACCESS_TOKEN="$GITHUB_TOKEN" -- npx -y @modelcontextprotocol/server-github
```

#### Enabling write scopes later

When you're ready to give the agent write access (e.g., to open PRs, comment on issues), generate a new token with broader scope on GitHub and re-register the server:
```bash
claude mcp remove github-stdio -s user
claude mcp add github-stdio -s user -e GITHUB_PERSONAL_ACCESS_TOKEN=<new-token> -- npx -y @modelcontextprotocol/server-github
```

### 2.5 Optional project-specific servers

Add these only if the project needs them. They live at `--scope local` because they're tied to a specific path.

**sqlite** (example: local-first data caching at `<repo>/data/<dbname>.db`):
```bash
mkdir -p "$(pwd)/data"
claude mcp add sqlite -s local -- npx -y mcp-server-sqlite-npx "$(pwd)/data/example.db"
```

The SQLite MCP server (`mcp-server-sqlite-npx` from johnnyoshika) is a community-maintained replacement for the archived `@modelcontextprotocol/server-sqlite`. The original is archived with an unpatched SQL injection vulnerability — do not install it.

### 2.6 Servers deliberately *not* installed by default

| Server | Why we skipped it |
|---|---|
| `@modelcontextprotocol/server-postgres` | **Archived with an unpatched SQL injection CVE.** If you need Postgres, use `HenkDz/postgresql-mcp-server` (community, maintained) or Supabase's own MCP server. |
| `@modelcontextprotocol/server-slack` | Archived. Slack released their own official MCP server in February 2026; install pattern still stabilizing. `korotovsky/slack-mcp-server` is the popular community choice if you need Slack now. |
| Docker Hub MCP (`docker/hub-mcp`) | Distributed as a git repo, not a clean npm package. Install when you have images to manage. |
| AWS / Kubernetes / Terraform MCPs | Defer until you have cloud infrastructure to manage. Each requires its own credential setup. |

---

## 3. Verifying MCP servers

```bash
claude mcp list
```

You should see each registered server with its connection status:
- `✓ Connected` — server starts cleanly. (Note: a credential-required server may show `✓ Connected` because it starts as a process, but actual tool calls will fail until the key is real.)
- `! Needs authentication` — OAuth-based server registered but not yet authenticated. Run `/mcp` inside Claude Code to complete the flow.
- `✗ Failed to connect` — server failed to start. Common causes: wrong package name, missing runtime (`uv`/`uvx`, `node`/`npx`), or a server-side requirement not met (e.g., the git MCP refuses a directory that isn't a git repository).

To remove a misconfigured server: `claude mcp remove <name> -s <scope>`.

---

## 4. Verifying skills

Ask Claude Code:
```
> What skills do you have available in this project?
```

Expected output includes the 14 local skills: 6 project skills (`tdd-loop`, `bug-investigation`, `refactor-protocol`, `spike-protocol`, `spec-authoring`, `data-analysis`), 4 office skills (`docx`, `pptx`, `xlsx`, `pdf`), and 4 routing-vendored skills (`systematic-debugging`, `writing-plans`, `brainstorming`, `karpathy-guidelines`).

---

## 5. Verifying hooks

The hooks fire on tool use; you can confirm they're wired by triggering them. Easiest test:

```bash
# Should fail with the pre-commit-tdd hook message:
echo '{"tool_name":"Bash","tool_input":{"command":"git commit -m foo"}}' \
  | $CLAUDE_PROJECT_DIR/.claude/hooks/pre-commit-tdd.sh
```

If you see the hook message on stderr (or the script exits non-zero), it's wired and runnable. The actual hook firing happens automatically when you invoke `git commit` via Claude Code.

To check the hook config that Claude Code is using:
```bash
jq '.hooks' .claude/settings.json
```

---

## 6. Adding more MCP servers

The baseline above is the recommended starting point. For more:

- **Browse the catalog:** see `.claude/reference/mcp-servers.md` for curated lists.
- **Add a new server:** use `claude mcp add` with the appropriate scope. Avoid editing `~/.claude.json` directly — it's managed by Claude Code.
- **Credential security:** for stdio servers, prefer `-e KEY=value` at registration time (stored in `~/.claude.json` outside the repo). For HTTP servers, prefer OAuth (no secret in config at all). Never commit real API keys.

---

## 7. Disabling hooks

To temporarily disable a hook (e.g., during a refactor where the TDD hook is blocking legitimate work):

1. Open `.claude/settings.json`.
2. Remove the entry from the `hooks` field for the hook you want to skip.
3. Save. Claude Code re-reads settings on the next tool call.
4. **Re-enable** as soon as the temporary work is done. Disable in a branch, restore on merge.

If you find yourself disabling a hook repeatedly for the same reason, that's a signal the hook needs scoping (file extensions, paths) — file an issue rather than working around it.

---

## 8. Archival: why this document changed (May 2026)

Earlier versions of this file declared four MCP servers (`filesystem`, `git`, `fetch`, `github`) directly in `.claude/settings.json` under a `mcpServers` field. **That config was always inert** — `mcpServers` is not a valid top-level field in Claude Code's settings.json schema, and the validator silently dropped it. The "baseline" MCP servers documented as ready-out-of-the-box never actually loaded.

Additionally:
- `@modelcontextprotocol/server-git` and `-fetch` were registered with `npx`, but those packages don't exist on npm — the Python versions on PyPI (`mcp-server-git`, `mcp-server-fetch`) are the real packages, run via `uvx`.
- `@modelcontextprotocol/server-github` has been formally superseded by GitHub's own official remote MCP server (`api.githubcopilot.com/mcp/`), which uses OAuth instead of PATs.

This version uses `claude mcp add` (the canonical install method) for everything, points each Python-based server at the right package via `uvx`, and switches GitHub to the official OAuth-based remote endpoint. The legacy PAT-based stdio install pattern is retained in Section 2.4 for environments where the OAuth-based HTTP server is not reachable.
