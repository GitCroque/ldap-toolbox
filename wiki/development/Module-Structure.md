# Structure des Modules

## Organisation du Projet

Le projet LDAP Health Monitor suit une structure modulaire claire qui facilite la navigation et la maintenance du code.

```
ldap-toolbox/
├── src/                          # Code source principal
│   ├── __init__.py              # Package root
│   ├── cli.py                   # Point d'entrée CLI (685 lignes)
│   │
│   ├── core/                    # Modules noyau
│   │   ├── __init__.py
│   │   ├── config.py            # Gestion configuration (227 lignes)
│   │   ├── connector.py         # Connexion LDAP (318 lignes)
│   │   └── models.py            # Modèles Pydantic (234 lignes)
│   │
│   ├── audit/                   # Modules d'audit
│   │   ├── __init__.py
│   │   ├── health.py            # Santé serveur (230 lignes)
│   │   ├── users.py             # Audit utilisateurs
│   │   ├── groups.py            # Audit groupes
│   │   ├── security.py          # Audit sécurité (63 lignes)
│   │   ├── structure.py         # Audit structure
│   │   └── consistency.py       # Audit cohérence
│   │
│   ├── monitor/                 # Modules de surveillance
│   │   ├── __init__.py
│   │   ├── daemon.py            # Daemon de surveillance
│   │   ├── metrics.py           # Collecte métriques
│   │   └── alerts.py            # Gestion alertes
│   │
│   ├── manage/                  # Modules de gestion
│   │   ├── __init__.py
│   │   ├── users.py             # Gestion utilisateurs
│   │   ├── groups.py            # Gestion groupes
│   │   ├── backup.py            # Sauvegarde/Export
│   │   └── cleanup.py           # Nettoyage/Maintenance
│   │
│   ├── reporters/               # Modules de reporting
│   │   ├── __init__.py
│   │   ├── console.py           # Reporter console (187 lignes)
│   │   ├── json.py              # Reporter JSON
│   │   ├── html.py              # Reporter HTML
│   │   ├── csv.py               # Reporter CSV
│   │   └── prometheus.py        # Reporter Prometheus
│   │
│   └── utils/                   # Utilitaires
│       └── __init__.py
│
├── tests/                       # Tests
│   ├── __init__.py
│   ├── conftest.py             # Fixtures pytest (32 lignes)
│   ├── unit/                   # Tests unitaires
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   └── test_connector.py
│   └── integration/            # Tests d'intégration
│       ├── test_audit.py
│       └── test_monitor.py
│
├── wiki/                        # Documentation
├── config.example.yaml          # Configuration exemple
├── pyproject.toml              # Configuration projet Python
├── requirements.txt            # Dépendances
└── README.md                   # Documentation principale
```

## Module Core (src/core/)

### Rôle et Responsabilités

Le module `core` contient les composants fondamentaux réutilisés par tous les autres modules.

### Structure Interne

#### 1. core/models.py

**Responsabilité:** Définir tous les modèles de données Pydantic

**Organisation:**
```python
# 1. Imports
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

# 2. Enums - Types énumérés
class AlertLevel(str, Enum):
    """Niveaux de sévérité des alertes."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class ObjectStatus(str, Enum):
    """Statut d'un objet LDAP."""
    ACTIVE = "active"
    DISABLED = "disabled"
    EXPIRED = "expired"

# 3. Configuration Models - Modèles de configuration
class LDAPConfig(BaseModel):
    """Configuration de connexion LDAP."""
    server: str
    port: int = 389
    use_ssl: bool = True
    # ... autres champs

class AuditConfig(BaseModel):
    """Configuration des audits."""
    checks: List[str] = Field(default=["health", "users", "groups"])
    thresholds: Dict[str, int] = Field(default_factory=dict)

# 4. Data Models - Modèles de données métier
class LDAPUser(BaseModel):
    """Représentation d'un utilisateur LDAP."""
    dn: str
    uid: str
    cn: str
    # ... autres attributs

class LDAPGroup(BaseModel):
    """Représentation d'un groupe LDAP."""
    dn: str
    cn: str
    members: List[str] = Field(default_factory=list)

# 5. Result Models - Modèles de résultats
class HealthCheckResult(BaseModel):
    """Résultat d'un check de santé."""
    status: CheckStatus
    response_time: float
    message: str
    details: Dict[str, Any] = Field(default_factory=dict)

class AuditIssue(BaseModel):
    """Problème découvert lors d'un audit."""
    level: AlertLevel
    category: str
    title: str
    description: str
    recommendation: Optional[str] = None

class AuditReport(BaseModel):
    """Rapport d'audit complet."""
    timestamp: datetime = Field(default_factory=datetime.now)
    health: Optional[HealthCheckResult] = None
    issues: List[AuditIssue] = Field(default_factory=list)
    score: int = 100
```

