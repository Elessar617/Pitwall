#!/usr/bin/env bash
# Hook: pre-commit-tdd.sh
# Trigger: PreToolUse on Bash with `git commit`
# Behavior: Block commit if code files have no corresponding test files in the same diff.
# Exempt: docs-only commits (no source files), config-only commits, the first commit.

set -euo pipefail

input=$(cat)
tool_name=$(echo "$input" | jq -r '.tool_name // ""')
command=$(echo "$input" | jq -r '.tool_input.command // ""')

# Only act on git commit invocations
if [[ "$tool_name" != "Bash" ]]; then exit 0; fi
if [[ ! "$command" =~ ^[[:space:]]*git[[:space:]]+commit ]]; then exit 0; fi

# Get the staged file list. Empty stage means git itself will block; let it.
staged=$(git diff --cached --name-only)
if [[ -z "$staged" ]]; then exit 0; fi

# Configurable: extensions considered "code" (not docs/config)
code_re='\.(py|ts|tsx|js|jsx|rs|go|rb|java|kt|swift|c|cpp|h|hpp|cs)$'
test_re='(^|/)(test_|tests?/|.*\.test\.|.*_test\.|.*\.spec\.)'

code_changed=0
test_changed=0
while IFS= read -r f; do
  if [[ "$f" =~ $code_re ]]; then
    if [[ "$f" =~ $test_re ]]; then
      test_changed=1
    else
      code_changed=1
    fi
  fi
done <<< "$staged"

if [[ $code_changed -eq 1 && $test_changed -eq 0 ]]; then
  cat >&2 <<EOF
[pre-commit-tdd] BLOCKED: this commit changes code files but adds no test files.

Per .claude/rules/testing-discipline.md, tests are written before (or with) the code they cover.

Staged code files (no matching test changes detected):
$(echo "$staged" | grep -E "$code_re" | grep -vE "$test_re" | sed 's/^/  - /')

Options:
  1. Add the corresponding test file changes to the same commit.
  2. If this is genuinely a non-tested change (refactor with snapshot proof, doc change in code, generated file), document why in the commit body and disable this hook in .claude/settings.json for the duration of the work, then re-enable.
EOF
  exit 1
fi

exit 0
