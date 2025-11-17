"""JSON output reporter."""

import json
from pathlib import Path
from typing import Any

from src.core.models import AuditReport, HealthCheckResult


class JSONReporter:
    """Formats output as JSON."""

    def export_health(self, health: HealthCheckResult, output_path: str) -> None:
        """Export health check to JSON.

        Args:
            health: Health check result
            output_path: Output file path
        """
        data = health.dict()
        self._write_json(data, output_path)

    def export_audit(self, report: AuditReport, output_path: str) -> None:
        """Export audit report to JSON.

        Args:
            report: Audit report
            output_path: Output file path
        """
        data = report.dict()
        self._write_json(data, output_path)

    def export_data(self, data: Any, output_path: str) -> None:
        """Export arbitrary data to JSON.

        Args:
            data: Data to export
            output_path: Output file path
        """
        self._write_json(data, output_path)

    def _write_json(self, data: Any, output_path: str) -> None:
        """Write data to JSON file.

        Args:
            data: Data to write
            output_path: Output file path
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
