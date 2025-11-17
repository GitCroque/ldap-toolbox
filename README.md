# LDAP Health Monitor

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Open-source CLI tool for auditing, monitoring, and managing LDAP servers. Designed to work with any LDAP server or Active Directory implementation.

## ✨ Features

- **🔍 Comprehensive Auditing**
  - Server health checks
  - User account analysis
  - Group membership validation
  - Directory structure verification
  - Security compliance checks
  - Data consistency validation

- **📊 Continuous Monitoring**
  - Real-time metrics collection
  - Configurable alerting (Slack, Email, Webhooks)
  - Prometheus metrics export
  - Performance tracking
  - Anomaly detection

- **🛠️ Management Operations**
  - User and group management
  - Bulk operations
  - Cleanup and maintenance
  - LDIF/JSON/YAML backup and export
  - Search and query capabilities

- **📈 Reporting**
  - Console output with rich formatting
  - JSON export for automation
  - HTML reports for documentation
  - CSV export for spreadsheets
  - Prometheus metrics for Grafana

## 🚀 Installation

### Using pip

```bash
pip install ldap-health-monitor
```

### Using pipx (recommended)

```bash
pipx install ldap-health-monitor
```

### From source

```bash
git clone https://github.com/yourusername/ldap-health-monitor.git
cd ldap-health-monitor
pip install -e .
```

## 📋 Requirements

- Python 3.10 or higher
- LDAP server access (read-only for auditing, write access for management)
- Configuration file with LDAP credentials

## 🎯 Quick Start

### 1. Initialize Configuration

```bash
ldap-monitor config init
```

This creates a `config.yaml` file. Edit it with your LDAP settings:

```yaml
ldap:
  server: ldap://ldap.example.com
  port: 389
  bind_dn: cn=admin,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com
```

### 2. Set Environment Variables

```bash
cp .env.example .env
# Edit .env with your credentials
export LDAP_PASSWORD="your-password"
```

### 3. Test Connection

```bash
ldap-monitor test connection
```

### 4. Run Health Check

```bash
ldap-monitor audit health
```

## 📖 Usage Examples

### Auditing

```bash
# Check server health
ldap-monitor audit health

# Audit users
ldap-monitor audit users --inactive --missing-attributes

# Audit groups
ldap-monitor audit groups --empty --large

# Run complete audit
ldap-monitor audit all --format html --output report.html
```

### Monitoring

```bash
# Start continuous monitoring
ldap-monitor monitor start

# View current metrics
ldap-monitor monitor metrics

# Start Prometheus metrics server
ldap-monitor monitor prometheus --port 9090
```

### User Management

```bash
# Search for users
ldap-monitor user search "john.doe"

# Show user details
ldap-monitor user show "uid=jdoe,ou=users,dc=example,dc=com"

# List all users
ldap-monitor user list --limit 50
```

### Group Management

```bash
# Search for groups
ldap-monitor group search "developers"

# Show group details
ldap-monitor group show "cn=developers,ou=groups,dc=example,dc=com"

# List group members
ldap-monitor group members "cn=developers,ou=groups,dc=example,dc=com"
```

### Backup and Export

```bash
# Full backup
ldap-monitor backup full --output backup.ldif

# Export users to CSV
ldap-monitor export users --output users.csv --format csv

# Export to JSON
ldap-monitor backup full --output backup.json --format json
```

### Cleanup

```bash
# Dry run (show what would be cleaned)
ldap-monitor cleanup dry-run

# Remove empty groups
ldap-monitor cleanup empty-groups --confirm
```

## ⚙️ Configuration

The tool is fully configurable via `config.yaml`. See [config.example.yaml](config.example.yaml) for all available options.

### Key Configuration Sections

- **ldap**: Connection settings and schema customization
- **audit**: Thresholds and required attributes
- **monitoring**: Metrics and alert configuration
- **alerts**: Slack, email, and webhook settings
- **management**: Safety settings for operations
- **backup**: Backup directory and retention
- **reports**: Output formats and locations

### Environment Variables

Sensitive values can be set via environment variables:

```bash
LDAP_PASSWORD=your-password
SLACK_WEBHOOK=https://hooks.slack.com/...
SMTP_PASSWORD=email-password
```

## 🔒 Security

**⚠️ IMPORTANT: Never commit LDAP data to version control!**

The `.gitignore` is configured to exclude:
- Configuration files (`config.yaml`, `.env`)
- Backups and exports (`*.ldif`, `backups/`, `exports/`)
- Reports and data files (`*.csv`, `*.json` exports)
- Logs with potential sensitive information

**Additional security measures:**
- ✅ Credentials via environment variables only
- ✅ TLS/SSL connections supported
- ✅ All operations are logged locally (not committed)
- ✅ Confirmations required for destructive operations
- ✅ Dry-run mode by default for risky operations
- ✅ Automatic backups before modifications

**Before committing, always verify:**
```bash
git status
# Make sure no .ldif, backup files, or config.yaml are staged
```

## 📊 Integration Examples

### Prometheus & Grafana

```bash
# Start Prometheus metrics endpoint
ldap-monitor monitor prometheus --port 9090

# Add to prometheus.yml
scrape_configs:
  - job_name: 'ldap-monitor'
    static_configs:
      - targets: ['localhost:9090']
```

### Slack Alerts

Configure in `config.yaml`:

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    mention_on_critical: "@channel"
```

### n8n Automation

```yaml
integrations:
  n8n:
    enabled: true
    webhook_url: ${N8N_WEBHOOK}
    events:
      - alert
      - audit_complete
```

## 🧪 Testing

```bash
# Run tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/unit/test_connector.py
```

## 📚 Documentation

**📖 [Documentation Wiki Complète →](wiki/)** - Guides détaillés, exemples et tutoriels

### Démarrage Rapide
- [Installation](docs/installation.md) - Guide d'installation rapide
- [Configuration](docs/configuration.md) - Configuration de base
- [Troubleshooting](docs/troubleshooting.md) - Résolution de problèmes

### Wiki - Documentation Détaillée
- **[Getting Started](wiki/getting-started/Installation.md)** - Installation complète (macOS, Linux, Windows)
- **[Configuration LDAP](wiki/configuration/LDAP-Configuration.md)** - Config détaillée (AD, OpenLDAP, FreeIPA)
- **[Audit Utilisateurs](wiki/features/audit/Users-Audit.md)** - Guide complet avec exemples
- **[Active Directory](wiki/guides/Active-Directory.md)** - Guide spécifique AD avec PowerShell
- **[FAQ](wiki/troubleshooting/FAQ.md)** - Questions fréquentes avec solutions

➡️ **[Explorer le wiki complet →](wiki/Home.md)**

## 🤝 Contributing

Contributions are welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/ldap-health-monitor.git
cd ldap-health-monitor

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 🐛 Bug Reports & Feature Requests

Please use [GitHub Issues](https://github.com/yourusername/ldap-health-monitor/issues) to report bugs or request features.

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [ldap3](https://github.com/cannatag/ldap3)
- CLI powered by [Click](https://click.palletsprojects.com/)
- Beautiful console output with [Rich](https://github.com/Textualize/rich)

## 🌟 Support

If you find this tool useful, please consider:
- ⭐ Starring the repository
- 🐛 Reporting bugs
- 💡 Suggesting new features
- 📖 Improving documentation
- 🤝 Contributing code

---

Made with ❤️ for the LDAP community