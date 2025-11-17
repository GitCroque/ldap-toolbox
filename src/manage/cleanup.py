"""Cleanup and maintenance module."""

from typing import List

from src.audit.groups import GroupAuditor
from src.core.connector import LDAPConnector
from src.core.models import Config


class CleanupManager:
    """Manages cleanup and maintenance operations."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize cleanup manager."""
        self.connector = connector
        self.config = config

    def cleanup_empty_groups(self, dry_run: bool = True) -> List[str]:
        """Remove empty groups.

        Args:
            dry_run: If True, only report what would be deleted

        Returns:
            List of affected group DNs
        """
        auditor = GroupAuditor(self.connector, self.config)
        groups = auditor._get_all_groups()

        empty_groups = [g.dn for g in groups if not g.members]

        if not dry_run and not self.config.management.allow_delete:
            raise PermissionError("Deletion is disabled in configuration")

        if not dry_run:
            for group_dn in empty_groups:
                self.connector.delete_entry(group_dn)

        return empty_groups

    def cleanup_orphans(self, dry_run: bool = True) -> int:
        """Remove orphaned group members.

        Args:
            dry_run: If True, only report what would be fixed

        Returns:
            Number of orphans removed
        """
        # Implementation would check and remove orphaned member references
        # This is a placeholder
        return 0
