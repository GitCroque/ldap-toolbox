#!/usr/bin/env bash
#
# Setup Automated Tasks Script
# Compatible with macOS (launchd) and Linux (cron)
#
# Usage: ./setup-cron.sh [install|uninstall]
#
# This script sets up automated tasks:
# - Daily audit at 6:00 AM
# - Daily backup at 2:00 AM
# - Weekly cleanup (Sundays at 3:00 AM)
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ACTION="${1:-install}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_PATH="${CONFIG_PATH:-$SCRIPT_DIR/../../config.yaml}"

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    echo -e "${BLUE}Detected: macOS (using launchd)${NC}"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    echo -e "${BLUE}Detected: Linux (using cron)${NC}"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi
echo ""

# macOS launchd setup
install_macos() {
    echo -e "${BLUE}Installing launchd jobs for macOS...${NC}"
    echo ""

    PLIST_DIR="$HOME/Library/LaunchAgents"
    mkdir -p "$PLIST_DIR"

    # Daily Audit (6:00 AM)
    AUDIT_PLIST="$PLIST_DIR/com.ldapmonitor.daily-audit.plist"
    cat > "$AUDIT_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ldapmonitor.daily-audit</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/daily-audit.sh</string>
        <string>$CONFIG_PATH</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>6</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/ldap-monitor-audit.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/ldap-monitor-audit-error.log</string>
</dict>
</plist>
EOF
    launchctl load "$AUDIT_PLIST" 2>/dev/null || true
    echo -e "${GREEN}✓ Daily audit job installed (6:00 AM)${NC}"

    # Daily Backup (2:00 AM)
    BACKUP_PLIST="$PLIST_DIR/com.ldapmonitor.daily-backup.plist"
    cat > "$BACKUP_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ldapmonitor.daily-backup</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/auto-backup.sh</string>
        <string>$CONFIG_PATH</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>2</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/ldap-monitor-backup.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/ldap-monitor-backup-error.log</string>
</dict>
</plist>
EOF
    launchctl load "$BACKUP_PLIST" 2>/dev/null || true
    echo -e "${GREEN}✓ Daily backup job installed (2:00 AM)${NC}"

    # Weekly Cleanup (Sundays at 3:00 AM)
    CLEANUP_PLIST="$PLIST_DIR/com.ldapmonitor.weekly-cleanup.plist"
    cat > "$CLEANUP_PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ldapmonitor.weekly-cleanup</string>
    <key>ProgramArguments</key>
    <array>
        <string>$SCRIPT_DIR/auto-cleanup.sh</string>
        <string>$CONFIG_PATH</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>0</integer>
        <key>Hour</key>
        <integer>3</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$HOME/Library/Logs/ldap-monitor-cleanup.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/Library/Logs/ldap-monitor-cleanup-error.log</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>DRY_RUN</key>
        <string>true</string>
    </dict>
</dict>
</plist>
EOF
    launchctl load "$CLEANUP_PLIST" 2>/dev/null || true
    echo -e "${GREEN}✓ Weekly cleanup job installed (Sundays 3:00 AM, dry-run mode)${NC}"

    echo ""
    echo -e "${BLUE}macOS launchd jobs installed:${NC}"
    echo "  Daily audit:   6:00 AM (every day)"
    echo "  Daily backup:  2:00 AM (every day)"
    echo "  Weekly cleanup: 3:00 AM (Sundays, dry-run)"
    echo ""
    echo "Logs location: $HOME/Library/Logs/ldap-monitor-*.log"
    echo ""
    echo "To view jobs:"
    echo "  launchctl list | grep ldapmonitor"
    echo ""
    echo "To manually run:"
    echo "  launchctl start com.ldapmonitor.daily-audit"
}

