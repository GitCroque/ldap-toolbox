# Guide de Testing

## Introduction

Le testing est une partie essentielle du développement de LDAP Health Monitor. Ce guide couvre la stratégie de test, les bonnes pratiques, et comment écrire des tests efficaces.

## Philosophie de Test

### Pyramide de Tests

```
            /\
           /  \
          / E2E\          ← Peu de tests end-to-end
         /------\
        /        \
       /Integration\      ← Tests d'intégration modérés
      /------------\
     /              \
    /   Unit Tests   \    ← Beaucoup de tests unitaires
   /------------------\
```

**Distribution recommandée:**
- **70%** Tests unitaires
- **20%** Tests d'intégration
- **10%** Tests end-to-end

## Architecture de Test

### Structure des Répertoires

```
tests/
├── __init__.py
├── conftest.py                 # Fixtures pytest globales
│
├── unit/                       # Tests unitaires
│   ├── __init__.py
│   ├── test_config.py         # Tests configuration
│   ├── test_models.py         # Tests modèles Pydantic
│   ├── test_connector.py      # Tests connecteur LDAP
│   ├── test_health_audit.py   # Tests audit santé
│   ├── test_user_audit.py     # Tests audit utilisateurs
│   └── ...
│
├── integration/                # Tests d'intégration
│   ├── __init__.py
│   ├── test_full_audit.py     # Test audit complet
│   ├── test_monitoring.py     # Test monitoring
│   └── test_cli.py            # Test commandes CLI
│
├── fixtures/                   # Données de test
│   ├── sample_config.yaml
│   ├── mock_ldap_data.json
│   └── expected_reports/
│
└── helpers/                    # Utilitaires de test
    ├── __init__.py
    ├── ldap_mock.py           # Mock serveur LDAP
    └── assertions.py           # Assertions personnalisées
```

## Configuration Pytest

### pyproject.toml

```toml
[tool.pytest.ini_options]
minversion = "7.0"
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]

# Options par défaut
addopts = [
    "-v",                          # Verbose
    "--strict-markers",            # Markers stricts
    "--tb=short",                  # Traceback court
    "--cov=src",                   # Couverture du code source
    "--cov-report=html",           # Rapport HTML
    "--cov-report=term-missing",   # Afficher lignes manquantes
    "--cov-fail-under=80",         # Échec si couverture < 80%
]

# Markers personnalisés
markers = [
    "unit: Unit tests",
    "integration: Integration tests",
    "slow: Slow tests",
    "ldap: Tests requiring LDAP server",
]

# Timeout par défaut
timeout = 300

[tool.coverage.run]
source = ["src"]
omit = [
    "*/tests/*",
    "*/test_*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

## Fixtures Pytest

### conftest.py Global

```python
"""Fixtures pytest globales."""

import pytest
from pathlib import Path
from typing import Dict, Any

from src.core.models import (
    Config,
    LDAPConfig,
    AuditConfig,
    MonitoringConfig,
)


@pytest.fixture
def sample_config() -> Config:
    """Configuration complète pour les tests.

    Returns:
        Configuration de test valide
    """
    ldap_config = LDAPConfig(
        server="ldap.test.com",
        port=389,
        use_ssl=False,
        use_tls=False,
        bind_dn="cn=admin,dc=test,dc=com",
        bind_password="test_password",
        base_dn="dc=test,dc=com",
        users_ou="ou=users,dc=test,dc=com",
        groups_ou="ou=groups,dc=test,dc=com",
    )

    audit_config = AuditConfig(
        checks=["health", "users", "groups"],
        thresholds={
            "response_time_warning_ms": 500,
            "response_time_critical_ms": 2000,
            "inactive_users_days": 90,
            "large_group_size": 1000,
        },
    )

    return Config(ldap=ldap_config, audit=audit_config)


