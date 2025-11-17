# Modèles de Données (Data Models)

## Introduction

Le LDAP Health Monitor utilise **Pydantic** pour tous ses modèles de données. Pydantic offre:
- Validation automatique des données
- Conversion de types
- Sérialisation/Désérialisation JSON
- Documentation auto-générée
- Support complet des type hints Python

## Architecture des Modèles

### Hiérarchie des Modèles

```
BaseModel (Pydantic)
│
├── Configuration Models (Configuration de l'application)
│   ├── LDAPConfig
│   ├── AuditConfig
│   ├── MonitoringConfig
│   ├── AlertsConfig
│   ├── ManagementConfig
│   ├── BackupConfig
│   ├── ReportsConfig
│   ├── IntegrationsConfig
│   ├── LoggingConfig
│   └── Config (modèle racine)
│
├── Data Models (Objets métier LDAP)
│   ├── LDAPUser
│   └── LDAPGroup
│
├── Result Models (Résultats d'opérations)
│   ├── HealthCheckResult
│   ├── AuditIssue
│   └── AuditReport
│
└── Monitoring Models (Surveillance)
    ├── Metric
    └── Alert
```

### Enums

```python
# Niveaux d'alerte
AlertLevel: INFO, WARNING, CRITICAL

# Statut d'objet LDAP
ObjectStatus: ACTIVE, DISABLED, EXPIRED, INACTIVE, UNKNOWN

# Statut de santé
CheckStatus: HEALTHY, WARNING, CRITICAL, UNKNOWN
```

## Configuration Models

### LDAPConfig

Modèle de configuration pour la connexion LDAP.

```python
class LDAPConfig(BaseModel):
    """Configuration de connexion LDAP."""

    # Connexion
    server: str                                 # Serveur LDAP (requis)
    port: int = 389                            # Port (défaut: 389)
    use_ssl: bool = True                       # Utiliser SSL
    use_tls: bool = True                       # Utiliser TLS
    bind_dn: str                               # DN de bind (requis)
    bind_password: str                         # Mot de passe (requis)
    base_dn: str                               # DN de base (requis)

    # Performance
    timeout: int = 10                          # Timeout en secondes
    retry_max: int = 3                         # Nombre max de retries
    retry_delay: int = 2                       # Délai entre retries (sec)
    page_size: int = 1000                      # Taille de page pour recherches

    # Structure LDAP
    users_ou: str                              # OU des utilisateurs
    groups_ou: str                             # OU des groupes
    user_objectclass: str = "inetOrgPerson"    # ObjectClass utilisateurs
    group_objectclass: str = "groupOfNames"    # ObjectClass groupes
    user_uid_attribute: str = "uid"            # Attribut UID
    group_member_attribute: str = "member"     # Attribut membres

    # Recherche
    search_scope: str = "SUBTREE"              # Scope de recherche
```

**Exemple d'utilisation:**
```python
# Création d'une configuration LDAP
ldap_config = LDAPConfig(
    server="ldap.example.com",
    port=636,
    use_ssl=True,
    bind_dn="cn=admin,dc=example,dc=com",
    bind_password="secret",
    base_dn="dc=example,dc=com",
    users_ou="ou=users,dc=example,dc=com",
    groups_ou="ou=groups,dc=example,dc=com",
)

# Accès aux valeurs
print(ldap_config.server)  # "ldap.example.com"
print(ldap_config.port)    # 636

# Validation automatique
try:
    invalid = LDAPConfig(server="test")  # Manque bind_dn, bind_password, etc.
except ValidationError as e:
    print(e)
```

**Depuis YAML:**
```yaml
ldap:
  server: ldap.example.com
  port: 636
  use_ssl: true
  bind_dn: cn=admin,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}  # Variable d'environnement
  base_dn: dc=example,dc=com
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com
```

### AuditConfig

Configuration pour les audits.

