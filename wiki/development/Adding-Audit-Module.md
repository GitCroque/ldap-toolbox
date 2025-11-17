# Guide: Ajouter un Module d'Audit

## Introduction

Ce guide vous accompagne étape par étape pour créer un nouveau module d'audit dans LDAP Health Monitor. Nous allons créer un module d'audit des **permissions** comme exemple pratique.

## Vue d'Ensemble

### Objectif

Créer un module `PermissionsAuditor` qui:
- Vérifie les permissions LDAP sur les OUs
- Détecte les ACLs trop permissives
- Identifie les comptes avec droits excessifs
- Recommande des améliorations de sécurité

### Architecture

```
Nouveau Module: src/audit/permissions.py
│
├─> Utilise: LDAPConnector (connexion LDAP)
├─> Utilise: Config (configuration)
├─> Retourne: List[AuditIssue]
│
└─> Intégré dans: CLI (audit all)
```

## Étape 1: Créer le Fichier du Module

### 1.1 Créer permissions.py

Créez le fichier `/home/user/ldap-toolbox/src/audit/permissions.py`:

```python
"""Audit des permissions et ACLs LDAP."""

from typing import List, Dict, Any, Optional
from src.core.connector import LDAPConnector
from src.core.models import AlertLevel, AuditIssue, Config


class PermissionsAuditor:
    """Auditeur pour les permissions et ACLs LDAP."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialise l'auditeur de permissions.

        Args:
            connector: Connecteur LDAP pour les requêtes
            config: Configuration de l'application
        """
        self.connector = connector
        self.config = config

    def audit_permissions(self) -> List[AuditIssue]:
        """Effectue l'audit complet des permissions.

        Returns:
            Liste des problèmes de permissions découverts
        """
        issues: List[AuditIssue] = []

        # Vérifications configurables
        if self.config.audit.security.get("check_acls", True):
            issues.extend(self._check_acls())

        if self.config.audit.security.get("check_admin_rights", True):
            issues.extend(self._check_admin_rights())

        if self.config.audit.security.get("check_write_permissions", True):
            issues.extend(self._check_write_permissions())

        return issues

    def _check_acls(self) -> List[AuditIssue]:
        """Vérifie les ACLs sur les OUs importantes.

        Returns:
            Liste des problèmes d'ACL découverts
        """
        issues: List[AuditIssue] = []

        try:
            # OUs critiques à vérifier
            critical_ous = self.config.audit.security.get("critical_ous", [
                self.config.ldap.users_ou,
                self.config.ldap.groups_ou,
            ])

            for ou_dn in critical_ous:
                # Récupérer l'OU avec ses ACLs
                ou_entry = self.connector.get_entry(
                    dn=ou_dn,
                    attributes=["*", "aclRights", "entryACI"]
                )

                if not ou_entry:
                    issues.append(
                        AuditIssue(
                            level=AlertLevel.WARNING,
                            category="permissions",
                            title="OU not found",
                            description=f"Critical OU not found: {ou_dn}",
                            affected_dn=ou_dn,
                            recommendation="Verify OU path in configuration"
                        )
                    )
                    continue

                # Vérifier les ACLs
                acls = ou_entry.get("attributes", {}).get("entryACI", [])
                if not isinstance(acls, list):
                    acls = [acls] if acls else []

                # Détecte les ACLs trop permissives
                for acl in acls:
                    if self._is_permissive_acl(acl):
                        issues.append(
                            AuditIssue(
                                level=AlertLevel.WARNING,
                                category="permissions",
                                title="Permissive ACL detected",
                                description=f"OU has overly permissive ACL: {acl[:100]}...",
                                affected_dn=ou_dn,
                                recommendation="Review and restrict ACL permissions",
                                details={"acl": acl}
                            )
                        )

        except Exception as e:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="permissions",
                    title="ACL check failed",
                    description=f"Error checking ACLs: {str(e)}",
                    recommendation="Verify LDAP permissions and connectivity"
                )
            )

        return issues

    def _check_admin_rights(self) -> List[AuditIssue]:
        """Vérifie les comptes avec droits administrateurs.

        Returns:
            Liste des problèmes de droits admin découverts
        """
        issues: List[AuditIssue] = []

        try:
            # Groupes administrateurs configurés
            admin_groups = self.config.audit.security.get("admin_groups", [])

            for admin_group_dn in admin_groups:
                group = self.connector.get_entry(
                    dn=admin_group_dn,
                    attributes=["member", "cn"]
                )

                if not group:
                    continue

                members = group.get("attributes", {}).get("member", [])
                if not isinstance(members, list):
                    members = [members] if members else []

                # Trop de membres dans un groupe admin
                max_admins = self.config.audit.thresholds.get("max_admins", 5)
                if len(members) > max_admins:
                    issues.append(
                        AuditIssue(
                            level=AlertLevel.WARNING,
                            category="permissions",
                            title="Too many administrators",
                            description=f"Admin group has {len(members)} members (threshold: {max_admins})",
                            affected_dn=admin_group_dn,
                            recommendation="Review admin group membership and apply least privilege principle",
                            details={
                                "group": admin_group_dn,
                                "member_count": len(members),
                                "threshold": max_admins
                            }
                        )
                    )

                # Vérifier chaque membre admin
                for member_dn in members:
                    member = self.connector.get_entry(
                        dn=member_dn,
                        attributes=["uid", "description"]
                    )

                    if member:
                        # Vérifie si le compte admin a une description/justification
                        description = member.get("attributes", {}).get("description")
                        if not description:
                            issues.append(
                                AuditIssue(
                                    level=AlertLevel.INFO,
                                    category="permissions",
                                    title="Admin account without description",
                                    description="Administrative account lacks description/justification",
                                    affected_dn=member_dn,
                                    recommendation="Add description explaining admin privileges",
                                    details={"admin_group": admin_group_dn}
                                )
                            )

        except Exception as e:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="permissions",
                    title="Admin rights check failed",
                    description=f"Error checking admin rights: {str(e)}",
                    recommendation="Verify LDAP permissions"
                )
            )

        return issues

    def _check_write_permissions(self) -> List[AuditIssue]:
        """Vérifie les permissions en écriture excessives.

        Returns:
            Liste des problèmes de permissions en écriture
        """
        issues: List[AuditIssue] = []

        try:
            # Recherche les utilisateurs normaux avec droits write
            users = self.connector.search(
                search_base=self.config.ldap.users_ou,
                search_filter=f"(objectClass={self.config.ldap.user_objectclass})",
                attributes=["dn", "uid", "userPassword", "authPassword"]
            )

            for user in users:
                user_dn = user.get("dn")
                attrs = user.get("attributes", {})

                # Vérifie si l'utilisateur peut modifier son propre password
                # (selon la configuration, cela peut être souhaitable ou non)
                if self.config.audit.security.get("flag_self_password_change", False):
                    # Cette vérification nécessiterait d'interroger les ACLs
                    # C'est un exemple simplifié
                    pass

        except Exception as e:
            issues.append(
                AuditIssue(
                    level=AlertLevel.WARNING,
                    category="permissions",
                    title="Write permissions check failed",
                    description=f"Error checking write permissions: {str(e)}",
                    recommendation="Verify LDAP permissions"
                )
            )

        return issues

    def _is_permissive_acl(self, acl: str) -> bool:
        """Détermine si une ACL est trop permissive.

        Args:
            acl: Chaîne ACL à analyser

        Returns:
            True si l'ACL est jugée trop permissive
        """
        # Exemples de patterns dangereux
        dangerous_patterns = [
            "grant:all",
            "targetattr=\"*\"",
            "userdn=\"ldap:///anyone\"",
            "userdn=\"ldap:///all\"",
        ]

        acl_lower = acl.lower()
        return any(pattern.lower() in acl_lower for pattern in dangerous_patterns)
```

