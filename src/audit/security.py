"""Security audit module."""

from typing import List

from src.core.connector import LDAPConnector
from src.core.models import AlertLevel, AuditIssue, Config


class SecurityAuditor:
    """Audits LDAP security settings."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize security auditor."""
        self.connector = connector
        self.config = config

    def audit_security(self) -> List[AuditIssue]:
        """Perform security audit."""
        issues: List[AuditIssue] = []

        if self.config.audit.security.get("check_privileged_accounts", True):
            issues.extend(self._check_privileged_accounts())

        return issues

    def _check_privileged_accounts(self) -> List[AuditIssue]:
        """Check privileged accounts."""
        issues: List[AuditIssue] = []

        try:
            privileged_groups = self.config.audit.security.get("privileged_groups", [])

            for group_dn in privileged_groups:
                group = self.connector.get_entry(group_dn)
                if group:
                    member_attr = self.config.ldap.group_member_attribute
                    members = group["attributes"].get(member_attr, [])
                    if not isinstance(members, list):
                        members = [members] if members else []

                    if members:
                        issues.append(
                            AuditIssue(
                                level=AlertLevel.INFO,
                                category="security",
                                title=f"Privileged group has {len(members)} members",
                                description=f"Group {group_dn} has {len(members)} members",
                                recommendation="Regularly review privileged group membership",
                                details={"group": group_dn, "member_count": len(members)},
                            )
                        )
        except Exception as e:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="security",
                    title="Security audit error",
                    description=f"Error during security audit: {str(e)}",
                )
            )

        return issues
