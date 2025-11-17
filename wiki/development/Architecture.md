# Architecture du LDAP Health Monitor

## Vue d'ensemble

Le LDAP Health Monitor est une application CLI construite avec Python qui suit une architecture modulaire et extensible basée sur le principe de séparation des responsabilités (Separation of Concerns). L'application est organisée en plusieurs couches distinctes, chacune ayant un rôle spécifique.

## Architecture Globale

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Interface                            │
│                        (src/cli.py)                              │
│                    Point d'entrée Click                          │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Configuration Layer                         │
│                    (src/core/config.py)                          │
│          Gestion de la configuration et validation               │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Core Layer                                │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐│
│  │   Connector      │  │     Models       │  │    Config      ││
│  │  (connector.py)  │  │   (models.py)    │  │  (config.py)   ││
│  │  Connexion LDAP  │  │ Modèles Pydantic │  │   Validation   ││
│  └──────────────────┘  └──────────────────┘  └────────────────┘│
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┬────────────┐
        │            │            │            │
        ▼            ▼            ▼            ▼
┌─────────────┐ ┌─────────┐ ┌──────────┐ ┌──────────┐
│   Audit     │ │ Monitor │ │  Manage  │ │ Reporter │
│   Module    │ │ Module  │ │  Module  │ │  Module  │
└─────────────┘ └─────────┘ └──────────┘ └──────────┘
│             │ │         │ │          │ │          │
│ • health    │ │• daemon │ │• users   │ │• console │
│ • users     │ │• metrics│ │• groups  │ │• json    │
│ • groups    │ │• alerts │ │• backup  │ │• html    │
│ • security  │ │         │ │• cleanup │ │• csv     │
│ • structure │ │         │ │          │ │• prom    │
│ • consisten │ │         │ │          │ │          │
└─────────────┘ └─────────┘ └──────────┘ └──────────┘
```

## Couches Architecturales

### 1. CLI Layer (Interface en Ligne de Commande)

La couche CLI est le point d'entrée de l'application, construite avec Click, un framework Python pour créer des interfaces en ligne de commande élégantes.

**Responsabilités:**
- Parser les arguments et options de ligne de commande
- Router les commandes vers les modules appropriés
- Gérer l'affichage des erreurs et des résultats
- Coordonner le flux d'exécution

**Exemple:**
```python
@cli.group()
@click.option("--config", "-c", help="Path to configuration file")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx: click.Context, config: Optional[str], verbose: bool) -> None:
    """LDAP Health Monitor - Audit, monitor, and manage LDAP servers."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config
    ctx.obj["verbose"] = verbose
```

### 2. Core Layer (Couche Noyau)

La couche noyau contient les composants fondamentaux de l'application.

#### 2.1 Connector (src/core/connector.py)

Gère toutes les interactions avec le serveur LDAP via la bibliothèque `ldap3`.

**Fonctionnalités:**
- Établissement de connexions LDAP/LDAPS
- Recherches LDAP avec pagination
- Opérations CRUD (Create, Read, Update, Delete)
- Gestion automatique des reconnexions
- Support du retry avec backoff exponentiel

**Exemple:**
```python
class LDAPConnector:
    def __init__(self, config: LDAPConfig) -> None:
        self.config = config
        self._server: Optional[Server] = None
        self._connection: Optional[Connection] = None

    def connect(self) -> Connection:
        """Établit une connexion au serveur LDAP avec retry."""
        last_exception = None
        for attempt in range(self.config.retry_max):
            try:
                self._connection = Connection(
                    self._server,
                    user=self.config.bind_dn,
                    password=self.config.bind_password,
                    auto_bind=True,
                    raise_exceptions=True,
                )
                return self._connection
            except LDAPException as e:
                last_exception = e
                if attempt < self.config.retry_max - 1:
                    time.sleep(self.config.retry_delay * (attempt + 1))
        raise LDAPException(f"Échec après {self.config.retry_max} tentatives")
```

#### 2.2 Models (src/core/models.py)

Définit tous les modèles de données en utilisant Pydantic pour la validation et la sérialisation.

**Types de modèles:**
- **Configuration Models:** `LDAPConfig`, `AuditConfig`, `MonitoringConfig`
- **Data Models:** `LDAPUser`, `LDAPGroup`
- **Result Models:** `HealthCheckResult`, `AuditIssue`, `AuditReport`
- **Monitoring Models:** `Metric`, `Alert`

**Exemple:**
```python
class LDAPUser(BaseModel):
    """Modèle représentant un utilisateur LDAP."""
    dn: str
    uid: str
    cn: str
    sn: str
    mail: Optional[str] = None
    status: ObjectStatus = ObjectStatus.UNKNOWN
    created: Optional[datetime] = None
    modified: Optional[datetime] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
```

#### 2.3 Config (src/core/config.py)

Gère le chargement, la validation et la substitution de variables d'environnement dans la configuration.

**Fonctionnalités:**
- Recherche automatique du fichier de configuration
- Chargement YAML avec validation Pydantic
- Substitution de variables d'environnement `${VAR}` ou `$VAR`
- Validation des répertoires et permissions
- Génération de fichiers de configuration

**Exemple:**
```python
class ConfigManager:
    def load(self, config_path: Optional[str] = None) -> Config:
        """Charge et valide la configuration."""
        load_dotenv()

        if not self.config_path:
            raise FileNotFoundError("Aucun fichier de configuration trouvé")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self._raw_config = yaml.safe_load(f) or {}

        # Remplace les variables d'environnement
        self._raw_config = self._replace_env_vars(self._raw_config)

        # Valide et crée l'objet Config
        self._config = Config(**self._raw_config)
        return self._config
```

### 3. Audit Module (src/audit/)

Le module d'audit est responsable de l'inspection et de l'analyse de l'état du serveur LDAP.

**Composants:**
- `health.py` - Vérification de santé du serveur
- `users.py` - Audit des utilisateurs
- `groups.py` - Audit des groupes
- `security.py` - Audit de sécurité
- `structure.py` - Audit de la structure
- `consistency.py` - Audit de cohérence

**Pattern d'implémentation:**
```python
class UserAuditor:
    def __init__(self, connector: LDAPConnector, config: Config):
        self.connector = connector
        self.config = config

    def audit_users(self, check_inactive: bool = True,
                   check_attributes: bool = True) -> List[AuditIssue]:
        """Effectue l'audit complet des utilisateurs."""
        issues: List[AuditIssue] = []

        if check_inactive:
            issues.extend(self._check_inactive_users())

        if check_attributes:
            issues.extend(self._check_missing_attributes())

        return issues
