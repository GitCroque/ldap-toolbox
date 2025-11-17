"""CSV output reporter."""

import csv
from pathlib import Path
from typing import Any, Dict, List


class CSVReporter:
    """Formats output as CSV."""

    def export_data(self, data: List[Dict[str, Any]], output_path: str) -> None:
        """Export data to CSV.

        Args:
            data: List of dictionaries to export
            output_path: Output file path
        """
        if not data:
            return

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Get all unique keys
        fieldnames = set()
        for row in data:
            fieldnames.update(row.keys())

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=sorted(fieldnames))
            writer.writeheader()
            writer.writerows(data)
