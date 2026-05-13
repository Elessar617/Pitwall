#!/usr/bin/env bash
PROFILE="${BLUEPRINT_HOOK_PROFILE:-standard}"
[ "$PROFILE" = "minimal" ] && exit 0
# Hook: block-cycle-overrun.sh
# Trigger: PreToolUse on Edit | Write when target path is build/workflows/*/03-validate/
# Behavior: Block if 5 or more review-N.md files already exist in the target dir.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')

case "$tool_name" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

target=$(echo "$input" | jq -r '.tool_input.file_path // ""')
if [[ -z "$target" ]]; then exit 0; fi

# Only fire for paths inside build/workflows/<slug>/03-validate/
if [[ ! "$target" =~ /build/workflows/[^/]+/03-validate/ ]]; then exit 0; fi

# Find the iteration's 03-validate dir from the target path
validate_dir=$(echo "$target" | sed 's|\(.*/03-validate\)/.*|\1|')

# Count existing review-N.md (any N)
review_count=$(find "$validate_dir" -maxdepth 1 -type f -name 'review-*.md' 2>/dev/null | wc -l | tr -d ' ')

if [[ "$review_count" -ge 5 ]]; then
  cat >&2 <<EOF
[block-cycle-overrun] BLOCKED: this iteration already has $review_count review cycles.

Per .claude/rules/review-discipline.md, the loop halts at 5 cycles. After this many failed cycles, the spec is likely wrong (not the implementation).

Iteration: $validate_dir

Required action:
  1. Stop the implementer/reviewer/adversary loop.
  2. Re-engage the planner with revised inputs (likely the original source artifact in spec/ needs revision).
  3. Generate a NEW iteration directory (build/workflows/<NN+1>-<slug>-v2/) rather than continuing this one.
  4. Document the escalation in 04-output/ESCALATION.md before opening a new iteration.
EOF
  exit 1
fi

exit 0