```python
class AuditConfig(BaseModel):
    """Configuration des audits."""

    # Types de vérifications à effectuer
    checks: List[str] = Field(
        default=["health", "users", "groups", "structure", "security", "consistency"]
    )

    # Seuils pour les alertes
    thresholds: Dict[str, int] = Field(default_factory=dict)
    # Exemples de seuils:
    # {
    #     "response_time_warning_ms": 500,
    #     "response_time_critical_ms": 2000,
    #     "inactive_users_days": 90,
    #     "large_group_size": 1000,
    #     "ssl_cert_expiry_warning_days": 30
    # }

    # Attributs requis pour validation
    required_user_attributes: List[str] = Field(
        default=["cn", "sn", "mail", "uid"]
    )
    required_group_attributes: List[str] = Field(
        default=["cn", "member"]
    )

    # Configuration sécurité
    security: Dict[str, Any] = Field(default_factory=dict)
    # Exemples:
    # {
    #     "check_privileged_accounts": true,
    #     "privileged_groups": ["cn=admins,ou=groups,dc=example,dc=com"]
    # }
```

**Exemple:**
```python
audit_config = AuditConfig(
    checks=["health", "users", "security"],
    thresholds={
        "inactive_users_days": 60,
        "response_time_warning_ms": 300,
    },
    required_user_attributes=["cn", "mail", "uid", "employeeNumber"],
)

# Vérifier si un check est activé
if "users" in audit_config.checks:
    # Effectuer l'audit des utilisateurs
    pass

# Récupérer un seuil avec valeur par défaut
inactive_days = audit_config.thresholds.get("inactive_users_days", 90)
```

### Config (Modèle Racine)

Le modèle principal qui contient toutes les configurations.

```python
class Config(BaseModel):
    """Configuration principale de l'application."""

    ldap: LDAPConfig                                          # Requis
    audit: AuditConfig = Field(default_factory=AuditConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    management: ManagementConfig = Field(default_factory=ManagementConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)
    reports: ReportsConfig = Field(default_factory=ReportsConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
```

**Utilisation:**
```python
# Chargement depuis YAML
with open("config.yaml") as f:
    config_dict = yaml.safe_load(f)

config = Config(**config_dict)

# Accès hiérarchique
print(config.ldap.server)
print(config.audit.thresholds.get("inactive_users_days"))
print(config.monitoring.interval)

# Sérialisation
config_json = config.model_dump_json(indent=2)
config_dict = config.model_dump()
```

## Data Models (Objets LDAP)

### LDAPUser

Représente un utilisateur LDAP.

```python
class LDAPUser(BaseModel):
    """Modèle représentant un utilisateur LDAP."""

    # Attributs standards LDAP
    dn: str                                    # Distinguished Name (requis)
    uid: str                                   # User ID (requis)
    cn: str                                    # Common Name (requis)
    sn: str                                    # Surname (requis)
    mail: Optional[str] = None                 # Email (optionnel)

    # Métadonnées
    status: ObjectStatus = ObjectStatus.UNKNOWN
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    last_logon: Optional[datetime] = None
    password_last_set: Optional[datetime] = None

    # Attributs supplémentaires (flexibles)
    attributes: Dict[str, Any] = Field(default_factory=dict)
```

**Création depuis données LDAP:**
```python
def _dict_to_user(ldap_entry: Dict[str, Any]) -> LDAPUser:
    """Convertit une entrée LDAP en objet LDAPUser."""
    attrs = ldap_entry["attributes"]

    return LDAPUser(
        dn=ldap_entry["dn"],
        uid=attrs.get("uid", ""),
        cn=attrs.get("cn", ""),
        sn=attrs.get("sn", ""),
        mail=attrs.get("mail"),
        created=_parse_ldap_timestamp(attrs.get("createTimestamp")),
        modified=_parse_ldap_timestamp(attrs.get("modifyTimestamp")),
        attributes=attrs  # Stocke tous les attributs bruts
    )
```

**Utilisation:**
```python
user = LDAPUser(
    dn="uid=jdoe,ou=users,dc=example,dc=com",
    uid="jdoe",
    cn="John Doe",
    sn="Doe",
    mail="john.doe@example.com",
    status=ObjectStatus.ACTIVE,
    attributes={
        "employeeNumber": "12345",
        "department": "IT",
        "telephoneNumber": "+1234567890"
    }
)

# Accès aux données
print(f"User: {user.cn} ({user.mail})")
print(f"Status: {user.status.value}")
print(f"Department: {user.attributes.get('department')}")

# Sérialisation JSON
user_json = user.model_dump_json()
# {
#   "dn": "uid=jdoe,ou=users,dc=example,dc=com",
#   "uid": "jdoe",
#   "cn": "John Doe",
#   ...
# }
```

### LDAPGroup

Représente un groupe LDAP.

