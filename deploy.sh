#!/bin/bash
# =============================================================================
# pySSM2 Deploy Script
# Installs, uninstalls, and manages the pySSM2 logger service
# =============================================================================

set -euo pipefail

INSTALL_DIR="/etc/pySSM2"
LOG_DIR="/var/log/subaru"
PYTHON_LOG_DIR="/var/log/subaru/python"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Detect current user and Wayland environment
CURRENT_USER="$(whoami)"
CURRENT_UID="$(id -u)"
WAYLAND_SOCK="$(ls /run/user/"$CURRENT_UID"/wayland-* 2>/dev/null | head -1 || true)"
if [ -n "$WAYLAND_SOCK" ]; then
    WAYLAND_DISP="$(basename "$WAYLAND_SOCK")"
else
    WAYLAND_DISP="wayland-1"
fi

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

info()  { echo "[INFO]  $*"; }
error() { echo "[ERROR] $*" >&2; }

require_root() {
    if [ "$EUID" -ne 0 ]; then
        error "This command must be run as root (use sudo)."
        exit 1
    fi
}

# -----------------------------------------------------------------------------
# Commands
# -----------------------------------------------------------------------------

cmd_help() {
    cat <<'EOF'
pySSM2 Deploy Script
====================

Usage: ./deploy.sh <command>

Installation:
  install        Install dependencies, deploy files, and set up systemd services
  uninstall      Remove systemd services and deployed files

Service:
  start          Start the logger service
  stop           Stop the logger service
  restart        Restart the logger service
  status         Show logger service status
  logs           Tail logger service logs

Other:
  update         Copy source files to /etc/pySSM2 (skip dependency install)
  help           Show this help message
EOF
}

cmd_install() {
    require_root

    info "Installing pySSM2..."
    info "  User:            $CURRENT_USER (uid=$CURRENT_UID)"
    info "  Wayland display: $WAYLAND_DISP"
    echo ""

    # -- Dependencies ----------------------------------------------------------
    info "Updating package list..."
    apt-get update

    info "Installing system packages..."
    apt-get install -y \
        python3-serial \
        python3-pygame

    info "Dependencies installed."
    echo ""

    # -- Deploy files ----------------------------------------------------------
    cmd_update

    # -- Systemd services ------------------------------------------------------
    info "Generating systemd service files..."

    sed \
        -e "s/__USER__/$CURRENT_USER/g" \
        -e "s/__UID__/$CURRENT_UID/g" \
        -e "s/__WAYLAND_DISPLAY__/$WAYLAND_DISP/g" \
        "$SCRIPT_DIR/systemd/subaruLogger.service" \
        > /etc/systemd/system/subaruLogger.service

    systemctl daemon-reload

    echo ""
    info "Install complete!"
    info "  User:            $CURRENT_USER"
    info "  XDG_RUNTIME_DIR: /run/user/$CURRENT_UID"
    info "  WAYLAND_DISPLAY: $WAYLAND_DISP"
    echo ""
    info "Start with: sudo ./deploy.sh start"
}

cmd_update() {
    require_root

    info "Deploying files to $INSTALL_DIR..."

    # Create directory structure
    mkdir -p "$INSTALL_DIR/gui"
    mkdir -p "$INSTALL_DIR/assets/fonts"
    mkdir -p "$LOG_DIR"
    mkdir -p "$PYTHON_LOG_DIR"

    # Source files
    cp "$SCRIPT_DIR/src/logger.py"           "$INSTALL_DIR/logger.py"
    cp "$SCRIPT_DIR/src/PySSM2.py"           "$INSTALL_DIR/PySSM2.py"
    cp "$SCRIPT_DIR/src/ecu_capabilities.py" "$INSTALL_DIR/ecu_capabilities.py"

    # Config
    cp "$SCRIPT_DIR/config/config.py"        "$INSTALL_DIR/config.py"

    # GUI
    cp "$SCRIPT_DIR/src/gui/__init__.py"     "$INSTALL_DIR/gui/__init__.py"
    cp "$SCRIPT_DIR/src/gui/app.py"          "$INSTALL_DIR/gui/app.py"
    cp "$SCRIPT_DIR/src/gui/dashboard.py"    "$INSTALL_DIR/gui/dashboard.py"
    cp "$SCRIPT_DIR/src/gui/popup.py"        "$INSTALL_DIR/gui/popup.py"
    cp "$SCRIPT_DIR/src/gui/theme.py"        "$INSTALL_DIR/gui/theme.py"

    # Assets
    cp "$SCRIPT_DIR/assets/fonts/DS-DIGII.TTF" "$INSTALL_DIR/assets/fonts/DS-DIGII.TTF"

    # Permissions
    chmod +x "$INSTALL_DIR/logger.py"
    chown -R "$CURRENT_USER:$CURRENT_USER" "$INSTALL_DIR"
    chmod 755 "$LOG_DIR"

    info "Files deployed."
}

cmd_uninstall() {
    require_root

    info "Uninstalling pySSM2..."

    # Stop and disable services (ignore errors if they don't exist)
    systemctl stop subaruLogger.service 2>/dev/null || true
    systemctl disable subaruLogger.service 2>/dev/null || true

    rm -f /etc/systemd/system/subaruLogger.service
    systemctl daemon-reload

    rm -rf "$INSTALL_DIR"

    info "Uninstall done."
    echo ""
    info "Note: Log files in $LOG_DIR were preserved."
    info "To remove logs: sudo rm -rf $LOG_DIR"
}

# -- Service shortcuts ---------------------------------------------------------

cmd_start()          { sudo systemctl start subaruLogger.service; }
cmd_stop()           { sudo systemctl stop subaruLogger.service; }
cmd_restart()        { sudo systemctl restart subaruLogger.service; }
cmd_status()         { systemctl status subaruLogger.service; }
cmd_logs()           { journalctl -u subaruLogger.service -f; }

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

case "${1:-help}" in
    install)        cmd_install ;;
    uninstall)      cmd_uninstall ;;
    update)         cmd_update ;;
    start)          cmd_start ;;
    stop)           cmd_stop ;;
    restart)        cmd_restart ;;
    status)         cmd_status ;;
    logs)           cmd_logs ;;
    help|--help|-h) cmd_help ;;
    *)
        error "Unknown command: $1"
        echo ""
        cmd_help
        exit 1
        ;;
esac
