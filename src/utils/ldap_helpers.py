"""LDAP helper functions and utilities."""

import re
from typing import Any, Dict, List, Optional, Tuple


def normalize_dn(dn: str) -> str:
    """Normalize a Distinguished Name.

    Args:
        dn: DN to normalize

    Returns:
        Normalized DN (lowercase, trimmed)
    """
    return dn.strip().lower()


def parse_dn(dn: str) -> List[Tuple[str, str]]:
    """Parse a Distinguished Name into components.

    Args:
        dn: DN to parse (e.g., "uid=jdoe,ou=users,dc=example,dc=com")

    Returns:
        List of (attribute, value) tuples
    """
    components = []
    parts = dn.split(',')

    for part in parts:
        if '=' in part:
            attr, value = part.split('=', 1)
            components.append((attr.strip(), value.strip()))

    return components


def get_rdn(dn: str) -> Optional[str]:
    """Get the Relative Distinguished Name (first component).

    Args:
        dn: Full DN

    Returns:
        RDN (e.g., "uid=jdoe") or None
    """
    components = parse_dn(dn)
    if components:
        attr, value = components[0]
        return f"{attr}={value}"
    return None


def get_parent_dn(dn: str) -> Optional[str]:
    """Get the parent DN.

    Args:
        dn: Full DN (e.g., "uid=jdoe,ou=users,dc=example,dc=com")

    Returns:
        Parent DN (e.g., "ou=users,dc=example,dc=com") or None
    """
    parts = dn.split(',', 1)
    if len(parts) > 1:
        return parts[1]
    return None


def build_dn(rdn: str, base_dn: str) -> str:
    """Build a full DN from RDN and base DN.

    Args:
        rdn: Relative DN (e.g., "uid=jdoe")
        base_dn: Base DN (e.g., "ou=users,dc=example,dc=com")

    Returns:
        Full DN
    """
    return f"{rdn},{base_dn}"


def is_child_of(dn: str, parent_dn: str) -> bool:
    """Check if DN is a child of parent DN.

    Args:
        dn: DN to check
        parent_dn: Potential parent DN

    Returns:
        True if dn is under parent_dn
    """
    dn_lower = normalize_dn(dn)
    parent_lower = normalize_dn(parent_dn)
    return dn_lower.endswith(parent_lower) and dn_lower != parent_lower


def escape_filter_value(value: str) -> str:
    """Escape special characters in LDAP filter values.

    Args:
        value: Value to escape

    Returns:
        Escaped value safe for LDAP filters
    """
    # LDAP filter special characters
    replacements = {
        '\\': '\\5c',
        '*': '\\2a',
        '(': '\\28',
        ')': '\\29',
        '\x00': '\\00',
    }

    for char, escaped in replacements.items():
        value = value.replace(char, escaped)

    return value


def build_filter(conditions: Dict[str, Any], operator: str = "&") -> str:
    """Build an LDAP filter from conditions.

    Args:
        conditions: Dictionary of attribute: value pairs
        operator: LDAP operator (&, |, !)

    Returns:
        LDAP filter string

    Example:
        >>> build_filter({"uid": "jdoe", "objectClass": "inetOrgPerson"})
        '(&(uid=jdoe)(objectClass=inetOrgPerson))'
    """
    if not conditions:
        return "(objectClass=*)"

    filters = []
    for attr, value in conditions.items():
        escaped_value = escape_filter_value(str(value))
        filters.append(f"({attr}={escaped_value})")

    if len(filters) == 1:
        return filters[0]

    return f"({operator}{''.join(filters)})"


def extract_attribute_from_dn(dn: str, attribute: str) -> Optional[str]:
    """Extract a specific attribute value from a DN.

    Args:
        dn: Full DN
        attribute: Attribute name to extract (e.g., "ou", "dc")

    Returns:
        Attribute value or None

    Example:
        >>> extract_attribute_from_dn("uid=jdoe,ou=users,dc=example,dc=com", "ou")
        'users'
    """
    components = parse_dn(dn)
    for attr, value in components:
        if attr.lower() == attribute.lower():
            return value
    return None