@pytest.fixture
def mock_ldap_connector(mocker):
    """Mock du connecteur LDAP.

    Args:
        mocker: Fixture pytest-mock

    Returns:
        Mock de LDAPConnector
    """
    from src.core.connector import LDAPConnector

    mock = mocker.Mock(spec=LDAPConnector)

    # Comportement par défaut
    mock.test_connection.return_value = (True, 100.0, None)
    mock.connect.return_value = mocker.Mock()
    mock.disconnect.return_value = None

    return mock


@pytest.fixture
def sample_ldap_users() -> list[Dict[str, Any]]:
    """Liste d'utilisateurs LDAP de test.

    Returns:
        Liste de dictionnaires représentant des utilisateurs
    """
    return [
        {
            "dn": "uid=jdoe,ou=users,dc=test,dc=com",
            "attributes": {
                "uid": "jdoe",
                "cn": "John Doe",
                "sn": "Doe",
                "mail": "john.doe@test.com",
                "userPassword": "{SSHA}hashedpassword",
            }
        },
        {
            "dn": "uid=asmith,ou=users,dc=test,dc=com",
            "attributes": {
                "uid": "asmith",
                "cn": "Alice Smith",
                "sn": "Smith",
                "mail": "alice.smith@test.com",
            }
        },
    ]


@pytest.fixture
def sample_ldap_groups() -> list[Dict[str, Any]]:
    """Liste de groupes LDAP de test.

    Returns:
        Liste de dictionnaires représentant des groupes
    """
    return [
        {
            "dn": "cn=developers,ou=groups,dc=test,dc=com",
            "attributes": {
                "cn": "developers",
                "member": [
                    "uid=jdoe,ou=users,dc=test,dc=com",
                    "uid=asmith,ou=users,dc=test,dc=com",
                ],
            }
        },
        {
            "dn": "cn=empty-group,ou=groups,dc=test,dc=com",
            "attributes": {
                "cn": "empty-group",
                "member": [],
            }
        },
    ]


@pytest.fixture
def temp_config_file(tmp_path, sample_config):
    """Crée un fichier de configuration temporaire.

    Args:
        tmp_path: Répertoire temporaire pytest
        sample_config: Configuration de test

    Returns:
        Path vers le fichier de configuration
    """
    import yaml

    config_file = tmp_path / "test_config.yaml"
    with open(config_file, "w") as f:
        yaml.dump(sample_config.model_dump(), f)

    return config_file
```

## Tests Unitaires

### Exemple: Tests de Modèles

```python
"""Tests pour les modèles Pydantic."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from src.core.models import (
    LDAPConfig,
    LDAPUser,
    AuditIssue,
    AlertLevel,
    CheckStatus,
)


class TestLDAPConfig:
    """Tests pour LDAPConfig."""

    def test_valid_config(self):
        """Test création d'une config valide."""
        config = LDAPConfig(
            server="ldap.example.com",
            port=389,
            bind_dn="cn=admin,dc=example,dc=com",
            bind_password="password",
            base_dn="dc=example,dc=com",
            users_ou="ou=users,dc=example,dc=com",
            groups_ou="ou=groups,dc=example,dc=com",
        )

        assert config.server == "ldap.example.com"
        assert config.port == 389
        assert config.use_ssl is True  # Valeur par défaut

    def test_missing_required_fields(self):
        """Test validation avec champs requis manquants."""
        with pytest.raises(ValidationError) as exc_info:
            LDAPConfig(server="ldap.example.com")

        errors = exc_info.value.errors()
        error_fields = [e["loc"][0] for e in errors]

        assert "bind_dn" in error_fields
        assert "bind_password" in error_fields
        assert "base_dn" in error_fields

    def test_port_validation(self):
        """Test validation du port."""
        # Port valide
        config = LDAPConfig(
            server="ldap.example.com",
            port=636,
            bind_dn="cn=admin,dc=example,dc=com",
            bind_password="password",
            base_dn="dc=example,dc=com",
            users_ou="ou=users,dc=example,dc=com",
            groups_ou="ou=groups,dc=example,dc=com",
        )
        assert config.port == 636

    def test_default_values(self):
        """Test valeurs par défaut."""
        config = LDAPConfig(
            server="ldap.example.com",
            bind_dn="cn=admin,dc=example,dc=com",
            bind_password="password",
            base_dn="dc=example,dc=com",
            users_ou="ou=users,dc=example,dc=com",
            groups_ou="ou=groups,dc=example,dc=com",
        )

        assert config.port == 389
        assert config.use_ssl is True
        assert config.timeout == 10
        assert config.retry_max == 3


