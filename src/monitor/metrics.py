"""Metrics collection module."""

import time
from datetime import datetime
from typing import Dict, List, Optional

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

from src.core.connector import LDAPConnector
from src.core.models import Config, Metric


class MetricsCollector:
    """Collects and manages LDAP metrics."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize metrics collector.

        Args:
            connector: LDAP connector instance
            config: Configuration object
        """
        self.connector = connector
        self.config = config
        self.registry = CollectorRegistry()
        self._init_prometheus_metrics()

    def _init_prometheus_metrics(self) -> None:
        """Initialize Prometheus metrics."""
        # Gauges for counts
        self.users_total = Gauge(
            "ldap_users_total",
            "Total number of LDAP users",
            ["status"],
            registry=self.registry,
        )

        self.groups_total = Gauge(
            "ldap_groups_total", "Total number of LDAP groups", registry=self.registry
        )

        self.response_time = Histogram(
            "ldap_response_time_seconds",
            "LDAP query response time",
            registry=self.registry,
        )

        # Counters
        self.auth_failures = Counter(
            "ldap_auth_failures_total", "Total authentication failures", registry=self.registry
        )

        self.connections_active = Gauge(
            "ldap_connections_active", "Active LDAP connections", registry=self.registry
        )

    def collect_all_metrics(self) -> List[Metric]:
        """Collect all configured metrics.

        Returns:
            List of collected metrics
        """
        metrics: List[Metric] = []
        timestamp = datetime.now()

        # Collect each enabled metric
        if "users_count" in self.config.monitoring.metrics:
            user_count = self._collect_user_count()
            metrics.append(
                Metric(name="users_total", value=user_count, timestamp=timestamp)
            )
            self.users_total.labels(status="total").set(user_count)

        if "groups_count" in self.config.monitoring.metrics:
            group_count = self._collect_group_count()
            metrics.append(
                Metric(name="groups_total", value=group_count, timestamp=timestamp)
            )
            self.groups_total.set(group_count)

        if "response_time" in self.config.monitoring.metrics:
            response_time = self._collect_response_time()
            metrics.append(
                Metric(
                    name="response_time_ms", value=response_time, timestamp=timestamp
                )
            )
            self.response_time.observe(response_time / 1000.0)

        return metrics

    def _collect_user_count(self) -> int:
        """Collect user count metric."""
        try:
            user_filter = f"(objectClass={self.config.ldap.user_objectclass})"
            users = self.connector.search(
                search_base=self.config.ldap.users_ou,
                search_filter=user_filter,
                attributes=["dn"],
            )
            return len(users)
        except Exception:
            return 0

    def _collect_group_count(self) -> int:
        """Collect group count metric."""
        try:
            group_filter = f"(objectClass={self.config.ldap.group_objectclass})"
            groups = self.connector.search(
                search_base=self.config.ldap.groups_ou,
                search_filter=group_filter,
                attributes=["dn"],
            )
            return len(groups)
        except Exception:
            return 0

    def _collect_response_time(self) -> float:
        """Collect response time metric."""
        success, response_time, _ = self.connector.test_connection()
        return response_time if success else 0.0

    def get_metrics_summary(self) -> Dict[str, any]:
        """Get summary of current metrics.

        Returns:
            Dictionary with current metric values
        """
        metrics = self.collect_all_metrics()
        return {metric.name: metric.value for metric in metrics}
