# Contrôle d'Accès et Permissions

## Table des Matières

- [Introduction](#introduction)
- [Architecture de Contrôle d'Accès](#architecture-de-contrôle-daccès)
- [Modèle RBAC](#modèle-rbac)
- [Modèle ABAC](#modèle-abac)
- [Authentification](#authentification)
- [Autorisation](#autorisation)
- [Gestion des Rôles](#gestion-des-rôles)
- [Permissions Granulaires](#permissions-granulaires)
- [Délégation d'Accès](#délégation-daccès)
- [Séparation des Privilèges](#séparation-des-privilèges)
- [Audit des Accès](#audit-des-accès)
- [Intégrations](#intégrations)
- [Meilleures Pratiques](#meilleures-pratiques)

## Introduction

Le contrôle d'accès est essentiel pour garantir que seules les personnes autorisées peuvent accéder aux fonctionnalités et données de LDAP Health Monitor. Ce guide couvre l'implémentation complète du contrôle d'accès basé sur les rôles (RBAC) et les attributs (ABAC).

### Principes Fondamentaux

```
┌─────────────────────────────────────────────────────────┐
│          PRINCIPE DU MOINDRE PRIVILÈGE                   │
├─────────────────────────────────────────────────────────┤
│  1. Authentification  →  Qui êtes-vous ?                │
│  2. Autorisation      →  Que pouvez-vous faire ?        │
│  3. Audit            →  Qu'avez-vous fait ?            │
└─────────────────────────────────────────────────────────┘
```

### Flux de Contrôle d'Accès

```
┌──────────────┐
│  Utilisateur │
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ Authentification │
│  - Identité      │
│  - MFA          │
│  - Session      │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│  Autorisation    │
│  - RBAC         │
│  - ABAC         │
│  - Policies     │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Exécution      │
│   de l'Action    │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│   Audit Log      │
└──────────────────┘
```

## Architecture de Contrôle d'Accès

### Configuration Générale

```yaml
# config/access-control.yml
access_control:
  # Mode de contrôle d'accès
  mode: "rbac"  # ou "abac", "hybrid"

  # Activation globale
  enabled: true

  # Politique par défaut
  default_policy: "deny"  # deny-by-default

  # Sources d'identité
  identity_sources:
    - type: "local"
      priority: 1

    - type: "ldap"
      priority: 2
      config:
        server: "ldaps://ldap.example.com"
        base_dn: "ou=users,dc=example,dc=com"

    - type: "oauth2"
      priority: 3
      config:
        provider: "keycloak"
        issuer: "https://auth.example.com/realms/ldap-monitor"

  # Cache des décisions
  cache:
    enabled: true
    ttl: 300  # 5 minutes
    max_entries: 10000
```

### Matrice de Permissions

```yaml
permissions_matrix:
  # Ressources
  resources:
    - audit
    - monitoring
    - management
    - configuration
    - users
    - reports

  # Actions
  actions:
    - read
    - write
    - execute
    - delete
    - admin

  # Matrice Rôle → Ressource → Actions
  mappings:
    viewer:
      audit: [read]
      monitoring: [read]
      reports: [read]

    operator:
      audit: [read, execute]
      monitoring: [read, execute]
      reports: [read, write]

    admin:
      audit: [read, write, execute, delete]
      monitoring: [read, write, execute, delete, admin]
      management: [read, write, execute, delete]
      configuration: [read, write]
      users: [read, write, delete]
      reports: [read, write, delete]
```

## Modèle RBAC

### Définition des Rôles

```yaml
# config/rbac.yml
rbac:
  enabled: true

  # Hiérarchie des rôles
  role_hierarchy:
    - name: "super_admin"
      inherits: []
      description: "Accès complet au système"

    - name: "admin"
      inherits: []
      description: "Administration standard"

    - name: "security_admin"
      inherits: []
      description: "Administration sécurité uniquement"

    - name: "operator"
      inherits: ["viewer"]
      description: "Opérations quotidiennes"

    - name: "viewer"
      inherits: []
      description: "Lecture seule"

    - name: "auditor"
      inherits: ["viewer"]
      description: "Audit et conformité"

  # Définition détaillée des rôles
  roles:
    # Super Administrateur
    - name: "super_admin"
      permissions:
        - "*:*:*"  # Tous les droits

      restrictions:
        require_mfa: true
        allowed_ips:
          - "10.1.0.0/16"
        allowed_hours: "00:00-23:59"
        max_concurrent_sessions: 1

    # Administrateur
    - name: "admin"
      permissions:
        # Audit
        - "audit:*:*"

        # Monitoring
        - "monitoring:*:*"

        # Gestion
        - "management:users:read,write,delete"
        - "management:groups:read,write,delete"
        - "management:cleanup:execute"

        # Configuration
        - "configuration:*:read,write"

        # Rapports
        - "reports:*:*"

      restrictions:
        require_mfa: true
        allowed_ips:
          - "10.1.0.0/16"

    # Administrateur Sécurité
    - name: "security_admin"
      permissions:
        # Sécurité
        - "security:audit_logs:read"
        - "security:access_control:read,write"
        - "security:policies:read,write"

        # Audit
        - "audit:security:read,execute"

        # Configuration sécurité
        - "configuration:security:read,write"

      restrictions:
        require_mfa: true
        allowed_ips:
          - "10.1.100.0/24"
        session_timeout: 1800

    # Opérateur
    - name: "operator"
      permissions:
        # Audit
        - "audit:health:read,execute"
        - "audit:users:read,execute"
        - "audit:groups:read,execute"
        - "audit:structure:read,execute"

        # Monitoring
        - "monitoring:metrics:read"
        - "monitoring:alerts:read"
        - "monitoring:dashboard:read"

        # Rapports
        - "reports:*:read,write"

        # Gestion limitée
        - "management:users:read"
        - "management:groups:read"

      restrictions:
        require_mfa: false
        allowed_hours: "07:00-19:00"

    # Viewer (Lecteur)
    - name: "viewer"
      permissions:
        # Lecture seule
        - "audit:*:read"
        - "monitoring:*:read"
        - "reports:*:read"
        - "management:*:read"

      restrictions:
        require_mfa: false

    # Auditeur
    - name: "auditor"
      permissions:
        # Audit complet
        - "audit:*:read,execute"

        # Logs de sécurité
        - "security:audit_logs:read,export"

        # Rapports
        - "reports:*:read,write,export"

        # Conformité
        - "compliance:*:read,execute"

      restrictions:
        require_mfa: true
        allowed_ips:
          - "10.1.200.0/24"
```

### Attribution des Rôles

```yaml
# config/role-assignments.yml
role_assignments:
  # Attribution par utilisateur
  users:
    - username: "john.doe"
      roles:
        - "admin"
      effective_from: "2024-01-01"
      effective_until: "2024-12-31"

    - username: "jane.smith"
      roles:
        - "operator"
      effective_from: "2024-01-01"

    - username: "security.team"
      roles:
        - "security_admin"
        - "auditor"

  # Attribution par groupe LDAP
  ldap_groups:
    - dn: "cn=ldap-admins,ou=groups,dc=example,dc=com"
      roles:
        - "admin"

    - dn: "cn=ldap-operators,ou=groups,dc=example,dc=com"
      roles:
        - "operator"

    - dn: "cn=security-team,ou=groups,dc=example,dc=com"
      roles:
        - "security_admin"

  # Attribution dynamique
  dynamic_assignments:
    - condition: "user.department == 'IT'"
      roles:
        - "operator"

    - condition: "user.title contains 'Security'"
      roles:
        - "security_admin"
```

## Modèle ABAC

### Politiques Basées sur les Attributs

```yaml
# config/abac.yml
abac:
  enabled: true

  # Attributs utilisateur
  user_attributes:
    - name
    - email
    - department
    - title
    - clearance_level
    - groups
    - location

  # Attributs de ressource
  resource_attributes:
    - type
    - classification
    - owner
    - created_at
    - tags

  # Attributs d'environnement
  environment_attributes:
    - time
    - date
    - day_of_week
    - ip_address
    - network_zone
    - request_origin

  # Politiques ABAC
  policies:
    # Politique 1: Accès basé sur le département
    - name: "department_based_access"
      description: "Accès basé sur le département"
      effect: "allow"
      conditions:
        - "user.department == 'IT' AND resource.type == 'audit'"
        - "user.department == 'Security' AND resource.type == 'security_audit'"

    # Politique 2: Accès temporel
    - name: "business_hours_only"
      description: "Accès pendant les heures ouvrables uniquement"
      effect: "allow"
      conditions:
        - "environment.day_of_week in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']"
        - "environment.time >= '08:00' AND environment.time <= '18:00'"

    # Politique 3: Accès basé sur la classification
    - name: "clearance_based_access"
      description: "Accès basé sur le niveau d'habilitation"
      effect: "allow"
      conditions:
        - "user.clearance_level >= resource.classification"

    # Politique 4: Accès géographique
    - name: "geographic_restriction"
      description: "Restriction géographique"
      effect: "deny"
      conditions:
        - "environment.network_zone == 'external' AND resource.classification > 2"

    # Politique 5: Propriétaire de ressource
    - name: "resource_owner_access"
      description: "Le propriétaire a tous les droits"
      effect: "allow"
      conditions:
        - "user.email == resource.owner"
```

### Moteur de Décision ABAC

```python
#!/usr/bin/env python3
# abac-engine.py

from typing import Dict, List, Any
import re
from datetime import datetime

class ABACEngine:
    def __init__(self, policies: List[Dict]):
        self.policies = policies

    def evaluate(self,
                 user_attrs: Dict[str, Any],
                 resource_attrs: Dict[str, Any],
                 environment_attrs: Dict[str, Any],
                 action: str) -> bool:
        """
        Évalue si l'accès doit être accordé
        """

        # Contexte complet
        context = {
            'user': user_attrs,
            'resource': resource_attrs,
            'environment': environment_attrs,
            'action': action
        }

        # Par défaut: deny
        decision = False

        # Évaluer chaque politique
        for policy in self.policies:
            if self._evaluate_policy(policy, context):
                if policy['effect'] == 'allow':
                    decision = True
                elif policy['effect'] == 'deny':
                    return False  # Deny l'emporte toujours

        return decision

    def _evaluate_policy(self, policy: Dict, context: Dict) -> bool:
        """
        Évalue une politique spécifique
        """

        conditions = policy.get('conditions', [])

        # Toutes les conditions doivent être vraies
        for condition in conditions:
            if not self._evaluate_condition(condition, context):
                return False

        return True

    def _evaluate_condition(self, condition: str, context: Dict) -> bool:
        """
        Évalue une condition
        """

        try:
            # Remplacer les références par les valeurs
            evaluated = condition

            # Remplacer user.attr
            for attr, value in context['user'].items():
                evaluated = evaluated.replace(f'user.{attr}', repr(value))

            # Remplacer resource.attr
            for attr, value in context['resource'].items():
                evaluated = evaluated.replace(f'resource.{attr}', repr(value))

            # Remplacer environment.attr
            for attr, value in context['environment'].items():
                evaluated = evaluated.replace(f'environment.{attr}', repr(value))

            # Évaluer l'expression
            return eval(evaluated)

        except Exception as e:
            print(f"Error evaluating condition: {e}")
            return False


# Exemple d'utilisation
if __name__ == '__main__':
    policies = [
        {
            'name': 'business_hours',
            'effect': 'allow',
            'conditions': [
                "environment.hour >= 8 and environment.hour <= 18"
            ]
        },
        {
            'name': 'clearance_based',
            'effect': 'allow',
            'conditions': [
                "user.clearance >= resource.classification"
            ]
        }
    ]

    engine = ABACEngine(policies)

    # Test
    user = {'clearance': 3, 'department': 'IT'}
    resource = {'classification': 2, 'type': 'audit'}
    environment = {'hour': 10, 'day': 'Monday'}

    result = engine.evaluate(user, resource, environment, 'read')
    print(f"Access granted: {result}")
```

## Authentification

### Méthodes d'Authentification

```yaml
# config/authentication.yml
authentication:
  # Méthodes supportées
  methods:
    - local
    - ldap
    - oauth2
    - saml
    - kerberos

  # Configuration par méthode
  local:
    enabled: true
    password_policy:
      min_length: 12
      require_complexity: true
    lockout:
      enabled: true
      max_attempts: 5
      lockout_duration: 1800

  ldap:
    enabled: true
    server: "ldaps://ldap.example.com:636"
    base_dn: "ou=users,dc=example,dc=com"
    bind_dn: "cn=auth-service,dc=example,dc=com"
    attributes:
      username: "uid"
      email: "mail"
      groups: "memberOf"

  oauth2:
    enabled: true
    provider: "keycloak"
    issuer: "https://auth.example.com/realms/ldap-monitor"
    client_id: "ldap-health-monitor"
    scopes:
      - openid
      - profile
      - email
      - roles

  saml:
    enabled: false
    idp_metadata_url: "https://idp.example.com/metadata"
    sp_entity_id: "ldap-health-monitor"

  # Multi-facteurs
  mfa:
    enabled: true
    required_for_roles:
      - admin
      - security_admin
      - super_admin

    methods:
      - totp
      - webauthn
      - sms

    totp:
      issuer: "LDAP Health Monitor"
      algorithm: "SHA256"
      digits: 6
      period: 30

    webauthn:
      rp_name: "LDAP Health Monitor"
      rp_id: "monitor.example.com"
      require_resident_key: false
```

### Session Management

```yaml
# config/sessions.yml
sessions:
  # Type de stockage
  storage: "redis"  # ou "memory", "database"

  # Configuration Redis
  redis:
    host: "localhost"
    port: 6379
    db: 0
    password_env: "REDIS_PASSWORD"
    tls: true

  # Paramètres de session
  cookie:
    name: "ldap_monitor_session"
    secure: true
    http_only: true
    same_site: "strict"
    domain: ".example.com"

  # Timeouts
  timeout:
    idle: 900        # 15 minutes d'inactivité
    absolute: 28800  # 8 heures maximum

  # Limitations
  max_concurrent_sessions_per_user: 3

  # Rotation des tokens
  rotate_on_privilege_change: true
  rotate_interval: 3600

  # Révocation
  revocation:
    enabled: true
    check_interval: 60
```

## Autorisation

### Vérification des Permissions

```python
#!/usr/bin/env python3
# authorization.py

from typing import List, Set
from functools import wraps

class AuthorizationError(Exception):
    pass

class Permission:
    def __init__(self, resource: str, action: str, scope: str = "*"):
        self.resource = resource
        self.action = action
        self.scope = scope

    def __str__(self):
        return f"{self.resource}:{self.scope}:{self.action}"

    def matches(self, required: 'Permission') -> bool:
        """Vérifie si cette permission satisfait celle requise"""

        # Wildcard matching
        if self.resource == "*" or self.resource == required.resource:
            if self.scope == "*" or self.scope == required.scope:
                if self.action == "*" or self.action == required.action:
                    return True

        return False


class Role:
    def __init__(self, name: str, permissions: List[Permission]):
        self.name = name
        self.permissions = permissions

    def has_permission(self, required: Permission) -> bool:
        """Vérifie si le rôle a la permission requise"""
        return any(p.matches(required) for p in self.permissions)


class User:
    def __init__(self, username: str, roles: List[Role]):
        self.username = username
        self.roles = roles

    def has_permission(self, required: Permission) -> bool:
        """Vérifie si l'utilisateur a la permission requise"""
        return any(role.has_permission(required) for role in self.roles)

    def get_all_permissions(self) -> Set[str]:
        """Retourne toutes les permissions de l'utilisateur"""
        perms = set()
        for role in self.roles:
            for perm in role.permissions:
                perms.add(str(perm))
        return perms


class AuthorizationManager:
    def __init__(self):
        self.users = {}
        self.roles = {}

    def check_permission(self, username: str, resource: str,
                        action: str, scope: str = "*") -> bool:
        """Vérifie si un utilisateur a une permission"""

        user = self.users.get(username)
        if not user:
            return False

        required = Permission(resource, action, scope)
        return user.has_permission(required)

    def require_permission(resource: str, action: str, scope: str = "*"):
        """Décorateur pour vérifier les permissions"""

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                # Récupérer l'utilisateur du contexte
                username = kwargs.get('username') or kwargs.get('user')

                if not username:
                    raise AuthorizationError("No user context")

                # Vérifier la permission
                auth_manager = kwargs.get('auth_manager')
                if not auth_manager:
                    raise AuthorizationError("No auth manager")

                if not auth_manager.check_permission(username, resource, action, scope):
                    raise AuthorizationError(
                        f"User {username} lacks permission {resource}:{scope}:{action}"
                    )

                return func(*args, **kwargs)

            return wrapper
        return decorator


# Exemple d'utilisation
@AuthorizationManager.require_permission('audit', 'execute', 'health')
def run_health_audit(username: str, auth_manager: AuthorizationManager):
    print(f"Running health audit for {username}")
    # ... logique de l'audit


# Configuration
if __name__ == '__main__':
    # Créer des permissions
    admin_perms = [
        Permission("*", "*", "*")
    ]

    operator_perms = [
        Permission("audit", "read", "*"),
        Permission("audit", "execute", "*"),
        Permission("monitoring", "read", "*")
    ]

    # Créer des rôles
    admin_role = Role("admin", admin_perms)
    operator_role = Role("operator", operator_perms)

    # Créer des utilisateurs
    admin_user = User("john.doe", [admin_role])
    operator_user = User("jane.smith", [operator_role])

    # Manager
    auth_manager = AuthorizationManager()
    auth_manager.users = {
        "john.doe": admin_user,
        "jane.smith": operator_user
    }

    # Tests
    print(auth_manager.check_permission("john.doe", "audit", "execute"))  # True
    print(auth_manager.check_permission("jane.smith", "audit", "execute"))  # True
    print(auth_manager.check_permission("jane.smith", "config", "write"))  # False
```

## Gestion des Rôles

### Interface de Gestion

```bash
#!/bin/bash
# role-management.sh

ROLES_FILE="/opt/ldap-monitor/config/roles.yml"
ASSIGNMENTS_FILE="/opt/ldap-monitor/config/role-assignments.yml"

# Lister les rôles
list_roles() {
    ldap-health-monitor admin roles list
}

# Créer un rôle
create_role() {
    local role_name="$1"

    cat <<EOF | ldap-health-monitor admin roles create
name: $role_name
permissions:
  - "audit:*:read"
  - "monitoring:*:read"
restrictions:
  require_mfa: false
EOF
}

# Assigner un rôle
assign_role() {
    local username="$1"
    local role_name="$2"

    ldap-health-monitor admin users assign-role \
        --user "$username" \
        --role "$role_name"
}

# Révoquer un rôle
revoke_role() {
    local username="$1"
    local role_name="$2"

    ldap-health-monitor admin users revoke-role \
        --user "$username" \
        --role "$role_name"
}

# Lister les permissions d'un utilisateur
list_user_permissions() {
    local username="$1"

    ldap-health-monitor admin users permissions \
        --user "$username"
}

# Audit des rôles
audit_roles() {
    echo "=== Audit des Rôles ==="

    # Rôles sans utilisateurs
    echo "Rôles inutilisés:"
    ldap-health-monitor admin roles audit --unused

    # Utilisateurs avec privilèges élevés
    echo "Utilisateurs avec privilèges admin:"
    ldap-health-monitor admin users list --role admin

    # Rôles expirés
    echo "Assignments expirés:"
    ldap-health-monitor admin roles audit --expired
}
```

## Permissions Granulaires

### Permissions au Niveau des Champs

```yaml
field_level_access:
  # Contrôle d'accès aux champs sensibles
  sensitive_fields:
    - name: "userPassword"
      roles_allowed: ["admin"]

    - name: "ssn"
      roles_allowed: ["admin", "hr_admin"]

    - name: "salary"
      roles_allowed: ["admin", "payroll_admin"]

  # Masquage des données
  data_masking:
    enabled: true

    rules:
      - field: "email"
        mask_for_roles: ["viewer"]
        mask_pattern: "***@***.***"

      - field: "phone"
        mask_for_roles: ["viewer", "operator"]
        mask_pattern: "***-***-****"
```

### Permissions Contextuelles

```yaml
contextual_permissions:
  # Permissions basées sur le contexte
  rules:
    # Limitation par heure
    - name: "after_hours_restriction"
      condition: "time < 08:00 OR time > 18:00"
      restrictions:
        deny_actions:
          - "management:*:delete"
          - "configuration:*:write"

    # Limitation par IP
    - name: "external_access_restriction"
      condition: "source_ip NOT IN allowed_ranges"
      restrictions:
        deny_actions:
          - "management:*:*"
          - "configuration:*:write"
        allow_actions:
          - "audit:*:read"
          - "monitoring:*:read"

    # Limitation par état système
    - name: "maintenance_mode"
      condition: "system.maintenance_mode == true"
      restrictions:
        allowed_roles:
          - "admin"
          - "super_admin"
```

## Délégation d'Accès

### Délégation Temporaire

```yaml
# config/delegation.yml
delegation:
  enabled: true

  # Politiques de délégation
  policies:
    # Délégation opérateur → admin temporaire
    - name: "temporary_admin"
      delegator_roles: ["admin"]
      delegate_roles: ["operator"]
      max_duration: 28800  # 8 heures
      require_approval: true
      approvers:
        - "security_admin"

    # Délégation pour urgence
    - name: "emergency_access"
      delegator_roles: ["super_admin"]
      delegate_roles: ["*"]
      max_duration: 3600  # 1 heure
      require_approval: false
      audit_level: "high"

  # Approbations
  approvals:
    required: true
    timeout: 3600  # 1 heure pour approuver
    quorum: 1  # Nombre d'approbateurs requis

  # Notifications
  notifications:
    on_delegation: true
    on_approval: true
    on_revocation: true
```

### Script de Délégation

```bash
#!/bin/bash
# delegate-access.sh

# Déléguer un accès temporaire
delegate_access() {
    local delegate_to="$1"
    local role="$2"
    local duration="$3"  # en secondes
    local reason="$4"

    ldap-health-monitor admin delegation create \
        --delegate-to "$delegate_to" \
        --role "$role" \
        --duration "$duration" \
        --reason "$reason"
}

# Approuver une délégation
approve_delegation() {
    local delegation_id="$1"

    ldap-health-monitor admin delegation approve \
        --id "$delegation_id"
}

# Révoquer une délégation
revoke_delegation() {
    local delegation_id="$1"

    ldap-health-monitor admin delegation revoke \
        --id "$delegation_id"
}

# Lister les délégations actives
list_delegations() {
    ldap-health-monitor admin delegation list --active
}
```

## Séparation des Privilèges

### Principe de Séparation

```yaml
separation_of_duties:
  enabled: true

  # Rôles mutuellement exclusifs
  mutually_exclusive:
    - roles: ["auditor", "admin"]
      reason: "Séparation audit / admin"

    - roles: ["developer", "production_admin"]
      reason: "Séparation dev / prod"

  # Opérations nécessitant plusieurs approbations
  multi_approval_operations:
    - operation: "user:delete"
      required_approvers: 2
      approver_roles: ["admin", "security_admin"]

    - operation: "config:security:write"
      required_approvers: 2
      approver_roles: ["admin", "security_admin"]

    - operation: "backup:restore"
      required_approvers: 3
      approver_roles: ["admin", "super_admin"]
```

## Audit des Accès

### Configuration de l'Audit

```yaml
access_audit:
  enabled: true

  # Événements à auditer
  events:
    - authentication_success
    - authentication_failure
    - authorization_success
    - authorization_failure
    - role_assignment
    - role_revocation
    - permission_change
    - delegation_created
    - delegation_approved
    - privileged_operation

  # Détails à capturer
  capture:
    - timestamp
    - username
    - user_ip
    - user_agent
    - action
    - resource
    - result
    - session_id
    - request_id

  # Stockage
  storage:
    type: "elasticsearch"
    endpoint: "https://logs.example.com:9200"
    index_pattern: "access-audit-%{+YYYY.MM.dd}"
    retention_days: 365

  # Alertes
  alerts:
    - event: "authorization_failure"
      threshold: 5
      window: 300
      action: "notify_security"

    - event: "privileged_operation"
      action: "log_detailed"
```

## Intégrations

### Intégration LDAP/Active Directory

```yaml
ldap_integration:
  enabled: true

  # Serveur LDAP
  server:
    uri: "ldaps://ldap.example.com:636"
    base_dn: "dc=example,dc=com"
    bind_dn: "cn=auth-service,dc=example,dc=com"

  # Mapping groupes → rôles
  group_role_mapping:
    - ldap_group: "cn=ldap-admins,ou=groups,dc=example,dc=com"
      roles: ["admin"]

    - ldap_group: "cn=ldap-operators,ou=groups,dc=example,dc=com"
      roles: ["operator"]

    - ldap_group: "cn=security-team,ou=groups,dc=example,dc=com"
      roles: ["security_admin", "auditor"]

  # Synchronisation
  sync:
    enabled: true
    interval: 3600  # 1 heure
    on_login: true
```

### Intégration OAuth2/OpenID Connect

```yaml
oauth2_integration:
  enabled: true

  # Provider
  provider: "keycloak"
  issuer: "https://auth.example.com/realms/ldap-monitor"

  # Client
  client_id: "ldap-health-monitor"
  client_secret_env: "OAUTH2_CLIENT_SECRET"

  # Scopes
  scopes:
    - openid
    - profile
    - email
    - roles

  # Mapping claims → rôles
  role_mapping:
    claim: "roles"
    mappings:
      - claim_value: "ldap-admin"
        roles: ["admin"]

      - claim_value: "ldap-operator"
        roles: ["operator"]
```

## Meilleures Pratiques

### Checklist de Sécurité

```markdown
## Configuration

- [ ] Principe du moindre privilège appliqué
- [ ] Rôles bien définis et documentés
- [ ] Séparation des privilèges configurée
- [ ] MFA activé pour les rôles privilégiés
- [ ] Timeouts de session configurés
- [ ] IP whitelisting activé

## Gestion des Rôles

- [ ] Revue régulière des rôles (trimestriel)
- [ ] Audit des utilisateurs privilégiés (mensuel)
- [ ] Révocation automatique des accès inactifs
- [ ] Documentation des changements de rôles
- [ ] Approbation requise pour rôles sensibles

## Audit

- [ ] Logs d'accès activés
- [ ] Monitoring des accès anormaux
- [ ] Alertes sur échecs d'authentification
- [ ] Rapports d'audit réguliers
- [ ] Rétention des logs conforme

## Délégation

- [ ] Politique de délégation définie
- [ ] Approbations configurées
- [ ] Durées maximales définies
- [ ] Audit des délégations actif
- [ ] Révocation automatique à expiration
```

---

**Note Importante**: Le contrôle d'accès est la pierre angulaire de la sécurité. Revoyez et auditez régulièrement vos configurations d'accès.