def format_ldap_timestamp(timestamp: Any) -> Optional[str]:
    """Format LDAP timestamp to human-readable format.

    Args:
        timestamp: LDAP timestamp (various formats)

    Returns:
        Formatted timestamp string or None
    """
    from datetime import datetime

    if timestamp is None:
        return None

    try:
        # Handle different timestamp formats
        if isinstance(timestamp, datetime):
            return timestamp.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(timestamp, str):
            # LDAP Generalized Time: YYYYMMDDHHMMSSsssZ
            if len(timestamp) >= 14:
                dt = datetime.strptime(timestamp[:14], "%Y%m%d%H%M%S")
                return dt.strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(timestamp, int):
            # Windows FILETIME or Unix timestamp
            if timestamp > 10000000000:  # Likely FILETIME
                # Convert Windows FILETIME to Unix timestamp
                unix_ts = (timestamp - 116444736000000000) / 10000000
                dt = datetime.fromtimestamp(unix_ts)
            else:
                dt = datetime.fromtimestamp(timestamp)
            return dt.strftime("%Y-%m-%d %H:%M:%S")

    except Exception:
        pass

    return None


def parse_useraccountcontrol(uac: int) -> Dict[str, bool]:
    """Parse Active Directory userAccountControl flags.

    Args:
        uac: userAccountControl integer value

    Returns:
        Dictionary of flag names and their boolean values
    """
    flags = {
        0x0001: "SCRIPT",
        0x0002: "ACCOUNTDISABLE",
        0x0008: "HOMEDIR_REQUIRED",
        0x0010: "LOCKOUT",
        0x0020: "PASSWD_NOTREQD",
        0x0040: "PASSWD_CANT_CHANGE",
        0x0080: "ENCRYPTED_TEXT_PWD_ALLOWED",
        0x0100: "TEMP_DUPLICATE_ACCOUNT",
        0x0200: "NORMAL_ACCOUNT",
        0x0800: "INTERDOMAIN_TRUST_ACCOUNT",
        0x1000: "WORKSTATION_TRUST_ACCOUNT",
        0x2000: "SERVER_TRUST_ACCOUNT",
        0x10000: "DONT_EXPIRE_PASSWORD",
        0x20000: "MNS_LOGON_ACCOUNT",
        0x40000: "SMARTCARD_REQUIRED",
        0x80000: "TRUSTED_FOR_DELEGATION",
        0x100000: "NOT_DELEGATED",
        0x200000: "USE_DES_KEY_ONLY",
        0x400000: "DONT_REQ_PREAUTH",
        0x800000: "PASSWORD_EXPIRED",
        0x1000000: "TRUSTED_TO_AUTH_FOR_DELEGATION",
    }

    result = {}
    for flag_value, flag_name in flags.items():
        result[flag_name] = bool(uac & flag_value)

    return result


def is_account_disabled(user_attributes: Dict[str, Any]) -> bool:
    """Check if an account is disabled.

    Works for both OpenLDAP and Active Directory.

    Args:
        user_attributes: User attributes dictionary

    Returns:
        True if account is disabled
    """
    # Active Directory
    if "userAccountControl" in user_attributes:
        uac = int(user_attributes["userAccountControl"])
        return bool(uac & 0x0002)  # ACCOUNTDISABLE

    # OpenLDAP or other
    if "accountStatus" in user_attributes:
        status = str(user_attributes["accountStatus"]).lower()
        return status in ["disabled", "inactive"]

    return False


def get_account_ou(dn: str) -> Optional[str]:
    """Extract the immediate OU from a DN.

    Args:
        dn: User or group DN

    Returns:
        OU name or None
    """
    return extract_attribute_from_dn(get_parent_dn(dn) or "", "ou")


def validate_dn(dn: str) -> bool:
    """Validate DN format.

    Args:
        dn: DN to validate

    Returns:
        True if DN is valid
    """
    if not dn or '=' not in dn:
        return False

    # Check for valid attribute types
    valid_attrs = ['cn', 'ou', 'dc', 'uid', 'o', 'c', 'l', 'st', 'street']
    components = parse_dn(dn)

    for attr, value in components:
        if attr.lower() not in valid_attrs:
            # Allow custom attributes but warn
            pass
        if not value:
            return False

    return True


def sanitize_ldap_output(data: Any) -> Any:
    """Sanitize LDAP data for safe output.

    Removes or masks sensitive attributes.

    Args:
        data: LDAP data (dict, list, or str)

    Returns:
        Sanitized data
    """
    sensitive_attrs = ['userPassword', 'password', 'unicodePwd', 'sambaNTPassword']

    if isinstance(data, dict):
        return {
            key: "***REDACTED***" if key in sensitive_attrs else sanitize_ldap_output(value)
            for key, value in data.items()
        }
    elif isinstance(data, list):
        return [sanitize_ldap_output(item) for item in data]
    else:
        return data
