"""Group management module."""

from typing import List, Optional

from src.core.connector import LDAPConnector
from src.core.models import Config, LDAPGroup


class GroupManager:
    """Manages LDAP groups."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize group manager."""
        self.connector = connector
        self.config = config

    def search_groups(self, query: str) -> List[LDAPGroup]:
        """Search for groups.

        Args:
            query: Search query (cn or description)

        Returns:
            List of matching groups
        """
        search_filter = (
            f"(&(objectClass={self.config.ldap.group_objectclass})"
            f"(|(cn=*{query}*)(description=*{query}*)))"
        )

        entries = self.connector.search(
            search_base=self.config.ldap.groups_ou, search_filter=search_filter
        )

        groups = []
        for entry in entries:
            attrs = entry.get("attributes", {})
            members = attrs.get(self.config.ldap.group_member_attribute, [])
            if not isinstance(members, list):
                members = [members] if members else []

            group = LDAPGroup(
                dn=entry["dn"],
                cn=attrs.get("cn", ""),
                members=members,
                description=attrs.get("description"),
                attributes=attrs,
            )
            groups.append(group)

        return groups

    def get_group(self, dn: str) -> Optional[LDAPGroup]:
        """Get group by DN.

        Args:
            dn: Group DN

        Returns:
            Group object or None
        """
        entry = self.connector.get_entry(dn)
        if not entry:
            return None

        attrs = entry.get("attributes", {})
        members = attrs.get(self.config.ldap.group_member_attribute, [])
        if not isinstance(members, list):
            members = [members] if members else []

        return LDAPGroup(
            dn=entry["dn"],
            cn=attrs.get("cn", ""),
            members=members,
            description=attrs.get("description"),
            attributes=attrs,
        )

    def list_groups(self) -> List[LDAPGroup]:
        """List all groups.

        Returns:
            List of groups
        """
        search_filter = f"(objectClass={self.config.ldap.group_objectclass})"

        entries = self.connector.search(
            search_base=self.config.ldap.groups_ou, search_filter=search_filter
        )

        groups = []
        for entry in entries:
            attrs = entry.get("attributes", {})
            members = attrs.get(self.config.ldap.group_member_attribute, [])
            if not isinstance(members, list):
                members = [members] if members else []

            group = LDAPGroup(
                dn=entry["dn"],
                cn=attrs.get("cn", ""),
                members=members,
                description=attrs.get("description"),
                attributes=attrs,
            )
            groups.append(group)

        return groups

    def get_members(self, group_dn: str) -> List[str]:
        """Get group members.

        Args:
            group_dn: Group DN

        Returns:
            List of member DNs
        """
        group = self.get_group(group_dn)
        return group.members if group else []
