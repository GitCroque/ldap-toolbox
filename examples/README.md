# LDAP Health Monitor - Examples

This directory contains ready-to-use scripts, templates, and configurations for automating LDAP operations.

## 📁 Directory Structure

```
examples/
├── scripts/          # Automation scripts (macOS/Linux compatible)
├── templates/        # CSV templates for bulk operations
├── docker-compose.yml  # Docker setup for testing
└── README.md         # This file
```

## 🚀 Scripts

All scripts are **macOS and Linux compatible** and include helpful output with colors and progress indicators.

### Daily Audit Script

**File:** `scripts/daily-audit.sh`

Performs a complete LDAP audit and generates HTML/JSON reports.

```bash
# Run with default config
./scripts/daily-audit.sh

# Run with custom config
./scripts/daily-audit.sh /path/to/config.yaml

# Environment variables
REPORT_DIR=./my-reports ./scripts/daily-audit.sh
```

**Features:**
- ✅ Validates configuration
- ✅ Tests LDAP connection
- ✅ Runs full audit
- ✅ Generates HTML + JSON reports
- ✅ Checks for critical issues
- ✅ Cleans old reports (30-day retention)
- ✅ Colored output with progress
- ✅ Exit codes for automation

**Scheduled execution:**
```bash
# Add to cron (Linux)
0 6 * * * /path/to/daily-audit.sh /path/to/config.yaml

# Or use make setup-cron (installs launchd on macOS)
make setup-cron
```

### Automated Backup Script

**File:** `scripts/auto-backup.sh`

Creates full LDAP backups with compression and retention management.

```bash
# Run with defaults
./scripts/auto-backup.sh

# Custom config and backup directory
./scripts/auto-backup.sh config.yaml /backups/ldap

# Set retention period
BACKUP_RETENTION_DAYS=60 ./scripts/auto-backup.sh
```

**Features:**
- ✅ Creates LDIF + JSON backups
- ✅ Compresses backups
- ✅ Verifies backup integrity
- ✅ Updates 'latest' symlink
- ✅ Automatic retention management
- ✅ Backup size and entry count
- ✅ macOS/Linux compatible

**Output:**
```
=== LDAP Automated Backup - 2025-01-15 ===

[1/6] Validating configuration...
✓ Configuration valid

[2/6] Testing LDAP connection...
✓ Connection successful

[3/6] Creating LDIF backup...
Output: ./backups/ldap-backup-20250115_140530.ldif
✓ Backup created: 2.3M in 8s

[4/6] Creating JSON backup...
✓ JSON backup created

[5/6] Verifying backup...
  Entries backed up: 1523
✓ Backup verified

[6/6] Cleaning old backups (retention: 30 days)...
✓ Removed 3 old backup(s)

=== Backup Summary ===
Date: 2025-01-15 140530
File: ./backups/ldap-backup-20250115_140530.ldif
Size: 2.3M
Entries: 1523
Status: SUCCESS
```

### Automated Cleanup Script

**File:** `scripts/auto-cleanup.sh`

Safely cleans up LDAP directory (empty groups, orphans, etc.).

```bash
# Dry-run mode (default - no changes)
./scripts/auto-cleanup.sh

# Actually perform cleanup
DRY_RUN=false ./scripts/auto-cleanup.sh

# Custom backup directory
BACKUP_DIR=/safe/backups ./scripts/auto-cleanup.sh
```

**Features:**
- ✅ **Dry-run by default** (safe!)
- ✅ Automatic backup before cleanup
- ✅ Cleans empty groups
- ✅ Removes orphaned members
- ✅ Verification after cleanup
- ✅ Detailed reporting

**Safety:**
- Always creates backup before cleanup
- Dry-run mode by default
- Requires explicit confirmation for live mode
- Verifies results after cleanup

### Monitoring Daemon Script

**File:** `scripts/monitor-daemon.sh`

Manages the LDAP monitoring daemon (start/stop/status/logs).

```bash
# Start daemon
./scripts/monitor-daemon.sh start

# Check status
./scripts/monitor-daemon.sh status

# View current metrics
./scripts/monitor-daemon.sh metrics

# Tail logs
./scripts/monitor-daemon.sh logs

# Stop daemon
./scripts/monitor-daemon.sh stop

# Restart
./scripts/monitor-daemon.sh restart
```