```python
class LDAPGroup(BaseModel):
    """Modèle représentant un groupe LDAP."""

    # Attributs standards
    dn: str                                    # Distinguished Name (requis)
    cn: str                                    # Common Name (requis)
    members: List[str] = Field(default_factory=list)  # DNs des membres
    description: Optional[str] = None

    # Métadonnées
    created: Optional[datetime] = None
    modified: Optional[datetime] = None

    # Attributs supplémentaires
    attributes: Dict[str, Any] = Field(default_factory=dict)
```

**Exemple:**
```python
group = LDAPGroup(
    dn="cn=developers,ou=groups,dc=example,dc=com",
    cn="developers",
    description="Development team",
    members=[
        "uid=jdoe,ou=users,dc=example,dc=com",
        "uid=asmith,ou=users,dc=example,dc=com",
    ],
    created=datetime(2024, 1, 1, 12, 0, 0),
)

# Opérations sur les membres
print(f"Group: {group.cn}")
print(f"Members count: {len(group.members)}")

# Vérifier si un utilisateur est membre
user_dn = "uid=jdoe,ou=users,dc=example,dc=com"
is_member = user_dn in group.members

# Ajouter un membre
group.members.append("uid=newuser,ou=users,dc=example,dc=com")
```

## Result Models

### HealthCheckResult

Résultat d'une vérification de santé.

```python
class HealthCheckResult(BaseModel):
    """Résultat d'une vérification de santé."""

    status: CheckStatus                         # HEALTHY, WARNING, CRITICAL
    response_time: float                        # Temps de réponse en ms
    message: str                                # Message descriptif
    details: Dict[str, Any] = Field(default_factory=dict)  # Détails additionnels
    timestamp: datetime = Field(default_factory=datetime.now)
```

**Exemple:**
```python
# Check réussi
healthy = HealthCheckResult(
    status=CheckStatus.HEALTHY,
    response_time=125.5,
    message="LDAP server is healthy",
    details={
        "response_time_ms": 125.5,
        "statistics": {
            "users_total": 1500,
            "groups_total": 50,
            "ous_total": 10
        },
        "server_info": {
            "host": "ldap.example.com",
            "port": 636,
            "ssl": True
        }
    }
)

# Check avec warning
warning = HealthCheckResult(
    status=CheckStatus.WARNING,
    response_time=750.0,
    message="LDAP server has warnings",
    details={
        "issues": [
            {
                "level": "warning",
                "title": "Elevated response time",
                "description": "Server response time is 750ms"
            }
        ]
    }
)

# Check critique
critical = HealthCheckResult(
    status=CheckStatus.CRITICAL,
    response_time=3000.0,
    message="Cannot connect to LDAP server",
    details={
        "error": "Connection timeout after 10 seconds"
    }
)
```

### AuditIssue

Représente un problème découvert lors d'un audit.

```python
class AuditIssue(BaseModel):
    """Problème découvert lors d'un audit."""

    level: AlertLevel                          # INFO, WARNING, CRITICAL
    category: str                              # Catégorie (users, groups, security...)
    title: str                                 # Titre court du problème
    description: str                           # Description détaillée
    affected_dn: Optional[str] = None         # DN de l'objet affecté
    recommendation: Optional[str] = None       # Recommandation pour résoudre
    details: Dict[str, Any] = Field(default_factory=dict)  # Détails supplémentaires
```

**Exemples:**
```python
# Issue WARNING - Utilisateur inactif
inactive_user_issue = AuditIssue(
    level=AlertLevel.WARNING,
    category="users",
    title="Inactive user account",
    description="User has not logged in for 180 days",
    affected_dn="uid=jdoe,ou=users,dc=example,dc=com",
    recommendation="Review account and consider disabling",
    details={
        "uid": "jdoe",
        "last_logon": "2023-06-01",
        "days_inactive": 180
    }
)

# Issue INFO - Groupe avec beaucoup de membres
large_group_issue = AuditIssue(
    level=AlertLevel.INFO,
    category="groups",
    title="Large group detected",
    description="Group has 1500 members",
    affected_dn="cn=all-employees,ou=groups,dc=example,dc=com",
    recommendation="Consider splitting into smaller groups for better performance",
    details={
        "group_name": "all-employees",
        "member_count": 1500,
        "threshold": 1000
    }
)

# Issue CRITICAL - Attribut manquant
missing_attr_issue = AuditIssue(
    level=AlertLevel.CRITICAL,
    category="users",
    title="Missing required attribute",
    description="User is missing required attribute 'mail'",
    affected_dn="uid=asmith,ou=users,dc=example,dc=com",
    recommendation="Add missing mail attribute",
    details={
        "uid": "asmith",
        "missing_attribute": "mail",
        "required_attributes": ["cn", "sn", "mail", "uid"]
    }
)
```