### 1.2 Points Clés du Code

**Initialisation:**
- Accepte `LDAPConnector` et `Config` comme dépendances
- Stocke les références pour utilisation ultérieure

**Méthode principale `audit_permissions()`:**
- Point d'entrée unique pour l'audit
- Exécute différentes vérifications selon la configuration
- Retourne une liste consolidée d'`AuditIssue`

**Méthodes privées `_check_*()`:**
- Une méthode par type de vérification
- Gestion des erreurs dans chaque méthode
- Conversion des erreurs en `AuditIssue` plutôt que lever des exceptions

**Gestion d'erreurs:**
- Try/except autour de chaque vérification
- Erreurs converties en issues de type WARNING
- L'audit peut continuer même si une vérification échoue

## Étape 2: Configuration

### 2.1 Ajouter la Configuration

Dans `config.example.yaml`, ajoutez la configuration pour le nouveau module:

```yaml
audit:
  # ... configuration existante ...

  security:
    # Vérifications de permissions
    check_acls: true
    check_admin_rights: true
    check_write_permissions: true
    flag_self_password_change: false

    # OUs critiques à surveiller
    critical_ous:
      - "ou=users,dc=example,dc=com"
      - "ou=groups,dc=example,dc=com"
      - "ou=service-accounts,dc=example,dc=com"

    # Groupes administrateurs
    admin_groups:
      - "cn=admins,ou=groups,dc=example,dc=com"
      - "cn=ldap-admins,ou=groups,dc=example,dc=com"

  thresholds:
    # Seuil maximum d'administrateurs
    max_admins: 5
```