class TestLDAPUser:
    """Tests pour LDAPUser."""

    def test_create_user(self):
        """Test création d'un utilisateur."""
        user = LDAPUser(
            dn="uid=jdoe,ou=users,dc=example,dc=com",
            uid="jdoe",
            cn="John Doe",
            sn="Doe",
            mail="john.doe@example.com",
        )

        assert user.uid == "jdoe"
        assert user.cn == "John Doe"
        assert user.mail == "john.doe@example.com"

    def test_optional_fields(self):
        """Test champs optionnels."""
        user = LDAPUser(
            dn="uid=jdoe,ou=users,dc=example,dc=com",
            uid="jdoe",
            cn="John Doe",
            sn="Doe",
        )

        assert user.mail is None
        assert user.created is None

    def test_serialization(self):
        """Test sérialisation JSON."""
        user = LDAPUser(
            dn="uid=jdoe,ou=users,dc=example,dc=com",
            uid="jdoe",
            cn="John Doe",
            sn="Doe",
            mail="john.doe@example.com",
        )

        user_dict = user.model_dump()

        assert user_dict["uid"] == "jdoe"
        assert user_dict["mail"] == "john.doe@example.com"

        # Recréer depuis dict
        user2 = LDAPUser(**user_dict)
        assert user2.uid == user.uid


class TestAuditIssue:
    """Tests pour AuditIssue."""

    def test_create_issue(self):
        """Test création d'une issue."""
        issue = AuditIssue(
            level=AlertLevel.WARNING,
            category="users",
            title="Inactive user",
            description="User has been inactive for 90 days",
            recommendation="Review and disable if needed",
        )

        assert issue.level == AlertLevel.WARNING
        assert issue.category == "users"
        assert issue.title == "Inactive user"

    def test_issue_with_details(self):
        """Test issue avec détails."""
        issue = AuditIssue(
            level=AlertLevel.CRITICAL,
            category="security",
            title="Weak password",
            description="Password does not meet requirements",
            details={"uid": "jdoe", "strength": "weak"},
        )

        assert issue.details["uid"] == "jdoe"
        assert issue.details["strength"] == "weak"
```

### Exemple: Tests d'Auditeur

```python
"""Tests pour UserAuditor."""

import pytest
from datetime import datetime, timedelta

from src.audit.users import UserAuditor
from src.core.models import Config, AlertLevel


