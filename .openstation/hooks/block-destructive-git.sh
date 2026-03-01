#!/usr/bin/env bash
# PreToolUse hook: block-destructive-git
# Matcher: Bash
#
# Blocks destructive git commands that can cause data loss.
# Follows the Claude Code hook protocol: reads JSON from stdin,
# writes JSON decision to stdout, always exits 0.

set -euo pipefail

# Read the full input from stdin
INPUT="$(cat)"

# --- Check tool_name ---------------------------------------------------------

TOOL_NAME=""

if command -v jq &>/dev/null; then
  TOOL_NAME="$(echo "$INPUT" | jq -r '.tool_name // empty')"
else
  TOOL_NAME="$(echo "$INPUT" | grep -o '"tool_name"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//')"
fi

# Pass through non-Bash tools
if [[ "$TOOL_NAME" != "Bash" ]]; then
  printf '{"permissionDecision":"allow"}\n'
  exit 0
fi

# --- Extract command ---------------------------------------------------------

COMMAND=""

if command -v jq &>/dev/null; then
  COMMAND="$(echo "$INPUT" | jq -r '.tool_input.command // empty')"
else
  # Fallback: extract command field with grep/sed
  COMMAND="$(echo "$INPUT" | grep -o '"command"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//')"
fi

# If no command found, allow (not a Bash call we care about)
if [[ -z "$COMMAND" ]]; then
  printf '{"permissionDecision":"allow"}\n'
  exit 0
fi

# --- Blocked patterns --------------------------------------------------------

# Each pattern is checked against the command string.
# Format: "pattern|reason"
BLOCKED=(
  'git push --force|Destroys remote history'
  'git push -f|Destroys remote history'
  'git reset --hard|Destroys local changes'
  'git checkout \.|Discards all changes'
  'git checkout -- \.|Discards all changes'
  'git restore \.|Discards all changes'
  'git clean -f|Deletes untracked files'
  'git branch -D|Force-deletes branches'
  'rm -rf \.git|Destroys repository'
)

for entry in "${BLOCKED[@]}"; do
  pattern="${entry%%|*}"
  reason="${entry#*|}"

  # Use grep for pattern matching (handles regex)
  if echo "$COMMAND" | grep -qE "$pattern"; then
    printf '{"permissionDecision":"deny","reason":"Blocked: %s (%s)"}\n' "$pattern" "$reason"
    exit 0
  fi
done

# Not a blocked command — allow
printf '{"permissionDecision":"allow"}\n'
exit 0
