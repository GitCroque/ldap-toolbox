"""LDAP server health check module."""

import ssl
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from src.core.connector import LDAPConnector
from src.core.models import AuditIssue, CheckStatus, AlertLevel, HealthCheckResult, Config


class HealthChecker:
    """Performs health checks on LDAP server."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize health checker.

        Args:
            connector: LDAP connector instance
            config: Configuration object
        """
        self.connector = connector
        self.config = config

    def check_health(self) -> HealthCheckResult:
        """Perform complete health check.

        Returns:
            Health check result with status and details
        """
        issues: List[AuditIssue] = []
        details: Dict[str, any] = {}

        # Test connection and response time
        success, response_time, error = self.connector.test_connection()

        if not success:
            return HealthCheckResult(
                status=CheckStatus.CRITICAL,
                response_time=response_time,
                message=f"Cannot connect to LDAP server: {error}",
                details={"error": error},
            )

        details["response_time_ms"] = response_time

        # Check response time thresholds
        threshold_critical = self.config.audit.thresholds.get("response_time_critical_ms", 2000)
        threshold_warning = self.config.audit.thresholds.get("response_time_warning_ms", 500)

        status = CheckStatus.HEALTHY
        if response_time > threshold_critical:
            status = CheckStatus.CRITICAL
            issues.append(
                AuditIssue(
                    level=AlertLevel.CRITICAL,
                    category="performance",
                    title="High response time",
                    description=f"Server response time is {response_time:.0f}ms (critical threshold: {threshold_critical}ms)",
                    recommendation="Check server load and network connectivity",
                )
            )
        elif response_time > threshold_warning:
            status = CheckStatus.WARNING
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="performance",
                    title="Elevated response time",
                    description=f"Server response time is {response_time:.0f}ms (warning threshold: {threshold_warning}ms)",
                    recommendation="Monitor server performance",
                )
            )

        # Get server information
        server_info = self.connector.get_server_info()
        details["server_info"] = server_info

        # Check SSL/TLS certificate if applicable
        if self.config.ldap.use_ssl or self.config.ldap.use_tls:
            cert_issues = self._check_certificate()
            issues.extend(cert_issues)
            if cert_issues:
                status = CheckStatus.WARNING

        # Get basic statistics
        stats = self._get_statistics()
        details["statistics"] = stats

        message = "LDAP server is healthy"
        if status == CheckStatus.WARNING:
            message = "LDAP server has warnings"
        elif status == CheckStatus.CRITICAL:
            message = "LDAP server has critical issues"

        details["issues"] = [issue.dict() for issue in issues]

        return HealthCheckResult(
            status=status, response_time=response_time, message=message, details=details
        )

    def _check_certificate(self) -> List[AuditIssue]:
        """Check SSL/TLS certificate validity.

        Returns:
            List of issues found with certificate
        """
        issues: List[AuditIssue] = []

        try:
            import socket

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with socket.create_connection(
                (self.config.ldap.server, self.config.ldap.port), timeout=10
            ) as sock:
                with context.wrap_socket(sock, server_hostname=self.config.ldap.server) as ssock:
                    cert = ssock.getpeercert()

                    if cert:
                        # Check expiration
                        not_after = cert.get("notAfter")
                        if not_after:
                            expiry_date = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
                            days_until_expiry = (expiry_date - datetime.now()).days

                            warning_days = self.config.audit.thresholds.get(
                                "ssl_cert_expiry_warning_days", 30
                            )

                            if days_until_expiry < 0:
                                issues.append(
                                    AuditIssue(
                                        level=AlertLevel.CRITICAL,
                                        category="security",
                                        title="SSL certificate expired",
                                        description=f"Certificate expired {abs(days_until_expiry)} days ago",
                                        recommendation="Renew SSL certificate immediately",
                                    )
                                )
                            elif days_until_expiry < warning_days:
                                issues.append(
                                    AuditIssue(
                                        level=AlertLevel.WARNING,
                                        category="security",
                                        title="SSL certificate expiring soon",
                                        description=f"Certificate expires in {days_until_expiry} days",
                                        recommendation="Plan certificate renewal",
                                    )
                                )

        except Exception as e:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="security",
                    title="Cannot check SSL certificate",
                    description=f"Failed to retrieve certificate: {str(e)}",
                    recommendation="Verify SSL/TLS configuration",
                )
            )

        return issues

    def _get_statistics(self) -> Dict[str, int]:
        """Get basic LDAP statistics.

        Returns:
            Dictionary with object counts
        """
        stats = {}

        try:
            # Count users
            user_filter = f"(objectClass={self.config.ldap.user_objectclass})"
            users = self.connector.search(
                search_base=self.config.ldap.users_ou,
                search_filter=user_filter,
                attributes=["dn"],
            )
            stats["users_total"] = len(users)

            # Count groups
            group_filter = f"(objectClass={self.config.ldap.group_objectclass})"
            groups = self.connector.search(
                search_base=self.config.ldap.groups_ou,
                search_filter=group_filter,
                attributes=["dn"],
            )
            stats["groups_total"] = len(groups)

            # Count OUs
            ous = self.connector.search(
                search_base=self.config.ldap.base_dn,
                search_filter="(objectClass=organizationalUnit)",
                attributes=["dn"],
            )
            stats["ous_total"] = len(ous)

        except Exception as e:
            # If we can't get stats, it's not critical
            stats["error"] = str(e)

        return stats

    def get_recommendations(self, health_result: HealthCheckResult) -> List[str]:
        """Generate recommendations based on health check.

        Args:
            health_result: Health check result

        Returns:
            List of recommendations
        """
        recommendations = []

        if "issues" in health_result.details:
            for issue in health_result.details["issues"]:
                if issue.get("recommendation"):
                    recommendations.append(issue["recommendation"])

        # Add general recommendations
        if health_result.status == CheckStatus.HEALTHY:
            recommendations.append("Consider setting up regular health monitoring")
            recommendations.append("Enable alerting for critical changes")

        return recommendations