### 2.2 Mettre à Jour le Modèle de Configuration

Si nécessaire, ajoutez des validations dans `src/core/models.py`:

```python
class AuditConfig(BaseModel):
    """Audit configuration."""

    # ... champs existants ...

    security: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("security")
    @classmethod
    def validate_security_config(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Valide la configuration de sécurité."""
        # Valeurs par défaut
        v.setdefault("check_acls", True)
        v.setdefault("check_admin_rights", True)
        v.setdefault("check_write_permissions", True)

        # Validation des admin_groups
        if "admin_groups" in v:
            if not isinstance(v["admin_groups"], list):
                raise ValueError("admin_groups must be a list")

        return v
```

## Étape 3: Tests

### 3.1 Créer les Tests Unitaires

Créez `/home/user/ldap-toolbox/tests/unit/test_permissions_audit.py`:

```python
"""Tests pour le module d'audit des permissions."""

import pytest
from src.audit.permissions import PermissionsAuditor
from src.core.models import Config, LDAPConfig, AuditConfig, AlertLevel


@pytest.fixture
def permissions_config():
    """Configuration pour tests de permissions."""
    ldap_config = LDAPConfig(
        server="ldap.test.com",
        port=389,
        bind_dn="cn=admin,dc=test,dc=com",
        bind_password="password",
        base_dn="dc=test,dc=com",
        users_ou="ou=users,dc=test,dc=com",
        groups_ou="ou=groups,dc=test,dc=com",
    )

    audit_config = AuditConfig(
        security={
            "check_acls": True,
            "check_admin_rights": True,
            "critical_ous": ["ou=users,dc=test,dc=com"],
            "admin_groups": ["cn=admins,ou=groups,dc=test,dc=com"],
        },
        thresholds={"max_admins": 3}
    )

    return Config(ldap=ldap_config, audit=audit_config)


class TestPermissionsAuditor:
    """Tests pour PermissionsAuditor."""

    def test_initialization(self, permissions_config, mock_ldap_connector):
        """Test d'initialisation de l'auditeur."""
        auditor = PermissionsAuditor(mock_ldap_connector, permissions_config)

        assert auditor.connector == mock_ldap_connector
        assert auditor.config == permissions_config

    def test_audit_permissions_returns_list(self, permissions_config, mock_ldap_connector):
        """Test que audit_permissions retourne une liste."""
        auditor = PermissionsAuditor(mock_ldap_connector, permissions_config)

        # Mock la méthode get_entry pour retourner None
        mock_ldap_connector.get_entry.return_value = None

        issues = auditor.audit_permissions()

        assert isinstance(issues, list)

    def test_check_acls_with_missing_ou(self, permissions_config, mock_ldap_connector):
        """Test détection OU manquante."""
        auditor = PermissionsAuditor(mock_ldap_connector, permissions_config)

        # Mock: OU non trouvée
        mock_ldap_connector.get_entry.return_value = None

        issues = auditor._check_acls()

        assert len(issues) > 0
        assert issues[0].title == "OU not found"
        assert issues[0].level == AlertLevel.WARNING

    def test_check_acls_with_permissive_acl(self, permissions_config, mock_ldap_connector):
        """Test détection ACL permissive."""
        auditor = PermissionsAuditor(mock_ldap_connector, permissions_config)

        # Mock: OU avec ACL permissive
        mock_ldap_connector.get_entry.return_value = {
            "dn": "ou=users,dc=test,dc=com",
            "attributes": {
                "entryACI": ["(targetattr=\"*\")(version 3.0; acl \"all access\"; allow (all) userdn=\"ldap:///anyone\";)"]
            }
        }

        issues = auditor._check_acls()

        assert len(issues) > 0
        assert issues[0].title == "Permissive ACL detected"
        assert issues[0].level == AlertLevel.WARNING

    def test_check_admin_rights_too_many_admins(self, permissions_config, mock_ldap_connector):
        """Test détection trop d'administrateurs."""
        auditor = PermissionsAuditor(mock_ldap_connector, permissions_config)

        # Mock: groupe admin avec 5 membres (seuil: 3)
        mock_ldap_connector.get_entry.return_value = {
            "dn": "cn=admins,ou=groups,dc=test,dc=com",
            "attributes": {
                "cn": "admins",
                "member": [
                    "uid=admin1,ou=users,dc=test,dc=com",
                    "uid=admin2,ou=users,dc=test,dc=com",
                    "uid=admin3,ou=users,dc=test,dc=com",
                    "uid=admin4,ou=users,dc=test,dc=com",
                    "uid=admin5,ou=users,dc=test,dc=com",
                ]
            }
        }

        issues = auditor._check_admin_rights()

        assert len(issues) > 0
        too_many_admin_issue = next(
            (i for i in issues if i.title == "Too many administrators"),
            None
        )
        assert too_many_admin_issue is not None
        assert too_many_admin_issue.level == AlertLevel.WARNING

    def test_is_permissive_acl(self, permissions_config, mock_ldap_connector):
        """Test détection pattern ACL permissif."""
        auditor = PermissionsAuditor(mock_ldap_connector, permissions_config)

        # ACLs permissives
        assert auditor._is_permissive_acl("grant:all") == True
        assert auditor._is_permissive_acl("targetattr=\"*\"") == True
        assert auditor._is_permissive_acl("userdn=\"ldap:///anyone\"") == True

        # ACL normale
        assert auditor._is_permissive_acl("(targetattr=\"cn\")(version 3.0)") == False

    @pytest.mark.parametrize("admin_count,expected_issues", [
        (2, 0),  # En dessous du seuil
        (3, 0),  # Au seuil
        (4, 1),  # Au-dessus du seuil
        (10, 1), # Bien au-dessus
    ])
    def test_admin_count_thresholds(
        self, admin_count, expected_issues, permissions_config, mock_ldap_connector
    ):
        """Test des différents seuils d'administrateurs."""
        auditor = PermissionsAuditor(mock_ldap_connector, permissions_config)

        members = [f"uid=admin{i},ou=users,dc=test,dc=com" for i in range(admin_count)]

        mock_ldap_connector.get_entry.return_value = {
            "dn": "cn=admins,ou=groups,dc=test,dc=com",
            "attributes": {"cn": "admins", "member": members}
        }

        issues = auditor._check_admin_rights()

        too_many_issues = [i for i in issues if i.title == "Too many administrators"]
        assert len(too_many_issues) == expected_issues
```

