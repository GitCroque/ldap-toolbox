"""Backup and export module."""

import gzip
import json
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import yaml

from src.core.connector import LDAPConnector
from src.core.models import Config


class BackupManager:
    """Manages LDAP backups and exports."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialize backup manager."""
        self.connector = connector
        self.config = config
        self.backup_dir = Path(self.config.backup.backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup_full(self, output_path: Optional[str] = None, format: str = "ldif") -> str:
        """Create full LDAP backup.

        Args:
            output_path: Optional custom output path
            format: Backup format (ldif, json, yaml)

        Returns:
            Path to backup file
        """
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"ldap_backup_{timestamp}.{format}"
            if self.config.backup.compress:
                filename += ".gz"
            output_path = str(self.backup_dir / filename)

        # Get all entries
        entries = self.connector.search(
            search_base=self.config.ldap.base_dn, search_filter="(objectClass=*)"
        )

        # Export based on format
        if format == "json":
            data = json.dumps(entries, indent=2, default=str)
        elif format == "yaml":
            data = yaml.dump(entries, default_flow_style=False)
        else:  # ldif
            data = self._export_ldif(entries)

        # Write to file
        if self.config.backup.compress:
            with gzip.open(output_path, "wt", encoding="utf-8") as f:
                f.write(data)
        else:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(data)

        return output_path

    def _export_ldif(self, entries: List[dict]) -> str:
        """Export entries to LDIF format.

        Args:
            entries: List of LDAP entries

        Returns:
            LDIF formatted string
        """
        lines = []
        for entry in entries:
            lines.append(f"dn: {entry['dn']}")
            for attr, value in entry.get("attributes", {}).items():
                if isinstance(value, list):
                    for v in value:
                        lines.append(f"{attr}: {v}")
                else:
                    lines.append(f"{attr}: {value}")
            lines.append("")  # Empty line between entries

        return "\n".join(lines)

    def export_users(self, output_path: str, format: str = "csv") -> str:
        """Export users to file.

        Args:
            output_path: Output file path
            format: Export format (csv, json, yaml)

        Returns:
            Path to export file
        """
        user_filter = f"(objectClass={self.config.ldap.user_objectclass})"
        users = self.connector.search(
            search_base=self.config.ldap.users_ou, search_filter=user_filter
        )

        if format == "csv":
            import csv

            with open(output_path, "w", newline="", encoding="utf-8") as f:
                if users:
                    # Get all unique attribute names
                    attrs = set()
                    for user in users:
                        attrs.update(user.get("attributes", {}).keys())

                    writer = csv.DictWriter(f, fieldnames=["dn"] + sorted(attrs))
                    writer.writeheader()

                    for user in users:
                        row = {"dn": user["dn"]}
                        row.update(user.get("attributes", {}))
                        writer.writerow(row)
        elif format == "json":
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(users, f, indent=2, default=str)
        else:  # yaml
            with open(output_path, "w", encoding="utf-8") as f:
                yaml.dump(users, f, default_flow_style=False)

        return output_path
