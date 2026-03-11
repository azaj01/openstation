#!/usr/bin/env bash
# install.sh — nvm-style installer for Open Station.
#
# Downloads the openstation repo to ~/.local/share/openstation/,
# symlinks the CLI binary to ~/.local/bin/openstation, and ensures
# PATH is configured.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/leonprou/openstation/v0.5.0/install.sh | bash
#   bash install.sh
#   bash install.sh --help

{

set -euo pipefail

# --- Config ------------------------------------------------------------------

OPENSTATION_VERSION="v0.7.0"
REPO_OWNER="leonprou"
REPO_NAME="openstation"
REPO_URL="https://github.com/${REPO_OWNER}/${REPO_NAME}.git"
RAW_BASE="https://raw.githubusercontent.com/${REPO_OWNER}/${REPO_NAME}/${OPENSTATION_VERSION}"

INSTALL_DIR="${OPENSTATION_DIR:-${HOME}/.local/share/openstation}"
BIN_DIR="${HOME}/.local/bin"

# --- Helpers -----------------------------------------------------------------

info()  { printf '  \033[1;32m✓\033[0m %s\n' "$1"; }
warn()  { printf '  \033[1;33m!\033[0m %s\n' "$1"; }
err()   { printf '  \033[1;31m✗\033[0m %s\n' "$1" >&2; }

usage() {
  cat <<'USAGE'
Usage: install.sh [OPTIONS]

Install Open Station CLI to ~/.local/share/openstation/ and make
the `openstation` binary available on PATH.

Options:
  --help       Show this help message

Environment:
  OPENSTATION_DIR   Override install location (default: ~/.local/share/openstation)

Examples:
  curl -fsSL https://raw.githubusercontent.com/leonprou/openstation/v0.5.0/install.sh | bash
  ./install.sh
USAGE
  exit 0
}

has_cmd() { command -v "$1" &>/dev/null; }

# --- Parse arguments ---------------------------------------------------------

while [[ $# -gt 0 ]]; do
  case "$1" in
    --help|-h) usage ;;
    *) err "Unknown option: $1"; usage ;;
  esac
done

# --- Banner ------------------------------------------------------------------

printf '\n\033[1mOpen Station Installer (%s)\033[0m\n\n' "$OPENSTATION_VERSION"

# --- Clone or update repo ----------------------------------------------------

if [[ -d "${INSTALL_DIR}/.git" ]]; then
  # Existing git install — pull updates
  printf 'Updating existing installation...\n'
  if has_cmd git; then
    git -C "$INSTALL_DIR" fetch --depth=1 origin tag "$OPENSTATION_VERSION" 2>/dev/null \
      || git -C "$INSTALL_DIR" fetch --depth=1 origin 2>/dev/null \
      || true
    git -C "$INSTALL_DIR" checkout "$OPENSTATION_VERSION" 2>/dev/null \
      || git -C "$INSTALL_DIR" checkout origin/main 2>/dev/null \
      || true
    info "Updated ${INSTALL_DIR}"
  else
    warn "git not found — cannot update. Remove ${INSTALL_DIR} and re-run to re-install."
  fi
elif [[ -d "$INSTALL_DIR" ]] && [[ ! -d "${INSTALL_DIR}/.git" ]]; then
  # Existing curl-based install — re-download
  printf 'Re-downloading (curl-based install)...\n'
  _do_curl_install=true
else
  # Fresh install
  printf 'Installing Open Station...\n'
  if has_cmd git; then
    git clone --depth=1 --branch "$OPENSTATION_VERSION" "$REPO_URL" "$INSTALL_DIR" 2>/dev/null \
      || git clone --depth=1 "$REPO_URL" "$INSTALL_DIR"
    info "Cloned to ${INSTALL_DIR}"
  else
    _do_curl_install=true
  fi
fi

# --- curl fallback (no git) -------------------------------------------------

if [[ "${_do_curl_install:-}" == "true" ]]; then
  if ! has_cmd curl; then
    err "Neither git nor curl found. Install one of them and retry."
    exit 1
  fi

  printf '  Downloading via curl (git not available)...\n'
  mkdir -p "$INSTALL_DIR"

  # Files to download — essential for CLI + init
  _files=(
    "dist/openstation"
    "docs/lifecycle.md"
    "docs/task.spec.md"
    "commands/openstation.create.md"
    "commands/openstation.dispatch.md"
    "commands/openstation.done.md"
    "commands/openstation.list.md"
    "commands/openstation.ready.md"
    "commands/openstation.reject.md"
    "commands/openstation.show.md"
    "commands/openstation.update.md"
    "skills/openstation-execute/SKILL.md"
    "templates/agents/architect.md"
    "templates/agents/author.md"
    "templates/agents/developer.md"
    "templates/agents/project-manager.md"
    "templates/agents/researcher.md"
  )

  _fail=0
  for f in "${_files[@]}"; do
    dst="${INSTALL_DIR}/${f}"
    mkdir -p "$(dirname "$dst")"
    if curl -fsSL "${RAW_BASE}/${f}" -o "$dst" 2>/dev/null; then
      : # success
    else
      warn "Failed to download: ${f}"
      _fail=1
    fi
  done

  if [[ $_fail -eq 1 ]]; then
    warn "Some files could not be downloaded. Install git for a complete install."
  fi

  info "Downloaded to ${INSTALL_DIR}"
fi

# --- Symlink CLI binary to PATH ----------------------------------------------

mkdir -p "$BIN_DIR"

_cli_src="${INSTALL_DIR}/dist/openstation"
_cli_dst="${BIN_DIR}/openstation"

if [[ ! -f "$_cli_src" ]]; then
  err "CLI binary not found at ${_cli_src}. Installation may be incomplete."
  exit 1
fi

chmod +x "$_cli_src"

# Create or update symlink
if [[ -L "$_cli_dst" ]] || [[ -f "$_cli_dst" ]]; then
  rm -f "$_cli_dst"
fi
ln -s "$_cli_src" "$_cli_dst"
info "Linked ${_cli_dst} → ${_cli_src}"

# --- Ensure PATH includes BIN_DIR -------------------------------------------

_add_path_to_profile() {
  local profile="$1"
  local export_line='export PATH="${HOME}/.local/bin:${PATH}"'

  # Already present?
  if grep -qF '.local/bin' "$profile" 2>/dev/null; then
    return 0
  fi

  printf '\n# Open Station\n%s\n' "$export_line" >> "$profile"
  info "Added PATH entry to ${profile}"
  return 0
}

if echo "$PATH" | tr ':' '\n' | grep -qx "$BIN_DIR"; then
  info "${BIN_DIR} already on PATH"
else
  _profile_updated=false

  # Detect shell and profile
  _shell_name="$(basename "${SHELL:-/bin/bash}")"
  case "$_shell_name" in
    zsh)
      _profiles=("${HOME}/.zshrc")
      ;;
    bash)
      # bash reads .bash_profile for login shells, .bashrc for interactive
      _profiles=()
      [[ -f "${HOME}/.bash_profile" ]] && _profiles+=("${HOME}/.bash_profile")
      [[ -f "${HOME}/.bashrc" ]] && _profiles+=("${HOME}/.bashrc")
      [[ ${#_profiles[@]} -eq 0 ]] && _profiles=("${HOME}/.bashrc")
      ;;
    *)
      _profiles=("${HOME}/.profile")
      ;;
  esac

  for _p in "${_profiles[@]}"; do
    if _add_path_to_profile "$_p"; then
      _profile_updated=true
      break
    fi
  done

  if [[ "$_profile_updated" == "false" ]]; then
    warn "${BIN_DIR} is not on your PATH."
    warn "Add this to your shell profile:"
    printf '    export PATH="%s:$PATH"\n' "$BIN_DIR"
  fi
fi

# --- Done --------------------------------------------------------------------

printf '\n\033[1;32mOpen Station installed successfully!\033[0m\n'
printf '\n'
printf 'Next steps:\n'
printf '  1. Open a new terminal (or run: source ~/.zshrc)\n'
printf '  2. Initialize a project: cd /path/to/project && openstation init\n'
printf '\n'

}