**Features:**
- ✅ PID file management
- ✅ Graceful shutdown
- ✅ Status checking
- ✅ Log rotation
- ✅ Process monitoring

### Cron/Launchd Setup Script

**File:** `scripts/setup-cron.sh`

Automatically sets up scheduled tasks on macOS (launchd) or Linux (cron).

```bash
# Install scheduled tasks
./scripts/setup-cron.sh install

# Remove scheduled tasks
./scripts/setup-cron.sh uninstall

# Custom config path
CONFIG_PATH=/path/to/config.yaml ./scripts/setup-cron.sh install
```

**Scheduled tasks:**
- 📅 **Daily audit**: 6:00 AM every day
- 💾 **Daily backup**: 2:00 AM every day
- 🧹 **Weekly cleanup**: 3:00 AM Sundays (dry-run mode)

**macOS (launchd):**
- Jobs installed in `~/Library/LaunchAgents/`
- Logs in `~/Library/Logs/ldap-monitor-*.log`
- View with: `launchctl list | grep ldapmonitor`

**Linux (cron):**
- Added to user's crontab
- Logs in `~/logs/ldap-monitor-*.log`
- View with: `crontab -l | grep ldap-monitor`

## 📋 CSV Templates

Ready-to-use CSV templates for bulk operations.

### Bulk Update Users

**File:** `templates/bulk-update-users.csv`

Update multiple user attributes at once.

```csv
dn,attribute,value
uid=jdoe,ou=users,dc=example,dc=com,department,IT
uid=jdoe,ou=users,dc=example,dc=com,telephoneNumber,+1-555-0100
uid=jsmith,ou=users,dc=example,dc=com,mail,john.smith@example.com
```

**Usage:**
```bash
ldap-monitor bulk set-attribute --from-file templates/bulk-update-users.csv --confirm
```

### Bulk Add Group Members

**File:** `templates/bulk-add-group-members.csv`

Add multiple users to groups.

```csv
group_dn,user_dn
"cn=developers,ou=groups,dc=example,dc=com","uid=jdoe,ou=users,dc=example,dc=com"
"cn=developers,ou=groups,dc=example,dc=com","uid=jsmith,ou=users,dc=example,dc=com"
```

**Usage:**
```bash
ldap-monitor bulk add-to-group --from-file templates/bulk-add-group-members.csv --confirm
```

### Bulk Disable Users

**File:** `templates/bulk-disable-users.csv`

Disable multiple user accounts.

```csv
dn,reason
uid=contractor1,ou=users,dc=example,dc=com,Contract ended
uid=test-user,ou=users,dc=example,dc=com,Test account cleanup
```

**Usage:**
```bash
ldap-monitor bulk disable --from-file templates/bulk-disable-users.csv --confirm
```

### New Users Import

**File:** `templates/new-users-import.csv`

Create multiple users at once.

```csv
uid,cn,sn,givenName,mail,telephoneNumber,department,title
jdoe,John Doe,Doe,John,john.doe@example.com,+1-555-0100,IT,Software Engineer
jsmith,Jane Smith,Smith,Jane,jane.smith@example.com,+1-555-0101,IT,Senior Developer
```

**Usage:**
```bash
ldap-monitor bulk create-users --from-file templates/new-users-import.csv --confirm
```

### Bulk Password Reset

**File:** `templates/bulk-password-reset.csv`

Reset passwords for multiple users.

```csv
dn,must_change
uid=jdoe,ou=users,dc=example,dc=com,true
uid=jsmith,ou=users,dc=example,dc=com,true
```

**Usage:**
```bash
ldap-monitor bulk reset-password --from-file templates/bulk-password-reset.csv --confirm
```

## 🐳 Docker Setup

**File:** `docker-compose.yml`

Complete Docker environment for testing with OpenLDAP, phpLDAPadmin, Prometheus, and Grafana.

```bash
# Start all services
docker-compose up -d

# Access services:
# - LDAP: localhost:389
# - LDAPS: localhost:636
# - phpLDAPadmin: http://localhost:8080
# - Prometheus: http://localhost:9090
# - Grafana: http://localhost:3000

# Stop services
docker-compose down
```

