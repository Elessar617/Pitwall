#!/usr/bin/env bash
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOOK="$REPO_ROOT/.claude/hooks/route-inject.sh"

echo "[test] empty input"
echo '' | "$HOOK"
if [ $? -ne 0 ]; then echo "FAIL: empty input did not exit 0"; exit 1; fi

echo "[test] malformed JSON input"
echo 'not json at all' | "$HOOK"
if [ $? -ne 0 ]; then echo "FAIL: malformed input did not exit 0"; exit 1; fi

echo "PASS: hook fails open on bad inputs"