**Bonnes pratiques:**
- Grouper les modèles par type (Config, Data, Result)
- Utiliser `Field()` pour les valeurs par défaut complexes
- Ajouter des docstrings pour tous les modèles
- Utiliser des Enums pour les valeurs restreintes
- Définir des validators avec `@field_validator` si nécessaire

#### 2. core/connector.py

**Responsabilité:** Gérer toutes les interactions avec LDAP

**Organisation:**
```python
# 1. Imports
import time
from typing import Any, Dict, List, Optional, Tuple
from ldap3 import ALL, ALL_ATTRIBUTES, Connection, Server, Tls
from ldap3.core.exceptions import LDAPException
from src.core.models import LDAPConfig

# 2. Classe principale
class LDAPConnector:
    """Gestionnaire de connexions LDAP."""

    def __init__(self, config: LDAPConfig) -> None:
        """Initialise le connecteur."""
        self.config = config
        self._server: Optional[Server] = None
        self._connection: Optional[Connection] = None

    # 3. Méthodes publiques de haut niveau
    def connect(self) -> Connection:
        """Établit la connexion LDAP."""
        pass

    def disconnect(self) -> None:
        """Ferme la connexion LDAP."""
        pass

    # 4. Opérations CRUD
    def search(self, search_base: str, ...) -> List[Dict[str, Any]]:
        """Recherche des entrées LDAP."""
        pass

    def get_entry(self, dn: str, ...) -> Optional[Dict[str, Any]]:
        """Récupère une entrée par DN."""
        pass

    def add_entry(self, dn: str, ...) -> bool:
        """Ajoute une nouvelle entrée."""
        pass

    def modify_entry(self, dn: str, ...) -> bool:
        """Modifie une entrée existante."""
        pass

    def delete_entry(self, dn: str) -> bool:
        """Supprime une entrée."""
        pass

    # 5. Opérations utilitaires
    def test_connection(self) -> Tuple[bool, float, Optional[str]]:
        """Test la connexion LDAP."""
        pass

    def get_server_info(self) -> Dict[str, Any]:
        """Récupère les infos du serveur."""
        pass

    # 6. Méthodes privées/helpers
    def _entry_to_dict(self, entry: Any) -> Dict[str, Any]:
        """Convertit une entrée LDAP en dict."""
        pass

    # 7. Context manager support
    def __enter__(self) -> "LDAPConnector":
        """Support du context manager."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Nettoyage du context manager."""
        self.disconnect()
```

**Dépendances:**
- `ldap3`: Bibliothèque cliente LDAP
- `src.core.models.LDAPConfig`: Configuration LDAP

**Utilisé par:**
- Tous les modules d'audit
- Tous les modules de gestion
- Module de monitoring

#### 3. core/config.py

**Responsabilité:** Charger, valider et gérer la configuration

**Organisation:**
```python
# 1. Imports
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from dotenv import load_dotenv
from src.core.models import Config

# 2. Classe principale
class ConfigManager:
    """Gestionnaire de configuration."""

    def __init__(self, config_path: Optional[str] = None) -> None:
        self.config_path = self._find_config(config_path)
        self._raw_config: Dict[str, Any] = {}
        self._config: Optional[Config] = None

    # 3. Méthodes publiques
    def load(self, config_path: Optional[str] = None) -> Config:
        """Charge et valide la configuration."""
        pass

    def validate(self) -> bool:
        """Valide la configuration actuelle."""
        pass

    def get_ldap_uri(self) -> str:
        """Construit l'URI LDAP complète."""
        pass

    def init_config(self, output_path: str = "config.yaml") -> None:
        """Crée un nouveau fichier de configuration."""
        pass

    # 4. Méthodes privées
    def _find_config(self, config_path: Optional[str] = None) -> Optional[Path]:
        """Recherche le fichier de configuration."""
        pass

    def _replace_env_vars(self, data: Any) -> Any:
        """Remplace ${VAR} par les variables d'environnement."""
        pass

    # 5. Property
    @property
    def config(self) -> Optional[Config]:
        """Accès à la configuration chargée."""
        return self._config

# 6. Fonctions globales/helpers
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Singleton pour le gestionnaire de configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager

def load_config(config_path: Optional[str] = None) -> Config:
    """Fonction utilitaire pour charger la configuration."""
    manager = get_config_manager()
    return manager.load(config_path)
```