```

### 4. Monitor Module (src/monitor/)

Le module de surveillance collecte des métriques et gère les alertes.

**Composants:**
- `daemon.py` - Service de surveillance en arrière-plan
- `metrics.py` - Collecte de métriques
- `alerts.py` - Gestion des alertes

**Architecture des métriques:**
```python
class MetricsCollector:
    def __init__(self, connector: LDAPConnector, config: Config):
        self.connector = connector
        self.config = config
        self.registry = CollectorRegistry()
        self._init_metrics()

    def collect_all_metrics(self) -> List[Metric]:
        """Collecte toutes les métriques configurées."""
        metrics = []

        for metric_name in self.config.monitoring.metrics:
            collector = self._get_collector(metric_name)
            if collector:
                metrics.append(collector())

        return metrics
```

### 5. Manage Module (src/manage/)

Le module de gestion permet d'effectuer des opérations sur le serveur LDAP.

**Composants:**
- `users.py` - Gestion des utilisateurs
- `groups.py` - Gestion des groupes
- `backup.py` - Sauvegarde et export
- `cleanup.py` - Nettoyage et maintenance

**Pattern CRUD:**
```python
class UserManager:
    def __init__(self, connector: LDAPConnector, config: Config):
        self.connector = connector
        self.config = config

    def create_user(self, user_data: Dict[str, Any]) -> LDAPUser:
        """Crée un nouvel utilisateur."""
        # Validation
        # Construction du DN
        # Ajout dans LDAP
        # Retour du modèle
        pass

    def get_user(self, dn: str) -> Optional[LDAPUser]:
        """Récupère un utilisateur par son DN."""
        pass

    def update_user(self, dn: str, changes: Dict[str, Any]) -> bool:
        """Met à jour un utilisateur."""
        pass

    def delete_user(self, dn: str) -> bool:
        """Supprime un utilisateur."""
        pass
