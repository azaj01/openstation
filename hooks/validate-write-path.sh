#!/usr/bin/env bash
# PreToolUse hook: validate-write-path
# Matcher: Write|Edit
#
# Allows writes only to vault directories. Denies everything else.
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

# Pass through non-Write/Edit tools
if [[ "$TOOL_NAME" != "Write" && "$TOOL_NAME" != "Edit" ]]; then
  printf '{"permissionDecision":"allow"}\n'
  exit 0
fi

# --- Extract file_path -------------------------------------------------------

FILE_PATH=""

if command -v jq &>/dev/null; then
  FILE_PATH="$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')"
else
  # Fallback: extract file_path with grep/sed
  # Handles: "file_path": "/some/path" or "file_path":"/some/path"
  FILE_PATH="$(echo "$INPUT" | grep -o '"file_path"[[:space:]]*:[[:space:]]*"[^"]*"' | head -1 | sed 's/.*:[[:space:]]*"//;s/"$//')"
fi

# If no file_path found, allow (not a Write/Edit call we care about)
if [[ -z "$FILE_PATH" ]]; then
  printf '{"permissionDecision":"allow"}\n'
  exit 0
fi

# --- Resolve project root ----------------------------------------------------

find_project_root() {
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/.openstation" ]] || [[ -d "$dir/agents" && -f "$dir/install.sh" ]]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  echo "$PWD"
}

PROJECT_ROOT="$(find_project_root)"

# --- Normalize path ----------------------------------------------------------

# Convert relative path to absolute
if [[ "$FILE_PATH" != /* ]]; then
  FILE_PATH="$PROJECT_ROOT/$FILE_PATH"
fi

# Resolve symlinks and ../ segments for comparison
# Use realpath if available, otherwise fall back to manual resolution
if command -v realpath &>/dev/null; then
  # --canonicalize-missing handles non-existent paths (new files)
  RESOLVED="$(realpath --canonicalize-missing "$FILE_PATH" 2>/dev/null || echo "$FILE_PATH")"
else
  RESOLVED="$FILE_PATH"
fi

# --- Allowed directories -----------------------------------------------------

# Source repo layout (development)
ALLOWED_PREFIXES=(
  "$PROJECT_ROOT/artifacts/"
  "$PROJECT_ROOT/tasks/"
  "$PROJECT_ROOT/agents/"
  "$PROJECT_ROOT/docs/"
  "$PROJECT_ROOT/skills/"
  "$PROJECT_ROOT/commands/"
  "$PROJECT_ROOT/hooks/"
)

# Installed layout (.openstation/)
ALLOWED_PREFIXES+=(
  "$PROJECT_ROOT/.openstation/artifacts/"
  "$PROJECT_ROOT/.openstation/tasks/"
  "$PROJECT_ROOT/.openstation/agents/"
  "$PROJECT_ROOT/.openstation/docs/"
  "$PROJECT_ROOT/.openstation/skills/"
  "$PROJECT_ROOT/.openstation/commands/"
  "$PROJECT_ROOT/.openstation/hooks/"
)

# CLAUDE.md at project root
ALLOWED_FILES=(
  "$PROJECT_ROOT/CLAUDE.md"
)

# --- Check path --------------------------------------------------------------

for prefix in "${ALLOWED_PREFIXES[@]}"; do
  if [[ "$RESOLVED" == "$prefix"* ]]; then
    printf '{"permissionDecision":"allow"}\n'
    exit 0
  fi
done

for allowed_file in "${ALLOWED_FILES[@]}"; do
  if [[ "$RESOLVED" == "$allowed_file" ]]; then
    printf '{"permissionDecision":"allow"}\n'
    exit 0
  fi
done

# Denied — path is outside vault directories
printf '{"permissionDecision":"deny","reason":"Write blocked: path is outside allowed vault directories: %s"}\n' "$FILE_PATH"
exit 0
