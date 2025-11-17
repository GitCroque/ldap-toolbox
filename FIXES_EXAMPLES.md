# 🔧 Exemples de code pour les corrections

Ce document fournit des exemples concrets de code pour implémenter les corrections recommandées dans l'audit.

---

## 🔴 1. Correction validation TLS (CRITIQUE)

### Modifications dans `src/core/models.py`

```python
class LDAPConfig(BaseModel):
    """LDAP connection configuration."""

    server: str
    port: int = 389
    use_ssl: bool = True
    use_tls: bool = True
    
    # 🆕 NOUVEAUX PARAMÈTRES
    tls_validate: bool = True  # Activer validation par défaut
    ca_bundle_path: Optional[str] = None  # Chemin vers bundle CA personnalisé
    tls_version: str = "TLSv1.2"  # Version TLS minimum
    
    bind_dn: str
    bind_password: str
    base_dn: str
    # ... reste inchangé
```

### Modifications dans `src/core/connector.py`

```python
import ssl
from ldap3 import ALL, Connection, Server, Tls
from ldap3.core.exceptions import LDAPException

class LDAPConnector:
    """Manages LDAP server connections."""

    def connect(self) -> Connection:
        """Establish connection to LDAP server."""
        if self._connection and self._connection.bound:
            return self._connection

        # 🔧 CRÉATION TLS SÉCURISÉE
        tls_config = None
        if self.config.use_tls or self.config.use_ssl:
            # Déterminer le niveau de validation
            if self.config.tls_validate:
                validate_mode = ssl.CERT_REQUIRED
            else:
                validate_mode = ssl.CERT_NONE
                # ⚠️ Warning en mode développement
                import warnings
                warnings.warn(
                    "TLS certificate validation is disabled. "
                    "This should only be used in development/test environments.",
                    SecurityWarning
                )
            
            # Créer configuration TLS
            tls_config = Tls(
                validate=validate_mode,
                version=getattr(ssl, f"PROTOCOL_{self.config.tls_version.replace('.', '_')}"),
                ca_certs_file=self.config.ca_bundle_path,
            )

        # Reste du code inchangé
        protocol = "ldaps" if self.config.use_ssl else "ldap"
        server_uri = f"{protocol}://{self.config.server}"

        self._server = Server(
            host=self.config.server,
            port=self.config.port,
            use_ssl=self.config.use_ssl,
            tls=tls_config,
            get_info=ALL,
            connect_timeout=self.config.timeout,
        )
        # ... reste inchangé
```

### Mise à jour de `config.example.yaml`

```yaml
ldap:
  # Connection settings
  server: ldap://ldap.example.com
  port: 389
  use_ssl: true
  use_tls: true
  
  # 🆕 TLS/SSL Configuration
  tls_validate: true  # Valider les certificats (recommandé)
  ca_bundle_path: /etc/ssl/certs/ca-bundle.crt  # Optionnel
  tls_version: TLSv1.2  # Version TLS minimum
  
  # Pour désactiver la validation (DÉVELOPPEMENT UNIQUEMENT):
  # tls_validate: false
  # ⚠️ ATTENTION: Ne jamais utiliser en production!
```

---

## 🧪 2. Tests du connecteur LDAP

### Créer `tests/unit/test_connector.py`