```

### 6. Reporter Module (src/reporters/)

Le module de reporting génère des rapports dans différents formats.

**Composants:**
- `console.py` - Affichage console avec Rich
- `json.py` - Export JSON
- `html.py` - Rapports HTML
- `csv.py` - Export CSV
- `prometheus.py` - Métriques Prometheus

**Interface commune:**
```python
class BaseReporter(ABC):
    """Interface de base pour tous les reporters."""

    @abstractmethod
    def report_health(self, health: HealthCheckResult) -> None:
        """Génère un rapport de santé."""
        pass

    @abstractmethod
    def report_audit(self, report: AuditReport) -> None:
        """Génère un rapport d'audit."""
        pass
```

## Patterns de Conception

### 1. Dependency Injection

Tous les modules reçoivent leurs dépendances via le constructeur :

```python
class HealthChecker:
    def __init__(self, connector: LDAPConnector, config: Config):
        self.connector = connector  # Injection de la connexion LDAP
        self.config = config        # Injection de la configuration
```

**Avantages:**
- Facilite les tests unitaires (injection de mocks)
- Réduit le couplage
- Améliore la lisibilité

### 2. Context Manager

Le connecteur LDAP supporte le protocole de context manager :

```python
with LDAPConnector(config.ldap) as conn:
    users = conn.search(
        search_base=config.ldap.users_ou,
        search_filter="(objectClass=inetOrgPerson)"
    )
# Connexion automatiquement fermée
```

### 3. Factory Pattern

Le ConfigManager utilise un pattern factory pour créer les instances :

```python
_config_manager: Optional[ConfigManager] = None

