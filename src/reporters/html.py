"""HTML output reporter."""

from pathlib import Path
from typing import Any

from jinja2 import Template

from src.core.models import AuditReport, HealthCheckResult


class HTMLReporter:
    """Formats output as HTML."""

    def __init__(self) -> None:
        """Initialize HTML reporter."""
        self.template = self._get_template()

    def export_audit(self, report: AuditReport, output_path: str) -> None:
        """Export audit report to HTML.

        Args:
            report: Audit report
            output_path: Output file path
        """
        html = self.template.render(report=report.dict())

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(html)

    def _get_template(self) -> Template:
        """Get HTML template."""
        template_str = """
<!DOCTYPE html>
<html>
<head>
    <title>LDAP Audit Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .issue { margin: 10px 0; padding: 10px; border-left: 4px solid; }
        .info { border-color: #2196F3; background: #E3F2FD; }
        .warning { border-color: #FF9800; background: #FFF3E0; }
        .critical { border-color: #F44336; background: #FFEBEE; }
        .stats { display: flex; gap: 20px; }
        .stat-box { padding: 15px; background: #f5f5f5; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>LDAP Audit Report</h1>
    <p>Generated: {{ report.timestamp }}</p>
    <p>Score: {{ report.score }}/100</p>

    <h2>Issues</h2>
    {% for issue in report.issues %}
    <div class="issue {{ issue.level }}">
        <strong>{{ issue.title }}</strong>
        <p>{{ issue.description }}</p>
        {% if issue.recommendation %}
        <p><em>Recommendation: {{ issue.recommendation }}</em></p>
        {% endif %}
    </div>
    {% endfor %}

    <h2>Recommendations</h2>
    <ul>
    {% for rec in report.recommendations %}
        <li>{{ rec }}</li>
    {% endfor %}
    </ul>
</body>
</html>
"""
        return Template(template_str)