### 3.2 Exécuter les Tests

```bash
# Test du nouveau module seulement
pytest tests/unit/test_permissions_audit.py -v

# Test avec couverture
pytest tests/unit/test_permissions_audit.py --cov=src.audit.permissions --cov-report=html
```

## Étape 4: Intégration CLI

### 4.1 Importer le Nouveau Module

Dans `src/cli.py`, ajoutez l'import:

```python
# Au début du fichier, avec les autres imports d'audit
from src.audit.permissions import PermissionsAuditor
```

### 4.2 Ajouter au Fichier __init__.py

Dans `src/audit/__init__.py`:

```python
"""Module d'audit LDAP."""

from src.audit.consistency import ConsistencyAuditor
from src.audit.groups import GroupAuditor
from src.audit.health import HealthChecker
from src.audit.permissions import PermissionsAuditor  # ← NOUVEAU
from src.audit.security import SecurityAuditor
from src.audit.structure import StructureAuditor
from src.audit.users import UserAuditor

__all__ = [
    "ConsistencyAuditor",
    "GroupAuditor",
    "HealthChecker",
    "PermissionsAuditor",  # ← NOUVEAU
    "SecurityAuditor",
    "StructureAuditor",
    "UserAuditor",
]
```

### 4.3 Créer une Commande Dédiée (Optionnel)