```python
"""Tests for LDAP connector."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from ldap3.core.exceptions import LDAPException

from src.core.connector import LDAPConnector
from src.core.models import LDAPConfig


@pytest.fixture
def ldap_config():
    """Basic LDAP configuration for testing."""
    return LDAPConfig(
        server="ldap.test.com",
        port=389,
        bind_dn="cn=admin,dc=test,dc=com",
        bind_password="password",
        base_dn="dc=test,dc=com",
        users_ou="ou=users,dc=test,dc=com",
        groups_ou="ou=groups,dc=test,dc=com",
        tls_validate=False,  # For tests
    )


class TestLDAPConnector:
    """Test suite for LDAPConnector."""

    def test_init(self, ldap_config):
        """Test connector initialization."""
        connector = LDAPConnector(ldap_config)
        assert connector.config == ldap_config
        assert connector._server is None
        assert connector._connection is None

    @patch('src.core.connector.Server')
    @patch('src.core.connector.Connection')
    def test_connect_success(self, mock_connection, mock_server, ldap_config):
        """Test successful connection."""
        # Setup mocks
        mock_conn_instance = MagicMock()
        mock_conn_instance.bound = True
        mock_connection.return_value = mock_conn_instance
        
        # Test connection
        connector = LDAPConnector(ldap_config)
        conn = connector.connect()
        
        # Assertions
        assert conn is not None
        assert conn.bound
        mock_server.assert_called_once()
        mock_connection.assert_called_once()

    @patch('src.core.connector.Server')
    @patch('src.core.connector.Connection')
    def test_connect_retry_on_failure(self, mock_connection, mock_server, ldap_config):
        """Test retry logic on connection failure."""
        # Configure retries
        ldap_config.retry_max = 3
        ldap_config.retry_delay = 0.1
        
        # Setup mocks - fail twice, succeed on third try
        mock_conn_instance = MagicMock()
        mock_conn_instance.bound = True
        mock_connection.side_effect = [
            LDAPException("Connection refused"),
            LDAPException("Timeout"),
            mock_conn_instance,
        ]
        
        # Test connection
        connector = LDAPConnector(ldap_config)
        conn = connector.connect()
        
        # Should succeed on third attempt
        assert conn is not None
        assert mock_connection.call_count == 3

    @patch('src.core.connector.Server')
    @patch('src.core.connector.Connection')
    def test_connect_max_retries_exceeded(self, mock_connection, mock_server, ldap_config):
        """Test that connection fails after max retries."""
        ldap_config.retry_max = 3
        ldap_config.retry_delay = 0.1
        
        # All attempts fail
        mock_connection.side_effect = LDAPException("Connection refused")
        
        connector = LDAPConnector(ldap_config)
        
        with pytest.raises(LDAPException) as exc_info:
            connector.connect()
        
        assert "Failed to connect after 3 attempts" in str(exc_info.value)

    @patch('src.core.connector.Connection')
    @patch('src.core.connector.Server')
    def test_search(self, mock_server, mock_connection, ldap_config):
        """Test LDAP search."""
        # Setup mocks
        mock_entry = MagicMock()
        mock_entry.entry_dn = "cn=test,dc=test,dc=com"
        mock_entry.entry_attributes = ["cn", "mail"]
        mock_entry.__getitem__ = lambda self, key: MagicMock(value="test_value")
        
        mock_conn_instance = MagicMock()
        mock_conn_instance.bound = True
        mock_conn_instance.entries = [mock_entry]
        mock_conn_instance.result = {"controls": {}}
        mock_connection.return_value = mock_conn_instance
        
        # Test search
        connector = LDAPConnector(ldap_config)
        results = connector.search(
            search_filter="(objectClass=*)",
            attributes=["cn", "mail"]
        )
        
        assert len(results) > 0
        assert results[0]["dn"] == "cn=test,dc=test,dc=com"

    def test_context_manager(self, ldap_config):
        """Test context manager functionality."""
        with patch('src.core.connector.Connection') as mock_connection:
            mock_conn = MagicMock()
            mock_conn.bound = True
            mock_connection.return_value = mock_conn
            
            with LDAPConnector(ldap_config) as connector:
                assert connector is not None
            
            # Verify disconnect was called
            mock_conn.unbind.assert_called_once()

    @patch('src.core.connector.Connection')
    @patch('src.core.connector.Server')
    def test_test_connection_success(self, mock_server, mock_connection, ldap_config):
        """Test connection test method."""
        mock_conn = MagicMock()
        mock_conn.bound = True
        mock_conn.search = MagicMock(return_value=True)
        mock_connection.return_value = mock_conn
        
        connector = LDAPConnector(ldap_config)
        success, response_time, error = connector.test_connection()
        
        assert success is True
        assert response_time > 0
        assert error is None

    @patch('src.core.connector.Connection')
    @patch('src.core.connector.Server')
    def test_test_connection_failure(self, mock_server, mock_connection, ldap_config):
        """Test connection test method with failure."""
        mock_connection.side_effect = LDAPException("Connection refused")
        
        connector = LDAPConnector(ldap_config)
        success, response_time, error = connector.test_connection()
        
        assert success is False
        assert response_time > 0
        assert "Connection refused" in error
```

---

## 🔍 3. Tests des auditors

### Créer `tests/unit/test_users.py`

