#!/usr/bin/env bash
#
# LDAP Monitoring Daemon Script
# Compatible with macOS and Linux
#
# Usage: ./monitor-daemon.sh [start|stop|status|restart] [config_path]
#
# This script manages the LDAP monitoring daemon:
# - Starts monitoring in background
# - Collects metrics continuously
# - Sends alerts when thresholds are exceeded
# - Manages PID file for process control
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
ACTION="${1:-status}"
CONFIG_PATH="${2:-config.yaml}"
PID_FILE="${PID_FILE:-./logs/ldap-monitor.pid}"
LOG_FILE="${LOG_FILE:-./logs/ldap-monitor-daemon.log}"

# Ensure log directory exists
mkdir -p "$(dirname "$PID_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

# Functions
start_daemon() {
    echo -e "${BLUE}Starting LDAP monitoring daemon...${NC}"

    # Check if already running
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${YELLOW}Daemon already running (PID: $PID)${NC}"
            return 1
        else
            echo -e "${YELLOW}Removing stale PID file${NC}"
            rm -f "$PID_FILE"
        fi
    fi

    # Validate config
    if ! ldap-monitor --config "$CONFIG_PATH" config validate &> /dev/null; then
        echo -e "${RED}Error: Invalid configuration${NC}"
        return 1
    fi

    # Start daemon in background
    nohup ldap-monitor --config "$CONFIG_PATH" monitor start --daemon \
        >> "$LOG_FILE" 2>&1 &

    PID=$!
    echo "$PID" > "$PID_FILE"

    # Wait a moment and check if it's running
    sleep 2
    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Daemon started (PID: $PID)${NC}"
        echo "  Config: $CONFIG_PATH"
        echo "  Log: $LOG_FILE"
        return 0
    else
        echo -e "${RED}Error: Daemon failed to start${NC}"
        echo "Check log: $LOG_FILE"
        rm -f "$PID_FILE"
        return 1
    fi
}

stop_daemon() {
    echo -e "${BLUE}Stopping LDAP monitoring daemon...${NC}"

    if [ ! -f "$PID_FILE" ]; then
        echo -e "${YELLOW}Daemon not running (no PID file)${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo -e "${YELLOW}Daemon not running (stale PID)${NC}"
        rm -f "$PID_FILE"
        return 1
    fi

    # Try graceful shutdown first
    echo "Sending TERM signal to PID $PID..."
    kill -TERM "$PID" 2>/dev/null || true

    # Wait up to 10 seconds for graceful shutdown
    for i in {1..10}; do
        if ! ps -p "$PID" > /dev/null 2>&1; then
            echo -e "${GREEN}✓ Daemon stopped gracefully${NC}"
            rm -f "$PID_FILE"
            return 0
        fi
        sleep 1
    done

    # Force kill if still running
    echo -e "${YELLOW}Forcing daemon shutdown...${NC}"
    kill -KILL "$PID" 2>/dev/null || true
    rm -f "$PID_FILE"
    echo -e "${GREEN}✓ Daemon stopped (forced)${NC}"
    return 0
}

status_daemon() {
    echo -e "${BLUE}LDAP Monitoring Daemon Status${NC}"
    echo ""

    if [ ! -f "$PID_FILE" ]; then
        echo -e "Status: ${RED}Not running${NC}"
        return 1
    fi

    PID=$(cat "$PID_FILE")

    if ps -p "$PID" > /dev/null 2>&1; then
        echo -e "Status: ${GREEN}Running${NC}"
        echo "PID: $PID"

        # Show process info (macOS/Linux compatible)
        if ps -p "$PID" -o pid,ppid,user,%cpu,%mem,etime,command 2>/dev/null; then
            :
        else
            ps -p "$PID" 2>/dev/null || true
        fi

        echo ""
        echo "Configuration: $CONFIG_PATH"
        echo "Log file: $LOG_FILE"

        # Show last few log entries
        if [ -f "$LOG_FILE" ]; then
            echo ""
            echo "Recent log entries:"
            tail -n 5 "$LOG_FILE" 2>/dev/null || echo "  (log file empty)"
        fi

        return 0
    else
        echo -e "Status: ${RED}Not running${NC} (stale PID: $PID)"
        rm -f "$PID_FILE"
        return 1
    fi
}

restart_daemon() {
    echo -e "${BLUE}Restarting LDAP monitoring daemon...${NC}"
    echo ""

    stop_daemon || true
    sleep 2
    start_daemon
}

show_metrics() {
    echo -e "${BLUE}Current LDAP Metrics${NC}"
    echo ""

    if ! command -v ldap-monitor &> /dev/null; then
        echo -e "${RED}Error: ldap-monitor not found${NC}"
        return 1
    fi

    ldap-monitor --config "$CONFIG_PATH" monitor metrics
}

# Main
case "$ACTION" in
    start)
        start_daemon
        ;;
    stop)
        stop_daemon
        ;;
    status)
        status_daemon
        ;;
    restart)
        restart_daemon
        ;;
    metrics)
        show_metrics
        ;;
    logs)
        if [ -f "$LOG_FILE" ]; then
            tail -f "$LOG_FILE"
        else
            echo -e "${RED}Log file not found: $LOG_FILE${NC}"
            exit 1
        fi
        ;;
    *)
        echo "LDAP Monitoring Daemon Control"
        echo ""
        echo "Usage: $0 [command] [config_path]"
        echo ""
        echo "Commands:"
        echo "  start     - Start monitoring daemon"
        echo "  stop      - Stop monitoring daemon"
        echo "  restart   - Restart monitoring daemon"
        echo "  status    - Show daemon status"
        echo "  metrics   - Show current metrics"
        echo "  logs      - Tail daemon logs"
        echo ""
        echo "Examples:"
        echo "  $0 start config.yaml"
        echo "  $0 status"
        echo "  $0 logs"
        echo ""
        echo "Environment variables:"
        echo "  PID_FILE  - Path to PID file (default: ./logs/ldap-monitor.pid)"
        echo "  LOG_FILE  - Path to log file (default: ./logs/ldap-monitor-daemon.log)"
        exit 1
        ;;
esac
