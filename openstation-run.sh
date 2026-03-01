#!/usr/bin/env bash
#
# openstation-run.sh — Launch an Open Station agent
#
# Supports two execution tiers:
#   Tier 1: Semi-autonomous (interactive, acceptEdits permission mode)
#   Tier 2: Fully autonomous (print mode, explicit tool allowlist, budget cap)
#
# Agent can be specified directly by name, or resolved from a task's
# frontmatter via --task.
#
# Flow: parse args → find project root → resolve agent → parse tools → exec
#
set -euo pipefail

# --- Constants ---------------------------------------------------------------

DEFAULT_TIER=2
DEFAULT_BUDGET=5
DEFAULT_TURNS=50

# Exit codes (documented in --help)
EXIT_USAGE=1
EXIT_NO_AGENT=2
EXIT_NO_CLAUDE=3
EXIT_AGENT_ERROR=4

# --- Output helpers ----------------------------------------------------------

err()  { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; }
info() { printf '\033[1;34minfo:\033[0m %s\n'  "$1" >&2; }

# --- Resolve project root ----------------------------------------------------

# Walk up from CWD looking for an Open Station project. Two layouts exist:
#   Installed: .openstation/ directory (target projects)
#   Source:    agents/ + install.sh (this repo)
find_project_root() {
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/.openstation" ]]; then
      echo "$dir"
      return 0
    fi
    if [[ -d "$dir/agents" && -f "$dir/install.sh" ]]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

# --- Parse allowed-tools from agent spec -------------------------------------

# Reads the `allowed-tools:` YAML list from an agent spec file.
# The list is a flat sequence of `- ToolName` entries under the
# `allowed-tools:` key in the YAML frontmatter. Outputs one tool per line.
#
# Example input (inside frontmatter):
#   allowed-tools:
#     - Read
#     - Write
#     - Bash
#
# This parser handles:
#   - Bare values:   - Read
#   - Quoted values: - "Read"  or  - 'Read'
parse_allowed_tools() {
  local spec_file="$1"
  local in_list=false

  while IFS= read -r line; do
    # Stop at end of frontmatter
    if [[ "$in_list" == true && "$line" == "---" ]]; then
      break
    fi

    # Detect start of the allowed-tools list
    if [[ "$line" =~ ^allowed-tools: ]]; then
      in_list=true
      continue
    fi

    if [[ "$in_list" == true ]]; then
      # A non-list-item line means we've left the allowed-tools block
      if [[ ! "$line" =~ ^[[:space:]]*-[[:space:]] ]]; then
        break
      fi
      # Extract value: strip leading "  - " then remove surrounding quotes
      local value="${line#*- }"
      value="${value#\"}" ; value="${value%\"}"
      value="${value#\'}" ; value="${value%\'}"
      echo "$value"
    fi
  done < "$spec_file"
}

# --- Resolve --task to agent name --------------------------------------------

# Given a task reference (numeric ID like "0013" or full slug like
# "0013-my-task"), find the task folder and extract its `agent:` field.
# Prints the agent name to stdout. Exits on error.
resolve_task_agent() {
  local project_root="$1"
  local task_ref="$2"

  # Search artifacts/tasks/ for a matching folder
  local task_dir=""
  for d in "$project_root"/artifacts/tasks/*/; do
    local name
    name="$(basename "$d")"
    if [[ "$name" == "$task_ref" || "$name" == "$task_ref"-* ]]; then
      task_dir="$d"
      break
    fi
  done

  if [[ -z "$task_dir" ]]; then
    err "Task not found: $task_ref"
    exit $EXIT_USAGE
  fi

  local spec="$task_dir/index.md"
  if [[ ! -f "$spec" ]]; then
    err "Task spec missing: $spec"
    exit $EXIT_USAGE
  fi

  # Extract agent field from YAML frontmatter
  local agent
  agent="$(sed -n 's/^agent: *//p' "$spec" | head -1)"
  if [[ -z "$agent" ]]; then
    err "No agent assigned to task: $(basename "$task_dir")"
    exit $EXIT_USAGE
  fi

  info "task $(basename "$task_dir") → agent $agent"
  echo "$agent"
}

# --- Locate agent spec -------------------------------------------------------

# Find the agent's markdown spec file. Checks installed path first
# (.openstation/agents/), then source repo path (agents/).
find_agent_spec() {
  local project_root="$1"
  local agent_name="$2"

  local installed="$project_root/.openstation/agents/$agent_name.md"
  local source="$project_root/agents/$agent_name.md"

  if [[ -f "$installed" ]]; then
    echo "$installed"
  elif [[ -f "$source" ]]; then
    echo "$source"
  else
    err "Agent spec not found: $agent_name"
    exit $EXIT_NO_AGENT
  fi
}

# --- Build claude command ----------------------------------------------------

# Assemble the claude CLI invocation as an array (safe, no eval).
# Tier 1: interactive session with acceptEdits permission mode.
# Tier 2: non-interactive print mode with explicit tool allowlist and budget.
build_command() {
  local agent_name="$1"
  local tier="$2"
  local budget="$3"
  local turns="$4"
  shift 4
  local tools=("$@")

  CMD=()

  if [[ "$tier" == "1" ]]; then
    CMD=(
      claude
      --agent "$agent_name"
      --permission-mode acceptEdits
    )
  else
    CMD=(
      claude
      -p "Execute your ready tasks."
      --agent "$agent_name"
      --allowedTools "${tools[@]}"
      --max-budget-usd "$budget"
      --max-turns "$turns"
      --output-format json
    )
  fi
}

# --- Usage -------------------------------------------------------------------

usage() {
  cat <<'USAGE'
Usage: openstation-run.sh <agent-name> [OPTIONS]
       openstation-run.sh --task <id-or-slug> [OPTIONS]

Launch an Open Station agent in autonomous or semi-autonomous mode.
Specify an agent directly, or use --task to resolve the agent from
a task's frontmatter.

Options:
  --task ID     Resolve agent from task (ID like 0013 or full slug)
  --tier 1|2    Execution tier (default: 2)
                  1 = Semi-autonomous (interactive, acceptEdits)
                  2 = Fully autonomous (print mode, allowedTools)
  --budget N    Max spend in USD (default: 5, tier 2 only)
  --turns N     Max agentic turns (default: 50, tier 2 only)
  --dry-run     Print the command without executing
  --help        Show this help message

Exit codes:
  0   Success
  1   Usage error (bad args, missing allowed-tools, no agent in task)
  2   Agent spec not found
  3   Claude CLI not found
  4   Agent exited with error
USAGE
  exit 0
}

# --- Parse arguments ---------------------------------------------------------

AGENT_NAME=""
TASK_REF=""
TIER="$DEFAULT_TIER"
BUDGET="$DEFAULT_BUDGET"
TURNS="$DEFAULT_TURNS"
DRY_RUN=false

[[ $# -eq 0 ]] && usage

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tier)
      [[ -z "${2:-}" ]] && { err "--tier requires a value (1 or 2)"; exit $EXIT_USAGE; }
      TIER="$2"
      [[ "$TIER" != "1" && "$TIER" != "2" ]] && { err "Invalid tier: $TIER (must be 1 or 2)"; exit $EXIT_USAGE; }
      shift 2 ;;
    --budget)
      [[ -z "${2:-}" ]] && { err "--budget requires a value"; exit $EXIT_USAGE; }
      BUDGET="$2"; shift 2 ;;
    --turns)
      [[ -z "${2:-}" ]] && { err "--turns requires a value"; exit $EXIT_USAGE; }
      TURNS="$2"; shift 2 ;;
    --task)
      [[ -z "${2:-}" ]] && { err "--task requires a task ID or slug"; exit $EXIT_USAGE; }
      TASK_REF="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    --help|-h)
      usage ;;
    -*)
      err "Unknown option: $1"; exit $EXIT_USAGE ;;
    *)
      [[ -n "$AGENT_NAME" ]] && { err "Unexpected argument: $1"; exit $EXIT_USAGE; }
      AGENT_NAME="$1"; shift ;;
  esac