```python
"""Tests for user auditor."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

from src.audit.users import UserAuditor
from src.core.models import LDAPUser, AlertLevel


@pytest.fixture
def user_auditor(mock_ldap_connector, sample_config):
    """Create user auditor instance."""
    return UserAuditor(mock_ldap_connector, sample_config)


@pytest.fixture
def sample_users():
    """Create sample users for testing."""
    return [
        LDAPUser(
            dn="uid=user1,ou=users,dc=test,dc=com",
            uid="user1",
            cn="User One",
            sn="One",
            mail="user1@test.com",
            attributes={
                "cn": "User One",
                "sn": "One",
                "mail": "user1@test.com",
                "uid": "user1"
            }
        ),
        LDAPUser(
            dn="uid=user2,ou=users,dc=test,dc=com",
            uid="user2",
            cn="User Two",
            sn="Two",
            mail=None,  # Missing email
            attributes={
                "cn": "User Two",
                "sn": "Two",
                "uid": "user2"
            }
        ),
        LDAPUser(
            dn="uid=user3,ou=users,dc=test,dc=com",
            uid="user3",
            cn="User Three",
            sn="Three",
            mail="user1@test.com",  # Duplicate email
            attributes={
                "cn": "User Three",
                "sn": "Three",
                "mail": "user1@test.com",
                "uid": "user3"
            }
        ),
    ]


class TestUserAuditor:
    """Test suite for UserAuditor."""

    def test_check_missing_attributes(self, user_auditor, sample_users):
        """Test detection of missing required attributes."""
        with patch.object(user_auditor, '_get_all_users', return_value=sample_users):
            issues = user_auditor._check_missing_attributes(sample_users)
            
            # Should detect user2 missing email
            assert len(issues) == 1
            assert issues[0].level == AlertLevel.WARNING
            assert "missing required attributes" in issues[0].title.lower()

    def test_check_duplicate_emails(self, user_auditor, sample_users):
        """Test detection of duplicate email addresses."""
        with patch.object(user_auditor, '_get_all_users', return_value=sample_users):
            issues = user_auditor._check_duplicate_attributes(sample_users)
            
            # Should detect duplicate email
            duplicate_issues = [i for i in issues if "duplicate email" in i.title.lower()]
            assert len(duplicate_issues) == 1
            assert duplicate_issues[0].level == AlertLevel.CRITICAL

    def test_check_duplicate_uids(self, user_auditor):
        """Test detection of duplicate UIDs."""
        users_with_dup_uid = [
            LDAPUser(
                dn="uid=user1,ou=users,dc=test,dc=com",
                uid="duplicate",
                cn="User One",
                sn="One",
                mail="user1@test.com",
                attributes={}
            ),
            LDAPUser(
                dn="uid=user2,ou=users,dc=test,dc=com",
                uid="duplicate",  # Same UID
                cn="User Two",
                sn="Two",
                mail="user2@test.com",
                attributes={}
            ),
        ]
        
        issues = user_auditor._check_duplicate_attributes(users_with_dup_uid)
        uid_issues = [i for i in issues if "duplicate uid" in i.title.lower()]
        
        assert len(uid_issues) == 1
        assert uid_issues[0].level == AlertLevel.CRITICAL

    def test_no_issues_with_valid_users(self, user_auditor):
        """Test that valid users produce no issues."""
        valid_users = [
            LDAPUser(
                dn="uid=user1,ou=users,dc=test,dc=com",
                uid="user1",
                cn="User One",
                sn="One",
                mail="user1@test.com",
                attributes={
                    "cn": "User One",
                    "sn": "One",
                    "mail": "user1@test.com",
                    "uid": "user1"
                }
            ),
        ]
        
        issues = []
        issues.extend(user_auditor._check_missing_attributes(valid_users))
        issues.extend(user_auditor._check_duplicate_attributes(valid_users))
        
        assert len(issues) == 0
```

---

## 💾 4. Tests de backup

### Créer `tests/unit/test_backup.py`