### AuditReport

Rapport d'audit complet.

```python
class AuditReport(BaseModel):
    """Rapport d'audit complet."""

    timestamp: datetime = Field(default_factory=datetime.now)
    health: Optional[HealthCheckResult] = None
    issues: List[AuditIssue] = Field(default_factory=list)
    statistics: Dict[str, Any] = Field(default_factory=dict)
    recommendations: List[str] = Field(default_factory=list)
    score: int = 100  # Score de santé (0-100)
```

**Construction d'un rapport:**
```python
# Création du rapport
report = AuditReport(
    timestamp=datetime.now(),
    health=health_check_result,
    issues=[],
    statistics={},
    score=100
)

# Ajout des issues depuis différents audits
report.issues.extend(user_auditor.audit_users())
report.issues.extend(group_auditor.audit_groups())
report.issues.extend(security_auditor.audit_security())

# Ajout des statistiques
report.statistics = {
    "total_users": 1500,
    "total_groups": 50,
    "issues_critical": len([i for i in report.issues if i.level == AlertLevel.CRITICAL]),
    "issues_warning": len([i for i in report.issues if i.level == AlertLevel.WARNING]),
    "issues_info": len([i for i in report.issues if i.level == AlertLevel.INFO]),
}

# Calcul du score (exemple simple)
critical_issues = len([i for i in report.issues if i.level == AlertLevel.CRITICAL])
warning_issues = len([i for i in report.issues if i.level == AlertLevel.WARNING])
report.score = max(0, 100 - (critical_issues * 10) - (warning_issues * 5))

# Ajout de recommandations
report.recommendations = [
    issue.recommendation
    for issue in report.issues
    if issue.recommendation
]

# Export JSON
with open("audit_report.json", "w") as f:
    f.write(report.model_dump_json(indent=2))
```

## Monitoring Models

### Metric

Représente une métrique de surveillance.

```python
class Metric(BaseModel):
    """Métrique de surveillance."""

    name: str                                  # Nom de la métrique
    value: float                               # Valeur numérique
    timestamp: datetime = Field(default_factory=datetime.now)
    labels: Dict[str, str] = Field(default_factory=dict)  # Labels Prometheus-style
```

**Exemples:**
```python
# Métrique simple
users_count = Metric(
    name="ldap_users_total",
    value=1500.0,
    labels={"instance": "ldap-prod"}
)

# Métrique de performance
response_time = Metric(
    name="ldap_response_time_ms",
    value=125.5,
    labels={
        "instance": "ldap-prod",
        "operation": "search"
    }
)

# Métrique de taux d'erreur
auth_failures = Metric(
    name="ldap_auth_failures_total",
    value=12.0,
    labels={
        "instance": "ldap-prod",
        "time_window": "1h"
    }
)

# Export format Prometheus
def to_prometheus_format(metric: Metric) -> str:
    """Convertit une métrique en format Prometheus."""
    labels_str = ",".join([f'{k}="{v}"' for k, v in metric.labels.items()])
    if labels_str:
        return f"{metric.name}{{{labels_str}}} {metric.value}"
    return f"{metric.name} {metric.value}"

print(to_prometheus_format(users_count))
# ldap_users_total{instance="ldap-prod"} 1500.0
```

### Alert

Représente une alerte de surveillance.

```python
class Alert(BaseModel):
    """Alerte de surveillance."""

    level: AlertLevel                          # INFO, WARNING, CRITICAL
    title: str                                 # Titre de l'alerte
    message: str                               # Message détaillé
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Dict[str, Any] = Field(default_factory=dict)
```

