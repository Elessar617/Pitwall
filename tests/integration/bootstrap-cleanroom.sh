#!/usr/bin/env bash
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

echo "[test] bootstrap idempotency"
./scripts/bootstrap.sh > /tmp/boot1.log 2>&1
./scripts/bootstrap.sh > /tmp/boot2.log 2>&1
if ! grep -q "complete" /tmp/boot1.log; then echo "FAIL run 1"; cat /tmp/boot1.log; exit 1; fi
if ! grep -q "complete" /tmp/boot2.log; then echo "FAIL run 2"; cat /tmp/boot2.log; exit 1; fi
echo "PASS: bootstrap is idempotent"
