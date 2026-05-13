#!/usr/bin/env bash
PROFILE="${BLUEPRINT_HOOK_PROFILE:-standard}"
[ "$PROFILE" = "minimal" ] && exit 0
# Hook: block-output-without-signoff.sh
# Trigger: PreToolUse on Edit | Write when target path is build/workflows/*/04-output/
# Behavior: Block unless latest review-N.md has verdict: pass AND latest adversary-N.md
#           has findings: none|minor.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')

case "$tool_name" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

target=$(echo "$input" | jq -r '.tool_input.file_path // ""')
if [[ -z "$target" ]]; then exit 0; fi

# Only fire for paths inside build/workflows/<slug>/04-output/
if [[ ! "$target" =~ /build/workflows/[^/]+/04-output/ ]]; then exit 0; fi

# Allow .gitkeep / .keep without sign-off (placeholder files)
basename=$(basename "$target")
if [[ "$basename" == ".gitkeep" || "$basename" == ".keep" ]]; then exit 0; fi

iteration_dir=$(echo "$target" | sed 's|\(.*\)/04-output/.*|\1|')
validate_dir="$iteration_dir/03-validate"

if [[ ! -d "$validate_dir" ]]; then
  cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: no 03-validate/ directory at $validate_dir.
Reviewer + adversary must run before output. See .claude/rules/review-discipline.md.
EOF
  exit 1
fi

# Find latest review-N.md and adversary-N.md
latest_review=$(find "$validate_dir" -maxdepth 1 -type f -name 'review-*.md' | sort -V | tail -1)
latest_adv=$(find "$validate_dir" -maxdepth 1 -type f -name 'adversary-*.md' | sort -V | tail -1)

if [[ -z "$latest_review" || -z "$latest_adv" ]]; then
  cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: missing review or adversary report.
  Latest review:    ${latest_review:-NONE}
  Latest adversary: ${latest_adv:-NONE}
Both required. See .claude/rules/review-discipline.md.
EOF
  exit 1
fi

# Parse frontmatter for verdict and findings
verdict=$(awk '/^verdict:/{print $2; exit}' "$latest_review" | tr -d '"')
findings=$(awk '/^findings:/{print $2; exit}' "$latest_adv" | tr -d '"')

if [[ "$verdict" != "pass" ]]; then
  cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: latest review verdict is "$verdict" (need "pass").
File: $latest_review
EOF
  exit 1
fi

case "$findings" in
  none|minor) ;;
  *)
    cat >&2 <<EOF
[block-output-without-signoff] BLOCKED: latest adversary findings is "$findings" (need "none" or "minor").
File: $latest_adv
EOF
    exit 1
    ;;
esac

exit 0
