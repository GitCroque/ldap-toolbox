# Guide de Style de Code

## Introduction

Ce guide définit les conventions de style et les meilleures pratiques pour le projet LDAP Health Monitor. Le respect de ces conventions assure la cohérence, la lisibilité et la maintenabilité du code.

## Principes Généraux

### Philosophie

1. **Lisibilité avant tout** - Le code est lu plus souvent qu'il n'est écrit
2. **Cohérence** - Suivre les patterns existants
3. **Simplicité** - Préférer les solutions simples
4. **Explicite > Implicite** - Le code doit être évident
5. **Documentation** - Documenter le "pourquoi", pas le "quoi"

### PEP 8

Nous suivons [PEP 8](https://www.python.org/dev/peps/pep-0008/) avec quelques adaptations.

## Formatage

### Outil: Black

Nous utilisons **Black** pour le formatage automatique.

```bash
# Formater un fichier
black src/audit/permissions.py

# Formater tout le projet
black src/

# Vérifier sans modifier
black --check src/
```

**Configuration (.black.toml):**
```toml
[tool.black]
line-length = 100
target-version = ['py39', 'py310', 'py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''
```

### Longueur de Ligne

- **Maximum:** 100 caractères (Black default: 88, nous utilisons 100)
- **Docstrings:** 72 caractères

```python
# Bon
def create_user(
    connector: LDAPConnector,
    uid: str,
    cn: str,
    mail: str,
    attributes: Optional[Dict[str, Any]] = None,
) -> LDAPUser:
    """Crée un nouvel utilisateur LDAP."""
    pass

# Mauvais - trop long
def create_user(connector: LDAPConnector, uid: str, cn: str, mail: str, attributes: Optional[Dict[str, Any]] = None) -> LDAPUser:
    pass
```

### Indentation

- **4 espaces** (jamais de tabs)
- Continuation alignée ou indentée de 4 espaces

```python
# Bon - aligned with delimiter
foo = long_function_name(
    var_one,
    var_two,
    var_three,
    var_four,
)

# Bon - hanging indent
foo = long_function_name(
    var_one, var_two,
    var_three, var_four,
)

# Mauvais - arguments sur première ligne sans indent
foo = long_function_name(var_one,
    var_two, var_three,
    var_four)
```

### Espaces

**Autour des opérateurs:**
```python
# Bon
x = 1
y = 2
result = x + y
z = (x + y) * (x - y)

# Mauvais
x=1
y=2
result=x+y
z=(x+y)*(x-y)
```

**Après virgules:**
```python
# Bon
spam(ham[1], {eggs: 2})
[1, 2, 3]

# Mauvais
spam(ham[1],{eggs:2})
[1,2,3]
```

**Pas d'espaces superflus:**
```python
# Bon
spam(ham[1], {eggs: 2})
dct['key'] = lst[index]

# Mauvais
spam( ham[ 1 ], { eggs: 2 } )
dct ['key'] = lst [index]
```

### Lignes Vides

```python
# 2 lignes vides avant les classes et fonctions top-level
import sys


def top_level_function():
    pass


class TopLevelClass:
    pass


# 1 ligne vide entre les méthodes
class MyClass:
    def method_one(self):
        pass

    def method_two(self):
        pass

    def method_three(self):
        pass


# Grouper logiquement dans les fonctions
def complex_function():
    # Group 1: Setup
    x = 1
    y = 2
    z = 3

    # Group 2: Processing
    result = process(x, y)
    final = transform(result, z)

    # Group 3: Return
    return final
```

## Imports

### Ordre des Imports

```python
"""Module docstring."""

# 1. Standard library imports
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

# 2. Related third-party imports
import click
import yaml
from ldap3 import ALL, Connection, Server
from pydantic import BaseModel, Field

# 3. Local application imports
from src.core.config import load_config
from src.core.connector import LDAPConnector
from src.core.models import AuditIssue, Config, AlertLevel
```

### Style des Imports

```python
# Bon - imports absolus
from src.core.models import Config
from src.audit.users import UserAuditor

# Mauvais - imports relatifs
from ..core.models import Config
from .users import UserAuditor

# Exception: imports relatifs OK dans les tests
# tests/unit/test_audit.py
from ..conftest import sample_config
```

### Imports Spécifiques vs Wildcard

```python
# Bon - imports spécifiques
from typing import Any, Dict, List, Optional
from src.core.models import Config, LDAPUser, AuditIssue

# Mauvais - wildcard import
from typing import *
from src.core.models import *

# Exception: OK pour __init__.py
# src/audit/__init__.py
from src.audit.health import *
from src.audit.users import *
```

## Nommage

### Conventions Générales

| Type | Convention | Exemple |
|------|-----------|---------|
| Module | `snake_case` | `user_auditor.py` |
| Package | `lowercase` | `audit/` |
| Classe | `PascalCase` | `UserAuditor` |
| Exception | `PascalCase` + Error | `ValidationError` |
| Fonction | `snake_case` | `audit_users()` |
| Méthode | `snake_case` | `check_health()` |
| Variable | `snake_case` | `user_count` |
| Constante | `UPPER_SNAKE_CASE` | `DEFAULT_PORT` |
| Privé | `_préfixe` | `_internal_method()` |
| Type Variable | `PascalCase` | `T`, `AnyStr` |

### Exemples Détaillés

**Classes:**
```python
# Bon
class UserAuditor:
    pass

class LDAPConnection:
    pass

class HTTPResponse:  # Acronymes en majuscules
    pass

# Mauvais
class user_auditor:
    pass

class ldapConnection:
    pass
```

**Fonctions et Méthodes:**
```python
# Bon
def audit_users():
    pass

def get_user_by_dn():
    pass

def _internal_helper():  # Privé
    pass

# Mauvais
def AuditUsers():
    pass

def GetUserByDN():
    pass
```

**Variables:**
```python
# Bon
user_count = 100
total_issues = 0
is_connected = True
has_permission = False

# Mauvais
UserCount = 100
totalIssues = 0
isconnected = True
```

**Constantes:**
```python
# Bon
DEFAULT_PORT = 389
MAX_RETRY_ATTEMPTS = 3
LDAP_TIMEOUT_SECONDS = 10

# Mauvais
default_port = 389
MaxRetryAttempts = 3
```

### Nommage Descriptif

```python
# Bon - noms descriptifs
def calculate_inactive_users_count(users: List[LDAPUser], days: int) -> int:
    inactive_count = 0
    threshold_date = datetime.now() - timedelta(days=days)

    for user in users:
        if user.last_logon and user.last_logon < threshold_date:
            inactive_count += 1

    return inactive_count

# Mauvais - noms cryptiques
def calc(u: List, d: int) -> int:
    c = 0
    t = datetime.now() - timedelta(days=d)

    for x in u:
        if x.ll and x.ll < t:
            c += 1

    return c
```

## Type Hints

### Utilisation Systématique

```python
from typing import Any, Dict, List, Optional

# Bon - tous les paramètres et retour typés
def search_users(
    connector: LDAPConnector,
    search_filter: str,
    attributes: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """Recherche des utilisateurs LDAP."""
    if attributes is None:
        attributes = ["uid", "cn", "mail"]

    return connector.search(
        search_base="ou=users,dc=example,dc=com",
        search_filter=search_filter,
        attributes=attributes,
    )

# Mauvais - pas de types
def search_users(connector, search_filter, attributes=None):
    if attributes is None:
        attributes = ["uid", "cn", "mail"]
    return connector.search(...)
```

### Types Courants

```python
from typing import Any, Dict, List, Optional, Tuple, Union

# Types simples
name: str = "John"
age: int = 30
score: float = 95.5
is_active: bool = True

# Collections
users: List[str] = ["user1", "user2"]
config: Dict[str, Any] = {"key": "value"}
coordinates: Tuple[int, int] = (10, 20)

# Optional (peut être None)
email: Optional[str] = None
count: Optional[int] = get_count()

# Union (plusieurs types possibles)
result: Union[int, str] = get_result()

# Callable
from typing import Callable
validator: Callable[[str], bool] = lambda x: len(x) > 0
```

### Annotations de Variables

```python
# Python 3.9+
from typing import Optional

class UserAuditor:
    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        self.connector: LDAPConnector = connector
        self.config: Config = config
        self._cache: Dict[str, Any] = {}
        self._last_check: Optional[datetime] = None
```

### Validation avec MyPy

```bash
# Vérifier les types
mypy src/

# Configuration mypy.ini
[mypy]
python_version = 3.9
warn_return_any = True
warn_unused_configs = True
disallow_untyped_defs = True
```

## Documentation

### Docstrings - Style Google

Nous utilisons le **Google Style** pour les docstrings.

#### Module Docstring

```python
"""Module d'audit des utilisateurs LDAP.

Ce module fournit la classe UserAuditor qui effectue diverses
vérifications sur les comptes utilisateurs LDAP, incluant:
- Détection des comptes inactifs
- Vérification des attributs requis
- Validation des mots de passe

Example:
    >>> from src.audit.users import UserAuditor
    >>> auditor = UserAuditor(connector, config)
    >>> issues = auditor.audit_users()
"""
```

#### Classe Docstring

```python
class UserAuditor:
    """Auditeur pour les comptes utilisateurs LDAP.

    Cette classe effectue des vérifications de santé et de sécurité
    sur les comptes utilisateurs d'un annuaire LDAP.

    Attributes:
        connector: Instance de LDAPConnector pour les requêtes LDAP
        config: Configuration de l'application
        last_audit: Timestamp du dernier audit (None si jamais exécuté)

    Example:
        >>> auditor = UserAuditor(connector, config)
        >>> issues = auditor.audit_users(check_inactive=True)
        >>> print(f"Found {len(issues)} issues")
    """

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialise l'auditeur d'utilisateurs.

        Args:
            connector: Connecteur LDAP pour effectuer les requêtes
            config: Configuration de l'application

        Raises:
            ValueError: Si le connector ou config est None
        """
        if connector is None or config is None:
            raise ValueError("connector and config are required")

        self.connector = connector
        self.config = config
        self.last_audit: Optional[datetime] = None
```

#### Fonction/Méthode Docstring

```python
def audit_users(
    self,
    check_inactive: bool = True,
    check_attributes: bool = True,
    inactive_threshold_days: Optional[int] = None,
) -> List[AuditIssue]:
    """Effectue l'audit complet des utilisateurs LDAP.

    Parcourt tous les utilisateurs et effectue différentes vérifications
    selon les paramètres fournis. Retourne une liste de problèmes découverts.

    Args:
        check_inactive: Si True, vérifie les comptes inactifs
        check_attributes: Si True, vérifie les attributs requis
        inactive_threshold_days: Nombre de jours d'inactivité avant alerte.
            Si None, utilise la valeur de la configuration (défaut: 90)

    Returns:
        Liste des problèmes découverts. Liste vide si aucun problème.

    Raises:
        LDAPException: Si impossible de se connecter au serveur LDAP
        ValueError: Si inactive_threshold_days est négatif

    Example:
        >>> auditor = UserAuditor(connector, config)
        >>> issues = auditor.audit_users(
        ...     check_inactive=True,
        ...     inactive_threshold_days=60
        ... )
        >>> for issue in issues:
        ...     print(f"{issue.level}: {issue.title}")
    """
    issues: List[AuditIssue] = []

    # Validation
    if inactive_threshold_days is not None and inactive_threshold_days < 0:
        raise ValueError("inactive_threshold_days must be positive")

    # Implementation...
    return issues
```

#### Docstring pour Property

```python
@property
def is_connected(self) -> bool:
    """Indique si le connecteur est actuellement connecté.

    Returns:
        True si connecté, False sinon
    """
    return self.connector.is_connected
```

### Commentaires Inline

```python
def complex_calculation(data: List[int]) -> int:
    """Effectue un calcul complexe."""

    # Filtrer les valeurs invalides (négatives et nulles)
    valid_data = [x for x in data if x > 0]

    # Calculer la moyenne pondérée
    # Formule: sum(x * weight) / sum(weight)
    # où weight = log(x + 1)
    weights = [math.log(x + 1) for x in valid_data]
    weighted_sum = sum(x * w for x, w in zip(valid_data, weights))
    total_weight = sum(weights)

    # Éviter division par zéro
    if total_weight == 0:
        return 0

    return int(weighted_sum / total_weight)
```

**Quand commenter:**
- ✅ Expliquer le "pourquoi"
- ✅ Clarifier un algorithme complexe
- ✅ Documenter les workarounds
- ✅ Expliquer les choix non évidents
- ❌ Répéter ce que le code fait déjà

```python
# Bon
# Utilise un timeout court car ce serveur est parfois lent à répondre
connection_timeout = 5

# On ne peut pas utiliser GROUP BY ici à cause d'une limitation LDAP
# Donc on groupe manuellement en Python
grouped_results = manually_group(results)

# Mauvais
# Incrémente le compteur
counter += 1

# Boucle sur les utilisateurs
for user in users:
    process(user)
```

## Structure du Code

### Organisation d'une Classe

```python
class ExampleClass:
    """Docstring de la classe."""

    # 1. Variables de classe (constantes)
    DEFAULT_TIMEOUT = 10
    MAX_RETRIES = 3

    # 2. __init__
    def __init__(self, param: str) -> None:
        """Docstring du constructeur."""
        self.param = param
        self._private_var = 0

    # 3. Properties
    @property
    def value(self) -> int:
        """Docstring de la property."""
        return self._private_var

    # 4. Méthodes publiques (ordre logique, pas alphabétique)
    def main_method(self) -> None:
        """Méthode principale."""
        pass

    def helper_method(self) -> None:
        """Méthode helper."""
        pass

    # 5. Méthodes privées
    def _internal_method(self) -> None:
        """Méthode interne."""
        pass

    # 6. Méthodes spéciales (__str__, __repr__, etc.)
    def __str__(self) -> str:
        """String representation."""
        return f"ExampleClass(param={self.param})"

    def __repr__(self) -> str:
        """Developer representation."""
        return f"ExampleClass(param={self.param!r})"
```

### Organisation d'un Module

```python
"""Module docstring."""

# 1. Imports (stdlib, third-party, local)
import os
from typing import List

import click
from pydantic import BaseModel

from src.core.config import Config

# 2. Constantes du module
DEFAULT_PORT = 389
MAX_CONNECTIONS = 100

# 3. Fonctions helper privées
def _internal_helper() -> None:
    """Helper interne."""
    pass

# 4. Classes
class MainClass:
    """Classe principale."""
    pass

class HelperClass:
    """Classe helper."""
    pass

# 5. Fonctions publiques
def public_function() -> None:
    """Fonction publique."""
    pass

# 6. Code exécutable (si __main__)
if __name__ == "__main__":
    public_function()
```

## Bonnes Pratiques

### 1. SOLID Principles

#### Single Responsibility

```python
# Bon - une responsabilité par classe
class UserAuditor:
    """Audit des utilisateurs seulement."""
    def audit_users(self): pass

class GroupAuditor:
    """Audit des groupes seulement."""
    def audit_groups(self): pass

# Mauvais - trop de responsabilités
class Auditor:
    def audit_users(self): pass
    def audit_groups(self): pass
    def generate_report(self): pass
    def send_email(self): pass
```

#### Dependency Injection

```python
# Bon - dépendances injectées
class UserAuditor:
    def __init__(self, connector: LDAPConnector, config: Config):
        self.connector = connector
        self.config = config

# Mauvais - dépendances hard-codées
class UserAuditor:
    def __init__(self):
        self.connector = LDAPConnector("ldap://...")
        self.config = Config.load()
```

### 2. Gestion d'Erreurs

```python
# Bon - spécifique et informatif
try:
    user = connector.get_user(dn)
except LDAPException as e:
    raise UserNotFoundError(f"Cannot find user {dn}: {e}") from e
except ConnectionError as e:
    raise LDAPConnectionError(f"Connection failed: {e}") from e

# Mauvais - trop générique
try:
    user = connector.get_user(dn)
except Exception:
    pass  # Silencieux = problèmes cachés
```

### 3. Context Managers

```python
# Bon - utilise context manager
with LDAPConnector(config) as conn:
    users = conn.search("ou=users,dc=example,dc=com")
    # Connexion fermée automatiquement

# Acceptable - fermeture manuelle
conn = LDAPConnector(config)
try:
    users = conn.search("ou=users,dc=example,dc=com")
finally:
    conn.disconnect()
```

### 4. List Comprehensions

```python
# Bon - concis et lisible
active_users = [u for u in users if u.status == "active"]
user_emails = [u.mail for u in users if u.mail]

# Mauvais - trop complexe, utiliser une boucle normale
result = [
    process(x) for x in data
    if x.value > 10 and x.value < 100
    and x.category in allowed_categories
    and validate(x)
]  # Trop complexe!

# Mieux pour cas complexe
result = []
for x in data:
    if x.value > 10 and x.value < 100:
        if x.category in allowed_categories:
            if validate(x):
                result.append(process(x))
```

### 5. Valeurs par Défaut

```python
# Bon - valeurs immuables
def function(name: str, count: int = 0, prefix: str = "user"):
    pass

# Bon - default_factory pour mutables
class Config(BaseModel):
    attributes: Dict[str, Any] = Field(default_factory=dict)
    members: List[str] = Field(default_factory=list)

# DANGER - mutable comme défaut
def bad_function(items: List[str] = []):  # Partagé entre appels!
    items.append("new")
    return items

# Correction
def good_function(items: Optional[List[str]] = None):
    if items is None:
        items = []
    items.append("new")
    return items
```

## Outils de Validation

### Configuration Pre-commit

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.9

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: ['--max-line-length=100', '--extend-ignore=E203,W503']

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ['--profile', 'black']
```

### Installation

```bash
# Installer pre-commit
pip install pre-commit

# Installer les hooks
pre-commit install

# Exécuter manuellement
pre-commit run --all-files
```

## Checklist Style

Avant de commit:

- [ ] Code formaté avec Black
- [ ] Pas d'erreurs Flake8
- [ ] MyPy passe sans erreurs
- [ ] Tous les imports sont organisés (isort)
- [ ] Docstrings complètes (Google style)
- [ ] Type hints partout
- [ ] Noms descriptifs et cohérents
- [ ] Commentaires pour le code complexe seulement
- [ ] Pas de code mort ou commenté
- [ ] Tests ajoutés/mis à jour

## Ressources

- [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- [PEP 257 - Docstrings](https://www.python.org/dev/peps/pep-0257/)
- [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Black Documentation](https://black.readthedocs.io/)
- [MyPy Documentation](https://mypy.readthedocs.io/)

## Conclusion

Un code propre et bien formaté:
- Est plus facile à lire et comprendre
- Réduit les bugs
- Facilite les reviews
- Améliore la collaboration
- Rend le projet professionnel

**Consistency is key!** 🔑
