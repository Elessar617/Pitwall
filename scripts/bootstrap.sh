#!/usr/bin/env bash
set -e
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "[bootstrap] verifying submodule..."
if [ ! -f external/ecc/README.md ]; then
  echo "[bootstrap] external/ecc/ empty - initializing submodule"
  git submodule update --init --recursive
fi

if [ ! -d node_modules ]; then
  echo "[bootstrap] installing npm deps..."
  npm install --silent
fi

echo "[bootstrap] rebuilding registries..."
npm run rebuild-registry

echo "[bootstrap] complete."
