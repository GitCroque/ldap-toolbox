"""Group audit module."""

from typing import Dict, List, Set

from src.core.connector import LDAPConnector
from src.core.models import AlertLevel, AuditIssue, Config, LDAPGroup


class GroupAuditor:
    """Audits LDAP groups for issues and inconsistencies."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize group auditor.

        Args:
            connector: LDAP connector instance
            config: Configuration object
        """
        self.connector = connector
        self.config = config

    def audit_groups(self) -> List[AuditIssue]:
        """Perform complete group audit.

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []

        # Get all groups
        groups = self._get_all_groups()

        # Check for various issues
        issues.extend(self._check_empty_groups(groups))
        issues.extend(self._check_large_groups(groups))
        issues.extend(self._check_orphaned_members(groups))
        issues.extend(self._check_duplicate_members(groups))

        return issues

    def _get_all_groups(self) -> List[LDAPGroup]:
        """Retrieve all groups from LDAP.

        Returns:
            List of LDAP groups
        """
        group_filter = f"(objectClass={self.config.ldap.group_objectclass})"

        entries = self.connector.search(
            search_base=self.config.ldap.groups_ou, search_filter=group_filter
        )

        groups = []
        for entry in entries:
            attrs = entry.get("attributes", {})
            members = attrs.get(self.config.ldap.group_member_attribute, [])

            # Ensure members is a list
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

    def _check_empty_groups(self, groups: List[LDAPGroup]) -> List[AuditIssue]:
        """Check for empty groups.

        Args:
            groups: List of groups to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []
        empty_groups = [g for g in groups if not g.members]

        max_empty = self.config.audit.thresholds.get("max_empty_groups", 5)

        if len(empty_groups) > max_empty:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="groups",
                    title=f"{len(empty_groups)} empty groups",
                    description=f"Found {len(empty_groups)} groups with no members",
                    recommendation="Remove unused empty groups",
                    details={
                        "count": len(empty_groups),
                        "sample": [g.dn for g in empty_groups[:10]],
                    },
                )
            )

        return issues

    def _check_large_groups(self, groups: List[LDAPGroup]) -> List[AuditIssue]:
        """Check for excessively large groups.

        Args:
            groups: List of groups to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []
        max_size = self.config.audit.thresholds.get("max_group_size", 100)

        large_groups = [g for g in groups if len(g.members) > max_size]

        if large_groups:
            issues.append(
                AuditIssue(
                    level=AlertLevel.INFO,
                    category="groups",
                    title=f"{len(large_groups)} large groups",
                    description=f"Found {len(large_groups)} groups with more than {max_size} members",
                    recommendation="Consider splitting large groups for better management",
                    details={
                        "groups": [
                            {"dn": g.dn, "member_count": len(g.members)}
                            for g in large_groups[:10]
                        ]
                    },
                )
            )

        return issues

    def _check_orphaned_members(self, groups: List[LDAPGroup]) -> List[AuditIssue]:
        """Check for group members that don't exist.

        Args:
            groups: List of groups to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []
        groups_with_orphans = []

        for group in groups:
            orphans = []
            for member_dn in group.members:
                # Check if member exists
                entry = self.connector.get_entry(member_dn, attributes=["dn"])
                if not entry:
                    orphans.append(member_dn)

            if orphans:
                groups_with_orphans.append({"group": group.dn, "orphans": orphans})

        if groups_with_orphans:
            total_orphans = sum(len(g["orphans"]) for g in groups_with_orphans)
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="groups",
                    title=f"{total_orphans} orphaned group members",
                    description=f"Found {total_orphans} group members that don't exist in {len(groups_with_orphans)} groups",
                    recommendation="Remove orphaned member references",
                    details={"groups": groups_with_orphans[:5]},
                )
            )

        return issues

    def _check_duplicate_members(self, groups: List[LDAPGroup]) -> List[AuditIssue]:
        """Check for duplicate members in groups.

        Args:
            groups: List of groups to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []
        groups_with_duplicates = []

        for group in groups:
            seen: Set[str] = set()
            duplicates: List[str] = []

            for member in group.members:
                if member in seen:
                    duplicates.append(member)
                seen.add(member)

            if duplicates:
                groups_with_duplicates.append(
                    {"group": group.dn, "duplicates": list(set(duplicates))}
                )

        if groups_with_duplicates:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="groups",
                    title=f"{len(groups_with_duplicates)} groups with duplicate members",
                    description=f"Found {len(groups_with_duplicates)} groups containing duplicate member entries",
                    recommendation="Remove duplicate member entries",
                    details={"groups": groups_with_duplicates[:5]},
                )
            )

        return issues

    def get_group_statistics(self) -> Dict[str, any]:
        """Get group statistics.

        Returns:
            Dictionary with group statistics
        """
        groups = self._get_all_groups()

        total_members = sum(len(g.members) for g in groups)
        avg_members = total_members / len(groups) if groups else 0

        stats = {
            "total": len(groups),
            "empty": len([g for g in groups if not g.members]),
            "total_members": total_members,
            "average_members": round(avg_members, 2),
        }

        return stats
