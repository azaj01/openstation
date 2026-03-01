#!/usr/bin/env bash
set -euo pipefail

# --- Constants ---------------------------------------------------------------

DEFAULT_TIER=2
DEFAULT_BUDGET=5
DEFAULT_TURNS=50

# Exit codes
EXIT_USAGE=1
EXIT_NO_AGENT=2
EXIT_NO_CLAUDE=3
EXIT_AGENT_ERROR=4

# --- Helpers -----------------------------------------------------------------

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

err() { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; }

# --- Resolve project root ----------------------------------------------------

# Walk up from CWD to find the project root. In installed projects,
# look for .openstation/; in the source repo, look for agents/.
find_project_root() {
  local dir="$PWD"
  while [[ "$dir" != "/" ]]; do
    if [[ -d "$dir/.openstation" ]] || [[ -d "$dir/agents" && -f "$dir/install.sh" ]]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

# --- Parse allowed-tools from agent frontmatter ------------------------------

# Reads the allowed-tools YAML list from an agent spec file.
# Outputs one tool per line.
parse_allowed_tools() {
  local spec_file="$1"
  local in_list=false

  while IFS= read -r line; do
    # End of frontmatter
    if [[ "$in_list" == true && "$line" == "---" ]]; then
      break
    fi

    # Start of allowed-tools list
    if [[ "$line" =~ ^allowed-tools: ]]; then
      in_list=true
      continue
    fi

    # Inside allowed-tools list — collect items
    if [[ "$in_list" == true ]]; then
      # Stop if we hit a non-list-item line (next field or end)
      if [[ ! "$line" =~ ^[[:space:]]*-[[:space:]] ]]; then
        break
      fi
      # Extract the value: strip leading "  - " and surrounding quotes
      local value="${line#*- }"
      value="${value#\"}"
      value="${value%\"}"
      value="${value#\'}"
      value="${value%\'}"
      echo "$value"
    fi
  done < "$spec_file"
}

# --- Parse arguments ---------------------------------------------------------

AGENT_NAME=""
TASK_REF=""
TIER="$DEFAULT_TIER"
BUDGET="$DEFAULT_BUDGET"
TURNS="$DEFAULT_TURNS"
DRY_RUN=false

if [[ $# -eq 0 ]]; then
  usage
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tier)
      if [[ -z "${2:-}" ]]; then
        err "--tier requires a value (1 or 2)"
        exit $EXIT_USAGE
      fi
      TIER="$2"
      if [[ "$TIER" != "1" && "$TIER" != "2" ]]; then
        err "Invalid tier: $TIER (must be 1 or 2)"
        exit $EXIT_USAGE
      fi
      shift 2
      ;;
    --budget)
      if [[ -z "${2:-}" ]]; then
        err "--budget requires a value"
        exit $EXIT_USAGE
      fi
      BUDGET="$2"
      shift 2
      ;;
    --turns)
      if [[ -z "${2:-}" ]]; then
        err "--turns requires a value"
        exit $EXIT_USAGE
      fi
      TURNS="$2"
      shift 2
      ;;
    --task)
      if [[ -z "${2:-}" ]]; then
        err "--task requires a task ID or slug"
        exit $EXIT_USAGE
      fi
      TASK_REF="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --help|-h)
      usage
      ;;
    -*)
      err "Unknown option: $1"
      exit $EXIT_USAGE
      ;;
    *)
      if [[ -n "$AGENT_NAME" ]]; then
        err "Unexpected argument: $1"
        exit $EXIT_USAGE
      fi
      AGENT_NAME="$1"
      shift
      ;;
  esac
done

if [[ -n "$AGENT_NAME" && -n "$TASK_REF" ]]; then
  err "Specify either an agent name or --task, not both"
  exit $EXIT_USAGE
fi

if [[ -z "$AGENT_NAME" && -z "$TASK_REF" ]]; then
  err "Agent name or --task is required"
  exit $EXIT_USAGE
fi

