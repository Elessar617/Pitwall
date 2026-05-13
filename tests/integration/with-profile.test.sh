#!/usr/bin/env bash
# Tests for scripts/with-profile.sh — the BLUEPRINT_HOOK_PROFILE wrapper.
#
# Verifies: usage gate, profile validation, env-var flow to child, exit-code
# propagation, argument pass-through. Matches the existing integration-test
# style (plain bash, FAIL+exit-1 on first regression).
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SCRIPT="$REPO_ROOT/scripts/with-profile.sh"

if [ ! -f "$SCRIPT" ]; then
  echo "FAIL: $SCRIPT does not exist"; exit 1
fi
if [ ! -x "$SCRIPT" ]; then
  echo "FAIL: $SCRIPT is not executable"; exit 1
fi

echo "[test] with-profile.sh: usage gate on missing args"
set +e
"$SCRIPT" >/dev/null 2>&1
rc_noargs=$?
"$SCRIPT" minimal >/dev/null 2>&1
rc_oneargs=$?
set -e
if [ "$rc_noargs" -eq 0 ]; then
  echo "FAIL: should exit non-zero on zero args (got 0)"; exit 1
fi
if [ "$rc_oneargs" -eq 0 ]; then
  echo "FAIL: should exit non-zero with only profile, no command (got 0)"; exit 1
fi
echo "PASS: usage gates fire on missing args"

echo "[test] with-profile.sh: rejects unknown profile"
set +e
"$SCRIPT" bogus true >/dev/null 2>&1
rc_bogus=$?
set -e
if [ "$rc_bogus" -eq 0 ]; then
  echo "FAIL: should reject profile 'bogus' (got exit 0)"; exit 1
fi
echo "PASS: unknown profile rejected"

echo "[test] with-profile.sh: minimal profile flows to child env"
OUTPUT="$("$SCRIPT" minimal bash -c 'echo "$BLUEPRINT_HOOK_PROFILE"')"
if [ "$OUTPUT" != "minimal" ]; then
  echo "FAIL: child saw '$OUTPUT', expected 'minimal'"; exit 1
fi
echo "PASS: minimal flows"

echo "[test] with-profile.sh: standard profile flows"
OUTPUT="$("$SCRIPT" standard bash -c 'echo "$BLUEPRINT_HOOK_PROFILE"')"
if [ "$OUTPUT" != "standard" ]; then
  echo "FAIL: expected 'standard', got '$OUTPUT'"; exit 1
fi
echo "PASS: standard flows"

echo "[test] with-profile.sh: strict profile flows"
OUTPUT="$("$SCRIPT" strict bash -c 'echo "$BLUEPRINT_HOOK_PROFILE"')"
if [ "$OUTPUT" != "strict" ]; then
  echo "FAIL: expected 'strict', got '$OUTPUT'"; exit 1
fi
echo "PASS: strict flows"

echo "[test] with-profile.sh: child exit code propagates (success)"
"$SCRIPT" minimal bash -c 'exit 0'

echo "[test] with-profile.sh: child exit code propagates (failure)"
set +e
"$SCRIPT" minimal bash -c 'exit 7'
rc=$?
set -e
if [ "$rc" -ne 7 ]; then
  echo "FAIL: expected exit code 7, got $rc"; exit 1
fi
echo "PASS: exit code propagates"

echo "[test] with-profile.sh: positional args pass through to child"
OUTPUT="$("$SCRIPT" standard echo "hello" "world")"
if [ "$OUTPUT" != "hello world" ]; then
  echo "FAIL: expected 'hello world', got '$OUTPUT'"; exit 1
fi
echo "PASS: args pass through"

echo "ALL with-profile tests passed"