**Dépendances:**
- `yaml`: Parser YAML
- `python-dotenv`: Support .env files
- `src.core.models.Config`: Modèle de configuration

**Pattern de recherche de configuration:**
```python
search_paths = [
    Path("config.yaml"),                                    # Répertoire courant
    Path("config.yml"),                                     # Variante .yml
    Path.home() / ".config" / "ldap-monitor" / "config.yaml",  # Home user
    Path("/etc/ldap-monitor/config.yaml"),                 # System-wide
]
```

## Module Audit (src/audit/)

### Structure Standard d'un Auditeur

Tous les auditeurs suivent le même pattern pour la cohérence:

```python
"""Module d'audit [description]."""

from typing import List
from src.core.connector import LDAPConnector
from src.core.models import AlertLevel, AuditIssue, Config


class [Name]Auditor:
    """Auditeur pour [description]."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialise l'auditeur.

        Args:
            connector: Connecteur LDAP
            config: Configuration de l'application
        """
        self.connector = connector
        self.config = config

    def audit_[domain](self) -> List[AuditIssue]:
        """Effectue l'audit complet de [domain].

        Returns:
            Liste des problèmes découverts
        """
        issues: List[AuditIssue] = []

        # Exécute chaque vérification configurée
        if self.config.audit.thresholds.get("check_[something]", True):
            issues.extend(self._check_[something]())

        return issues

    def _check_[something](self) -> List[AuditIssue]:
        """Vérifie [something specific].

        Returns:
            Liste des problèmes trouvés pour cette vérification
        """
        issues: List[AuditIssue] = []

        try:
            # Logique de vérification
            # ...

            # Si problème détecté:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="[category]",
                    title="[Titre du problème]",
                    description="[Description détaillée]",
                    affected_dn="[DN de l'objet affecté]",
                    recommendation="[Recommandation pour résoudre]",
                    details={"key": "value"}
                )
            )

        except Exception as e:
            # Gestion d'erreur: convertir en AuditIssue
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="audit",
                    title=f"Erreur lors de l'audit [domain]",
                    description=str(e),
                    recommendation="Vérifier la connexion et les permissions"
                )
            )

        return issues
```

### Exemple: audit/users.py

```python
"""Audit des utilisateurs LDAP."""

from datetime import datetime, timedelta
from typing import List
from src.core.connector import LDAPConnector
from src.core.models import AlertLevel, AuditIssue, Config, LDAPUser, ObjectStatus


class UserAuditor:
    """Auditeur pour les utilisateurs LDAP."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        self.connector = connector
        self.config = config

    def audit_users(
        self,
        check_inactive: bool = True,
        check_attributes: bool = True,
        check_passwords: bool = False
    ) -> List[AuditIssue]:
        """Effectue l'audit complet des utilisateurs."""
        issues: List[AuditIssue] = []

        if check_inactive:
            issues.extend(self._check_inactive_users())

        if check_attributes:
            issues.extend(self._check_missing_attributes())

        if check_passwords:
            issues.extend(self._check_password_policy())

        return issues

    def _check_inactive_users(self) -> List[AuditIssue]:
        """Détecte les utilisateurs inactifs."""
        issues = []
        # ... implémentation
        return issues

    def _check_missing_attributes(self) -> List[AuditIssue]:
        """Détecte les attributs manquants."""
        issues = []
        # ... implémentation
        return issues
```

### Fichier __init__.py

Le fichier `__init__.py` de chaque module expose les classes principales:

```python
"""Module d'audit LDAP."""

from src.audit.health import HealthChecker
from src.audit.users import UserAuditor
from src.audit.groups import GroupAuditor
from src.audit.security import SecurityAuditor
from src.audit.structure import StructureAuditor
from src.audit.consistency import ConsistencyAuditor

__all__ = [
    "HealthChecker",
    "UserAuditor",
    "GroupAuditor",
    "SecurityAuditor",
    "StructureAuditor",
    "ConsistencyAuditor",
]
```

