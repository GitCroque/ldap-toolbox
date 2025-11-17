"""User management module."""

from typing import Dict, List, Optional

from src.core.connector import LDAPConnector
from src.core.models import Config, LDAPUser


class UserManager:
    """Manages LDAP users."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize user manager."""
        self.connector = connector
        self.config = config

    def search_users(self, query: str) -> List[LDAPUser]:
        """Search for users.

        Args:
            query: Search query (uid, cn, or mail)

        Returns:
            List of matching users
        """
        search_filter = (
            f"(&(objectClass={self.config.ldap.user_objectclass})"
            f"(|(uid=*{query}*)(cn=*{query}*)(mail=*{query}*)))"
        )

        entries = self.connector.search(
            search_base=self.config.ldap.users_ou, search_filter=search_filter
        )

        users = []
        for entry in entries:
            attrs = entry.get("attributes", {})
            user = LDAPUser(
                dn=entry["dn"],
                uid=attrs.get(self.config.ldap.user_uid_attribute, ""),
                cn=attrs.get("cn", ""),
                sn=attrs.get("sn", ""),
                mail=attrs.get("mail"),
                attributes=attrs,
            )
            users.append(user)

        return users

    def get_user(self, dn: str) -> Optional[LDAPUser]:
        """Get user by DN.

        Args:
            dn: User DN

        Returns:
            User object or None
        """
        entry = self.connector.get_entry(dn)
        if not entry:
            return None

        attrs = entry.get("attributes", {})
        return LDAPUser(
            dn=entry["dn"],
            uid=attrs.get(self.config.ldap.user_uid_attribute, ""),
            cn=attrs.get("cn", ""),
            sn=attrs.get("sn", ""),
            mail=attrs.get("mail"),
            attributes=attrs,
        )

    def list_users(self, limit: Optional[int] = None) -> List[LDAPUser]:
        """List all users.

        Args:
            limit: Optional limit on number of users

        Returns:
            List of users
        """
        search_filter = f"(objectClass={self.config.ldap.user_objectclass})"

        entries = self.connector.search(
            search_base=self.config.ldap.users_ou, search_filter=search_filter
        )

        if limit:
            entries = entries[:limit]

        users = []
        for entry in entries:
            attrs = entry.get("attributes", {})
            user = LDAPUser(
                dn=entry["dn"],
                uid=attrs.get(self.config.ldap.user_uid_attribute, ""),
                cn=attrs.get("cn", ""),
                sn=attrs.get("sn", ""),
                mail=attrs.get("mail"),
                attributes=attrs,
            )
            users.append(user)

        return users

    def set_attribute(self, dn: str, attribute: str, value: str) -> bool:
        """Set user attribute.

        Args:
            dn: User DN
            attribute: Attribute name
            value: New value

        Returns:
            True if successful
        """
        from ldap3 import MODIFY_REPLACE

        changes = {attribute: [(MODIFY_REPLACE, [value])]}
        return self.connector.modify_entry(dn, changes)