# --- Validate prerequisites --------------------------------------------------

# Check claude is on $PATH
if ! command -v claude &>/dev/null; then
  err "claude CLI not found on \$PATH"
  exit $EXIT_NO_CLAUDE
fi

# Find project root
PROJECT_ROOT=""
if ! PROJECT_ROOT="$(find_project_root)"; then
  err "Could not find Open Station project root"
  exit $EXIT_USAGE
fi

# --- Resolve --task to agent name --------------------------------------------

if [[ -n "$TASK_REF" ]]; then
  # Find task folder matching the ref (numeric ID or full slug)
  TASK_DIR=""
  for d in "$PROJECT_ROOT"/artifacts/tasks/*/; do
    basename="$(basename "$d")"
    # Match by full slug or numeric prefix
    if [[ "$basename" == "$TASK_REF" ]] || [[ "$basename" == "$TASK_REF"-* ]]; then
      TASK_DIR="$d"
      break
    fi
  done

  if [[ -z "$TASK_DIR" ]]; then
    err "Task not found: $TASK_REF"
    exit $EXIT_USAGE
  fi

  TASK_SPEC="$TASK_DIR/index.md"
  if [[ ! -f "$TASK_SPEC" ]]; then
    err "Task spec missing: $TASK_SPEC"
    exit $EXIT_USAGE
  fi

  # Extract agent field from frontmatter
  AGENT_NAME="$(sed -n 's/^agent: *//p' "$TASK_SPEC" | head -1)"
  if [[ -z "$AGENT_NAME" ]]; then
    err "No agent assigned to task: $(basename "$TASK_DIR")"
    exit $EXIT_USAGE
  fi

  printf '\033[1;34minfo:\033[0m task %s → agent %s\n' "$(basename "$TASK_DIR")" "$AGENT_NAME" >&2
fi

# Locate agent spec — try installed path first, then source repo
AGENT_SPEC=""
if [[ -f "$PROJECT_ROOT/.openstation/agents/$AGENT_NAME.md" ]]; then
  AGENT_SPEC="$PROJECT_ROOT/.openstation/agents/$AGENT_NAME.md"
elif [[ -f "$PROJECT_ROOT/agents/$AGENT_NAME.md" ]]; then
  AGENT_SPEC="$PROJECT_ROOT/agents/$AGENT_NAME.md"
else
  err "Agent spec not found: $AGENT_NAME"
  exit $EXIT_NO_AGENT
fi

# --- Build command -----------------------------------------------------------

# Read allowed-tools (needed for tier 2, validated for both)
mapfile -t TOOLS < <(parse_allowed_tools "$AGENT_SPEC")

if [[ ${#TOOLS[@]} -eq 0 ]]; then
  err "No allowed-tools found in agent spec: $AGENT_SPEC"
  exit $EXIT_USAGE
fi

# Build the command as an array (no eval)
CMD=()

if [[ "$TIER" == "1" ]]; then
  # Tier 1: Semi-autonomous — interactive with acceptEdits
  CMD=(
    claude
    --agent "$AGENT_NAME"
    --permission-mode acceptEdits
  )
elif [[ "$TIER" == "2" ]]; then
  # Tier 2: Fully autonomous — print mode with allowlist
  CMD=(
    claude
    -p "Execute your ready tasks."
    --agent "$AGENT_NAME"
    --allowedTools
  )
  for tool in "${TOOLS[@]}"; do
    CMD+=("$tool")
  done
  CMD+=(
    --max-budget-usd "$BUDGET"
    --max-turns "$TURNS"
    --output-format json
  )
fi

# --- Execute or print --------------------------------------------------------

if [[ "$DRY_RUN" == true ]]; then
  # Print the command in a copy-pasteable format
  printf '%q' "${CMD[0]}"
  for arg in "${CMD[@]:1}"; do
    printf ' %q' "$arg"
  done
  printf '\n'
  exit 0
fi

cd "$PROJECT_ROOT"
exec "${CMD[@]}"
