#!/usr/bin/env bash
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

OLD_SHA="$(git -C external/ecc rev-parse HEAD)"
echo "[update-ecc] current ECC SHA: $OLD_SHA"

git submodule update --remote external/ecc

NEW_SHA="$(git -C external/ecc rev-parse HEAD)"
echo "[update-ecc] new ECC SHA:     $NEW_SHA"

if [ "$OLD_SHA" = "$NEW_SHA" ]; then
  echo "[update-ecc] no upstream changes; exiting."
  exit 0
fi

OLD_AGENTS="$(jq 'length' .claude/registry/ecc-agents.json 2>/dev/null || echo 0)"
OLD_SKILLS="$(jq 'length' .claude/registry/ecc-skills.json 2>/dev/null || echo 0)"
OLD_COMMANDS="$(jq 'length' .claude/registry/ecc-commands.json 2>/dev/null || echo 0)"

npm run rebuild-registry

NEW_AGENTS="$(jq 'length' .claude/registry/ecc-agents.json)"
NEW_SKILLS="$(jq 'length' .claude/registry/ecc-skills.json)"
NEW_COMMANDS="$(jq 'length' .claude/registry/ecc-commands.json)"

echo
echo "[update-ecc] inventory diff:"
echo "  agents:   $OLD_AGENTS -> $NEW_AGENTS"
echo "  skills:   $OLD_SKILLS -> $NEW_SKILLS"
echo "  commands: $OLD_COMMANDS -> $NEW_COMMANDS"

git add external/ecc .claude/registry/
echo
echo "[update-ecc] staged the submodule bump and registry updates."
echo "Review with:  git diff --staged"
echo "Commit when ready."
