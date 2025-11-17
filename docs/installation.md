# Installation Guide

## Prerequisites

- Python 3.10 or higher
- pip or pipx
- Access to an LDAP server

## Installation Methods

### Using pip (Recommended for development)

```bash
pip install ldap-health-monitor
```

### Using pipx (Recommended for users)

pipx installs the tool in an isolated environment:

```bash
pipx install ldap-health-monitor
```

### From Source

For development or customization:

```bash
git clone https://github.com/yourusername/ldap-health-monitor.git
cd ldap-health-monitor
pip install -e .
```

## Post-Installation

Verify the installation:

```bash
ldap-monitor --help
ldap-monitor version
```

## Next Steps

1. Create a configuration file: `ldap-monitor config init`
2. Edit `config.yaml` with your LDAP settings
3. Test the connection: `ldap-monitor test connection`
4. Run your first audit: `ldap-monitor audit health`

## Troubleshooting

### ImportError: No module named 'ldap3'

Install dependencies:

```bash
pip install -r requirements.txt
```

### Permission denied errors

Use virtual environment or pipx to avoid system-wide installation issues.

### macOS specific notes

On macOS, you may need to install OpenSSL:

```bash
brew install openssl
```