**Services:**
- **OpenLDAP**: Test LDAP server
- **phpLDAPadmin**: Web UI for LDAP
- **Prometheus**: Metrics collection
- **Grafana**: Metrics visualization

## 🔧 Makefile

Quick commands for common operations.

```bash
# Show all available commands
make help

# Installation
make install           # Install package
make install-dev       # Install with dev dependencies
make dev-setup        # Complete dev environment setup

# LDAP Operations
make config-init       # Create config.yaml
make config-validate   # Validate configuration
make test-connection   # Test LDAP connection
make audit            # Full audit (HTML report)
make audit-users      # Audit users only
make audit-groups     # Audit groups only
make backup           # Create LDIF backup
make export-users     # Export users to CSV

# Monitoring
make monitor-start     # Start monitoring daemon
make monitor-stop      # Stop monitoring daemon
make monitor-status    # Show daemon status
make monitor-metrics   # Show current metrics

# Cleanup
make cleanup-dry-run   # Analyze what would be cleaned
make cleanup          # Run cleanup (with confirmation)

# Automation
make setup-cron       # Setup automated tasks
make remove-cron      # Remove automated tasks

# Development
make test             # Run tests
make test-cov         # Run tests with coverage
make lint             # Run linters
make format           # Format code with black
make clean            # Clean up generated files

# Scripts (direct execution)
make run-daily-audit   # Run daily audit script
make run-backup       # Run backup script
make run-cleanup      # Run cleanup script (dry-run)

# Documentation
make docs             # Open README
make wiki             # Open wiki
```

**Examples:**
```bash
# Quick audit with custom config
make audit CONFIG=production.yaml

# Setup development environment
make dev-setup

# Run tests with coverage
make test-cov

# Setup automated tasks
make setup-cron
```

## 📚 Best Practices

### For Production

1. **Always test first:**
   ```bash
   # Test on dev/staging first
   make config-validate
   make test-connection
   make audit-health
   ```

2. **Use dry-run mode:**
   ```bash
   # Check what would happen
   make cleanup-dry-run
   DRY_RUN=true ./scripts/auto-cleanup.sh
   ```

3. **Regular backups:**
   ```bash
   # Setup automated backups
   make setup-cron

   # Or manual
   make backup
   ```

4. **Monitor continuously:**
   ```bash
   # Start monitoring daemon
   make monitor-start

   # Check status
   make monitor-status
   ```

### For Development

1. **Setup environment:**
   ```bash
   make dev-setup
   ```

2. **Run tests before commits:**
   ```bash
   make test
   make lint
   ```

3. **Use Docker for testing:**
   ```bash
   cd examples
   docker-compose up -d
   # Configure ldap-monitor to use localhost:389
   ```

## 🆘 Troubleshooting

### Scripts not executable

```bash
chmod +x examples/scripts/*.sh
```

### macOS: jq not found

```bash
brew install jq
```

### Linux: Dependencies missing

```bash
# Ubuntu/Debian
sudo apt install jq

# RHEL/CentOS
sudo dnf install jq
```

### Cron jobs not running

**macOS:**
```bash
# Check launchd logs
cat ~/Library/Logs/ldap-monitor-audit.log
cat ~/Library/Logs/ldap-monitor-audit-error.log

# List jobs
launchctl list | grep ldapmonitor

# Manually trigger
launchctl start com.ldapmonitor.daily-audit
```

**Linux:**
```bash
# Check cron logs
cat ~/logs/ldap-monitor-audit.log

# Verify cron entries
crontab -l | grep ldap-monitor

# Check cron service
systemctl status cron  # Debian/Ubuntu
systemctl status crond # RHEL/CentOS
```

## 📖 More Information

- [Main README](../README.md)
- [Wiki Documentation](../wiki/Home.md)
- [Configuration Guide](../wiki/configuration/LDAP-Configuration.md)
- [Troubleshooting](../wiki/troubleshooting/FAQ.md)

## 🤝 Contributing

Have a useful script or template? Please contribute!

1. Fork the repository
2. Add your script/template to `examples/`
3. Document it in this README
4. Submit a Pull Request
