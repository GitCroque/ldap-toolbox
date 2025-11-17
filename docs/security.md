# Security Best Practices

## 🚨 Critical: Protecting LDAP Data

### Never Commit Sensitive Data

**The following files contain sensitive LDAP data and MUST NEVER be committed:**

1. **Configuration files**
   - `config.yaml` - Contains LDAP credentials
   - `.env` - Environment variables with passwords

2. **Backups and exports**
   - `*.ldif` - Full LDAP directory dumps
   - `backups/` - All backup files
   - `exports/` - All export files

3. **Reports and data**
   - `users*.csv` - User listings
   - `groups*.json` - Group data
   - `audit*.html` - Audit reports with sensitive info
   - `*.log` - Logs may contain DN and queries

### Verification Before Commit

**Always check before committing:**

```bash
# Check what files are staged
git status

# View the actual changes
git diff --cached

# If you see any of these, DO NOT COMMIT:
# - config.yaml
# - *.ldif
# - backups/
# - users.csv, groups.json, etc.
```

### .gitignore Protection

The `.gitignore` is configured to protect:

```gitignore
# Configuration
config.yaml
.env

# LDAP Data
*.ldif
*.ldif.gz
backups/
exports/
backup*.json

# Reports
reports/
users*.csv
groups*.json
audit*.html
```

### Credential Management

**DO:**
- ✅ Use environment variables for all passwords
- ✅ Store `.env` file locally only
- ✅ Use different credentials for dev/staging/prod
- ✅ Rotate passwords regularly
- ✅ Use read-only credentials for auditing

**DON'T:**
- ❌ Hardcode passwords in config files
- ❌ Commit `.env` files
- ❌ Share credentials via chat/email
- ❌ Use production credentials in development
- ❌ Give write access unless necessary

### Safe Configuration Sharing

If you need to share configuration (e.g., with a team):

1. **Use the example file:**
   ```bash
   # Share config.example.yaml (safe)
   # NOT config.yaml (contains secrets)
   ```

2. **Document required variables:**
   ```yaml
   # In config.example.yaml
   bind_password: ${LDAP_PASSWORD}  # Set in .env
   ```

3. **Share setup instructions, not credentials**

### Backup Security

**Protecting backups:**

1. **Encrypt backups:**
   ```bash
   # After creating backup
   gpg -c backup.ldif
   rm backup.ldif  # Remove unencrypted version
   ```

2. **Store backups securely:**
   - Use encrypted storage
   - Limit access permissions
   - Don't store in public locations

3. **Clean old backups:**
   ```bash
   # Configure retention in config.yaml
   backup:
     retention_days: 30
   ```

### Access Control

**LDAP credentials should have:**

- **For auditing:** Read-only access
- **For management:** Limited write access
- **For backups:** Read-only, possibly with replication rights
- **Never:** Full admin unless absolutely necessary

### Incident Response

**If credentials are accidentally committed:**

1. **Immediately rotate credentials:**
   ```bash
   # Change LDAP bind password
   # Update .env file
   # Update config.yaml
   ```

2. **Remove from Git history:**
   ```bash
   # Use git-filter-repo or BFG Repo-Cleaner
   # Contact your Git admin if using shared repo
   ```

3. **Audit access logs:**
   - Check LDAP server logs
   - Verify no unauthorized access occurred

### Monitoring and Logging

**Secure your logs:**

1. **Local logs only:**
   ```yaml
   logging:
     file: ./logs/ldap-monitor.log  # Not committed
     console: true
   ```

2. **Sanitize sensitive data:**
   - Don't log passwords
   - Be careful with DN logging
   - Avoid logging full queries with sensitive filters

3. **Log rotation:**
   ```yaml
   logging:
     max_bytes: 10485760  # 10MB
     backup_count: 5
   ```

### Network Security

**Secure LDAP connections:**

1. **Always use TLS/SSL:**
   ```yaml
   ldap:
     use_ssl: true
     use_tls: true
   ```

2. **Verify certificates:**
   ```python
   # In production, enable certificate verification
   # Don't use self-signed certs without proper CA
   ```

3. **Use VPN/bastion for remote access:**
   - Don't expose LDAP directly to internet
   - Use jump hosts or VPN

### Compliance

**For regulated environments:**

- Document all access
- Implement audit trails
- Regular security reviews
- Follow data protection regulations (GDPR, etc.)
- Encrypt data at rest and in transit

### Quick Security Checklist

Before deploying:

- [ ] `.env` file is not committed
- [ ] `config.yaml` is not committed
- [ ] TLS/SSL is enabled
- [ ] Using read-only credentials for audits
- [ ] Backup encryption is configured
- [ ] Log files are in `.gitignore`
- [ ] Alert channels (Slack/email) are configured
- [ ] Access is restricted to authorized users only
- [ ] Regular security audits are scheduled

## Getting Help

If you discover a security vulnerability:

1. **DO NOT** open a public GitHub issue
2. Email security@example.com (replace with your security contact)
3. Provide details privately
4. Wait for acknowledgment before public disclosure

---

**Remember: Security is everyone's responsibility!**