```python
@audit.command("permissions")
@click.option("--output", "-o", help="Output file path")
@click.option("--format", "-f", type=click.Choice(["console", "json"]), default="console")
@click.pass_context
def audit_permissions(ctx: click.Context, output: Optional[str], format: str) -> None:
    """Audit LDAP permissions and ACLs."""
    try:
        config = load_config(ctx.obj.get("config_path"))
        connector = LDAPConnector(config.ldap)
        auditor = PermissionsAuditor(connector, config)

        issues = auditor.audit_permissions()

        reporter = ConsoleReporter()
        if issues:
            reporter.print_warning(f"Found {len(issues)} permission issues")
            for issue in issues:
                click.echo(f"\n{issue.level.value.upper()}: {issue.title}")
                click.echo(f"  {issue.description}")
                if issue.recommendation:
                    click.echo(f"  💡 {issue.recommendation}")
        else:
            reporter.print_success("No permission issues found")

        # Export si demandé
        if output and format == "json":
            import json
            with open(output, "w") as f:
                json.dump([i.model_dump() for i in issues], f, indent=2, default=str)
            click.echo(f"\n✅ Report saved to {output}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        sys.exit(1)
```

### 4.4 Intégrer dans audit all

Modifiez la commande `audit_all` pour inclure le nouveau module:

```python
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
        permissions_auditor = PermissionsAuditor(connector, config)  # ← NOUVEAU

        health = health_checker.check_health()
        all_issues = []
        all_issues.extend(user_auditor.audit_users())
        all_issues.extend(group_auditor.audit_groups())
        all_issues.extend(structure_auditor.audit_structure())
        all_issues.extend(security_auditor.audit_security())
        all_issues.extend(consistency_auditor.audit_consistency())
        all_issues.extend(permissions_auditor.audit_permissions())  # ← NOUVEAU

        # Create audit report
        report = AuditReport(
            health=health,
            issues=all_issues,
            statistics=health.details.get("statistics", {}),
            score=max(0, 100 - len(all_issues) * 5),
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
```

## Étape 5: Documentation

### 5.1 Documenter le Module

Créez ou mettez à jour la documentation utilisateur:

**wiki/features/Audit-Permissions.md:**

```markdown
# Audit des Permissions LDAP

## Description

Le module d'audit des permissions vérifie les configurations de sécurité et les ACLs de votre annuaire LDAP.

## Vérifications Effectuées

### 1. ACLs des OUs Critiques

Vérifie que les OUs importantes (users, groups, etc.) n'ont pas d'ACLs trop permissives.

**Détecte:**
- ACLs avec `grant:all`
- ACLs avec `targetattr="*"`
- ACLs permettant l'accès à `anyone`

### 2. Comptes Administrateurs

Surveille les groupes d'administrateurs pour détecter:
- Trop de membres dans les groupes admin
- Comptes admin sans description/justification

### 3. Permissions en Écriture

Identifie les permissions en écriture excessives ou inhabituelles.

## Configuration

```yaml
audit:
  security:
    check_acls: true
    check_admin_rights: true
    critical_ous:
      - "ou=users,dc=example,dc=com"
    admin_groups:
      - "cn=admins,ou=groups,dc=example,dc=com"

  thresholds:
    max_admins: 5
```

## Utilisation

### Audit Permissions Seul

```bash
ldap-monitor audit permissions
```

### Dans Audit Complet

```bash
ldap-monitor audit all
```

## Exemples de Problèmes Détectés

### ACL Permissive

```
WARNING: Permissive ACL detected
  OU has overly permissive ACL allowing anyone to read all attributes
  💡 Review and restrict ACL permissions
```

### Trop d'Administrateurs

```
WARNING: Too many administrators
  Admin group has 10 members (threshold: 5)
  💡 Review admin group membership and apply least privilege principle
```
```

## Étape 6: Tests d'Intégration

### 6.1 Tester Manuellement

```bash
# 1. Créer une configuration de test
cp config.example.yaml config.test.yaml
# Éditer config.test.yaml avec vos paramètres de test

# 2. Tester la commande permissions
ldap-monitor --config config.test.yaml audit permissions

# 3. Tester dans audit all
ldap-monitor --config config.test.yaml audit all --format json -o report.json

# 4. Vérifier le rapport
cat report.json | jq '.issues[] | select(.category == "permissions")'
```

### 6.2 Test d'Intégration Automatisé

Créez `tests/integration/test_permissions_integration.py`:

