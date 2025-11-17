"""Main CLI interface for LDAP Health Monitor."""

import sys
from typing import Optional

import click

from src.audit.consistency import ConsistencyAuditor
from src.audit.groups import GroupAuditor
from src.audit.health import HealthChecker
from src.audit.security import SecurityAuditor
from src.audit.structure import StructureAuditor
from src.audit.users import UserAuditor
from src.core.config import ConfigManager, load_config
from src.core.connector import LDAPConnector
from src.core.models import AuditReport
from src.manage.backup import BackupManager
from src.manage.cleanup import CleanupManager
from src.manage.groups import GroupManager
from src.manage.users import UserManager
from src.monitor.daemon import MonitoringDaemon
from src.monitor.metrics import MetricsCollector
from src.monitor.alerts import AlertManager
from src.reporters.console import ConsoleReporter
from src.reporters.csv import CSVReporter
from src.reporters.html import HTMLReporter
from src.reporters.json import JSONReporter
from src.reporters.prometheus import PrometheusReporter


# Global options
@click.group()
@click.option("--config", "-c", help="Path to configuration file", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """LDAP Health Monitor - Audit, monitor, and manage LDAP servers."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose


# ============================================================================
# CONFIG COMMANDS
# ============================================================================


@cli.group()
def config() -> None:
    """Configuration management commands."""
    pass


@config.command("init")
@click.option("--output", "-o", default="config.yaml", help="Output path for config file")
def config_init(output: str) -> None:
    """Initialize a new configuration file."""
    try:
        manager = ConfigManager()
        manager.init_config(output)
        click.echo(f"✅ Configuration file created: {output}")
        click.echo("Please edit the file to configure your LDAP settings.")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@config.command("validate")
@click.pass_context
def config_validate(ctx: click.Context) -> None:
    """Validate configuration file."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        manager = ConfigManager(ctx.obj.get("config_path"))
        manager._config = config
        manager.validate()
        click.echo("✅ Configuration is valid")
    except Exception as e:
        click.echo(f"❌ Configuration error: {e}", err=True)
        sys.exit(1)


@config.command("show")
@click.pass_context
def config_show(ctx: click.Context) -> None:
    """Show current configuration."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        reporter = JSONReporter()
        import json

        click.echo(json.dumps(config.dict(), indent=2, default=str))
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# AUDIT COMMANDS
# ============================================================================


@cli.group()
def audit() -> None:
    """Audit LDAP directory."""
    pass


@audit.command("health")
@click.option("--output", "-o", help="Output file path")
@click.option("--format", "-f", type=click.Choice(["console", "json", "html"]), default="console")
@click.pass_context
def audit_health(ctx: click.Context, output: Optional[str], format: str) -> None:
    """Check LDAP server health."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        checker = HealthChecker(connector, config)

        health = checker.check_health()

        if format == "console":
            reporter = ConsoleReporter()
            reporter.report_health(health)
        elif format == "json":
            if not output:
                output = "health_report.json"
            reporter = JSONReporter()
            reporter.export_health(health, output)
            click.echo(f"✅ Report saved to {output}")
        elif format == "html":
            click.echo("HTML format not yet implemented for health checks")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@audit.command("users")
@click.option("--inactive", is_flag=True, help="Check for inactive users")
@click.option("--missing-attributes", is_flag=True, help="Check for missing attributes")
@click.option("--output", "-o", help="Output file path")
@click.option("--format", "-f", type=click.Choice(["console", "json", "csv"]), default="console")
@click.pass_context
def audit_users(
    ctx: click.Context, inactive: bool, missing_attributes: bool, output: Optional[str], format: str
) -> None:
    """Audit LDAP users."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        auditor = UserAuditor(connector, config)

        issues = auditor.audit_users(
            check_inactive=inactive, check_attributes=missing_attributes or True
        )

        reporter = ConsoleReporter()
        if issues:
            reporter.print_warning(f"Found {len(issues)} issues")
            for issue in issues:
                click.echo(f"\n{issue.level.value.upper()}: {issue.title}")
                click.echo(f"  {issue.description}")
                if issue.recommendation:
                    click.echo(f"  💡 {issue.recommendation}")
        else:
            reporter.print_success("No issues found")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@audit.command("groups")
@click.option("--empty", is_flag=True, help="Show empty groups")
@click.option("--large", is_flag=True, help="Show large groups")
@click.pass_context
def audit_groups(ctx: click.Context, empty: bool, large: bool) -> None:
    """Audit LDAP groups."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        auditor = GroupAuditor(connector, config)

        issues = auditor.audit_groups()

        reporter = ConsoleReporter()
        if issues:
            reporter.print_warning(f"Found {len(issues)} issues")
            for issue in issues:
                click.echo(f"\n{issue.level.value.upper()}: {issue.title}")
                click.echo(f"  {issue.description}")
                if issue.recommendation:
                    click.echo(f"  💡 {issue.recommendation}")
        else:
            reporter.print_success("No issues found")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@audit.command("all")
@click.option("--output", "-o", help="Output file path")
@click.option("--format", "-f", type=click.Choice(["console", "json", "html"]), default="console")
@click.pass_context
def audit_all(ctx: click.Context, output: Optional[str], format: str) -> None:
    """Run all audit checks."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)

        # Run all audits
        health_checker = HealthChecker(connector, config)
        user_auditor = UserAuditor(connector, config)
        group_auditor = GroupAuditor(connector, config)
        structure_auditor = StructureAuditor(connector, config)
        security_auditor = SecurityAuditor(connector, config)
        consistency_auditor = ConsistencyAuditor(connector, config)

        health = health_checker.check_health()
        all_issues = []
        all_issues.extend(user_auditor.audit_users())
        all_issues.extend(group_auditor.audit_groups())
        all_issues.extend(structure_auditor.audit_structure())
        all_issues.extend(security_auditor.audit_security())
        all_issues.extend(consistency_auditor.audit_consistency())

        # Create audit report
        report = AuditReport(
            health=health,
            issues=all_issues,
            statistics=health.details.get("statistics", {}),
            score=max(0, 100 - len(all_issues) * 5),  # Simple scoring
        )

        # Output report
        if format == "console":
            reporter = ConsoleReporter()
            reporter.report_audit(report)
        elif format == "json":
            if not output:
                output = "audit_report.json"
            reporter = JSONReporter()
            reporter.export_audit(report, output)
            click.echo(f"✅ Report saved to {output}")
        elif format == "html":
            if not output:
                output = "audit_report.html"
            reporter = HTMLReporter()
            reporter.export_audit(report, output)
            click.echo(f"✅ Report saved to {output}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# MONITOR COMMANDS
# ============================================================================


@cli.group()
def monitor() -> None:
    """Monitor LDAP server."""
    pass


@monitor.command("start")
@click.option("--daemon", "-d", is_flag=True, help="Run as daemon")
@click.pass_context
def monitor_start(ctx: click.Context, daemon: bool) -> None:
    """Start monitoring."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        daemon_proc = MonitoringDaemon(connector, config)

        click.echo("Starting LDAP monitoring...")
        daemon_proc.start(daemon=daemon)

    except KeyboardInterrupt:
        click.echo("\nMonitoring stopped")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@monitor.command("metrics")
@click.pass_context
def monitor_metrics(ctx: click.Context) -> None:
    """Show current metrics."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        collector = MetricsCollector(connector, config)

        metrics = collector.collect_all_metrics()

        reporter = ConsoleReporter()
        for metric in metrics:
            click.echo(f"{metric.name}: {metric.value}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@monitor.command("prometheus")
@click.option("--port", "-p", default=9090, help="Port for Prometheus metrics server")
@click.pass_context
def monitor_prometheus(ctx: click.Context, port: int) -> None:
    """Start Prometheus metrics server."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        collector = MetricsCollector(connector, config)

        # Update config with custom port
        config.integrations.prometheus["port"] = port

        reporter = PrometheusReporter(config, collector.registry)
        reporter.start_server()

        click.echo(f"Prometheus metrics available at http://localhost:{port}/metrics")
        click.echo("Press Ctrl+C to stop")

        # Keep running
        import time

        while True:
            collector.collect_all_metrics()
            time.sleep(config.monitoring.interval)

    except KeyboardInterrupt:
        click.echo("\nStopped")
    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# USER MANAGEMENT COMMANDS
# ============================================================================


@cli.group()
def user() -> None:
    """User management commands."""
    pass


@user.command("search")
@click.argument("query")
@click.pass_context
def user_search(ctx: click.Context, query: str) -> None:
    """Search for users."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = UserManager(connector, config)

        users = manager.search_users(query)

        if users:
            click.echo(f"Found {len(users)} users:")
            for user in users:
                click.echo(f"  {user.uid} ({user.cn}) - {user.mail}")
        else:
            click.echo("No users found")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@user.command("show")
@click.argument("dn")
@click.pass_context
def user_show(ctx: click.Context, dn: str) -> None:
    """Show user details."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = UserManager(connector, config)

        user = manager.get_user(dn)

        if user:
            click.echo(f"DN: {user.dn}")
            click.echo(f"UID: {user.uid}")
            click.echo(f"CN: {user.cn}")
            click.echo(f"Email: {user.mail}")
            click.echo("\nAll attributes:")
            for key, value in user.attributes.items():
                click.echo(f"  {key}: {value}")
        else:
            click.echo("User not found")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@user.command("list")
@click.option("--limit", "-n", type=int, help="Limit number of results")
@click.pass_context
def user_list(ctx: click.Context, limit: Optional[int]) -> None:
    """List all users."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = UserManager(connector, config)

        users = manager.list_users(limit=limit)

        click.echo(f"Total users: {len(users)}\n")
        for user in users:
            click.echo(f"{user.uid}: {user.cn} ({user.mail})")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# GROUP MANAGEMENT COMMANDS
# ============================================================================


@cli.group()
def group() -> None:
    """Group management commands."""
    pass


@group.command("search")
@click.argument("query")
@click.pass_context
def group_search(ctx: click.Context, query: str) -> None:
    """Search for groups."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = GroupManager(connector, config)

        groups = manager.search_groups(query)

        if groups:
            click.echo(f"Found {len(groups)} groups:")
            for grp in groups:
                click.echo(f"  {grp.cn} ({len(grp.members)} members)")
        else:
            click.echo("No groups found")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@group.command("show")
@click.argument("dn")
@click.pass_context
def group_show(ctx: click.Context, dn: str) -> None:
    """Show group details."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = GroupManager(connector, config)

        grp = manager.get_group(dn)

        if grp:
            click.echo(f"DN: {grp.dn}")
            click.echo(f"CN: {grp.cn}")
            click.echo(f"Description: {grp.description}")
            click.echo(f"Members: {len(grp.members)}")
        else:
            click.echo("Group not found")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@group.command("list")
@click.pass_context
def group_list(ctx: click.Context) -> None:
    """List all groups."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = GroupManager(connector, config)

        groups = manager.list_groups()

        click.echo(f"Total groups: {len(groups)}\n")
        for grp in groups:
            click.echo(f"{grp.cn}: {len(grp.members)} members")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@group.command("members")
@click.argument("dn")
@click.pass_context
def group_members(ctx: click.Context, dn: str) -> None:
    """Show group members."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = GroupManager(connector, config)

        members = manager.get_members(dn)

        if members:
            click.echo(f"Members ({len(members)}):")
            for member in members:
                click.echo(f"  {member}")
        else:
            click.echo("No members")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# CLEANUP COMMANDS
# ============================================================================


@cli.group()
def cleanup() -> None:
    """Cleanup and maintenance commands."""
    pass


@cleanup.command("dry-run")
@click.pass_context
def cleanup_dry_run(ctx: click.Context) -> None:
    """Show what would be cleaned up."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = CleanupManager(connector, config)

        empty_groups = manager.cleanup_empty_groups(dry_run=True)

        click.echo(f"Would remove {len(empty_groups)} empty groups")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cleanup.command("empty-groups")
@click.option("--confirm", is_flag=True, help="Confirm deletion")
@click.pass_context
def cleanup_empty_groups(ctx: click.Context, confirm: bool) -> None:
    """Remove empty groups."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = CleanupManager(connector, config)

        empty_groups = manager.cleanup_empty_groups(dry_run=not confirm)

        if confirm:
            click.echo(f"✅ Removed {len(empty_groups)} empty groups")
        else:
            click.echo(f"Would remove {len(empty_groups)} empty groups")
            click.echo("Use --confirm to actually delete")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# BACKUP COMMANDS
# ============================================================================


@cli.group()
def backup() -> None:
    """Backup and export commands."""
    pass


@backup.command("full")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--format", "-f", type=click.Choice(["ldif", "json", "yaml"]), default="ldif")
@click.pass_context
def backup_full(ctx: click.Context, output: str, format: str) -> None:
    """Create full LDAP backup."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = BackupManager(connector, config)

        click.echo("Creating backup...")
        path = manager.backup_full(output, format=format)
        click.echo(f"✅ Backup saved to {path}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def export() -> None:
    """Export data commands."""
    pass


@export.command("users")
@click.option("--output", "-o", required=True, help="Output file path")
@click.option("--format", "-f", type=click.Choice(["csv", "json", "yaml"]), default="csv")
@click.pass_context
def export_users(ctx: click.Context, output: str, format: str) -> None:
    """Export users to file."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        manager = BackupManager(connector, config)

        click.echo("Exporting users...")
        path = manager.export_users(output, format=format)
        click.echo(f"✅ Users exported to {path}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# TEST COMMANDS
# ============================================================================


@cli.group()
def test() -> None:
    """Test commands."""
    pass


@test.command("connection")
@click.pass_context
def test_connection(ctx: click.Context) -> None:
    """Test LDAP connection."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)

        click.echo("Testing LDAP connection...")
        success, response_time, error = connector.test_connection()

        if success:
            click.echo(f"✅ Connection successful ({response_time:.0f}ms)")
        else:
            click.echo(f"❌ Connection failed: {error}", err=True)
            sys.exit(1)

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)


# ============================================================================
# UTILITY COMMANDS
# ============================================================================


@cli.command("version")
def version() -> None:
    """Show version information."""
    click.echo("LDAP Health Monitor v1.0.0")


if __name__ == "__main__":
    cli(obj={})
