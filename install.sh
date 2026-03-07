#!/usr/bin/env bash
set -euo pipefail

# install.sh — Install the openstation CLI binary and run init.
#
# Sole responsibility: get `openstation` onto $PATH, then delegate
# all scaffolding to `openstation init`.

REPO_OWNER="leonprou"
REPO_NAME="openstation"
BRANCH="main"
BASE_URL="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${BRANCH}"
INSTALL_DIR="${HOME}/.local/bin"

# --- Source repo guard -------------------------------------------------------

if [[ -d "agents" && -f "install.sh" ]]; then
  printf '\033[1;31merror:\033[0m Cannot install into the source repo itself.\n' >&2
  printf '       Run this from a target project directory instead.\n' >&2
  exit 1
fi

# --- Helpers -----------------------------------------------------------------

info()  { printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
err()   { printf '  \033[1;31m✗\033[0m %s\n' "$1" >&2; }

usage() {
  cat <<'USAGE'
Usage: install.sh [OPTIONS]

Install the openstation CLI and initialize Open Station in the
current project.

Options:
  --local PATH     Copy files from a local clone instead of downloading
  --no-agents      Skip installing example agent specs
  --force          Overwrite user-owned files during init
  --dry-run        Show what init would do without writing
  --help           Show this help message

Examples:
  curl -fsSL https://raw.githubusercontent.com/leonprou/openstation/main/install.sh | bash
  ./install.sh --local /path/to/openstation
  ./install.sh --no-agents
USAGE
  exit 0
}

# --- Parse arguments ---------------------------------------------------------

LOCAL_PATH=""
INIT_ARGS=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    --local)
      LOCAL_PATH="$2"
      INIT_ARGS+=(--local "$2")
      shift 2
      ;;
    --no-agents)
      INIT_ARGS+=(--no-agents)
      shift
      ;;
    --force)
      INIT_ARGS+=(--force)
      shift
      ;;
    --dry-run)
      INIT_ARGS+=(--dry-run)
      shift
      ;;
    --help|-h)
      usage
      ;;
    *)
      err "Unknown option: $1"
      usage
      ;;
  esac
done

# --- Install CLI binary ------------------------------------------------------

printf '\n\033[1mOpen Station Installer\033[0m\n\n'

printf 'Installing CLI binary...\n'

mkdir -p "$INSTALL_DIR"

if [[ -n "$LOCAL_PATH" ]]; then
  if [[ ! -d "$LOCAL_PATH" ]]; then
    err "Local path does not exist: $LOCAL_PATH"
    exit 1
  fi
  # Normalize to absolute path
  LOCAL_PATH="$(cd "$LOCAL_PATH" && pwd)"
  cp "$LOCAL_PATH/bin/openstation" "$INSTALL_DIR/openstation"
else
  if ! command -v curl &>/dev/null; then
    err "curl is required but not found. Install it or use --local."
    exit 1
  fi
  curl -fsSL "$BASE_URL/bin/openstation" -o "$INSTALL_DIR/openstation"
fi

chmod +x "$INSTALL_DIR/openstation"
info "Installed $INSTALL_DIR/openstation"

# Check if INSTALL_DIR is on PATH
if ! echo "$PATH" | tr ':' '\n' | grep -qx "$INSTALL_DIR"; then
  printf '\n  \033[1;33m!\033[0m %s is not on your PATH.\n' "$INSTALL_DIR"
  printf '    Add this to your shell profile:\n'
  printf '    export PATH="%s:$PATH"\n\n' "$INSTALL_DIR"
fi

# --- Run openstation init ----------------------------------------------------

printf '\nRunning openstation init...\n\n'
exec "$INSTALL_DIR/openstation" init "${INIT_ARGS[@]}"
