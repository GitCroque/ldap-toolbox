"""Console output reporter."""

from typing import Any, Dict, List

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from tabulate import tabulate

from src.core.models import AlertLevel, AuditIssue, AuditReport, CheckStatus, HealthCheckResult


class ConsoleReporter:
    """Formats output for console display."""

    def __init__(self) -> None:
        """Initialize console reporter."""
        self.console = Console()

    def report_health(self, health: HealthCheckResult) -> None:
        """Display health check results.

        Args:
            health: Health check result
        """
        # Status emoji
        status_emoji = {
            CheckStatus.HEALTHY: "✅",
            CheckStatus.WARNING: "⚠️",
            CheckStatus.CRITICAL: "❌",
            CheckStatus.UNKNOWN: "❓",
        }

        # Create header
        title = "LDAP Health Check"
        emoji = status_emoji.get(health.status, "")

        content = f"""
Server Status: {emoji} {health.status.value.title()}
Response Time: {health.response_time:.0f}ms

{health.message}
"""

        panel = Panel(content, title=title, border_style="blue")
        self.console.print(panel)

        # Display statistics if available
        if "statistics" in health.details:
            self._display_statistics(health.details["statistics"])

        # Display issues if any
        if "issues" in health.details and health.details["issues"]:
            self.console.print("\n🔍 Issues Found:")
            for issue in health.details["issues"]:
                self._display_issue(issue)

    def report_audit(self, report: AuditReport) -> None:
        """Display audit report.

        Args:
            report: Audit report
        """
        self.console.print(f"\n📊 Audit Report - {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
        self.console.print(f"Score: {report.score}/100\n")

        # Group issues by category
        issues_by_category: Dict[str, List[AuditIssue]] = {}
        for issue in report.issues:
            cat = issue.category
            if cat not in issues_by_category:
                issues_by_category[cat] = []
            issues_by_category[cat].append(issue)

        # Display issues by category
        for category, issues in issues_by_category.items():
            self.console.print(f"\n[bold]{category.title()}[/bold]")
            for issue in issues:
                self._display_issue(issue.dict())

        # Display recommendations
        if report.recommendations:
            self.console.print("\n💡 Recommendations:")
            for rec in report.recommendations:
                self.console.print(f"  • {rec}")

    def _display_statistics(self, stats: Dict[str, Any]) -> None:
        """Display statistics table.

        Args:
            stats: Statistics dictionary
        """
        self.console.print("\n📊 Statistics:")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Object Type")
        table.add_column("Count", justify="right")

        for key, value in stats.items():
            if isinstance(value, (int, float)):
                table.add_row(key.replace("_", " ").title(), str(value))

        self.console.print(table)

    def _display_issue(self, issue: Dict[str, Any]) -> None:
        """Display a single issue.

        Args:
            issue: Issue dictionary
        """
        level_emoji = {
            "info": "ℹ️",
            "warning": "⚠️",
            "critical": "🔴",
        }

        level = issue.get("level", "info")
        emoji = level_emoji.get(level, "")
        title = issue.get("title", "")
        description = issue.get("description", "")

        self.console.print(f"  {emoji} {title}")
        self.console.print(f"     {description}")

        if issue.get("recommendation"):
            self.console.print(f"     💡 {issue['recommendation']}")

    def display_table(
        self, data: List[Dict[str, Any]], headers: List[str], title: Optional[str] = None
    ) -> None:
        """Display data as a table.

        Args:
            data: List of dictionaries to display
            headers: List of column headers
            title: Optional table title
        """
        if title:
            self.console.print(f"\n[bold]{title}[/bold]")

        if not data:
            self.console.print("No data to display")
            return

        table = Table(show_header=True, header_style="bold cyan")

        for header in headers:
            table.add_column(header)

        for row in data:
            table.add_row(*[str(row.get(h, "")) for h in headers])

        self.console.print(table)

    def print_success(self, message: str) -> None:
        """Print success message.

        Args:
            message: Success message
        """
        self.console.print(f"[green]✅ {message}[/green]")

    def print_error(self, message: str) -> None:
        """Print error message.

        Args:
            message: Error message
        """
        self.console.print(f"[red]❌ {message}[/red]")

    def print_warning(self, message: str) -> None:
        """Print warning message.

        Args:
            message: Warning message
        """
        self.console.print(f"[yellow]⚠️  {message}[/yellow]")

    def print_info(self, message: str) -> None:
        """Print info message.

        Args:
            message: Info message
        """
        self.console.print(f"[blue]ℹ️  {message}[/blue]")