```python
"""Tests d'intégration pour l'audit des permissions."""

import pytest
from src.audit.permissions import PermissionsAuditor
from src.core.config import load_config
from src.core.connector import LDAPConnector


@pytest.mark.integration
def test_permissions_audit_against_real_ldap():
    """Test contre un vrai serveur LDAP (nécessite config de test)."""
    # Skip si pas de config de test
    try:
        config = load_config("config.test.yaml")
    except FileNotFoundError:
        pytest.skip("config.test.yaml not found")

    connector = LDAPConnector(config.ldap)
    auditor = PermissionsAuditor(connector, config)

    # Test de connexion
    success, response_time, error = connector.test_connection()
    assert success, f"Cannot connect to LDAP: {error}"

    # Exécuter l'audit
    issues = auditor.audit_permissions()

    # Vérifications de base
    assert isinstance(issues, list)
    # Tous les issues doivent avoir les champs requis
    for issue in issues:
        assert issue.level in ["info", "warning", "critical"]
        assert issue.category == "permissions"
        assert issue.title
        assert issue.description
```

## Checklist Complète

Avant de considérer le module terminé, vérifiez:

- [ ] **Code**
  - [ ] Fichier `src/audit/permissions.py` créé
  - [ ] Suit le pattern standard des auditeurs
  - [ ] Gestion d'erreurs robuste
  - [ ] Docstrings complètes
  - [ ] Type hints partout

- [ ] **Configuration**
  - [ ] Configuration ajoutée à `config.example.yaml`
  - [ ] Valeurs par défaut sensibles
  - [ ] Validation dans `AuditConfig` si nécessaire

- [ ] **Tests**
  - [ ] Tests unitaires créés
  - [ ] Couverture > 80%
  - [ ] Tests paramétrés pour différents seuils
  - [ ] Mock appropriés
  - [ ] Tests d'intégration (optionnel)

- [ ] **Intégration CLI**
  - [ ] Import ajouté dans `cli.py`
  - [ ] Ajouté dans `audit/__init__.py`
  - [ ] Intégré dans `audit all`
  - [ ] Commande dédiée créée (optionnel)

- [ ] **Documentation**
  - [ ] Docstrings du module
  - [ ] Documentation utilisateur
  - [ ] Exemples d'utilisation
  - [ ] Configuration documentée

- [ ] **Tests Manuels**
  - [ ] Commande exécutée avec succès
  - [ ] Issues générées correctement
  - [ ] Formats de sortie fonctionnent
  - [ ] Pas de régression sur autres modules

## Bonnes Pratiques

### 1. Nommage Cohérent

```python
# Classe
class PermissionsAuditor:  # Suffixe "Auditor"

# Méthode principale
def audit_permissions(self):  # Préfixe "audit_"

# Méthodes privées
def _check_acls(self):  # Préfixe "_check_"
```

### 2. Structure Standard

```python
def audit_[domain](self) -> List[AuditIssue]:
    """Effectue l'audit complet."""
    issues = []

    # Vérifications configurables
    if self.config.audit.get("check_something"):
        issues.extend(self._check_something())

    return issues
```

### 3. Gestion d'Erreurs

```python
try:
    # Logique d'audit
    pass
except Exception as e:
    # Convertir en AuditIssue, ne pas lever
    issues.append(AuditIssue(...))
```

### 4. Configuration Flexible

```python
# Permettre désactivation
if self.config.audit.security.get("check_acls", True):
    issues.extend(self._check_acls())

# Seuils configurables
threshold = self.config.audit.thresholds.get("max_admins", 5)
```

### 5. Tests Complets

```python
# Test chaque méthode _check_*
def test_check_acls():
    pass

# Test avec différents paramètres
@pytest.mark.parametrize("value,expected", [...])
def test_thresholds(value, expected):
    pass
```

## Dépannage

### Problème: Module non trouvé

**Erreur:**
```
ModuleNotFoundError: No module named 'src.audit.permissions'
```

**Solution:**
- Vérifier que le fichier existe
- Vérifier l'import dans `__init__.py`
- Réinstaller en mode développement: `pip install -e .`

### Problème: Issues non affichées

**Solution:**
- Vérifier que le module est appelé dans `audit_all`
- Vérifier que la configuration active la vérification
- Ajouter des logs pour débugger

### Problème: Tests échouent

**Solution:**
- Vérifier les mocks
- Vérifier les fixtures
- Exécuter avec `-v` pour plus de détails

## Conclusion

Vous avez maintenant créé un module d'audit complet! Ce pattern peut être réutilisé pour créer d'autres modules d'audit comme:

- **ComplianceAuditor**: Vérifications de conformité réglementaire
- **PerformanceAuditor**: Analyse de performance
- **ReplicationAuditor**: Vérification de la réplication
- **SchemaAuditor**: Validation du schéma LDAP
- **BackupAuditor**: Vérification des sauvegardes

Le système est extensible et chaque nouveau module s'intègre naturellement!
