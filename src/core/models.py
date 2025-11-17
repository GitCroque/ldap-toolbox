"""Data models for LDAP Health Monitor."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class AlertLevel(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class ObjectStatus(str, Enum):
    """LDAP object status."""

    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"
    INACTIVE = "inactive"
    UNKNOWN = "unknown"


class CheckStatus(str, Enum):
    """Health check status."""

    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


class LDAPConfig(BaseModel):
    """LDAP connection configuration."""

    server: str
    port: int = 389
    use_ssl: bool = True
    use_tls: bool = True
    bind_dn: str
    bind_password: str
    base_dn: str
    timeout: int = 10
    retry_max: int = 3
    retry_delay: int = 2
    users_ou: str
    groups_ou: str
    user_objectclass: str = "inetOrgPerson"
    group_objectclass: str = "groupOfNames"
    user_uid_attribute: str = "uid"
    group_member_attribute: str = "member"
    page_size: int = 1000
    search_scope: str = "SUBTREE"


class AuditConfig(BaseModel):
    """Audit configuration."""

    checks: List[str] = Field(
        default=["health", "users", "groups", "structure", "security", "consistency"]
    )
    thresholds: Dict[str, int] = Field(default_factory=dict)
    required_user_attributes: List[str] = Field(default=["cn", "sn", "mail", "uid"])
    required_group_attributes: List[str] = Field(default=["cn", "member"])
    security: Dict[str, Any] = Field(default_factory=dict)


class MonitoringConfig(BaseModel):
    """Monitoring configuration."""

    enabled: bool = True
    interval: int = 300
    retention_days: int = 90
    metrics: List[str] = Field(
        default=["users_count", "groups_count", "response_time", "auth_failures"]
    )
    alerts: Dict[str, Any] = Field(default_factory=dict)


class AlertsConfig(BaseModel):
    """Alerts configuration."""

    slack: Dict[str, Any] = Field(default_factory=dict)
    email: Dict[str, Any] = Field(default_factory=dict)
    webhook: Dict[str, Any] = Field(default_factory=dict)
    levels: Dict[str, bool] = Field(default={"info": True, "warning": True, "critical": True})


class ManagementConfig(BaseModel):
    """Management operations configuration."""

    allow_delete: bool = False
    allow_bulk_operations: bool = True
    require_confirmation: bool = True
    backup_before_modify: bool = True
    dry_run_by_default: bool = True
    batch_size: int = 100
    batch_delay: int = 1


class BackupConfig(BaseModel):
    """Backup configuration."""

    auto_backup: bool = True
    backup_dir: str = "./backups"
    retention_days: int = 30
    compress: bool = True
    format: str = "ldif"


class ReportsConfig(BaseModel):
    """Reports configuration."""

    output_dir: str = "./reports"
    default_format: str = "html"
    include_graphs: bool = True
    include_recommendations: bool = True


class IntegrationsConfig(BaseModel):
    """Integrations configuration."""

    prometheus: Dict[str, Any] = Field(default_factory=dict)
    n8n: Dict[str, Any] = Field(default_factory=dict)


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "./logs/ldap-monitor.log"
    max_bytes: int = 10485760
    backup_count: int = 5
    console: bool = True


class Config(BaseModel):
    """Main configuration model."""

    ldap: LDAPConfig
    audit: AuditConfig = Field(default_factory=AuditConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    management: ManagementConfig = Field(default_factory=ManagementConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class LDAPUser(BaseModel):
    """LDAP user object."""

    dn: str
    uid: str
    cn: str
    sn: str
    mail: Optional[str] = None
    status: ObjectStatus = ObjectStatus.UNKNOWN
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    last_logon: Optional[datetime] = None
    password_last_set: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class LDAPGroup(BaseModel):
    """LDAP group object."""

    dn: str
    cn: str
    members: List[str] = Field(default_factory=list)
    description: Optional[str] = None
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)


class HealthCheckResult(BaseModel):
    """Health check result."""

    status: CheckStatus
    response_time: float
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)


class AuditIssue(BaseModel):
    """Audit issue found."""

    level: AlertLevel
    category: str
    title: str
    description: str
    affected_dn: Optional[str] = None
    recommendation: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class AuditReport(BaseModel):
    """Complete audit report."""

    timestamp: datetime = Field(default_factory=datetime.now)
    health: Optional[HealthCheckResult] = None
    issues: List[AuditIssue] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    score: int = 100


class Metric(BaseModel):
    """Monitoring metric."""

    name: str
    value: float
    timestamp: datetime = Field(default_factory=datetime.now)
    labels: Dict[str, str] = Field(default_factory=dict)


class Alert(BaseModel):
    """Monitoring alert."""

    level: AlertLevel
    title: str
    message: str
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)