## Module Monitor (src/monitor/)

### Structure du Module

```python
monitor/
├── __init__.py           # Exports
├── daemon.py            # Service de surveillance
├── metrics.py           # Collecte de métriques
└── alerts.py            # Gestion des alertes
```

### Exemple: monitor/metrics.py

```python
"""Collecte de métriques LDAP."""

from datetime import datetime
from typing import List, Dict, Any
from prometheus_client import CollectorRegistry, Gauge, Counter
from src.core.connector import LDAPConnector
from src.core.models import Config, Metric


class MetricsCollector:
    """Collecteur de métriques LDAP."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        self.connector = connector
        self.config = config
        self.registry = CollectorRegistry()
        self._init_metrics()

    def _init_metrics(self) -> None:
        """Initialise les métriques Prometheus."""
        self.users_count = Gauge(
            'ldap_users_total',
            'Total number of LDAP users',
            registry=self.registry
        )
        self.groups_count = Gauge(
            'ldap_groups_total',
            'Total number of LDAP groups',
            registry=self.registry
        )
        # ... autres métriques

    def collect_all_metrics(self) -> List[Metric]:
        """Collecte toutes les métriques configurées."""
        metrics = []

        for metric_name in self.config.monitoring.metrics:
            collector_method = getattr(self, f"collect_{metric_name}", None)
            if collector_method:
                metric = collector_method()
                if metric:
                    metrics.append(metric)

        return metrics

    def collect_users_count(self) -> Metric:
        """Collecte le nombre d'utilisateurs."""
        users = self.connector.search(
            search_base=self.config.ldap.users_ou,
            search_filter=f"(objectClass={self.config.ldap.user_objectclass})",
            attributes=["dn"]
        )

        count = len(users)
        self.users_count.set(count)

        return Metric(
            name="users_count",
            value=float(count),
            timestamp=datetime.now(),
            labels={"type": "users"}
        )
```

## Module Manage (src/manage/)

### Structure CRUD Standard

```python
"""Gestion des [resource]."""

from typing import Dict, Any, List, Optional
from src.core.connector import LDAPConnector
from src.core.models import Config, LDAP[Resource]


class [Resource]Manager:
    """Gestionnaire pour les [resource]."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        self.connector = connector
        self.config = config

    # CREATE
    def create_[resource](self, data: Dict[str, Any]) -> LDAP[Resource]:
        """Crée un nouveau [resource]."""
        pass

    # READ
    def get_[resource](self, dn: str) -> Optional[LDAP[Resource]]:
        """Récupère un [resource] par son DN."""
        pass

    def list_[resources](self, limit: Optional[int] = None) -> List[LDAP[Resource]]:
        """Liste tous les [resources]."""
        pass

    def search_[resources](self, query: str) -> List[LDAP[Resource]]:
        """Recherche des [resources]."""
        pass

    # UPDATE
    def update_[resource](self, dn: str, changes: Dict[str, Any]) -> bool:
        """Met à jour un [resource]."""
        pass

    # DELETE
    def delete_[resource](self, dn: str) -> bool:
        """Supprime un [resource]."""
        pass

    # HELPERS
    def _build_dn(self, uid: str) -> str:
        """Construit le DN complet."""
        pass

    def _validate_[resource]_data(self, data: Dict[str, Any]) -> bool:
        """Valide les données du [resource]."""
        pass

    def _dict_to_[resource](self, data: Dict[str, Any]) -> LDAP[Resource]:
        """Convertit un dict en objet [Resource]."""
        pass
```

## Module Reporters (src/reporters/)

### Interface Commune

Tous les reporters peuvent implémenter cette interface:

```python
"""Interface de base pour les reporters."""

from abc import ABC, abstractmethod
from typing import Optional
from src.core.models import HealthCheckResult, AuditReport


class BaseReporter(ABC):
    """Classe de base abstraite pour les reporters."""

    @abstractmethod
    def report_health(self, health: HealthCheckResult) -> None:
        """Génère un rapport de santé."""
        pass

    @abstractmethod
    def report_audit(self, report: AuditReport) -> None:
        """Génère un rapport d'audit."""
        pass

    @abstractmethod
    def export_audit(self, report: AuditReport, output_path: str) -> None:
        """Exporte un rapport d'audit vers un fichier."""
        pass
```