def get_config_manager() -> ConfigManager:
    """Retourne l'instance singleton du gestionnaire de configuration."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager
```

### 4. Strategy Pattern

Les reporters utilisent le pattern Strategy pour permettre différents formats de sortie :

```python
def output_report(report: AuditReport, format: str):
    reporters = {
        "console": ConsoleReporter(),
        "json": JSONReporter(),
        "html": HTMLReporter(),
        "csv": CSVReporter(),
    }

    reporter = reporters.get(format)
    if reporter:
        reporter.report_audit(report)
```

### 5. Builder Pattern

Les audits utilisent un pattern builder pour construire progressivement les rapports :

```python
report = AuditReport(
    timestamp=datetime.now(),
    health=health_checker.check_health(),
    issues=[],
    statistics={},
)

# Ajoute progressivement les issues
report.issues.extend(user_auditor.audit_users())
report.issues.extend(group_auditor.audit_groups())
report.issues.extend(security_auditor.audit_security())

# Calcule le score final
report.score = max(0, 100 - len(report.issues) * 5)
```

## Flux de Données

### Flux d'Audit Complet

```
1. Utilisateur exécute: ldap-monitor audit all

2. CLI Layer
   └─> Parse arguments
   └─> Charge configuration via ConfigManager
   └─> Crée LDAPConnector

3. Core Layer
   └─> LDAPConnector.connect()
   └─> Valide connexion

4. Audit Layer
   └─> HealthChecker.check_health()
       ├─> Test connexion
       ├─> Vérifie temps de réponse
       ├─> Vérifie certificat SSL
       └─> Collecte statistiques

   └─> UserAuditor.audit_users()
       ├─> Recherche tous les utilisateurs
       ├─> Vérifie utilisateurs inactifs
       ├─> Vérifie attributs manquants
       └─> Retourne liste d'AuditIssue

   └─> GroupAuditor.audit_groups()
       ├─> Recherche tous les groupes
       ├─> Vérifie groupes vides
       ├─> Vérifie groupes trop grands
       └─> Retourne liste d'AuditIssue

   └─> SecurityAuditor.audit_security()
   └─> StructureAuditor.audit_structure()
   └─> ConsistencyAuditor.audit_consistency()

5. Aggregation
   └─> Construction de AuditReport
       ├─> Timestamp
       ├─> HealthCheckResult
       ├─> Liste complète d'AuditIssue
       ├─> Statistiques
       └─> Score calculé

6. Reporter Layer
   └─> ConsoleReporter.report_audit()
       ├─> Formate avec Rich
       ├─> Groupe par catégorie
       ├─> Affiche statistiques
       └─> Affiche recommandations

7. CLI Layer
   └─> Affiche résultat
   └─> Retourne code de sortie
```

### Flux de Surveillance Continue

```
1. Utilisateur exécute: ldap-monitor monitor start --daemon

2. CLI Layer
   └─> Parse arguments
   └─> Charge configuration

3. Monitor Layer
   └─> MonitoringDaemon.start(daemon=True)
       │
       ├─> Initialise MetricsCollector
       ├─> Initialise AlertManager
       │
       └─> Boucle infinie
           │
           ├─> MetricsCollector.collect_all_metrics()
           │   ├─> Compte utilisateurs
           │   ├─> Compte groupes
           │   ├─> Mesure temps de réponse
           │   ├─> Vérifie échecs d'auth
           │   └─> Stocke métriques
           │
           ├─> Évalue seuils d'alerte
           │
           ├─> AlertManager.check_alerts()
           │   ├─> Compare métriques aux seuils
           │   └─> Si seuil dépassé:
           │       ├─> Crée Alert
           │       └─> Envoie notifications
           │           ├─> Slack
           │           ├─> Email
           │           └─> Webhook
           │
           └─> Sleep(config.monitoring.interval)
```

## Gestion des Erreurs

### Hiérarchie d'Exceptions

```python
LDAPException (ldap3)
├─> ConnectionError
├─> AuthenticationError
└─> SearchError

ApplicationError (custom)
├─> ConfigurationError
├─> ValidationError
└─> AuditError
```

### Stratégie de Gestion

**Au niveau Connector:**
```python
def search(self, search_base: str, search_filter: str) -> List[Dict]:
    try:
        conn = self.connect()
        conn.search(search_base, search_filter, attributes=ALL_ATTRIBUTES)
        return [self._entry_to_dict(e) for e in conn.entries]
    except LDAPException as e:
        raise LDAPException(f"Échec de recherche: {e}") from e
```

**Au niveau Audit:**
```python
def audit_users(self) -> List[AuditIssue]:
    issues: List[AuditIssue] = []

    try:
        # Logique d'audit
        pass
    except LDAPException as e:
        # Convertit en AuditIssue plutôt que de lever une exception
        issues.append(
            AuditIssue(
                level=AlertLevel.CRITICAL,
                category="audit",
                title="Échec de l'audit utilisateurs",
                description=str(e),
                recommendation="Vérifier la connexion LDAP"
            )
        )

    return issues
```

**Au niveau CLI:**
```python
@audit.command("all")
def audit_all(ctx: click.Context):
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        # ... logique ...
    except Exception as e:
        click.echo(f"❌ Erreur: {e}", err=True)
        sys.exit(1)
```

## Sécurité

### Gestion des Credentials

**Meilleures pratiques:**
1. Ne jamais stocker de mots de passe en clair dans le code
2. Utiliser des variables d'environnement
3. Supporter `.env` files
4. Valider les permissions des fichiers de configuration

```python
# Dans config.yaml
ldap:
  bind_dn: "cn=admin,dc=example,dc=com"
  bind_password: "${LDAP_BIND_PASSWORD}"  # Depuis env var

# Ou dans .env
LDAP_BIND_PASSWORD=secret_password
```

### Validation SSL/TLS

```python
if self.config.use_tls:
    tls_config = Tls(
        validate=ssl.CERT_REQUIRED,  # En production
        ca_certs_file="/path/to/ca.crt",
        version=ssl.PROTOCOL_TLSv1_2
    )
```

### Sanitization des Inputs

```python
def search_users(self, query: str) -> List[LDAPUser]:
    # Échappe les caractères spéciaux LDAP
    safe_query = escape_filter_chars(query)
    search_filter = f"(uid={safe_query})"
    # ...
```

## Performance

### Optimisations Implémentées

**1. Pagination des Résultats**
```python
def search(self, paged: bool = True) -> List[Dict]:
    if paged:
        conn.search(
            search_base=base,
            search_filter=search_filter,
            paged_size=self.config.page_size  # 1000 par défaut
        )
```

**2. Caching de Connexions**
```python
def connect(self) -> Connection:
    if self._connection and self._connection.bound:
        return self._connection  # Réutilise la connexion existante
    # ... établit nouvelle connexion
```

**3. Sélection d'Attributs**
```python
# Mauvais - récupère tous les attributs
users = connector.search(attributes=ALL_ATTRIBUTES)

# Bon - ne récupère que ce qui est nécessaire
users = connector.search(attributes=["dn", "uid", "mail"])
```

**4. Batch Operations**
```python
class ManagementConfig(BaseModel):
    batch_size: int = 100      # Traite par lots
    batch_delay: int = 1       # Pause entre lots (secondes)
```

## Tests

### Architecture de Test

```
tests/
├── unit/              # Tests unitaires isolés
│   ├── test_config.py
│   ├── test_models.py
│   └── test_connector.py
├── integration/       # Tests d'intégration
│   ├── test_audit.py
│   └── test_monitor.py
└── conftest.py       # Fixtures partagées
```

### Fixtures Principales

```python
@pytest.fixture
def sample_config() -> Config:
    """Configuration de test."""
    return Config(ldap=LDAPConfig(...))

@pytest.fixture
def mock_ldap_connector(mocker):
    """Mock du connecteur LDAP."""
    mock = mocker.Mock(spec=LDAPConnector)
    mock.test_connection.return_value = (True, 100.0, None)
    return mock
```

## Extensibilité

### Ajouter un Nouveau Module d'Audit

1. Créer `src/audit/custom.py`
2. Implémenter la classe avec signature standard
3. Retourner `List[AuditIssue]`
4. Enregistrer dans `audit_all()` du CLI

### Ajouter un Nouveau Format de Reporter

1. Créer `src/reporters/custom.py`
2. Hériter de `BaseReporter` ou implémenter l'interface
3. Implémenter `report_health()` et `report_audit()`
4. Ajouter au mapping dans le CLI

## Bonnes Pratiques

1. **Type Hints**: Utiliser partout pour la clarté et la validation IDE
2. **Docstrings**: Format Google style pour toutes les fonctions publiques
3. **Logging**: Utiliser le module logging, pas print()
4. **Configuration**: Tout doit être configurable, rien de hard-codé
5. **Validation**: Utiliser Pydantic pour valider toutes les données
6. **Immutabilité**: Privilégier les structures immuables quand possible
7. **Context Managers**: Pour les ressources qui doivent être nettoyées
8. **Error Handling**: Gérer gracieusement, ne jamais exposer de stack traces à l'utilisateur

## Conclusion

Cette architecture modulaire permet:
- **Maintenabilité**: Code organisé et facile à comprendre
- **Testabilité**: Composants découplés et injectables
- **Extensibilité**: Facile d'ajouter de nouvelles fonctionnalités
- **Réutilisabilité**: Modules indépendants réutilisables
- **Scalabilité**: Performance optimisée pour grandes installations LDAP