done

# Exactly one of agent name or --task must be provided
if [[ -n "$AGENT_NAME" && -n "$TASK_REF" ]]; then
  err "Specify either an agent name or --task, not both"
  exit $EXIT_USAGE
fi
if [[ -z "$AGENT_NAME" && -z "$TASK_REF" ]]; then
  err "Agent name or --task is required"
  exit $EXIT_USAGE
fi

# --- Main flow ---------------------------------------------------------------

# 1. Check prerequisites
if ! command -v claude &>/dev/null; then
  err "claude CLI not found on \$PATH"
  exit $EXIT_NO_CLAUDE
fi

PROJECT_ROOT=""
if ! PROJECT_ROOT="$(find_project_root)"; then
  err "Could not find Open Station project root"
  exit $EXIT_USAGE
fi

# 2. Resolve agent name (from --task if needed)
if [[ -n "$TASK_REF" ]]; then
  AGENT_NAME="$(resolve_task_agent "$PROJECT_ROOT" "$TASK_REF")"
fi

# 3. Locate agent spec and parse allowed tools
AGENT_SPEC="$(find_agent_spec "$PROJECT_ROOT" "$AGENT_NAME")"

mapfile -t TOOLS < <(parse_allowed_tools "$AGENT_SPEC")
if [[ ${#TOOLS[@]} -eq 0 ]]; then
  err "No allowed-tools found in agent spec: $AGENT_SPEC"
  exit $EXIT_USAGE
fi

# 4. Build the claude command
build_command "$AGENT_NAME" "$TIER" "$BUDGET" "$TURNS" "${TOOLS[@]}"

# 5. Execute or dry-run
if [[ "$DRY_RUN" == true ]]; then
  printf '%q' "${CMD[0]}"
  for arg in "${CMD[@]:1}"; do
    printf ' %q' "$arg"
  done
  printf '\n'
  exit 0
fi

cd "$PROJECT_ROOT"
exec "${CMD[@]}"
