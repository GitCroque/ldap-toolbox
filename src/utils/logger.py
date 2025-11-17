"""Centralized logging configuration."""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str = "ldap-monitor",
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_bytes: int = 10485760,  # 10MB
    backup_count: int = 5,
    console: bool = True,
    format_string: Optional[str] = None,
) -> logging.Logger:
    """Setup and configure logger.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file (None to disable file logging)
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console: Enable console logging
        format_string: Custom format string

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers
    logger.handlers.clear()

    # Default format
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    formatter = logging.Formatter(format_string)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # File handler with rotation
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.handlers.RotatingFileHandler(
            log_file, maxBytes=max_bytes, backupCount=backup_count
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str = "ldap-monitor") -> logging.Logger:
    """Get logger instance.

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class OperationLogger:
    """Logger for LDAP operations with context."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize operation logger.

        Args:
            logger: Logger instance (creates new one if None)
        """
        self.logger = logger or get_logger()

    def log_connection(self, server: str, port: int, success: bool, error: Optional[str] = None):
        """Log LDAP connection attempt.

        Args:
            server: LDAP server
            port: LDAP port
            success: Connection success
            error: Error message if failed
        """
        if success:
            self.logger.info(f"Connected to LDAP server: {server}:{port}")
        else:
            self.logger.error(f"Failed to connect to {server}:{port}: {error}")

    def log_search(self, base_dn: str, filter: str, result_count: int):
        """Log LDAP search operation.

        Args:
            base_dn: Search base DN
            filter: Search filter
            result_count: Number of results
        """
        self.logger.debug(f"Search: base={base_dn}, filter={filter}, results={result_count}")

    def log_modification(
        self, dn: str, operation: str, success: bool, error: Optional[str] = None
    ):
        """Log LDAP modification.

        Args:
            dn: Target DN
            operation: Operation type (add, modify, delete)
            success: Operation success
            error: Error message if failed
        """
        if success:
            self.logger.info(f"{operation.upper()}: {dn}")
        else:
            self.logger.error(f"Failed {operation} on {dn}: {error}")

    def log_audit(self, audit_type: str, issues_found: int, duration: float):
        """Log audit completion.

        Args:
            audit_type: Type of audit
            issues_found: Number of issues found
            duration: Audit duration in seconds
        """
        self.logger.info(
            f"Audit '{audit_type}' completed: {issues_found} issues found in {duration:.2f}s"
        )

    def log_backup(self, output_file: str, entry_count: int, success: bool):
        """Log backup operation.

        Args:
            output_file: Backup file path
            entry_count: Number of entries backed up
            success: Backup success
        """
        if success:
            self.logger.info(f"Backup completed: {entry_count} entries -> {output_file}")
        else:
            self.logger.error(f"Backup failed: {output_file}")

    def log_alert(self, level: str, title: str, channels: list):
        """Log alert sent.

        Args:
            level: Alert level
            title: Alert title
            channels: Channels alert was sent to
        """
        self.logger.info(f"Alert sent ({level}): {title} -> {', '.join(channels)}")


def configure_from_config(config: dict) -> logging.Logger:
    """Configure logging from configuration dict.

    Args:
        config: Configuration dictionary with logging section

    Returns:
        Configured logger
    """
    logging_config = config.get("logging", {})

    return setup_logger(
        name="ldap-monitor",
        level=logging_config.get("level", "INFO"),
        log_file=logging_config.get("file", "./logs/ldap-monitor.log"),
        max_bytes=logging_config.get("max_bytes", 10485760),
        backup_count=logging_config.get("backup_count", 5),
        console=logging_config.get("console", True),
        format_string=logging_config.get("format"),
    )


# Example usage functions
def example_usage():
    """Example usage of logger."""
    # Basic setup
    logger = setup_logger(
        name="ldap-monitor", level="DEBUG", log_file="./logs/ldap-monitor.log", console=True
    )

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")
    logger.critical("Critical message")

    # With operation context
    op_logger = OperationLogger(logger)
    op_logger.log_connection("ldap.example.com", 389, True)
    op_logger.log_search("dc=example,dc=com", "(objectClass=user)", 150)
    op_logger.log_modification("uid=jdoe,ou=users,dc=example,dc=com", "modify", True)
    op_logger.log_audit("users", 5, 2.34)
    op_logger.log_backup("backup.ldif", 1000, True)
