#!/usr/bin/env bash
# with-profile.sh — run a command with BLUEPRINT_HOOK_PROFILE set in env.
#
# Usage:
#   scripts/with-profile.sh <profile> <command> [args...]
#
# Profiles:
#   minimal   hooks no-op (exit 0 immediately). Useful for spikes in lab/.
#   standard  default; all 4 hooks run their normal checks.
#   strict    reserved for ship/ workflows; currently identical to standard.
#
# Examples:
#   scripts/with-profile.sh minimal claude       # spike-friendly Claude Code session
#   scripts/with-profile.sh strict gh pr list    # max-strictness for release prep
#
# The 4 hooks under .claude/hooks/ read $BLUEPRINT_HOOK_PROFILE on each
# invocation; setting it for the child process is enough to flow the
# routing-layer's recommended profile into actual hook behavior.

set -euo pipefail

usage() {
  cat >&2 <<EOF
Usage: $0 <profile> <command> [args...]
Profiles: minimal | standard | strict
EOF
  exit 64  # EX_USAGE
}

if [ "$#" -lt 2 ]; then
  usage
fi

profile="$1"
shift

case "$profile" in
  minimal|standard|strict)
    ;;
  *)
    echo "error: unknown profile '$profile' (expected: minimal, standard, strict)" >&2
    exit 64
    ;;
esac

export BLUEPRINT_HOOK_PROFILE="$profile"
exec "$@"
