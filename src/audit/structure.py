"""Structure audit module."""

from typing import Dict, List

from src.core.connector import LDAPConnector
from src.core.models import AlertLevel, AuditIssue, Config


class StructureAuditor:
    """Audits LDAP directory structure."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize structure auditor."""
        self.connector = connector
        self.config = config

    def audit_structure(self) -> List[AuditIssue]:
        """Perform structure audit."""
        issues: List[AuditIssue] = []
        issues.extend(self._check_empty_ous())
        return issues

    def _check_empty_ous(self) -> List[AuditIssue]:
        """Check for empty organizational units."""
        issues: List[AuditIssue] = []

        try:
            ous = self.connector.search(
                search_base=self.config.ldap.base_dn,
                search_filter="(objectClass=organizationalUnit)",
                attributes=["dn"],
            )

            empty_ous = []
            for ou in ous:
                # Check if OU has any children
                children = self.connector.search(
                    search_base=ou["dn"],
                    search_filter="(objectClass=*)",
                    attributes=["dn"],
                )
                if len(children) <= 1:  # Only the OU itself
                    empty_ous.append(ou["dn"])

            if empty_ous:
                issues.append(
                    AuditIssue(
                        level=AlertLevel.INFO,
                        category="structure",
                        title=f"{len(empty_ous)} empty organizational units",
                        description=f"Found {len(empty_ous)} OUs with no children",
                        recommendation="Consider removing unused OUs",
                        details={"ous": empty_ous[:10]},
                    )
                )
        except Exception as e:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="structure",
                    title="Structure audit error",
                    description=f"Error during structure audit: {str(e)}",
                )
            )

        return issues
