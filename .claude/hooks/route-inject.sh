#!/usr/bin/env bash
# UserPromptSubmit hook for Claude Code. Reads stdin (CC hook input JSON),
# extracts the prompt, runs scripts/route.mjs, returns CC injection JSON.
set -u
INPUT="$(cat)"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"

# Extract prompt via Node (safe parse; falls back to empty on error)
PROMPT="$(printf '%s' "$INPUT" | node -e 'let raw=""; process.stdin.on("data",d=>raw+=d); process.stdin.on("end",()=>{try{const j=JSON.parse(raw);console.log(j.prompt||j.tool_input?.prompt||"");}catch{console.log("");}})' 2>/dev/null)"

if [ -z "$PROMPT" ]; then exit 0; fi

# Run route.mjs; capture output; on error, fail silent
NARROWING="$(node "$REPO_ROOT/scripts/route.mjs" --prompt "$PROMPT" 2>/dev/null || true)"

if [ -z "$NARROWING" ]; then exit 0; fi

# Emit CC hook output (additionalContext gets injected as system message)
ESCAPED="$(printf '%s' "$NARROWING" | head -c 4000 | sed 's/\\/\\\\/g; s/"/\\"/g; s/$/\\n/' | tr -d '\n' | sed 's/\\n$//')"
printf '{"hookSpecificOutput":{"additionalContext":"%s"}}\n' "$ESCAPED"
