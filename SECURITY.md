# Security

## Supported Scope

This repo is a scaffold, not a hosted service. Security reports should focus on committed files, scripts, hooks, setup guidance, and anything that could cause secrets or private local state to be published accidentally.

## Reporting

Use GitHub private vulnerability reporting if it is enabled for the repository. If it is not enabled, open a minimal issue that says a security report is available, but do not include exploit details or secrets in the public issue body.

## Secret Handling

- Do not commit real tokens, API keys, passwords, local memory files, MCP memory graphs, or personal environment files.
- Use environment-variable references in `.claude/settings.json`; do not place raw credentials in version-controlled configuration.
- Keep `.env.local`, `.claude/.mcp-memory.json`, `.remember/`, `.serena/`, `.agents/`, `.codex/`, and maintainer-only notes ignored.
- Before making the repository public, run `npm run audit:agent-surface` and `npm test`.

## Agent Surface Audit

Run:

```bash
npm run audit:agent-surface
```

This checks the tracked and local agent instruction surface for hidden Unicode or HTML prompt payloads, raw secret-looking values, risky shell permission allowances, missing deny rules for secret-bearing paths, and MCP budget creep. It intentionally excludes the generated registry snapshots and the ECC submodule content; those are upstream/vendor inputs that should be refreshed and reviewed separately.
