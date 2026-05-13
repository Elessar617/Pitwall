#!/usr/bin/env bash
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OLD_SKILLS="$(jq 'length' .claude/registry/harness-skills.json 2>/dev/null || echo 0)"
OLD_MCPS="$(jq 'length' .claude/registry/harness-mcps.json 2>/dev/null || echo 0)"

npm run rebuild-harness

NEW_SKILLS="$(jq 'length' .claude/registry/harness-skills.json)"
NEW_MCPS="$(jq 'length' .claude/registry/harness-mcps.json)"

echo "[refresh-harness] inventory diff:"
echo "  harness skills: $OLD_SKILLS -> $NEW_SKILLS"
echo "  harness MCPs:   $OLD_MCPS -> $NEW_MCPS"

git add .claude/registry/harness-*.json
echo "[refresh-harness] staged. Review with 'git diff --staged' and commit when ready."
