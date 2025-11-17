#!/usr/bin/env bash
#
# Automated LDAP Cleanup Script
# Compatible with macOS and Linux
#
# Usage: ./auto-cleanup.sh [config_path]
#
# This script safely cleans up your LDAP directory:
# - Empty groups
# - Orphaned group members
# - Inactive accounts (optional)
# - Always creates backup before cleanup
# - Dry-run mode by default
#

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Configuration
CONFIG_PATH="${1:-config.yaml}"
DRY_RUN="${DRY_RUN:-true}"
BACKUP_DIR="${BACKUP_DIR:-./backups/cleanup}"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}=== LDAP Automated Cleanup - $DATE ===${NC}"
echo ""

if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}⚠️  DRY-RUN MODE - No changes will be made${NC}"
    echo "To actually perform cleanup, run with: DRY_RUN=false ./auto-cleanup.sh"
    echo ""
fi

# Check ldap-monitor
if ! command -v ldap-monitor &> /dev/null; then
    echo -e "${RED}Error: ldap-monitor not found${NC}"
    exit 1
fi

# Step 1: Validate config
echo -e "${BLUE}[1/5] Validating configuration...${NC}"
if ! ldap-monitor --config "$CONFIG_PATH" config validate &> /dev/null; then
    echo -e "${RED}Error: Invalid configuration${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Configuration valid${NC}"
echo ""

# Step 2: Backup before cleanup (only if not dry-run)
if [ "$DRY_RUN" != "true" ]; then
    echo -e "${BLUE}[2/5] Creating safety backup...${NC}"
    BACKUP_FILE="$BACKUP_DIR/pre-cleanup-$TIMESTAMP.ldif"

    if ldap-monitor --config "$CONFIG_PATH" backup full \
        --output "$BACKUP_FILE" &> /dev/null; then
        echo -e "${GREEN}✓ Backup created: $BACKUP_FILE${NC}"
    else
        echo -e "${RED}Error: Backup failed - aborting cleanup${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}[2/5] Skipping backup (dry-run mode)${NC}"
fi
echo ""

# Step 3: Analyze what needs cleanup
echo -e "${BLUE}[3/5] Analyzing directory...${NC}"

# Create temporary file for results
REPORT_FILE=$(mktemp)
trap "rm -f $REPORT_FILE" EXIT

ldap-monitor --config "$CONFIG_PATH" cleanup dry-run > "$REPORT_FILE" 2>&1 || true

# Parse results
EMPTY_GROUPS=$(grep -c "empty group" "$REPORT_FILE" || echo "0")
ORPHANS=$(grep -c "orphan" "$REPORT_FILE" || echo "0")

echo "  Empty groups found: $EMPTY_GROUPS"
echo "  Orphaned members found: $ORPHANS"
echo ""

if [ "$EMPTY_GROUPS" -eq 0 ] && [ "$ORPHANS" -eq 0 ]; then
    echo -e "${GREEN}✓ Nothing to clean up!${NC}"
    exit 0
fi

# Step 4: Perform cleanup
echo -e "${BLUE}[4/5] Performing cleanup...${NC}"

CONFIRM_FLAG=""
if [ "$DRY_RUN" != "true" ]; then
    CONFIRM_FLAG="--confirm"
fi

# Clean empty groups
if [ "$EMPTY_GROUPS" -gt 0 ]; then
    echo "Cleaning empty groups..."
    if ldap-monitor --config "$CONFIG_PATH" cleanup empty-groups $CONFIRM_FLAG 2>&1; then
        echo -e "${GREEN}✓ Empty groups cleaned${NC}"
    else
        echo -e "${YELLOW}⚠️  Some empty groups could not be cleaned${NC}"
    fi
fi

# Clean orphaned members
if [ "$ORPHANS" -gt 0 ]; then
    echo "Cleaning orphaned members..."
    if ldap-monitor --config "$CONFIG_PATH" cleanup orphans $CONFIRM_FLAG 2>&1; then
        echo -e "${GREEN}✓ Orphaned members cleaned${NC}"
    else
        echo -e "${YELLOW}⚠️  Some orphaned members could not be cleaned${NC}"
    fi
fi
echo ""

# Step 5: Verify cleanup
if [ "$DRY_RUN" != "true" ]; then
    echo -e "${BLUE}[5/5] Verifying cleanup...${NC}"

    # Re-run dry-run to check what's left
    VERIFY_FILE=$(mktemp)
    trap "rm -f $REPORT_FILE $VERIFY_FILE" EXIT

    ldap-monitor --config "$CONFIG_PATH" cleanup dry-run > "$VERIFY_FILE" 2>&1 || true

    REMAINING_EMPTY=$(grep -c "empty group" "$VERIFY_FILE" || echo "0")
    REMAINING_ORPHANS=$(grep -c "orphan" "$VERIFY_FILE" || echo "0")

    echo "  Remaining empty groups: $REMAINING_EMPTY"
    echo "  Remaining orphaned members: $REMAINING_ORPHANS"

    if [ "$REMAINING_EMPTY" -eq 0 ] && [ "$REMAINING_ORPHANS" -eq 0 ]; then
        echo -e "${GREEN}✓ Cleanup successful!${NC}"
    else
        echo -e "${YELLOW}⚠️  Some items remain (may require manual intervention)${NC}"
    fi
else
    echo -e "${BLUE}[5/5] Skipping verification (dry-run mode)${NC}"
fi
echo ""

# Summary
echo -e "${BLUE}=== Cleanup Summary ===${NC}"
echo "Date: $DATE"
if [ "$DRY_RUN" = "true" ]; then
    echo -e "Mode: ${YELLOW}DRY-RUN${NC}"
else
    echo -e "Mode: ${GREEN}LIVE${NC}"
    echo "Backup: $BACKUP_FILE"
fi
echo ""
echo "Items found:"
echo "  Empty groups: $EMPTY_GROUPS"
echo "  Orphaned members: $ORPHANS"
echo ""

if [ "$DRY_RUN" = "true" ]; then
    echo -e "${YELLOW}To perform actual cleanup:${NC}"
    echo "  DRY_RUN=false ./auto-cleanup.sh"
else
    if [ "$REMAINING_EMPTY" -eq 0 ] && [ "$REMAINING_ORPHANS" -eq 0 ]; then
        echo -e "Status: ${GREEN}COMPLETE${NC}"
    else
        echo -e "Status: ${YELLOW}PARTIAL${NC}"
        echo "Some items could not be cleaned automatically."
        echo "Please review manually or check permissions."
    fi
fi
