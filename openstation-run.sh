#!/usr/bin/env bash
#
# openstation-run.sh — Launch an Open Station agent
#
# Two collection strategies, one execution pipeline:
#
#   By-Agent: openstation-run.sh <agent-name> [OPTIONS]
#     Agent self-discovers tasks at runtime via openstation-execute skill.
#     Collection is opaque to the script.
#
#   By-Task:  openstation-run.sh --task <id-or-slug> [OPTIONS]
#     Script surveys the task tree, discovers ready subtasks, and builds
#     an explicit queue of (task-dir, agent-name) pairs.
#
# Pipeline: parse args → find root → COLLECT tasks → EXECUTE under tier constraints
#
# Each mode supports two tiers:
#   Tier 1: Interactive (acceptEdits permission mode)
#   Tier 2: Autonomous (print mode, explicit tool allowlist, budget cap)
#
set -euo pipefail

# --- Constants ---------------------------------------------------------------

DEFAULT_TIER=2
DEFAULT_BUDGET=5
DEFAULT_TURNS=50
DEFAULT_MAX_TASKS=1

# Exit codes (documented in --help)
EXIT_USAGE=1
EXIT_NO_AGENT=2
EXIT_NO_CLAUDE=3
EXIT_AGENT_ERROR=4
EXIT_TASK_NOT_READY=5

# --- Output helpers ----------------------------------------------------------

err()  { printf '\033[1;31merror:\033[0m %s\n' "$1" >&2; }
info() { printf '\033[1;34minfo:\033[0m %s\n'  "$1" >&2; }

# --- Shared utilities --------------------------------------------------------

# Walk up from CWD looking for an Open Station project. Two layouts exist:
#   Installed: .openstation/ directory (target projects, checked first)
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

# --- Execution helpers -------------------------------------------------------
# Shared machinery for launching agents under tier-based constraints.
# Used by both collection strategies.

# Read a single YAML frontmatter field from a task/agent spec.
# Usage: get_field <file> <field-name>
# Prints the value to stdout (empty string if field is missing or blank).
get_field() {
  local file="$1"
  local field="$2"
  sed -n "s/^${field}: *//p" "$file" | head -1
}

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

# Reads the `allowed-tools:` YAML list from an agent spec file.
# Handles bare values (- Read), quoted values (- "Bash(ls *)").
# Outputs one tool per line. Stops at end of frontmatter or next YAML key.
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

# Assemble the claude CLI invocation as an array (safe, no eval).
# Tier 1: interactive session with acceptEdits permission mode.
# Tier 2: autonomous print mode with explicit tool allowlist and budget.
#
# Args: agent_name tier budget turns prompt tools...
build_command() {
  local agent_name="$1"
  local tier="$2"
  local budget="$3"
  local turns="$4"
  local prompt="$5"
  shift 5
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
      -p "$prompt"
      --agent "$agent_name"
      --allowedTools "${tools[@]}"
      --max-budget-usd "$budget"
      --max-turns "$turns"
      --output-format json
    )
  fi
}

# --- Collection helpers (task collection only) -------------------------------
# Build an explicit task queue by surveying the task tree.

