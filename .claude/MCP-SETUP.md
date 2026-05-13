# MCP & Plugin Setup

This document covers post-clone setup for the agent infrastructure: installing the recommended Claude Code plugins, providing credentials for the GitHub MCP, and verifying everything works.

The four hooks in `.claude/hooks/` and the credential-free MCP servers (`filesystem`, `git`, `fetch`) work out of the box once the repo is cloned. The GitHub MCP and the two recommended plugins require setup.

---

## 1. Plugin installation

This repo benefits from two community plugins, declared in `settings.json` under `_pluginsNote`. Install them after cloning:

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

## 2. GitHub MCP credential setup

The `github` MCP server requires a GitHub Personal Access Token (PAT) to authenticate.

### 2.1 Create the token

1. Go to https://github.com/settings/tokens
2. Click **Generate new token (classic)** or **Fine-grained tokens** → **Generate new token**.
3. **Recommended scopes for read-only first use:**
   - `repo` (read access to repos you'll work with) — or use a fine-grained token scoped to specific repos
   - `read:org` (if you need org info)
   - `read:user` (basic user info)
4. **Do NOT grant write scopes (`workflow`, `delete_repo`, etc.) until you've used the read-only setup for at least one full work session and are comfortable.**
5. Copy the token immediately — GitHub will not show it again.

### 2.2 Make the token available

Set the env var in your shell profile so Claude Code can read it:

```bash
# In ~/.zshrc or ~/.bash_profile (whichever you use)
export GITHUB_TOKEN="<your-token-value>"
```

Reload your shell or source the file. Verify:
```bash
test -n "$GITHUB_TOKEN" && echo "GITHUB_TOKEN is set"
```
Expected: `GITHUB_TOKEN is set` (do not echo the token value).

### 2.3 Restart Claude Code so it picks up the env var

Quit and relaunch your Claude Code session in a shell where `GITHUB_TOKEN` is set.

### 2.4 Enabling write scopes later

When you're ready to give the agent write access (e.g., to open PRs, comment on issues), edit your token's scopes on GitHub (or generate a new one with broader scope) and update `GITHUB_TOKEN` in your shell profile. No `settings.json` change needed.

---

## 3. Verifying MCP servers

After Claude Code is running with the env var set, ask it to list MCP servers:

```
> What MCP servers do you have available?
```

Or run from the CLI:
```bash
claude mcp list
```

Expected output includes `filesystem`, `git`, `fetch`, `github`. If `github` is missing or shows an auth error, recheck `GITHUB_TOKEN`.

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

The four configured MCP servers (filesystem, git, fetch, github) are the recommended baseline. For more:

- **Browse the catalog:** see `.claude/reference/mcp-servers.md` for curated lists (Stripe, Slack, Notion, Postgres, Puppeteer, etc.)
- **Add a new server:** edit `.claude/settings.json` → `mcpServers` and append a new entry. Restart Claude Code.
- **Credential security:** never put raw secrets in `settings.json` (it's version-controlled). Use `${ENV_VAR}` references and document the env var here.

---

## 7. Disabling hooks

To temporarily disable a hook (e.g., during a refactor where the TDD hook is blocking legitimate work):

1. Open `.claude/settings.json`.
2. Remove the entry from the `hooks` field for the hook you want to skip.
3. Save. Claude Code re-reads settings on the next tool call.
4. **Re-enable** as soon as the temporary work is done. Disable in a branch, restore on merge.

If you find yourself disabling a hook repeatedly for the same reason, that's a signal the hook needs scoping (file extensions, paths) — file an issue rather than working around it.
