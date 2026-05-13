# MCP Server Catalog

The four MCP servers configured in `.claude/settings.json` (`filesystem`, `git`, `fetch`, `github`) are the baseline. This file catalogs additional MCP servers available from the community and how to find more. Sourced from the Clief Resource Index (`docs/teaching/clief-notes/resource_index.pdf`, §4).

## How to add a server

1. Find the server (browse the directories below).
2. Read the source. **MCP servers can execute code on your machine.** Only install from repos you trust.
3. Add an entry to `.claude/settings.json` → `mcpServers`. Use `${ENV_VAR}` placeholders for credentials.
4. Document the env var setup in `.claude/MCP-SETUP.md`.
5. Restart Claude Code.

## Reference / first-party

| Server | Source | Purpose |
|---|---|---|
| Reference servers | github.com/modelcontextprotocol/servers | Filesystem, GitHub, Google Drive, Slack, Postgres, Puppeteer, etc. The canonical examples. |
| GitHub MCP (official) | github.com/github/github-mcp-server | Already configured in this repo (`github` server). Repo management, issue/PR automation, CI/CD intelligence, code analysis, Dependabot. |
| Stripe Agent Toolkit | github.com/stripe/agent-toolkit | Payments: products, customers, payment links, invoices, subscriptions. By Stripe. |

## Curated lists (for discovery)

| List | URL | Editorial style |
|---|---|---|
| `punkpeye/awesome-mcp-servers` | github.com/punkpeye/awesome-mcp-servers | Largest curated list, categorized with icons. Web directory included. |
| `wong2/awesome-mcp-servers` | github.com/wong2/awesome-mcp-servers | Broader categories; cross-reference with punkpeye. |
| `tolkonepiu/best-of-mcp-servers` | github.com/tolkonepiu/best-of-mcp-servers | 410+ servers ranked by quality score (stars, contributors, commit frequency). Updated weekly. |

**Recommended search order:** `tolkonepiu/best-of-mcp-servers` first (quality signal), then the awesome lists (coverage).

## Spec / protocol

[modelcontextprotocol.io](https://modelcontextprotocol.io) — official MCP spec, example servers and clients, guidance on building custom servers.

## Building a custom MCP server

If no existing server fits and you want Claude to interact with an internal tool:

- Reference: github.com/modelcontextprotocol/servers (study a similar one)
- SDKs: official Python and TypeScript SDKs at modelcontextprotocol.io
- Pattern: wrap your internal API in MCP's tool/resource/prompt vocabulary; expose the minimum surface area you need.
- Test locally before adding to `settings.json`.