### Exemple: reporters/console.py

```python
"""Reporter pour affichage console."""

from typing import Any, Dict, List
from rich.console import Console
from rich.table import Table
from src.core.models import HealthCheckResult, AuditReport


class ConsoleReporter:
    """Formateur pour affichage console avec Rich."""

    def __init__(self) -> None:
        self.console = Console()

    def report_health(self, health: HealthCheckResult) -> None:
        """Affiche le résultat de santé."""
        # Utilise Rich pour formater
        pass

    def report_audit(self, report: AuditReport) -> None:
        """Affiche le rapport d'audit."""
        # Groupe par catégorie, affiche avec couleurs
        pass

    def print_success(self, message: str) -> None:
        """Affiche un message de succès."""
        self.console.print(f"[green]✅ {message}[/green]")

    def print_error(self, message: str) -> None:
        """Affiche un message d'erreur."""
        self.console.print(f"[red]❌ {message}[/red]")
```

## Module CLI (src/cli.py)

### Organisation des Commandes

```python
"""Interface CLI principale."""

import click
from typing import Optional

# 1. Groupe principal
@click.group()
@click.option("--config", "-c", help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True)
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """LDAP Health Monitor CLI."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose


# 2. Groupes de commandes par domaine
@cli.group()
def config() -> None:
    """Configuration management."""
    pass

@cli.group()
def audit() -> None:
    """Audit commands."""
    pass

@cli.group()
def monitor() -> None:
    """Monitoring commands."""
    pass

@cli.group()
def user() -> None:
    """User management."""
    pass

@cli.group()
def group() -> None:
    """Group management."""
    pass


# 3. Commandes spécifiques
@config.command("init")
@click.option("--output", "-o", default="config.yaml")
def config_init(output: str) -> None:
    """Initialize configuration."""
    pass

@audit.command("all")
@click.option("--output", "-o", help="Output file")
@click.option("--format", "-f", type=click.Choice(["console", "json", "html"]))
@click.pass_context
def audit_all(ctx: click.Context, output: Optional[str], format: str) -> None:
    """Run all audits."""
    try:
        # 1. Charger la configuration
        config = load_config(ctx.obj.get("config_path"))

        # 2. Créer le connecteur
        connector = LDAPConnector(config.ldap)

        # 3. Créer les auditeurs
        # 4. Exécuter les audits
        # 5. Générer le rapport
        # 6. Afficher/Exporter

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
```

### Hiérarchie des Commandes

```
ldap-monitor
├── config
│   ├── init          # Créer config
│   ├── validate      # Valider config
│   └── show          # Afficher config
│
├── audit
│   ├── health        # Check santé
│   ├── users         # Audit users
│   ├── groups        # Audit groups
│   └── all           # Audit complet
│
├── monitor
│   ├── start         # Démarrer monitoring
│   ├── metrics       # Afficher métriques
│   └── prometheus    # Server Prometheus
│
├── user
│   ├── list          # Lister users
│   ├── search        # Chercher users
│   └── show          # Détails user
│
├── group
│   ├── list          # Lister groups
│   ├── search        # Chercher groups
│   ├── show          # Détails group
│   └── members       # Membres d'un groupe
│
├── cleanup
│   ├── dry-run       # Simuler nettoyage
│   └── empty-groups  # Supprimer groupes vides
│
├── backup
│   └── full          # Sauvegarde complète
│
├── export
│   └── users         # Exporter users
│
├── test
│   └── connection    # Tester connexion
│
└── version           # Afficher version
```

## Imports et Dépendances

### Graphe de Dépendances

```
cli.py
├─> core.config (ConfigManager, load_config)
├─> core.connector (LDAPConnector)
├─> core.models (Config, AuditReport, ...)
├─> audit.*  (tous les auditeurs)
├─> monitor.* (daemon, metrics, alerts)
├─> manage.* (users, groups, backup, cleanup)
└─> reporters.* (console, json, html, csv, prometheus)

audit.*
├─> core.connector (LDAPConnector)
└─> core.models (Config, AuditIssue, AlertLevel, ...)

monitor.*
├─> core.connector (LDAPConnector)
└─> core.models (Config, Metric, Alert, ...)

manage.*
├─> core.connector (LDAPConnector)
└─> core.models (Config, LDAPUser, LDAPGroup, ...)

reporters.*
└─> core.models (HealthCheckResult, AuditReport, ...)

core.config
└─> core.models (Config)

core.connector
└─> core.models (LDAPConfig)
```