**Exemples:**
```python
# Alerte haute latence
high_latency_alert = Alert(
    level=AlertLevel.WARNING,
    title="High LDAP Response Time",
    message="LDAP server response time exceeded 500ms threshold",
    details={
        "current_value": 750.0,
        "threshold": 500.0,
        "metric": "ldap_response_time_ms"
    }
)

# Alerte échecs d'authentification
auth_failure_alert = Alert(
    level=AlertLevel.CRITICAL,
    title="Elevated Authentication Failures",
    message="Authentication failure rate exceeded 10 per minute",
    details={
        "current_rate": 15.5,
        "threshold": 10.0,
        "time_window": "1m"
    }
)

# Conversion pour Slack
def to_slack_message(alert: Alert) -> Dict[str, Any]:
    """Convertit une alerte en message Slack."""
    color = {
        AlertLevel.INFO: "good",
        AlertLevel.WARNING: "warning",
        AlertLevel.CRITICAL: "danger"
    }

    return {
        "attachments": [
            {
                "color": color[alert.level],
                "title": alert.title,
                "text": alert.message,
                "fields": [
                    {"title": k, "value": str(v), "short": True}
                    for k, v in alert.details.items()
                ],
                "ts": int(alert.timestamp.timestamp())
            }
        ]
    }
```

## Validation Avancée

### Validators Personnalisés

```python
from pydantic import field_validator, model_validator

class LDAPConfig(BaseModel):
    server: str
    port: int
    bind_dn: str

    @field_validator("server")
    @classmethod
    def validate_server(cls, v: str) -> str:
        """Valide le format du serveur."""
        if not v or v.isspace():
            raise ValueError("Server cannot be empty")
        # Retirer le protocole si présent
        v = v.replace("ldap://", "").replace("ldaps://", "")
        return v

    @field_validator("port")
    @classmethod
    def validate_port(cls, v: int) -> int:
        """Valide le port."""
        if v < 1 or v > 65535:
            raise ValueError("Port must be between 1 and 65535")
        return v

    @field_validator("bind_dn")
    @classmethod
    def validate_bind_dn(cls, v: str) -> str:
        """Valide le format du DN."""
        if "dc=" not in v.lower():
            raise ValueError("bind_dn must contain DC components")
        return v

    @model_validator(mode='after')
    def validate_ssl_port(self) -> 'LDAPConfig':
        """Valide la cohérence SSL/port."""
        if self.use_ssl and self.port == 389:
            # Warning: port standard non-SSL avec SSL activé
            import warnings
            warnings.warn("SSL enabled but using standard LDAP port 389")
        return self
```

### Validation Conditionnelle

```python
class AuditConfig(BaseModel):
    check_passwords: bool = False
    password_min_age_days: Optional[int] = None
    password_max_age_days: Optional[int] = None

    @model_validator(mode='after')
    def validate_password_config(self) -> 'AuditConfig':
        """Valide la configuration des mots de passe."""
        if self.check_passwords:
            if self.password_max_age_days is None:
                raise ValueError(
                    "password_max_age_days required when check_passwords is True"
                )
            if self.password_min_age_days and self.password_max_age_days:
                if self.password_min_age_days >= self.password_max_age_days:
                    raise ValueError(
                        "password_min_age_days must be less than password_max_age_days"
                    )
        return self
```

## Sérialisation et Désérialisation

### JSON

```python
# Objet -> JSON
user = LDAPUser(dn="...", uid="jdoe", cn="John Doe", sn="Doe")

# Méthode 1: JSON string
json_str = user.model_dump_json(indent=2)

# Méthode 2: Dict puis JSON
user_dict = user.model_dump()
json_str = json.dumps(user_dict, default=str)  # default=str pour datetime

# JSON -> Objet
user_data = json.loads(json_str)
user = LDAPUser(**user_data)
```

### YAML

```python
import yaml

# Objet -> YAML
config = Config(ldap=ldap_config, audit=audit_config)
config_dict = config.model_dump()

with open("config.yaml", "w") as f:
    yaml.dump(config_dict, f, default_flow_style=False)

# YAML -> Objet
with open("config.yaml") as f:
    config_dict = yaml.safe_load(f)

config = Config(**config_dict)
```

### Exclusion de Champs

```python
# Exclure des champs sensibles
config_dict = config.model_dump(exclude={"ldap": {"bind_password"}})

# Exclure les None
user_dict = user.model_dump(exclude_none=True)

# Exclure les valeurs par défaut
config_dict = config.model_dump(exclude_defaults=True)
```

## Bonnes Pratiques

### 1. Utiliser Field() pour Métadonnées

```python
class User(BaseModel):
    uid: str = Field(..., min_length=1, max_length=50, description="User ID")
    age: int = Field(ge=0, le=150, description="User age")
    email: str = Field(..., pattern=r'^[\w\.-]+@[\w\.-]+\.\w+$')
```

