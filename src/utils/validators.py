"""Validation utilities for LDAP attributes."""

import re
from typing import Optional, Tuple


class AttributeValidator:
    """Validates common LDAP attributes."""

    # Email regex pattern (RFC 5322 simplified)
    EMAIL_PATTERN = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )

    # Phone patterns (international and common formats)
    PHONE_PATTERNS = {
        'international': re.compile(r'^\+?[1-9]\d{1,14}$'),
        'us': re.compile(r'^(\+1)?[-.\s]?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})$'),
        'simple': re.compile(r'^[0-9\s\-\+\(\)\.]{10,20}$'),
    }

    # URL pattern
    URL_PATTERN = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain
        r'localhost|'  # localhost
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # or IP
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$',
        re.IGNORECASE
    )

    # Date patterns
    DATE_PATTERNS = {
        'iso': re.compile(r'^\d{4}-\d{2}-\d{2}$'),  # YYYY-MM-DD
        'ldap': re.compile(r'^\d{14}Z$'),  # YYYYMMDDHHMMSSsssZ
        'us': re.compile(r'^\d{2}/\d{2}/\d{4}$'),  # MM/DD/YYYY
    }

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """Validate email address.

        Args:
            email: Email address to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not email:
            return False, "Email is empty"

        if not isinstance(email, str):
            return False, "Email must be a string"

        email = email.strip()

        if not AttributeValidator.EMAIL_PATTERN.match(email):
            return False, "Invalid email format"

        # Additional checks
        if '..' in email:
            return False, "Email contains consecutive dots"

        if email.startswith('.') or email.endswith('.'):
            return False, "Email starts or ends with a dot"

        local, domain = email.rsplit('@', 1)

        if len(local) > 64:
            return False, "Email local part too long (max 64 characters)"

        if len(domain) > 255:
            return False, "Email domain too long (max 255 characters)"

        return True, None

    @staticmethod
    def validate_phone(phone: str, format: str = 'simple') -> Tuple[bool, Optional[str]]:
        """Validate phone number.

        Args:
            phone: Phone number to validate
            format: Format to validate against ('international', 'us', 'simple')

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not phone:
            return False, "Phone number is empty"

        if not isinstance(phone, str):
            return False, "Phone number must be a string"

        phone = phone.strip()

        pattern = AttributeValidator.PHONE_PATTERNS.get(format)
        if not pattern:
            return False, f"Unknown phone format: {format}"

        if not pattern.match(phone):
            return False, f"Phone number doesn't match {format} format"

        return True, None

    @staticmethod
    def validate_url(url: str) -> Tuple[bool, Optional[str]]:
        """Validate URL.

        Args:
            url: URL to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not url:
            return False, "URL is empty"

        if not isinstance(url, str):
            return False, "URL must be a string"

        url = url.strip()

        if not AttributeValidator.URL_PATTERN.match(url):
            return False, "Invalid URL format"

        if len(url) > 2048:
            return False, "URL too long (max 2048 characters)"

        return True, None

    @staticmethod
    def validate_date(date_str: str, format: str = 'iso') -> Tuple[bool, Optional[str]]:
        """Validate date string.

        Args:
            date_str: Date string to validate
            format: Format to validate against ('iso', 'ldap', 'us')

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not date_str:
            return False, "Date is empty"

        if not isinstance(date_str, str):
            return False, "Date must be a string"

        pattern = AttributeValidator.DATE_PATTERNS.get(format)
        if not pattern:
            return False, f"Unknown date format: {format}"

        if not pattern.match(date_str):
            return False, f"Date doesn't match {format} format"

        # Additional validation for actual date values
        try:
            from datetime import datetime

            if format == 'iso':
                datetime.strptime(date_str, '%Y-%m-%d')
            elif format == 'ldap':
                datetime.strptime(date_str[:14], '%Y%m%d%H%M%S')
            elif format == 'us':
                datetime.strptime(date_str, '%m/%d/%Y')
        except ValueError as e:
            return False, f"Invalid date value: {str(e)}"

        return True, None

    @staticmethod
    def validate_cn(cn: str) -> Tuple[bool, Optional[str]]:
        """Validate Common Name.

        Args:
            cn: Common Name to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not cn:
            return False, "CN is empty"

        if not isinstance(cn, str):
            return False, "CN must be a string"

        cn = cn.strip()

        if len(cn) < 1:
            return False, "CN is too short"

        if len(cn) > 64:
            return False, "CN too long (max 64 characters)"

        # Check for invalid characters
        invalid_chars = ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        for char in invalid_chars:
            if char in cn:
                return False, f"CN contains invalid character: {char}"

        return True, None

    @staticmethod
    def validate_uid(uid: str) -> Tuple[bool, Optional[str]]:
        """Validate User ID.

        Args:
            uid: User ID to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not uid:
            return False, "UID is empty"

        if not isinstance(uid, str):
            return False, "UID must be a string"

        uid = uid.strip()

        # UID should be alphanumeric with dashes, underscores, dots
        if not re.match(r'^[a-zA-Z0-9._-]+$', uid):
            return False, "UID contains invalid characters (only alphanumeric, ., _, - allowed)"

        if len(uid) < 2:
            return False, "UID too short (min 2 characters)"

        if len(uid) > 256:
            return False, "UID too long (max 256 characters)"

        # Should not start with a number
        if uid[0].isdigit():
            return False, "UID should not start with a number"

        return True, None

    @staticmethod
    def validate_dn(dn: str) -> Tuple[bool, Optional[str]]:
        """Validate Distinguished Name.

        Args:
            dn: DN to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not dn:
            return False, "DN is empty"

        if not isinstance(dn, str):
            return False, "DN must be a string"

        if '=' not in dn:
            return False, "DN must contain at least one '=' sign"

        # Check for valid RDN components
        components = dn.split(',')
        for component in components:
            if '=' not in component:
                return False, f"Invalid DN component: {component}"

            attr, value = component.split('=', 1)
            if not attr.strip() or not value.strip():
                return False, f"Empty attribute or value in component: {component}"

        return True, None

    @staticmethod
    def validate_attribute_value(
        attribute: str, value: str, custom_validators: Optional[dict] = None
    ) -> Tuple[bool, Optional[str]]:
        """Validate an attribute value based on attribute type.

        Args:
            attribute: Attribute name
            value: Attribute value
            custom_validators: Optional dictionary of custom validators

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Map of attribute names to validator methods
        validators = {
            'mail': AttributeValidator.validate_email,
            'email': AttributeValidator.validate_email,
            'telephoneNumber': lambda v: AttributeValidator.validate_phone(v, 'simple'),
            'mobile': lambda v: AttributeValidator.validate_phone(v, 'simple'),
            'cn': AttributeValidator.validate_cn,
            'uid': AttributeValidator.validate_uid,
            'sAMAccountName': AttributeValidator.validate_uid,
            'labeledURI': AttributeValidator.validate_url,
        }

        # Add custom validators
        if custom_validators:
            validators.update(custom_validators)

        # Get validator for this attribute
        validator = validators.get(attribute.lower())

        if validator:
            return validator(value)

        # No specific validator, just check it's not empty
        if not value or not str(value).strip():
            return False, f"{attribute} is empty"

        return True, None


def validate_user_attributes(attributes: dict, required_attributes: list) -> dict:
    """Validate all user attributes.

    Args:
        attributes: User attributes dictionary
        required_attributes: List of required attribute names

    Returns:
        Dictionary with validation results
    """
    validator = AttributeValidator()
    results = {
        'valid': True,
        'missing': [],
        'invalid': {},
    }

    # Check required attributes
    for attr in required_attributes:
        if attr not in attributes or not attributes[attr]:
            results['missing'].append(attr)
            results['valid'] = False

    # Validate present attributes
    for attr, value in attributes.items():
        if value:
            is_valid, error = validator.validate_attribute_value(attr, str(value))
            if not is_valid:
                results['invalid'][attr] = error
                results['valid'] = False

    return results


def sanitize_attribute_value(value: str, max_length: Optional[int] = None) -> str:
    """Sanitize an attribute value.

    Args:
        value: Value to sanitize
        max_length: Optional maximum length

    Returns:
        Sanitized value
    """
    if not isinstance(value, str):
        value = str(value)

    # Trim whitespace
    value = value.strip()

    # Remove control characters
    value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')

    # Truncate if needed
    if max_length and len(value) > max_length:
        value = value[:max_length]

    return value
