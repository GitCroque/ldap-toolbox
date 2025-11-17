# Troubleshooting Guide

## Connection Issues

### Cannot connect to LDAP server

1. Check server address and port
2. Verify firewall settings
3. Test with ldapsearch: `ldapsearch -x -H ldap://server -D "cn=admin,dc=example,dc=com" -W`

### SSL/TLS errors

- Verify SSL is properly configured
- Check certificate validity
- For testing, you can disable SSL verification (not recommended for production)

## Configuration Errors

### Configuration file not found

Specify the path explicitly:

```bash
ldap-monitor --config /path/to/config.yaml audit health
```

### Invalid configuration

Run validation:

```bash
ldap-monitor config validate
```

## Permission Issues

### Access denied

- Verify bind credentials
- Check LDAP ACLs
- Ensure bind DN has read access

### Cannot delete/modify

- Check `management.allow_delete` setting
- Verify write permissions
- Use `--confirm` flag for operations

## Performance Issues

### Slow queries

- Adjust `page_size` in config
- Increase `timeout` value
- Check LDAP server performance

### High memory usage

- Reduce `page_size`
- Limit search scope
- Use filters to narrow results

## Common Error Messages

### "Configuration not loaded"

Run with config file:

```bash
ldap-monitor --config config.yaml <command>
```

### "LDAP bind failed"

Check credentials in .env file or config.yaml

### "Module not found"

Install dependencies:

```bash
pip install -r requirements.txt
```

## Getting Help

- Check logs in `./logs/ldap-monitor.log`
- Enable verbose mode: `ldap-monitor --verbose`
- Report issues: https://github.com/yourusername/ldap-health-monitor/issues