# Given a task reference (numeric ID or full slug), return the canonical
# task directory path. Prints path to stdout. Exits on error.
find_task_dir() {
  local project_root="$1"
  local task_ref="$2"

  for d in "$project_root"/artifacts/tasks/*/; do
    local name
    name="$(basename "$d")"
    if [[ "$name" == "$task_ref" || "$name" == "$task_ref"-* ]]; then
      echo "$d"
      return 0
    fi
  done

  err "Task not found: $task_ref"
  exit $EXIT_USAGE
}

# Check that a task's status is "ready". Exits with EXIT_TASK_NOT_READY if not.
assert_task_ready() {
  local task_dir="$1"
  local spec="$task_dir/index.md"

  if [[ ! -f "$spec" ]]; then
    err "Task spec missing: $spec"
    exit $EXIT_USAGE
  fi

  local status
  status="$(get_field "$spec" "status")"
  if [[ "$status" != "ready" ]]; then
    err "Task $(basename "$task_dir") has status '$status' (expected 'ready')"
    exit $EXIT_TASK_NOT_READY
  fi
}

# Scan a task directory for symlinked sub-task folders. Prints one sub-task
# directory path per line. When force=true, returns all subtasks regardless
# of status; otherwise only those with status "ready".
find_ready_subtasks() {
  local task_dir="$1"
  local force="${2:-false}"

  for entry in "$task_dir"/*/; do
    [[ -d "$entry" ]] || continue
    # Sub-tasks are symlinks to sibling directories under artifacts/tasks/
    [[ -L "${entry%/}" ]] || continue
    local sub_spec="$entry/index.md"
    [[ -f "$sub_spec" ]] || continue
    if [[ "$force" == true ]]; then
      echo "${entry%/}"
    else
      local status
      status="$(get_field "$sub_spec" "status")"
      if [[ "$status" == "ready" ]]; then
        echo "${entry%/}"
      fi
    fi
  done
}

# Launch an agent for a single task. Resolves agent from task frontmatter,
# builds the command, and executes in a subshell (not exec, so the caller
# can continue iterating the queue).
# Returns the exit code of the agent process.
run_single_task() {
  local project_root="$1"
  local task_dir="$2"
  local tier="$3"
  local budget="$4"
  local turns="$5"
  local dry_run="$6"

  local spec="$task_dir/index.md"
  local task_name
  task_name="$(basename "$task_dir")"

  # Resolve agent
  local agent
  agent="$(get_field "$spec" "agent")"
  if [[ -z "$agent" ]]; then
    err "No agent assigned to task: $task_name"
    return $EXIT_USAGE
  fi

  info "task $task_name → agent $agent"

  # Locate agent spec and parse tools
  local agent_spec
  agent_spec="$(find_agent_spec "$project_root" "$agent")"

  local -a tools
  mapfile -t tools < <(parse_allowed_tools "$agent_spec")
  if [[ ${#tools[@]} -eq 0 ]]; then
    err "No allowed-tools found in agent spec: $agent_spec"
    return $EXIT_USAGE
  fi

  # Build command with task-specific prompt
  local prompt="Execute task $task_name. Read its spec at artifacts/tasks/$task_name/index.md and work through the requirements."
  build_command "$agent" "$tier" "$budget" "$turns" "$prompt" "${tools[@]}"

  if [[ "$dry_run" == true ]]; then
    printf '%q' "${CMD[0]}"
    for arg in "${CMD[@]:1}"; do
      printf ' %q' "$arg"
    done
    printf '\n'
    return 0
  fi

  info "Launching agent $agent for task $task_name..."
  (cd "$project_root" && "${CMD[@]}")
  return $?
}

# --- Usage -------------------------------------------------------------------

usage() {
  cat <<'USAGE'
Usage: openstation-run.sh <agent-name> [OPTIONS]
       openstation-run.sh --task <id-or-slug> [OPTIONS]

Two collection strategies, one execution pipeline:

  By-Agent:  openstation-run.sh <agent-name>
    Agent self-discovers tasks at runtime via openstation-execute skill.

  By-Task:   openstation-run.sh --task <id-or-slug>
    Script surveys the task tree, discovers ready subtasks, and executes
    agents per-subtask. Falls back to the parent task if no subtasks exist.

Options:
  --task ID        Execute task by ID or slug (by-task mode)
  --max-tasks N    Max tasks to execute before stopping (default: 1,
                   by-task mode only)
  --tier 1|2       Execution tier (default: 2)
                     1 = Interactive (acceptEdits)
                     2 = Autonomous (print mode, allowedTools, budget)
  --budget N       Max spend in USD per agent invocation (default: 5, tier 2)
  --turns N        Max agentic turns per agent invocation (default: 50, tier 2)
  --force          Skip status checks (execute tasks in any status)
  --dry-run        Print the command(s) without executing
  --help           Show this help message

Exit codes:
  0   Success
  1   Usage error (bad args, missing allowed-tools, no agent in task)
  2   Agent spec not found
  3   Claude CLI not found
  4   Agent exited with error
  5   Task status is not 'ready' (bypassed with --force)
USAGE
  exit 0
}

# --- Parse arguments ---------------------------------------------------------

AGENT_NAME=""
TASK_REF=""
TIER="$DEFAULT_TIER"
BUDGET="$DEFAULT_BUDGET"
TURNS="$DEFAULT_TURNS"
MAX_TASKS="$DEFAULT_MAX_TASKS"
DRY_RUN=false
FORCE=false

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
    --max-tasks)
      [[ -z "${2:-}" ]] && { err "--max-tasks requires a value"; exit $EXIT_USAGE; }
      MAX_TASKS="$2"; shift 2 ;;
    --dry-run)
      DRY_RUN=true; shift ;;
    --force)
      FORCE=true; shift ;;
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