class TestUserAuditor:
    """Tests pour UserAuditor."""

    def test_initialization(self, sample_config, mock_ldap_connector):
        """Test initialisation de l'auditeur."""
        auditor = UserAuditor(mock_ldap_connector, sample_config)

        assert auditor.connector == mock_ldap_connector
        assert auditor.config == sample_config

    def test_audit_users_returns_list(self, sample_config, mock_ldap_connector):
        """Test que audit_users retourne une liste."""
        auditor = UserAuditor(mock_ldap_connector, sample_config)

        # Mock le retour de search
        mock_ldap_connector.search.return_value = []

        issues = auditor.audit_users()

        assert isinstance(issues, list)

    def test_audit_users_with_inactive_users(self, sample_config, mock_ldap_connector):
        """Test détection utilisateurs inactifs."""
        auditor = UserAuditor(mock_ldap_connector, sample_config)

        # Mock utilisateur inactif depuis 120 jours
        inactive_date = datetime.now() - timedelta(days=120)
        mock_ldap_connector.search.return_value = [
            {
                "dn": "uid=inactive,ou=users,dc=test,dc=com",
                "attributes": {
                    "uid": "inactive",
                    "cn": "Inactive User",
                    "sn": "User",
                    "modifyTimestamp": inactive_date.strftime("%Y%m%d%H%M%SZ"),
                }
            }
        ]

        issues = auditor.audit_users(check_inactive=True)

        # Devrait détecter l'utilisateur inactif
        inactive_issues = [i for i in issues if "inactive" in i.title.lower()]
        assert len(inactive_issues) > 0

    def test_audit_users_missing_attributes(self, sample_config, mock_ldap_connector):
        """Test détection attributs manquants."""
        auditor = UserAuditor(mock_ldap_connector, sample_config)

        # Mock utilisateur sans email
        mock_ldap_connector.search.return_value = [
            {
                "dn": "uid=nomail,ou=users,dc=test,dc=com",
                "attributes": {
                    "uid": "nomail",
                    "cn": "No Mail User",
                    "sn": "User",
                    # mail manquant
                }
            }
        ]

        issues = auditor.audit_users(check_attributes=True)

        # Devrait détecter l'attribut manquant
        missing_attr_issues = [i for i in issues if "missing" in i.title.lower()]
        assert len(missing_attr_issues) > 0

    @pytest.mark.parametrize("inactive_days,should_flag", [
        (30, False),   # Pas assez inactif
        (90, True),    # Juste au seuil
        (120, True),   # Au-dessus du seuil
        (365, True),   # Très inactif
    ])
    def test_inactive_threshold(
        self, inactive_days, should_flag, sample_config, mock_ldap_connector
    ):
        """Test différents seuils d'inactivité."""
        auditor = UserAuditor(mock_ldap_connector, sample_config)

        inactive_date = datetime.now() - timedelta(days=inactive_days)
        mock_ldap_connector.search.return_value = [
            {
                "dn": "uid=user,ou=users,dc=test,dc=com",
                "attributes": {
                    "uid": "user",
                    "cn": "Test User",
                    "sn": "User",
                    "modifyTimestamp": inactive_date.strftime("%Y%m%d%H%M%SZ"),
                }
            }
        ]

        issues = auditor.audit_users(check_inactive=True)

        inactive_issues = [i for i in issues if "inactive" in i.title.lower()]
        if should_flag:
            assert len(inactive_issues) > 0
        else:
            assert len(inactive_issues) == 0
```

## Tests d'Intégration

### Exemple: Test d'Audit Complet

```python
"""Tests d'intégration pour audit complet."""

import pytest
from click.testing import CliRunner

from src.cli import cli
from src.core.config import load_config
from src.core.connector import LDAPConnector


@pytest.mark.integration
class TestFullAudit:
    """Tests d'intégration pour audit complet."""

    def test_audit_all_command(self, temp_config_file, tmp_path):
        """Test de la commande audit all."""
        runner = CliRunner()

        output_file = tmp_path / "report.json"

        result = runner.invoke(
            cli,
            [
                "--config", str(temp_config_file),
                "audit", "all",
                "--format", "json",
                "--output", str(output_file)
            ]
        )

        # Note: Ce test échouera sans serveur LDAP
        # En pratique, on utiliserait un mock ou un serveur de test

        assert result.exit_code in [0, 1]  # 0 = success, 1 = issues trouvées

    @pytest.mark.ldap
    def test_audit_against_test_ldap(self):
        """Test contre un serveur LDAP de test.

        Nécessite:
        - Variable d'environnement TEST_LDAP_SERVER
        - Serveur LDAP de test accessible
        """
        import os

        if not os.getenv("TEST_LDAP_SERVER"):
            pytest.skip("TEST_LDAP_SERVER not configured")

        # Configuration depuis env
        config = load_config("config.test.yaml")
        connector = LDAPConnector(config.ldap)

        # Test de connexion
        success, response_time, error = connector.test_connection()
        assert success, f"Cannot connect to test LDAP: {error}"

        # Exécuter audit complet
        from src.audit.health import HealthChecker
        from src.audit.users import UserAuditor

        health_checker = HealthChecker(connector, config)
        user_auditor = UserAuditor(connector, config)

        health = health_checker.check_health()
        assert health.status in ["healthy", "warning", "critical"]

        issues = user_auditor.audit_users()
        assert isinstance(issues, list)