### 2. Valeurs par Défaut Intelligentes

```python
# Bon - utilise Field pour default_factory
attributes: Dict[str, Any] = Field(default_factory=dict)
members: List[str] = Field(default_factory=list)

# Mauvais - partage la même liste entre instances!
# members: List[str] = []  # NE PAS FAIRE
```

### 3. Type Hints Précis

```python
# Bon
from typing import Optional, List, Dict, Any

issues: List[AuditIssue] = Field(default_factory=list)
mail: Optional[str] = None
details: Dict[str, Any] = Field(default_factory=dict)

# Moins bon
issues = []  # Type non spécifié
mail = None  # Type non clair
```

### 4. Documentation avec Docstrings

```python
class AuditReport(BaseModel):
    """Rapport d'audit complet.

    Attributes:
        timestamp: Date et heure de génération du rapport
        health: Résultat du check de santé (optionnel)
        issues: Liste de tous les problèmes découverts
        statistics: Statistiques agrégées
        recommendations: Liste de recommandations
        score: Score de santé global (0-100)
    """

    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Date et heure de génération"
    )
    score: int = Field(
        default=100,
        ge=0,
        le=100,
        description="Score de santé (0-100)"
    )
```

### 5. Immutabilité quand Approprié

```python
from pydantic import ConfigDict

class ImmutableConfig(BaseModel):
    """Configuration immuable."""

    model_config = ConfigDict(frozen=True)

    server: str
    port: int

# Utilisation
config = ImmutableConfig(server="ldap.example.com", port=389)
# config.port = 636  # Erreur! Frozen model
```

### 6. Alias pour Compatibilité

```python
class LDAPUser(BaseModel):
    """Utilisateur avec alias pour compatibilité."""

    # Champ interne: uid
    # Alias externe: username
    uid: str = Field(..., alias="username")
    cn: str = Field(..., alias="commonName")

    model_config = ConfigDict(populate_by_name=True)

# Utilisation
user = LDAPUser(username="jdoe", commonName="John Doe")
print(user.uid)  # "jdoe"

# Sérialisation avec alias
print(user.model_dump(by_alias=True))
# {"username": "jdoe", "commonName": "John Doe"}
```

## Exemples Complets

### Créer et Valider un Rapport d'Audit

```python
from datetime import datetime
from src.core.models import (
    AuditReport, AuditIssue, HealthCheckResult,
    CheckStatus, AlertLevel
)

# 1. Créer le health check
health = HealthCheckResult(
    status=CheckStatus.HEALTHY,
    response_time=150.0,
    message="Server is healthy"
)

# 2. Créer des issues
issues = [
    AuditIssue(
        level=AlertLevel.WARNING,
        category="users",
        title="Inactive user",
        description="User inactive for 90 days",
        affected_dn="uid=jdoe,ou=users,dc=example,dc=com",
        recommendation="Review and disable if needed"
    ),
    AuditIssue(
        level=AlertLevel.INFO,
        category="groups",
        title="Empty group",
        description="Group has no members",
        affected_dn="cn=old-team,ou=groups,dc=example,dc=com",
        recommendation="Consider removing empty group"
    ),
]

# 3. Créer le rapport
report = AuditReport(
    timestamp=datetime.now(),
    health=health,
    issues=issues,
    statistics={
        "users_total": 1500,
        "groups_total": 50,
        "issues_critical": 0,
        "issues_warning": 1,
        "issues_info": 1,
    },
    recommendations=[i.recommendation for i in issues if i.recommendation],
    score=95  # 100 - (0*10) - (1*5)
)

# 4. Valider et exporter
print(f"Rapport valide: {report.model_validate(report)}")
print(f"Score: {report.score}/100")
print(f"Issues: {len(report.issues)}")

# 5. Export JSON
with open("report.json", "w") as f:
    f.write(report.model_dump_json(indent=2))
```

## Conclusion

Les modèles Pydantic dans LDAP Health Monitor offrent:

- **Type Safety**: Validation automatique des types
- **Validation**: Rules personnalisées avec validators
- **Sérialisation**: JSON/YAML facile
- **Documentation**: Schémas auto-générés
- **Maintenabilité**: Code clair et auto-documenté

Toujours utiliser Pydantic pour:
- Configuration
- Données métier
- API responses
- Validation d'entrée utilisateur