# 2. Branch on collection strategy
if [[ -n "$TASK_REF" ]]; then
  # ── TASK COLLECTION ───────────────────────────────────────────────────
  # Survey the task tree, build an explicit queue, execute via subshells.

  # Collect: find and validate the task
  TASK_DIR="$(find_task_dir "$PROJECT_ROOT" "$TASK_REF")"
  TASK_NAME="$(basename "$TASK_DIR")"
  if [[ "$FORCE" != true ]]; then
    assert_task_ready "$TASK_DIR"
  fi
  info "Task collection: $TASK_NAME"

  # Collect: discover ready subtasks
  mapfile -t SUBTASKS < <(find_ready_subtasks "$TASK_DIR" "$FORCE")

  if [[ ${#SUBTASKS[@]} -gt 0 ]]; then
    # ── Execute: iterate subtask queue ─────────────────────────────────
    info "Found ${#SUBTASKS[@]} ready subtask(s)"

    COMPLETED=0
    REMAINING=${#SUBTASKS[@]}

    for subtask_dir in "${SUBTASKS[@]}"; do
      if [[ "$COMPLETED" -ge "$MAX_TASKS" ]]; then
        break
      fi

      local_name="$(basename "$subtask_dir")"
      info "[$((COMPLETED + 1))/$MAX_TASKS] Executing subtask: $local_name"

      if run_single_task "$PROJECT_ROOT" "$subtask_dir" "$TIER" "$BUDGET" "$TURNS" "$DRY_RUN"; then
        COMPLETED=$((COMPLETED + 1))
        REMAINING=$((REMAINING - 1))
      else
        err "Subtask $local_name failed (exit $?)"
        break
      fi
    done

    # Print summary
    info "Summary: $COMPLETED completed, $REMAINING remaining of ${#SUBTASKS[@]} subtask(s)"
    if [[ "$REMAINING" -gt 0 && "$COMPLETED" -ge "$MAX_TASKS" ]]; then
      info "Task limit reached ($MAX_TASKS). Re-run to continue."
    fi
  else
    # ── Execute: no subtasks, run parent task directly ─────────────────
    info "No subtasks found, executing task directly"
    run_single_task "$PROJECT_ROOT" "$TASK_DIR" "$TIER" "$BUDGET" "$TURNS" "$DRY_RUN"
  fi

else
  # ── AGENT COLLECTION ──────────────────────────────────────────────────
  # Agent self-discovers tasks at runtime. Script resolves the agent spec,
  # parses tools, and launches with exec (replaces shell).

  # Execute: locate agent spec and parse allowed tools
  AGENT_SPEC="$(find_agent_spec "$PROJECT_ROOT" "$AGENT_NAME")"

  mapfile -t TOOLS < <(parse_allowed_tools "$AGENT_SPEC")
  if [[ ${#TOOLS[@]} -eq 0 ]]; then
    err "No allowed-tools found in agent spec: $AGENT_SPEC"
    exit $EXIT_USAGE
  fi

  # Execute: build command and launch
  build_command "$AGENT_NAME" "$TIER" "$BUDGET" "$TURNS" "Execute your ready tasks." "${TOOLS[@]}"

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
fi