```python
"""Tests for backup manager."""

import pytest
import json
import yaml
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from src.manage.backup import BackupManager


@pytest.fixture
def backup_manager(mock_ldap_connector, sample_config, tmp_path):
    """Create backup manager instance."""
    sample_config.backup.backup_dir = str(tmp_path)
    return BackupManager(mock_ldap_connector, sample_config)


@pytest.fixture
def sample_ldap_entries():
    """Sample LDAP entries for testing."""
    return [
        {
            "dn": "uid=user1,ou=users,dc=test,dc=com",
            "attributes": {
                "cn": "User One",
                "mail": "user1@test.com",
                "uid": "user1"
            }
        },
        {
            "dn": "uid=user2,ou=users,dc=test,dc=com",
            "attributes": {
                "cn": "User Two",
                "mail": "user2@test.com",
                "uid": "user2"
            }
        },
    ]


class TestBackupManager:
    """Test suite for BackupManager."""

    def test_backup_full_ldif(self, backup_manager, sample_ldap_entries):
        """Test full backup in LDIF format."""
        with patch.object(backup_manager.connector, 'search', return_value=sample_ldap_entries):
            backup_path = backup_manager.backup_full(format="ldif")
            
            assert Path(backup_path).exists()
            assert backup_path.endswith(".ldif") or backup_path.endswith(".ldif.gz")
            
            # Verify content
            content = Path(backup_path).read_text()
            assert "dn: uid=user1" in content
            assert "cn: User One" in content

    def test_backup_full_json(self, backup_manager, sample_ldap_entries):
        """Test full backup in JSON format."""
        with patch.object(backup_manager.connector, 'search', return_value=sample_ldap_entries):
            backup_path = backup_manager.backup_full(format="json")
            
            assert Path(backup_path).exists()
            
            # Verify it's valid JSON
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            assert len(data) == 2
            assert data[0]["dn"] == "uid=user1,ou=users,dc=test,dc=com"

    def test_backup_full_yaml(self, backup_manager, sample_ldap_entries):
        """Test full backup in YAML format."""
        with patch.object(backup_manager.connector, 'search', return_value=sample_ldap_entries):
            backup_path = backup_manager.backup_full(format="yaml")
            
            assert Path(backup_path).exists()
            
            # Verify it's valid YAML
            with open(backup_path, 'r') as f:
                data = yaml.safe_load(f)
            
            assert len(data) == 2
            assert data[0]["dn"] == "uid=user1,ou=users,dc=test,dc=com"

    def test_export_users_csv(self, backup_manager, sample_ldap_entries, tmp_path):
        """Test user export in CSV format."""
        output_path = str(tmp_path / "users.csv")
        
        with patch.object(backup_manager.connector, 'search', return_value=sample_ldap_entries):
            result_path = backup_manager.export_users(output_path, format="csv")
            
            assert Path(result_path).exists()
            
            # Verify CSV content
            content = Path(result_path).read_text()
            assert "dn,cn,mail,uid" in content
            assert "user1@test.com" in content
            assert "user2@test.com" in content

    def test_backup_compression(self, backup_manager, sample_ldap_entries):
        """Test that compression works when enabled."""
        backup_manager.config.backup.compress = True
        
        with patch.object(backup_manager.connector, 'search', return_value=sample_ldap_entries):
            backup_path = backup_manager.backup_full(format="json")
            
            assert backup_path.endswith(".gz")
            assert Path(backup_path).exists()
```

---

## ⚙️ 5. Configuration CI/CD

### Créer `.github/workflows/test.yml`

```yaml
name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -e ".[dev]"
    
    - name: Lint with ruff
      run: |
        ruff check src/ tests/
    
    - name: Check formatting with black
      run: |
        black --check src/ tests/
    
    - name: Type check with mypy
      run: |
        mypy src/
      continue-on-error: true  # Don't fail on type errors initially
    
    - name: Run tests with pytest
      run: |
        pytest --cov=src --cov-report=xml --cov-report=term-missing
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        fail_ci_if_error: false
```

### Créer `.github/workflows/lint.yml`

```yaml
name: Lint

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  lint:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.10"
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install black ruff mypy
    
    - name: Lint with ruff
      run: ruff check src/ tests/
    
    - name: Check formatting with black
      run: black --check src/ tests/
    
    - name: Type check with mypy
      run: mypy src/
```

---

## 📝 6. Exemple de documentation manquante

### Créer `docs/security.md`

```markdown
# Guide de sécurité

## Configuration TLS/SSL

### Activer la validation TLS (Recommandé)

```yaml
ldap:
  use_ssl: true
  use_tls: true
  tls_validate: true  # ✅ IMPORTANT
  ca_bundle_path: /etc/ssl/certs/ca-bundle.crt
```

⚠️ **ATTENTION**: Ne jamais désactiver `tls_validate` en production !

### Environnement de développement

Pour les tests locaux uniquement :

```yaml
ldap:
  tls_validate: false  # ⚠️ DÉVELOPPEMENT UNIQUEMENT
```

## Gestion des credentials

### Variables d'environnement (Recommandé)

```bash
# .env
LDAP_PASSWORD=your-secure-password
SLACK_WEBHOOK=https://hooks.slack.com/...
SMTP_PASSWORD=your-email-password
```

### Fichier de configuration

❌ **Ne JAMAIS faire** :
```yaml
ldap:
  bind_password: "mon-mot-de-passe"  # DANGEREUX !
