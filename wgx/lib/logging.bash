#!/usr/bin/env bash

# logging.bash - Eine einfache Logging-Bibliothek für Bash-Skripte.
#
# USAGE:
#   source logging.bash
#   log_info "Das ist eine Info-Meldung."
#   log_warn "Das ist eine Warnung."
#   log_error "Das ist ein Fehler."

# Farben für die Ausgabe
readonly COLOR_RESET="\033[0m"
readonly COLOR_RED="\033[0;31m"
readonly COLOR_YELLOW="\033[0;33m"
readonly COLOR_BLUE="\033[0;34m"

# Log-Funktion für verschiedene Level
_log() {
  local level="$1"
  local color="$2"
  shift 2
  local message="$@"
  local timestamp=$(date +"%Y-%m-%d %H:%M:%S")

  printf "${color}[%s] [%s]: %s${COLOR_RESET}\n" "$timestamp" "$level" "$message" >&2
}

# Öffentliche Logging-Funktionen
log_info() {
  _log "INFO" "$COLOR_BLUE" "$@"
}

log_warn() {
  _log "WARN" "$COLOR_YELLOW" "$@"
}

log_error() {
  _log "ERROR" "$COLOR_RED" "$@"
}
