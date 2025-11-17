# Configuration Guide

## Configuration File

The tool is configured via `config.yaml`. Create one with:

```bash
ldap-monitor config init
```

## Essential Settings

### LDAP Connection

```yaml
ldap:
  server: ldap://ldap.example.com
  port: 389
  use_ssl: true
  use_tls: true
  bind_dn: cn=admin,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com
```

### Schema Customization

Adapt to your LDAP schema:

```yaml
ldap:
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
  user_uid_attribute: uid
  group_member_attribute: member
```

## Environment Variables

Store sensitive data in environment variables:

```bash
export LDAP_PASSWORD="your-password"
export SLACK_WEBHOOK="https://hooks.slack.com/..."
export SMTP_PASSWORD="smtp-password"
```

Reference them in config:

```yaml
bind_password: ${LDAP_PASSWORD}
```

## Configuration Validation

Validate your configuration:

```bash
ldap-monitor config validate
```

View current configuration:

```bash
ldap-monitor config show
```

## Common Configurations

### Active Directory

```yaml
ldap:
  server: ldap://dc.example.com
  port: 389
  user_objectclass: user
  group_objectclass: group
  user_uid_attribute: sAMAccountName
  group_member_attribute: member
```

### OpenLDAP

```yaml
ldap:
  server: ldap://ldap.example.com
  port: 389
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
  user_uid_attribute: uid
  group_member_attribute: member
```

## Advanced Settings

See [config.example.yaml](../config.example.yaml) for all available options.
