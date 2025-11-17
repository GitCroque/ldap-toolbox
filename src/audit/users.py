"""User audit module."""

from datetime import datetime, timedelta
from typing import Dict, List, Set

from src.core.connector import LDAPConnector
from src.core.models import AlertLevel, AuditIssue, Config, LDAPUser, ObjectStatus


class UserAuditor:
    """Audits LDAP users for issues and inconsistencies."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize user auditor.

        Args:
            connector: LDAP connector instance
            config: Configuration object
        """
        self.connector = connector
        self.config = config

    def audit_users(
        self, check_inactive: bool = True, check_attributes: bool = True
    ) -> List[AuditIssue]:
        """Perform complete user audit.

        Args:
            check_inactive: Check for inactive accounts
            check_attributes: Check for missing/invalid attributes

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []

        # Get all users
        users = self._get_all_users()

        # Check for various issues
        issues.extend(self._check_disabled_users(users))
        issues.extend(self._check_missing_attributes(users))
        issues.extend(self._check_duplicate_attributes(users))

        if check_inactive:
            issues.extend(self._check_inactive_users(users))

        return issues

    def _get_all_users(self) -> List[LDAPUser]:
        """Retrieve all users from LDAP.

        Returns:
            List of LDAP users
        """
        user_filter = f"(objectClass={self.config.ldap.user_objectclass})"

        entries = self.connector.search(
            search_base=self.config.ldap.users_ou, search_filter=user_filter
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

    def _check_disabled_users(self, users: List[LDAPUser]) -> List[AuditIssue]:
        """Check for disabled user accounts.

        Args:
            users: List of users to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []
        disabled_count = 0

        for user in users:
            # Check userAccountControl or other disable mechanisms
            # This is implementation-specific, adapt for your LDAP
            attrs = user.attributes
            if attrs.get("userAccountControl"):
                uac = int(attrs["userAccountControl"])
                if uac & 0x0002:  # ACCOUNTDISABLE flag
                    disabled_count += 1

        if disabled_count > 0:
            issues.append(
                AuditIssue(
                    level=AlertLevel.INFO,
                    category="users",
                    title=f"{disabled_count} disabled user accounts",
                    description=f"Found {disabled_count} disabled user accounts",
                    recommendation="Review and clean up disabled accounts",
                )
            )

        return issues

    def _check_missing_attributes(self, users: List[LDAPUser]) -> List[AuditIssue]:
        """Check for users missing required attributes.

        Args:
            users: List of users to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []
        required_attrs = self.config.audit.required_user_attributes

        users_with_missing = []

        for user in users:
            missing = []
            for attr in required_attrs:
                if not user.attributes.get(attr):
                    missing.append(attr)

            if missing:
                users_with_missing.append({"dn": user.dn, "missing": missing})

        if users_with_missing:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="users",
                    title=f"{len(users_with_missing)} users missing required attributes",
                    description=f"Found {len(users_with_missing)} users with missing attributes",
                    recommendation="Complete user profiles with required attributes",
                    details={"users": users_with_missing[:10]},  # Show first 10
                )
            )

        return issues

    def _check_duplicate_attributes(self, users: List[LDAPUser]) -> List[AuditIssue]:
        """Check for duplicate values in unique attributes.

        Args:
            users: List of users to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []

        # Check for duplicate emails
        email_map: Dict[str, List[str]] = {}
        for user in users:
            email = user.mail
            if email:
                email = email.lower()
                if email not in email_map:
                    email_map[email] = []
                email_map[email].append(user.dn)

        duplicates = {email: dns for email, dns in email_map.items() if len(dns) > 1}

        if duplicates:
            issues.append(
                AuditIssue(
                    level=AlertLevel.CRITICAL,
                    category="users",
                    title=f"{len(duplicates)} duplicate email addresses",
                    description=f"Found {len(duplicates)} email addresses used by multiple users",
                    recommendation="Ensure email addresses are unique",
                    details={"duplicates": dict(list(duplicates.items())[:5])},
                )
            )

        # Check for duplicate UIDs
        uid_map: Dict[str, List[str]] = {}
        for user in users:
            uid = user.uid
            if uid:
                if uid not in uid_map:
                    uid_map[uid] = []
                uid_map[uid].append(user.dn)

        uid_duplicates = {uid: dns for uid, dns in uid_map.items() if len(dns) > 1}

        if uid_duplicates:
            issues.append(
                AuditIssue(
                    level=AlertLevel.CRITICAL,
                    category="users",
                    title=f"{len(uid_duplicates)} duplicate UIDs",
                    description=f"Found {len(uid_duplicates)} UIDs used by multiple users",
                    recommendation="Ensure UIDs are unique",
                    details={"duplicates": dict(list(uid_duplicates.items())[:5])},
                )
            )

        return issues

    def _check_inactive_users(self, users: List[LDAPUser]) -> List[AuditIssue]:
        """Check for inactive user accounts.

        Args:
            users: List of users to check

        Returns:
            List of issues found
        """
        issues: List[AuditIssue] = []
        inactive_threshold = self.config.audit.thresholds.get("inactive_days", 90)
        cutoff_date = datetime.now() - timedelta(days=inactive_threshold)

        inactive_users = []

        for user in users:
            # Check lastLogon or lastLogonTimestamp (implementation-specific)
            last_logon = user.attributes.get("lastLogon") or user.attributes.get(
                "lastLogonTimestamp"
            )

            if last_logon:
                # Convert LDAP timestamp to datetime if needed
                # This is implementation-specific
                try:
                    if isinstance(last_logon, datetime):
                        if last_logon < cutoff_date:
                            inactive_users.append(user.dn)
                except Exception:
                    pass

        if inactive_users:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="users",
                    title=f"{len(inactive_users)} inactive users",
                    description=f"Found {len(inactive_users)} users inactive for more than {inactive_threshold} days",
                    recommendation="Review and disable or remove inactive accounts",
                    details={"count": len(inactive_users), "sample": inactive_users[:10]},
                )
            )

        return issues

    def get_user_statistics(self) -> Dict[str, int]:
        """Get user statistics.

        Returns:
            Dictionary with user statistics
        """
        users = self._get_all_users()

        stats = {
            "total": len(users),
            "with_email": sum(1 for u in users if u.mail),
            "without_email": sum(1 for u in users if not u.mail),
        }

        return stats
