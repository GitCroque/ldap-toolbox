#!/usr/bin/env bash
#
# Daily LDAP Audit Script
# Compatible with macOS and Linux
#
# Usage: ./daily-audit.sh [config_path]
#
# This script performs a daily audit of your LDAP directory and:
# - Creates a full audit report (HTML + JSON)
# - Checks for critical issues
# - Sends notifications if configured
# - Maintains audit history
#

set -euo pipefail

# Colors for output (macOS compatible)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
CONFIG_PATH="${1:-config.yaml}"
REPORT_DIR="${REPORT_DIR:-./reports/daily}"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Ensure report directory exists
mkdir -p "$REPORT_DIR"

echo -e "${BLUE}=== LDAP Daily Audit - $DATE ===${NC}"
echo ""

# Step 1: Check if ldap-monitor is installed
if ! command -v ldap-monitor &> /dev/null; then
    echo -e "${RED}Error: ldap-monitor not found${NC}"
    echo "Please install: pip install ldap-health-monitor"
    exit 1
fi

# Step 2: Validate configuration
echo -e "${BLUE}[1/5] Validating configuration...${NC}"
if ! ldap-monitor --config "$CONFIG_PATH" config validate &> /dev/null; then
    echo -e "${RED}Error: Invalid configuration${NC}"
    ldap-monitor --config "$CONFIG_PATH" config validate
    exit 1
fi
echo -e "${GREEN}✓ Configuration valid${NC}"
echo ""

# Step 3: Test LDAP connection
echo -e "${BLUE}[2/5] Testing LDAP connection...${NC}"
if ! ldap-monitor --config "$CONFIG_PATH" test connection &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to LDAP server${NC}"
    ldap-monitor --config "$CONFIG_PATH" test connection
    exit 1
fi
echo -e "${GREEN}✓ Connection successful${NC}"
echo ""

# Step 4: Run complete audit
echo -e "${BLUE}[3/5] Running full audit...${NC}"
HTML_REPORT="$REPORT_DIR/audit-$TIMESTAMP.html"
JSON_REPORT="$REPORT_DIR/audit-$TIMESTAMP.json"

if ldap-monitor --config "$CONFIG_PATH" audit all \
    --format html \
    --output "$HTML_REPORT"; then
    echo -e "${GREEN}✓ HTML report: $HTML_REPORT${NC}"
else
    echo -e "${RED}Error: Audit failed${NC}"
    exit 1
fi

# Also save JSON for programmatic access
ldap-monitor --config "$CONFIG_PATH" audit all \
    --format json \
    --output "$JSON_REPORT" &> /dev/null

echo -e "${GREEN}✓ JSON report: $JSON_REPORT${NC}"
echo ""

# Step 5: Check for critical issues
echo -e "${BLUE}[4/5] Checking for critical issues...${NC}"
CRITICAL_COUNT=0

if command -v jq &> /dev/null; then
    CRITICAL_COUNT=$(jq -r '.statistics.critical // 0' "$JSON_REPORT" 2>/dev/null || echo "0")
    WARNING_COUNT=$(jq -r '.statistics.warning // 0' "$JSON_REPORT" 2>/dev/null || echo "0")

    echo "  Critical issues: $CRITICAL_COUNT"
    echo "  Warnings: $WARNING_COUNT"

    if [ "$CRITICAL_COUNT" -gt 0 ]; then
        echo -e "${RED}⚠️  ATTENTION: $CRITICAL_COUNT critical issues found!${NC}"

        # Extract critical issues
        echo ""
        echo "Critical issues:"
        jq -r '.issues[] | select(.level == "critical") | "  - \(.title)"' "$JSON_REPORT" 2>/dev/null || true
    else
        echo -e "${GREEN}✓ No critical issues${NC}"
    fi
else
    echo -e "${YELLOW}Warning: jq not installed, cannot parse JSON${NC}"
    echo "Install with: brew install jq (macOS) or apt install jq (Linux)"
fi
echo ""

# Step 6: Cleanup old reports (keep last 30 days)
echo -e "${BLUE}[5/5] Cleaning old reports...${NC}"
if [ -d "$REPORT_DIR" ]; then
    # macOS compatible find command
    find "$REPORT_DIR" -name "audit-*.html" -type f -mtime +30 -delete 2>/dev/null || true
    find "$REPORT_DIR" -name "audit-*.json" -type f -mtime +30 -delete 2>/dev/null || true
    echo -e "${GREEN}✓ Cleaned reports older than 30 days${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}=== Summary ===${NC}"
echo "Date: $DATE"
echo "Report: $HTML_REPORT"
if [ "$CRITICAL_COUNT" -gt 0 ]; then
    echo -e "Status: ${RED}CRITICAL${NC} ($CRITICAL_COUNT issues)"
    exit 1
elif [ "${WARNING_COUNT:-0}" -gt 0 ]; then
    echo -e "Status: ${YELLOW}WARNING${NC} ($WARNING_COUNT issues)"
else
    echo -e "Status: ${GREEN}OK${NC}"
fi

echo ""
echo "To view the report:"
echo "  open $HTML_REPORT  # macOS"
echo "  xdg-open $HTML_REPORT  # Linux"
