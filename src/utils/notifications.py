"""Notification helpers for various channels."""

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Optional

import requests


class NotificationHelper:
    """Helper class for sending notifications."""

    @staticmethod
    def send_slack(
        webhook_url: str,
        message: str,
        title: Optional[str] = None,
        level: str = "info",
        channel: Optional[str] = None,
        username: str = "LDAP Monitor",
    ) -> bool:
        """Send notification to Slack.

        Args:
            webhook_url: Slack webhook URL
            message: Message text
            title: Optional message title
            level: Message level (info, warning, critical)
            channel: Optional channel override
            username: Bot username

        Returns:
            True if sent successfully
        """
        colors = {"info": "#36a64f", "warning": "#ff9900", "critical": "#ff0000"}

        payload = {
            "username": username,
            "icon_emoji": ":robot_face:",
        }

        if channel:
            payload["channel"] = channel

        if title:
            payload["attachments"] = [
                {
                    "color": colors.get(level, "#808080"),
                    "title": title,
                    "text": message,
                    "footer": "LDAP Health Monitor",
                    "ts": int(__import__("time").time()),
                }
            ]
        else:
            payload["text"] = message

        try:
            response = requests.post(webhook_url, json=payload, timeout=10)
            return response.status_code == 200
        except Exception:
            return False

    @staticmethod
    def send_email(
        smtp_host: str,
        smtp_port: int,
        from_addr: str,
        to_addrs: list,
        subject: str,
        body: str,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        use_tls: bool = True,
    ) -> bool:
        """Send email notification.

        Args:
            smtp_host: SMTP server hostname
            smtp_port: SMTP server port
            from_addr: From email address
            to_addrs: List of recipient addresses
            subject: Email subject
            body: Email body (plain text or HTML)
            smtp_user: SMTP username (if auth required)
            smtp_password: SMTP password (if auth required)
            use_tls: Use TLS encryption

        Returns:
            True if sent successfully
        """
        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = from_addr
            msg["To"] = ", ".join(to_addrs)
            msg["Subject"] = subject

            # Add body
            if "<html>" in body.lower():
                msg.attach(MIMEText(body, "html"))
            else:
                msg.attach(MIMEText(body, "plain"))

            # Send
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                if use_tls:
                    server.starttls()
                if smtp_user and smtp_password:
                    server.login(smtp_user, smtp_password)
                server.send_message(msg)

            return True
        except Exception:
            return False

    @staticmethod
    def send_webhook(
        url: str,
        payload: Dict,
        method: str = "POST",
        headers: Optional[Dict] = None,
    ) -> bool:
        """Send generic webhook notification.

        Args:
            url: Webhook URL
            payload: Data to send
            method: HTTP method (POST, GET, PUT)
            headers: Optional HTTP headers

        Returns:
            True if sent successfully
        """
        if headers is None:
            headers = {"Content-Type": "application/json"}

        try:
            if method.upper() == "POST":
                response = requests.post(url, json=payload, headers=headers, timeout=10)
            elif method.upper() == "PUT":
                response = requests.put(url, json=payload, headers=headers, timeout=10)
            else:
                response = requests.get(url, params=payload, headers=headers, timeout=10)

            return response.status_code in [200, 201, 202]
        except Exception:
            return False

    @staticmethod
    def format_alert_message(
        title: str, message: str, details: Optional[Dict] = None, level: str = "info"
    ) -> str:
        """Format alert message for display.

        Args:
            title: Alert title
            message: Alert message
            details: Optional additional details
            level: Alert level

        Returns:
            Formatted message
        """
        emoji = {"info": "ℹ️", "warning": "⚠️", "critical": "🔴"}

        lines = [f"{emoji.get(level, '')} **{title}**", "", message]

        if details:
            lines.append("")
            lines.append("**Details:**")
            for key, value in details.items():
                lines.append(f"• {key}: {value}")

        return "\n".join(lines)

    @staticmethod
    def format_slack_blocks(
        title: str, message: str, fields: Optional[Dict] = None, level: str = "info"
    ) -> list:
        """Format Slack blocks for rich formatting.

        Args:
            title: Block title
            message: Main message
            fields: Optional fields dictionary
            level: Alert level

        Returns:
            List of Slack blocks
        """
        blocks = [
            {"type": "header", "text": {"type": "plain_text", "text": title}},
            {"type": "section", "text": {"type": "mrkdwn", "text": message}},
        ]

        if fields:
            field_blocks = []
            for key, value in fields.items():
                field_blocks.append({"type": "mrkdwn", "text": f"*{key}:*\n{value}"})

            blocks.append({"type": "section", "fields": field_blocks})

        # Add context
        emoji = {"info": ":information_source:", "warning": ":warning:", "critical": ":rotating_light:"}
        blocks.append(
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"{emoji.get(level, '')} LDAP Health Monitor",
                    }
                ],
            }
        )

        return blocks


def send_test_notifications(config: Dict) -> Dict[str, bool]:
    """Send test notifications to all configured channels.

    Args:
        config: Configuration dictionary with alert settings

    Returns:
        Dictionary with results for each channel
    """
    helper = NotificationHelper()
    results = {}

    # Test Slack
    if config.get("alerts", {}).get("slack", {}).get("enabled"):
        slack_config = config["alerts"]["slack"]
        results["slack"] = helper.send_slack(
            webhook_url=slack_config.get("webhook_url", ""),
            message="Test notification from LDAP Health Monitor",
            title="Test Alert",
            level="info",
            channel=slack_config.get("channel"),
            username=slack_config.get("username", "LDAP Monitor"),
        )

    # Test Email
    if config.get("alerts", {}).get("email", {}).get("enabled"):
        email_config = config["alerts"]["email"]
        results["email"] = helper.send_email(
            smtp_host=email_config.get("smtp_host", ""),
            smtp_port=email_config.get("smtp_port", 587),
            from_addr=email_config.get("from", ""),
            to_addrs=email_config.get("to", []),
            subject="[Test] LDAP Health Monitor",
            body="This is a test notification from LDAP Health Monitor.",
            smtp_user=email_config.get("smtp_user"),
            smtp_password=email_config.get("smtp_password"),
            use_tls=email_config.get("smtp_use_tls", True),
        )

    # Test Webhook
    if config.get("alerts", {}).get("webhook", {}).get("enabled"):
        webhook_config = config["alerts"]["webhook"]
        results["webhook"] = helper.send_webhook(
            url=webhook_config.get("url", ""),
            payload={"test": True, "message": "Test notification from LDAP Health Monitor"},
            method=webhook_config.get("method", "POST"),
            headers=webhook_config.get("headers"),
        )

    return results