```

✅ **À faire** :
```yaml
ldap:
  bind_password: ${LDAP_PASSWORD}  # Variable d'environnement
```

## Permissions LDAP recommandées

### Pour l'audit (lecture seule)

```ldif
dn: cn=ldap-monitor-ro,ou=services,dc=example,dc=com
objectClass: person
cn: ldap-monitor-ro
userPassword: {SSHA}...
```

Permissions minimales :
- Lecture sur `ou=users`
- Lecture sur `ou=groups`
- Pas de permissions d'écriture

### Pour la gestion (lecture/écriture)

Permissions supplémentaires :
- Écriture sur `ou=users`
- Écriture sur `ou=groups`
- Suppression (si `allow_delete: true`)

## Bonnes pratiques

1. ✅ Utiliser des comptes de service dédiés
2. ✅ Activer l'audit trail
3. ✅ Limiter les permissions au strict nécessaire
4. ✅ Rotate les mots de passe régulièrement
5. ✅ Surveiller les logs
6. ✅ Activer le rate limiting
7. ✅ Utiliser TLS/SSL systématiquement
8. ✅ Chiffrer les backups sensibles

## Checklist de sécurité

- [ ] TLS activé et validé
- [ ] Credentials dans variables d'environnement
- [ ] Compte de service avec permissions minimales
- [ ] Logging activé
- [ ] Backups chiffrés
- [ ] Rate limiting activé
- [ ] Alertes configurées
- [ ] Audit régulier des permissions
```

---

## 📦 7. Publication sur PyPI

### Script de publication

```bash
#!/bin/bash
# publish.sh

set -e

echo "🔍 Vérification de la version..."
VERSION=$(python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])")
echo "Version actuelle: $VERSION"

echo ""
echo "🧪 Exécution des tests..."
pytest

echo ""
echo "🔍 Vérification du code..."
ruff check src/
black --check src/
mypy src/

echo ""
echo "🏗️  Build du package..."
python -m build

echo ""
echo "🔍 Vérification du package..."
twine check dist/*

echo ""
read -p "Publier sur PyPI ? (y/N) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    echo "📦 Publication sur PyPI..."
    twine upload dist/*
    echo "✅ Package publié avec succès!"
else
    echo "❌ Publication annulée"
fi
```

---

## 🐳 8. Dockerfile production

```dockerfile
# Multi-stage build for smaller image
FROM python:3.10-slim as builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Final stage
FROM python:3.10-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder
COPY --from=builder /build/wheels /wheels
RUN pip install --no-cache /wheels/*

# Copy application
COPY . .
RUN pip install --no-cache-dir .

# Create directories
RUN mkdir -p /app/logs /app/backups /app/reports /app/config

# Non-root user
RUN useradd -m -u 1000 ldap-monitor && \
    chown -R ldap-monitor:ldap-monitor /app
USER ldap-monitor

# Volume for data
VOLUME ["/app/logs", "/app/backups", "/app/reports", "/app/config"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD ldap-monitor test connection || exit 1

# Entry point
ENTRYPOINT ["ldap-monitor"]
CMD ["--help"]
```

### Docker-compose complet

```yaml
version: '3.8'

services:
  ldap-monitor:
    build: .
    container_name: ldap-monitor
    volumes:
      - ./config.yaml:/app/config/config.yaml:ro
      - ./logs:/app/logs
      - ./backups:/app/backups
      - ./reports:/app/reports
    environment:
      - LDAP_PASSWORD=${LDAP_PASSWORD}
      - SLACK_WEBHOOK=${SLACK_WEBHOOK}
    command: monitor start
    restart: unless-stopped
    depends_on:
      - openldap

  openldap:
    image: osixia/openldap:latest
    container_name: ldap-server
    environment:
      LDAP_ORGANISATION: "Example Inc"
      LDAP_DOMAIN: "example.com"
      LDAP_ADMIN_PASSWORD: "admin"
    ports:
      - "389:389"
      - "636:636"
    volumes:
      - ldap_data:/var/lib/ldap
      - ldap_config:/etc/ldap/slapd.d

  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: "admin"
    volumes:
      - grafana_data:/var/lib/grafana
    depends_on:
      - prometheus

volumes:
  ldap_data:
  ldap_config:
  prometheus_data:
  grafana_data:
```

---

**Document créé le 17 novembre 2025**  
*Basé sur AUDIT_REPORT.md*

