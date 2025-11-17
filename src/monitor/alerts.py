"""Alerting module."""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests

from src.core.models import Alert, AlertLevel, Config


class AlertManager:
    """Manages alert notifications."""

    def __init__(self, config: Config) -> None:
        """Initialize alert manager.

        Args:
            config: Configuration object
        """
        self.config = config

    def send_alert(self, alert: Alert) -> bool:
        """Send alert through configured channels.

        Args:
            alert: Alert to send

        Returns:
            True if at least one channel succeeded
        """
        if not self.config.monitoring.alerts.get("enabled", False):
            return False

        # Check if this alert level should be sent
        if not self.config.alerts.levels.get(alert.level.value, True):
            return False

        success = False
        channels = self.config.monitoring.alerts.get("channels", [])

        if "slack" in channels and self.config.alerts.slack.get("enabled", False):
            if self._send_slack(alert):
                success = True

        if "email" in channels and self.config.alerts.email.get("enabled", False):
            if self._send_email(alert):
                success = True

        if "webhook" in channels and self.config.alerts.webhook.get("enabled", False):
            if self._send_webhook(alert):
                success = True

        return success

    def _send_slack(self, alert: Alert) -> bool:
        """Send alert to Slack.

        Args:
            alert: Alert to send

        Returns:
            True if successful
        """
        webhook_url = self.config.alerts.slack.get("webhook_url")
        if not webhook_url:
            return False

        # Build Slack message
        color = {
            AlertLevel.INFO: "#36a64f",
            AlertLevel.WARNING: "#ff9900",
            AlertLevel.CRITICAL: "#ff0000",
        }.get(alert.level, "#808080")

        message = {
            "username": self.config.alerts.slack.get("username", "LDAP Monitor"),
            "icon_emoji": self.config.alerts.slack.get("icon_emoji", ":warning:"),
            "channel": self.config.alerts.slack.get("channel", "#alerts"),
            "attachments": [
                {
                    "color": color,
                    "title": alert.title,
                    "text": alert.message,
                    "footer": "LDAP Health Monitor",
                    "ts": int(alert.timestamp.timestamp()),
                    "fields": [
                        {"title": "Level", "value": alert.level.value.upper(), "short": True},
                        {
                            "title": "Time",
                            "value": alert.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                            "short": True,
                        },
                    ],
                }
            ],
        }

        # Add mention for critical alerts
        if alert.level == AlertLevel.CRITICAL:
            mention = self.config.alerts.slack.get("mention_on_critical", "")
            if mention:
                message["text"] = mention

        try:
            response = requests.post(webhook_url, json=message, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    def _send_email(self, alert: Alert) -> bool:
        """Send alert via email.

        Args:
            alert: Alert to send

        Returns:
            True if successful
        """
        import smtplib
        from email.mime.multipart import MIMEMultipart
        from email.mime.text import MIMEText

        smtp_config = self.config.alerts.email

        try:
            # Build email
            msg = MIMEMultipart()
            msg["From"] = smtp_config.get("from", "ldap-monitor@example.com")
            msg["To"] = ", ".join(smtp_config.get("to", []))
            subject_prefix = smtp_config.get("subject_prefix", "[LDAP Monitor]")
            msg["Subject"] = f"{subject_prefix} {alert.level.value.upper()}: {alert.title}"

            # Email body
            body = f"""
LDAP Health Monitor Alert

Level: {alert.level.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{alert.title}

{alert.message}

Details:
{json.dumps(alert.details, indent=2) if alert.details else 'None'}
"""
            msg.attach(MIMEText(body, "plain"))

            # Send email
            with smtplib.SMTP(
                smtp_config.get("smtp_host"), smtp_config.get("smtp_port", 587)
            ) as server:
                if smtp_config.get("smtp_use_tls", True):
                    server.starttls()
                server.login(smtp_config.get("smtp_user"), smtp_config.get("smtp_password"))
                server.send_message(msg)

            return True
        except Exception:
            return False

    def _send_webhook(self, alert: Alert) -> bool:
        """Send alert to generic webhook.

        Args:
            alert: Alert to send

        Returns:
            True if successful
        """
        webhook_url = self.config.alerts.webhook.get("url")
        if not webhook_url:
            return False

        payload = {
            "level": alert.level.value,
            "title": alert.title,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "details": alert.details,
        }

        try:
            method = self.config.alerts.webhook.get("method", "POST")
            headers = self.config.alerts.webhook.get("headers", {})

            if method.upper() == "POST":
                response = requests.post(webhook_url, json=payload, headers=headers, timeout=10)
            else:
                response = requests.get(webhook_url, params=payload, headers=headers, timeout=10)

            return response.status_code in [200, 201, 202]
        except Exception:
            return False

    def create_alert(
        self, level: AlertLevel, title: str, message: str, details: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create and send an alert.

        Args:
            level: Alert level
            title: Alert title
            message: Alert message
            details: Optional additional details

        Returns:
            Created alert
        """
        alert = Alert(level=level, title=title, message=message, details=details or {})
        self.send_alert(alert)
        return alert