# Linux cron setup
install_linux() {
    echo -e "${BLUE}Installing cron jobs for Linux...${NC}"
    echo ""

    # Make scripts executable
    chmod +x "$SCRIPT_DIR"/*.sh

    CRON_FILE="/tmp/ldap-monitor-cron-$$"

    # Export current crontab
    crontab -l > "$CRON_FILE" 2>/dev/null || touch "$CRON_FILE"

    # Remove existing ldap-monitor entries
    grep -v "ldap-monitor" "$CRON_FILE" > "$CRON_FILE.new" || touch "$CRON_FILE.new"
    mv "$CRON_FILE.new" "$CRON_FILE"

    # Add new entries
    cat >> "$CRON_FILE" << EOF

# LDAP Health Monitor - Automated Tasks
# Daily audit at 6:00 AM
0 6 * * * $SCRIPT_DIR/daily-audit.sh "$CONFIG_PATH" >> $HOME/logs/ldap-monitor-audit.log 2>&1

# Daily backup at 2:00 AM
0 2 * * * $SCRIPT_DIR/auto-backup.sh "$CONFIG_PATH" >> $HOME/logs/ldap-monitor-backup.log 2>&1

# Weekly cleanup on Sundays at 3:00 AM (dry-run mode)
0 3 * * 0 DRY_RUN=true $SCRIPT_DIR/auto-cleanup.sh "$CONFIG_PATH" >> $HOME/logs/ldap-monitor-cleanup.log 2>&1
EOF

    # Install new crontab
    crontab "$CRON_FILE"
    rm "$CRON_FILE"

    echo -e "${GREEN}✓ Cron jobs installed${NC}"
    echo ""
    echo -e "${BLUE}Scheduled tasks:${NC}"
    echo "  Daily audit:   6:00 AM (every day)"
    echo "  Daily backup:  2:00 AM (every day)"
    echo "  Weekly cleanup: 3:00 AM (Sundays, dry-run)"
    echo ""
    echo "Logs location: $HOME/logs/ldap-monitor-*.log"
    echo ""
    echo "To view cron jobs:"
    echo "  crontab -l | grep ldap-monitor"
}

# Uninstall macOS
uninstall_macos() {
    echo -e "${BLUE}Uninstalling launchd jobs...${NC}"

    PLIST_DIR="$HOME/Library/LaunchAgents"

    for job in daily-audit daily-backup weekly-cleanup; do
        PLIST="$PLIST_DIR/com.ldapmonitor.$job.plist"
        if [ -f "$PLIST" ]; then
            launchctl unload "$PLIST" 2>/dev/null || true
            rm "$PLIST"
            echo -e "${GREEN}✓ Removed $job job${NC}"
        fi
    done
}

# Uninstall Linux
uninstall_linux() {
    echo -e "${BLUE}Uninstalling cron jobs...${NC}"

    CRON_FILE="/tmp/ldap-monitor-cron-$$"

    # Export current crontab
    crontab -l > "$CRON_FILE" 2>/dev/null || touch "$CRON_FILE"

    # Remove ldap-monitor entries
    grep -v "ldap-monitor" "$CRON_FILE" > "$CRON_FILE.new" || touch "$CRON_FILE.new"
    grep -v "LDAP Health Monitor" "$CRON_FILE.new" > "$CRON_FILE" || touch "$CRON_FILE"

    # Install cleaned crontab
    crontab "$CRON_FILE"
    rm -f "$CRON_FILE" "$CRON_FILE.new"

    echo -e "${GREEN}✓ Cron jobs removed${NC}"
}

# Main
case "$ACTION" in
    install)
        if [ "$OS" = "macos" ]; then
            install_macos
        else
            install_linux
        fi

        echo -e "${YELLOW}Note: Cleanup runs in DRY-RUN mode by default.${NC}"
        echo "To enable actual cleanup, edit the job and set DRY_RUN=false"
        ;;

    uninstall)
        if [ "$OS" = "macos" ]; then
            uninstall_macos
        else
            uninstall_linux
        fi
        echo -e "${GREEN}✓ All automated tasks removed${NC}"
        ;;

    *)
        echo "Setup Automated LDAP Tasks"
        echo ""
        echo "Usage: $0 [install|uninstall]"
        echo ""
        echo "Commands:"
        echo "  install    - Install automated tasks"
        echo "  uninstall  - Remove automated tasks"
        echo ""
        echo "Environment variables:"
        echo "  CONFIG_PATH - Path to config.yaml (default: ../../config.yaml)"
        echo ""
        echo "Scheduled tasks:"
        echo "  Daily audit:   6:00 AM"
        echo "  Daily backup:  2:00 AM"
        echo "  Weekly cleanup: 3:00 AM (Sundays, dry-run)"
        exit 1
        ;;
esac
