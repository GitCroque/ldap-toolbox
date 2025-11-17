"""Monitoring daemon module."""

import time
from datetime import datetime
from typing import Optional

import schedule

from src.core.config import Config
from src.core.connector import LDAPConnector
from src.monitor.alerts import AlertManager
from src.monitor.metrics import MetricsCollector
from src.core.models import AlertLevel


class MonitoringDaemon:
    """Runs continuous monitoring of LDAP server."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize monitoring daemon.

        Args:
            connector: LDAP connector instance
            config: Configuration object
        """
        self.connector = connector
        self.config = config
        self.metrics_collector = MetricsCollector(connector, config)
        self.alert_manager = AlertManager(config)
        self._running = False

    def start(self, daemon: bool = False) -> None:
        """Start monitoring daemon.

        Args:
            daemon: Run as background daemon
        """
        if not self.config.monitoring.enabled:
            print("Monitoring is disabled in configuration")
            return

        print(f"Starting LDAP monitoring (interval: {self.config.monitoring.interval}s)")

        # Schedule periodic checks
        interval = self.config.monitoring.interval
        schedule.every(interval).seconds.do(self._collect_and_check)

        self._running = True

        # Run initial check
        self._collect_and_check()

        # Main loop
        try:
            while self._running:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nStopping monitoring daemon...")
            self._running = False

    def stop(self) -> None:
        """Stop monitoring daemon."""
        self._running = False

    def _collect_and_check(self) -> None:
        """Collect metrics and check for alerts."""
        try:
            # Collect metrics
            metrics = self.metrics_collector.collect_all_metrics()

            # Check thresholds and send alerts
            for metric in metrics:
                self._check_metric_thresholds(metric)

        except Exception as e:
            # Send error alert
            self.alert_manager.create_alert(
                level=AlertLevel.CRITICAL,
                title="Monitoring error",
                message=f"Error during monitoring: {str(e)}",
            )

    def _check_metric_thresholds(self, metric: any) -> None:
        """Check if metric exceeds thresholds.

        Args:
            metric: Metric to check
        """
        if metric.name == "response_time_ms":
            threshold = self.config.monitoring.alerts.get("response_time_threshold", 2000)
            if metric.value > threshold:
                self.alert_manager.create_alert(
                    level=AlertLevel.WARNING,
                    title="High LDAP response time",
                    message=f"LDAP response time is {metric.value:.0f}ms (threshold: {threshold}ms)",
                    details={"response_time": metric.value, "threshold": threshold},
                )

    def get_status(self) -> dict:
        """Get daemon status.

        Returns:
            Status information
        """
        return {
            "running": self._running,
            "interval": self.config.monitoring.interval,
            "enabled_metrics": self.config.monitoring.metrics,
        }
