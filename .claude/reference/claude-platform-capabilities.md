# Claude Platform Capabilities

This file summarizes Claude's capabilities outside Claude Code (Projects, Memory, etc.), and the cross-platform decision sequence.

This repo is Claude Code-first; this file exists so the agent (and you) know what other Claude surfaces exist and when they're appropriate.

## Projects (Claude.ai)

A persistent workspace inside Claude.ai with its own knowledge base (≤200K tokens), custom instructions, and chat history. Use Projects when:

- Returning to the same body of work across many conversations
- A team needs shared AI workspace access
- You're re-uploading the same documents repeatedly

Skip when: one-off questions, quick brainstorming, knowledge base would exceed 200K tokens.

**For this repo:** Claude Code's `.claude/` infrastructure plays the same role at the project level. If you also use Claude.ai for non-Code work (docs, brainstorming, slide decks), a Project there can hold cross-conversation context.

## Memory (Claude.ai)

Cross-conversation personalization. Memory is account-scoped, applies outside Projects. Use Memory for: stable preferences (writing style, technical level). Skip when: working inside a Project (Project context overrides), need precise structured context, want incognito mode.

**For Claude Code:** the equivalent is `~/.claude/projects/<repo-path>/memory/` — a file-based memory system Claude Code maintains. Different mechanism, same goal.

## The decision sequence

When starting any task on any Claude surface, run through these in order:

1. **Need persistent context?** → use a Project (Claude.ai) or rely on `CLAUDE.md` + `.claude/` (Claude Code).
2. **Need external data?** → enable MCP connectors / upload files. No → proceed.
3. **Repeatable process?** → build or use a skill. No → prompt directly.
4. **Output format?**
   - File → file creation skill (`.claude/skills/{docx,pptx,xlsx,pdf}/`)
   - Interactive → artifact (Claude.ai)
   - Data → code execution (Claude.ai sandbox or local)
   - Text → just talk
5. **Need deep reasoning?** → extended thinking. No → standard response.

This is the routing logic embedded in this repo's top-level `CONTEXT.md`.
