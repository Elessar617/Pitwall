#!/usr/bin/env bash
PROFILE="${BLUEPRINT_HOOK_PROFILE:-standard}"
[ "$PROFILE" = "minimal" ] && exit 0
# Hook: enforce-portability.sh
# Trigger: PostToolUse on Edit | Write when target path is .claude/rules/ or .claude/skills/
# Behavior: Grep the file content against .claude/.portability-deny.txt; fail if any
#           denied term is found (case-insensitive, word-ish boundaries).
# Exempt path: .claude/skills/{docx,pptx,xlsx,pdf}/ — vendored from anthropics/skills.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')

case "$tool_name" in
  Edit|Write|MultiEdit) ;;
  *) exit 0 ;;
esac

target=$(echo "$input" | jq -r '.tool_input.file_path // ""')
if [[ -z "$target" ]]; then exit 0; fi

# Only fire on .claude/rules/ or .claude/skills/
if [[ ! "$target" =~ /\.claude/(rules|skills)/ ]]; then exit 0; fi

# Exempt vendored office skills
if [[ "$target" =~ /\.claude/skills/(docx|pptx|xlsx|pdf)/ ]]; then exit 0; fi

# Locate the deny list relative to the .claude/ root
claude_root=$(echo "$target" | sed 's|\(.*/\.claude\)/.*|\1|')
deny_file="$claude_root/.portability-deny.txt"

if [[ ! -f "$deny_file" ]]; then
  # No deny list = nothing to enforce. Not an error.
  exit 0
fi

# File must exist (PostToolUse runs after the write)
if [[ ! -f "$target" ]]; then exit 0; fi

violations=()
while IFS= read -r term || [[ -n "$term" ]]; do
  # Skip blank lines and comments
  term=$(echo "$term" | sed 's/#.*$//' | xargs)
  [[ -z "$term" ]] && continue

  if grep -qi -- "$term" "$target"; then
    violations+=("$term")
  fi
done < "$deny_file"

if [[ ${#violations[@]} -gt 0 ]]; then
  cat >&2 <<EOF
[enforce-portability] VIOLATION: domain-specific terms found in $target
  $(printf '  - %s\n' "${violations[@]}")

Per .claude/rules/portability-discipline.md, files in .claude/rules/ and .claude/skills/ must stay domain-agnostic. Move the project-specific reference to .claude/reference/ instead.

Edit your file to remove these terms (or generalize the phrasing), then write again.
EOF
  exit 1
fi

exit 0