```

## Mocking

### Mock LDAP Connector

```python
"""Mock helper pour LDAPConnector."""

from typing import Dict, Any, List, Optional
from unittest.mock import Mock


class MockLDAPConnector:
    """Mock complet de LDAPConnector pour tests."""

    def __init__(self):
        """Initialise le mock avec données par défaut."""
        self.users: List[Dict[str, Any]] = []
        self.groups: List[Dict[str, Any]] = []
        self.connected = False

    def connect(self):
        """Simule connexion."""
        self.connected = True
        return Mock()

    def disconnect(self):
        """Simule déconnexion."""
        self.connected = False

    def test_connection(self):
        """Simule test de connexion."""
        return (True, 100.0, None)

    def search(
        self,
        search_base: str,
        search_filter: str,
        attributes: Optional[List[str]] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """Simule recherche LDAP."""
        if "ou=users" in search_base:
            return self.users
        elif "ou=groups" in search_base:
            return self.groups
        return []

    def get_entry(self, dn: str, attributes: Optional[List[str]] = None):
        """Simule récupération d'une entrée."""
        # Chercher dans users
        for user in self.users:
            if user["dn"] == dn:
                return user

        # Chercher dans groups
        for group in self.groups:
            if group["dn"] == dn:
                return group

        return None

    def add_user(self, user_data: Dict[str, Any]):
        """Ajoute un utilisateur au mock."""
        self.users.append(user_data)

    def add_group(self, group_data: Dict[str, Any]):
        """Ajoute un groupe au mock."""
        self.groups.append(group_data)
```

**Utilisation:**

```python
def test_with_mock_connector():
    """Test utilisant le mock connector."""
    mock = MockLDAPConnector()

    # Ajouter des données de test
    mock.add_user({
        "dn": "uid=jdoe,ou=users,dc=test,dc=com",
        "attributes": {
            "uid": "jdoe",
            "cn": "John Doe",
            "mail": "john@test.com"
        }
    })

    # Utiliser dans l'auditeur
    auditor = UserAuditor(mock, config)
    issues = auditor.audit_users()

    assert isinstance(issues, list)
```

## Couverture de Code

### Générer un Rapport de Couverture

```bash
# Exécuter tests avec couverture
pytest --cov=src --cov-report=html --cov-report=term

# Ouvrir le rapport HTML
open htmlcov/index.html
```

### Interpréter la Couverture

**Objectifs:**
- **Global:** ≥ 80%
- **Core modules:** ≥ 90%
- **Utils:** ≥ 85%
- **CLI:** ≥ 70%

**Améliorer la couverture:**

```python
# Ajouter tests pour branches non couvertes
def function_with_branches(value):
    if value > 10:  # Branche 1
        return "high"
    elif value > 5:  # Branche 2
        return "medium"
    else:  # Branche 3
        return "low"

# Tests pour couvrir toutes les branches
@pytest.mark.parametrize("value,expected", [
    (15, "high"),    # Couvre branche 1
    (7, "medium"),   # Couvre branche 2
    (3, "low"),      # Couvre branche 3
])
def test_all_branches(value, expected):
    assert function_with_branches(value) == expected
```

## Tests Paramétrés

### Utiliser pytest.mark.parametrize

```python
@pytest.mark.parametrize("port,expected_valid", [
    (389, True),      # Port LDAP standard
    (636, True),      # Port LDAPS standard
    (1, True),        # Port minimum valide
    (65535, True),    # Port maximum valide
    (0, False),       # Port invalide
    (65536, False),   # Port trop grand
    (-1, False),      # Port négatif
])
def test_port_validation(port, expected_valid):
    """Test validation du port avec différentes valeurs."""
    if expected_valid:
        config = LDAPConfig(
            server="ldap.test.com",
            port=port,
            bind_dn="cn=admin,dc=test,dc=com",
            bind_password="password",
            base_dn="dc=test,dc=com",
            users_ou="ou=users,dc=test,dc=com",
            groups_ou="ou=groups,dc=test,dc=com",
        )
        assert config.port == port
    else:
        with pytest.raises(ValidationError):
            LDAPConfig(
                server="ldap.test.com",
                port=port,
                # ... autres champs
            )
```

## Bonnes Pratiques

### 1. AAA Pattern (Arrange, Act, Assert)

```python
def test_user_creation():
    # Arrange - Préparer les données
    user_data = {
        "uid": "jdoe",
        "cn": "John Doe",
        "sn": "Doe"
    }

    # Act - Exécuter l'action
    user = LDAPUser(**user_data, dn="uid=jdoe,ou=users,dc=test,dc=com")

    # Assert - Vérifier le résultat
    assert user.uid == "jdoe"
    assert user.cn == "John Doe"
```

### 2. Un Test, Une Assertion Principale

```python
# Bon
def test_user_has_correct_uid():
    user = create_test_user()
    assert user.uid == "jdoe"

def test_user_has_correct_cn():
    user = create_test_user()
    assert user.cn == "John Doe"

# Moins bon - trop d'assertions
def test_user():
    user = create_test_user()
    assert user.uid == "jdoe"
    assert user.cn == "John Doe"
    assert user.mail == "john@test.com"
    # Si la première échoue, on ne sait pas si les autres passent
```

### 3. Noms de Tests Descriptifs

```python
# Bon
def test_audit_detects_inactive_user_after_90_days():
    pass

def test_config_validation_fails_when_missing_bind_dn():
    pass

# Moins bon
def test_audit():
    pass

def test_config():
    pass
```

### 4. Utiliser Fixtures pour DRY

```python
@pytest.fixture
def inactive_user():
    """Utilisateur inactif pour tests."""
    return {
        "dn": "uid=inactive,ou=users,dc=test,dc=com",
        "attributes": {
            "uid": "inactive",
            "lastLogon": (datetime.now() - timedelta(days=120)).isoformat()
        }
    }

def test_inactive_detection(inactive_user):
    # Utilise la fixture
    assert is_inactive(inactive_user)

def test_inactive_recommendation(inactive_user):
    # Réutilise la même fixture
    assert get_recommendation(inactive_user) == "Disable account"
```

### 5. Tests Isolés

```python
# Chaque test doit être indépendant

# Mauvais - dépend d'un état global
counter = 0

def test_increment():
    global counter
    counter += 1
    assert counter == 1

def test_increment_again():
    global counter
    counter += 1
    assert counter == 2  # Échouera si exécuté seul!

# Bon - tests isolés
def test_increment():
    counter = 0
    counter += 1
    assert counter == 1

def test_increment_again():
    counter = 0
    counter += 1
    assert counter == 1
```

## Commandes Utiles

```bash
# Exécuter tous les tests
pytest

# Tests unitaires seulement
pytest tests/unit/

# Tests d'intégration seulement
pytest tests/integration/

# Avec verbosité
pytest -v

# Tests spécifiques
pytest tests/unit/test_config.py
pytest tests/unit/test_config.py::TestLDAPConfig::test_valid_config

# Avec couverture
pytest --cov=src --cov-report=html

# Tests marqués
pytest -m unit
pytest -m integration
pytest -m "not slow"

# Arrêter au premier échec
pytest -x

# Afficher print statements
pytest -s

# Tests en parallèle (nécessite pytest-xdist)
pytest -n auto

# Mode watch (nécessite pytest-watch)
ptw
```

## Conclusion

Un bon testing garantit:
- **Fiabilité**: Code qui fonctionne
- **Confiance**: Déployer sans crainte
- **Documentation**: Tests comme exemples
- **Refactoring**: Changer sans casser
- **Qualité**: Code maintenable

Écrivez des tests, toujours!
