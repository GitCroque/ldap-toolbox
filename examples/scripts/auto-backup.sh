#!/usr/bin/env bash
#
# Automated LDAP Backup Script
# Compatible with macOS and Linux
#
# Usage: ./auto-backup.sh [config_path] [backup_dir]
#
# Features:
# - Full LDAP backup with compression
# - Retention management (keeps last N days)
# - Backup verification
# - Email notification on failure (if configured)
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
BACKUP_DIR="${2:-./backups}"
DATE=$(date +%Y-%m-%d)
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}

# Create backup directory
mkdir -p "$BACKUP_DIR"

echo -e "${BLUE}=== LDAP Automated Backup - $DATE ===${NC}"
echo ""

# Check ldap-monitor
if ! command -v ldap-monitor &> /dev/null; then
    echo -e "${RED}Error: ldap-monitor not found${NC}"
    exit 1
fi

# Backup file paths
BACKUP_FILE="$BACKUP_DIR/ldap-backup-$TIMESTAMP.ldif"
BACKUP_JSON="$BACKUP_DIR/ldap-backup-$TIMESTAMP.json"
LATEST_LINK="$BACKUP_DIR/latest.ldif"

# Step 1: Validate config
echo -e "${BLUE}[1/6] Validating configuration...${NC}"
if ! ldap-monitor --config "$CONFIG_PATH" config validate &> /dev/null; then
    echo -e "${RED}Error: Invalid configuration${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Configuration valid${NC}"
echo ""

# Step 2: Test connection
echo -e "${BLUE}[2/6] Testing LDAP connection...${NC}"
if ! ldap-monitor --config "$CONFIG_PATH" test connection &> /dev/null; then
    echo -e "${RED}Error: Cannot connect to LDAP server${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Connection successful${NC}"
echo ""

# Step 3: Create LDIF backup
echo -e "${BLUE}[3/6] Creating LDIF backup...${NC}"
echo "Output: $BACKUP_FILE"

START_TIME=$(date +%s)

if ldap-monitor --config "$CONFIG_PATH" backup full \
    --output "$BACKUP_FILE" \
    --format ldif; then

    END_TIME=$(date +%s)
    DURATION=$((END_TIME - START_TIME))

    # Get file size (macOS compatible)
    if command -v gdu &> /dev/null; then
        # GNU du (installed via brew coreutils on macOS)
        SIZE=$(gdu -h "$BACKUP_FILE" | cut -f1)
    elif du --version 2>&1 | grep -q GNU; then
        # GNU du on Linux
        SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    else
        # BSD du (macOS default)
        SIZE=$(du -h "$BACKUP_FILE" | awk '{print $1}')
    fi

    echo -e "${GREEN}✓ Backup created: $SIZE in ${DURATION}s${NC}"
else
    echo -e "${RED}Error: Backup failed${NC}"
    exit 1
fi
echo ""

# Step 4: Create JSON backup (for easier parsing)
echo -e "${BLUE}[4/6] Creating JSON backup...${NC}"
if ldap-monitor --config "$CONFIG_PATH" backup full \
    --output "$BACKUP_JSON" \
    --format json &> /dev/null; then
    echo -e "${GREEN}✓ JSON backup created${NC}"
fi
echo ""

# Step 5: Verify backup
echo -e "${BLUE}[5/6] Verifying backup...${NC}"
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    # Count entries in LDIF
    ENTRY_COUNT=$(grep -c "^dn:" "$BACKUP_FILE" || echo "0")
    echo "  Entries backed up: $ENTRY_COUNT"

    if [ "$ENTRY_COUNT" -gt 0 ]; then
        echo -e "${GREEN}✓ Backup verified${NC}"

        # Update latest symlink
        ln -sf "$(basename "$BACKUP_FILE")" "$LATEST_LINK" 2>/dev/null || true
    else
        echo -e "${RED}Error: Backup appears empty${NC}"
        exit 1
    fi
else
    echo -e "${RED}Error: Backup file missing or empty${NC}"
    exit 1
fi
echo ""

# Step 6: Cleanup old backups
echo -e "${BLUE}[6/6] Cleaning old backups (retention: $RETENTION_DAYS days)...${NC}"
if [ -d "$BACKUP_DIR" ]; then
    # Find and delete old backups (macOS compatible)
    OLD_COUNT=$(find "$BACKUP_DIR" -name "ldap-backup-*.ldif" -type f -mtime +$RETENTION_DAYS | wc -l | tr -d ' ')

    if [ "$OLD_COUNT" -gt 0 ]; then
        find "$BACKUP_DIR" -name "ldap-backup-*.ldif" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
        find "$BACKUP_DIR" -name "ldap-backup-*.json" -type f -mtime +$RETENTION_DAYS -delete 2>/dev/null || true
        echo -e "${GREEN}✓ Removed $OLD_COUNT old backup(s)${NC}"
    else
        echo "  No old backups to remove"
    fi
fi
echo ""

# Summary
echo -e "${BLUE}=== Backup Summary ===${NC}"
echo "Date: $DATE $TIMESTAMP"
echo "File: $BACKUP_FILE"
echo "Size: $SIZE"
echo "Entries: $ENTRY_COUNT"
echo -e "Status: ${GREEN}SUCCESS${NC}"
echo ""

echo "To restore from this backup:"
echo "  ldap-monitor restore --file $BACKUP_FILE --dry-run"
echo "  ldap-monitor restore --file $BACKUP_FILE --confirm"
echo ""

echo "Latest backup symlink:"
echo "  $LATEST_LINK -> $(readlink "$LATEST_LINK" 2>/dev/null || echo "N/A")"