### Règles d'Import

**1. Imports absolus uniquement:**
```python
# Bon
from src.core.models import Config
from src.core.connector import LDAPConnector

# Mauvais
from ..core.models import Config
from .connector import LDAPConnector
```

**2. Ordre des imports:**
```python
# 1. Standard library
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

# 2. Third-party
import click
import yaml
from ldap3 import Connection
from pydantic import BaseModel

# 3. Local application
from src.core.config import load_config
from src.core.connector import LDAPConnector
from src.core.models import Config
```

**3. Éviter les imports circulaires:**
```python
# Si A importe B et B importe A = problème

# Solution: utiliser des imports dans les fonctions
def function_that_needs_rarely_used_module():
    from src.other.module import RarelyUsed
    # utilisation
```

## Conventions de Nommage

### Fichiers et Modules

- **Modules:** `snake_case.py`
- **Packages:** `lowercase/`
- **Tests:** `test_module_name.py`

### Classes

- **Classes:** `PascalCase`
- **Auditeurs:** `[Name]Auditor`
- **Managers:** `[Name]Manager`
- **Reporters:** `[Name]Reporter`
- **Models:** `[Name]` (ex: `LDAPUser`, `AuditReport`)

### Fonctions et Méthodes

- **Publiques:** `snake_case()`
- **Privées:** `_snake_case()`
- **Très privées:** `__snake_case()` (name mangling)
- **Properties:** `@property def snake_case()`

### Variables et Constantes

- **Variables:** `snake_case`
- **Constantes:** `UPPER_SNAKE_CASE`
- **Privées:** `_snake_case`

### Exemples

```python
# Constantes
DEFAULT_PORT = 389
MAX_RETRY_ATTEMPTS = 3

# Classes
class UserAuditor:
    pass

class LDAPConfig(BaseModel):
    pass

# Fonctions
def load_config(path: str) -> Config:
    pass

def _validate_credentials() -> bool:
    pass

# Variables
user_count = 100
_internal_cache = {}
```

## Structure de Test

```python
"""Tests pour [module]."""

import pytest
from src.core.models import Config
from src.audit.users import UserAuditor


class TestUserAuditor:
    """Tests pour UserAuditor."""

    def test_audit_users_with_valid_data(self, sample_config, mock_ldap_connector):
        """Test avec données valides."""
        auditor = UserAuditor(mock_ldap_connector, sample_config)
        issues = auditor.audit_users()
        assert isinstance(issues, list)

    def test_audit_users_with_inactive_users(self, sample_config, mock_ldap_connector):
        """Test détection utilisateurs inactifs."""
        # Setup mock
        # Execute
        # Assert

    @pytest.mark.parametrize("inactive_days,expected_issues", [
        (30, 0),
        (90, 1),
        (365, 5),
    ])
    def test_inactive_thresholds(self, inactive_days, expected_issues):
        """Test des différents seuils d'inactivité."""
        pass
```

## Bonnes Pratiques

### 1. Un Fichier, Une Responsabilité

Chaque fichier doit avoir une responsabilité claire et unique.

### 2. Taille des Fichiers

- **Idéal:** 200-400 lignes
- **Maximum:** 1000 lignes
- Si plus grand, envisager de découper

### 3. Documentation

Chaque module doit avoir:
- Docstring de module en haut
- Docstrings pour toutes les classes publiques
- Docstrings pour toutes les fonctions publiques

### 4. Organisation Interne

Structure recommandée pour un fichier:
1. Docstring de module
2. Imports (stdlib, third-party, local)
3. Constantes
4. Classes/Fonctions (ordre logique)
5. Code exécutable (si __main__)

### 5. Exports Explicites

```python
# Dans __init__.py
__all__ = [
    "ClassName",
    "function_name",
]
```

## Conclusion

Cette structure modulaire permet:
- Navigation facile dans le code
- Découplage des responsabilités
- Facilité de test
- Facilité d'extension
- Maintenabilité à long terme
