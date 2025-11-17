# Configuration des Audits

## Table des Matières

- [Introduction](#introduction)
- [Types d'Audits](#types-daudits)
- [Configuration des Checks](#configuration-des-checks)
- [Seuils et Thresholds](#seuils-et-thresholds)
- [Attributs Obligatoires](#attributs-obligatoires)
- [Audit de Sécurité](#audit-de-sécurité)
- [Règles Personnalisées](#règles-personnalisées)
- [Niveaux de Sévérité](#niveaux-de-sévérité)
- [Planification des Audits](#planification-des-audits)
- [Rapports d'Audit](#rapports-daudit)
- [Exemples Pratiques](#exemples-pratiques)
- [Optimisation des Performances](#optimisation-des-performances)
- [Dépannage](#dépannage)

## Introduction

Les audits LDAP permettent de vérifier régulièrement la santé, la sécurité et la conformité de votre annuaire. Le système d'audit analyse plusieurs aspects de votre infrastructure LDAP et génère des rapports détaillés avec des recommandations.

### Objectifs des Audits

1. **Santé** : Vérifier la disponibilité et les performances du serveur
2. **Conformité** : S'assurer que les données respectent les règles définies
3. **Sécurité** : Détecter les vulnérabilités et risques potentiels
4. **Qualité** : Maintenir l'intégrité et la cohérence des données
5. **Optimisation** : Identifier les opportunités d'amélioration

### Fréquence Recommandée

```yaml
# Production
schedule:
  health: "*/5 * * * *"     # Toutes les 5 minutes
  users: "0 */6 * * *"      # Toutes les 6 heures
  groups: "0 */6 * * *"     # Toutes les 6 heures
  security: "0 2 * * *"     # Quotidien à 2h
  consistency: "0 3 * * 0"  # Hebdomadaire (dimanche 3h)
```

## Types d'Audits

### Health Check (Santé)

Vérifie la disponibilité et les performances du serveur LDAP.

```yaml
audit:
  checks:
    - health

  thresholds:
    response_time_warning_ms: 500
    response_time_critical_ms: 2000
    ssl_cert_expiry_warning_days: 30
```

**Éléments vérifiés :**

- Connectivité au serveur
- Temps de réponse
- Disponibilité du service
- Validité du certificat SSL/TLS
- Capacité d'authentification

**Exemple de résultat :**

```json
{
  "check": "health",
  "status": "healthy",
  "response_time": 145,
  "ssl_valid_until": "2025-12-31",
  "ssl_days_remaining": 120,
  "issues": []
}
```

### Users Audit (Audit Utilisateurs)

Analyse les comptes utilisateurs pour détecter les anomalies.

```yaml
audit:
  checks:
    - users

  thresholds:
    inactive_days: 90
    password_expiry_warning_days: 30
    max_password_age_days: 180

  required_user_attributes:
    - cn
    - sn
    - mail
    - uid
    - employeeNumber
```

**Vérifications effectuées :**

1. **Comptes inactifs**
   - Dernière connexion > seuil configuré
   - Recommandation : désactivation ou suppression

2. **Attributs manquants**
   - Comparaison avec la liste des attributs requis
   - Impact : problèmes d'authentification ou d'autorisation

3. **Doublons**
   - Emails en double
   - UIDs en double
   - Impact : confusion, erreurs d'attribution

4. **Comptes désactivés**
   - Inventaire des comptes désactivés
   - Recommandation : nettoyage périodique

**Configuration avancée :**

```yaml
audit:
  checks:
    - users

  users:
    # Détection des inactifs
    inactive_detection:
      enabled: true
      days: 90
      exclude_groups:
        - cn=service-accounts,ou=groups,dc=example,dc=com

    # Vérification des attributs
    attribute_validation:
      required:
        - cn
        - sn
        - mail
      recommended:
        - telephoneNumber
        - departmentNumber
      format_validation:
        mail: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
        telephoneNumber: "^\\+?[0-9]{10,}$"

    # Détection des doublons
    duplicate_detection:
      attributes:
        - mail
        - employeeNumber
      case_sensitive: false

    # Politique de mots de passe
    password_policy:
      check_expiry: true
      warning_days: 30
      max_age_days: 180
      check_never_expires: true
```

### Groups Audit (Audit Groupes)

Analyse les groupes pour optimiser la structure.

```yaml
audit:
  checks:
    - groups

  thresholds:
    max_empty_groups: 5
    max_group_size: 100
    max_nested_depth: 3
```

**Vérifications effectuées :**

1. **Groupes vides**
   - Groupes sans membres
   - Recommandation : suppression si non utilisés

2. **Groupes trop grands**
   - Groupes dépassant la taille maximale
   - Impact : performances, gestion difficile

3. **Membres orphelins**
   - Références à des utilisateurs inexistants
   - Recommandation : nettoyage

4. **Membres dupliqués**
   - Même membre plusieurs fois dans un groupe
   - Recommandation : déduplication

5. **Imbrication excessive**
   - Groupes imbriqués au-delà du seuil
   - Impact : complexité, performances

**Configuration avancée :**

```yaml
audit:
  checks:
    - groups

  groups:
    # Groupes vides
    empty_groups:
      max_allowed: 5
      exclude:
        - cn=template-*,ou=groups,dc=example,dc=com
      action: report  # report, warn, alert

    # Taille des groupes
    group_size:
      warning_threshold: 100
      critical_threshold: 500
      large_groups_action: split_recommendation

    # Membres orphelins
    orphaned_members:
      check_enabled: true
      auto_cleanup: false  # Ne jamais activer sans confirmation

    # Imbrication
    nesting:
      max_depth: 3
      check_circular: true
      visualize_tree: true

    # Cohérence
    consistency:
      check_member_exists: true
      check_duplicate_members: true
      validate_member_objectclass: true
```

### Structure Audit (Audit Structure)

Vérifie l'organisation de l'arborescence LDAP.

```yaml
audit:
  checks:
    - structure

  structure:
    # OUs attendues
    required_ous:
      - ou=users,dc=example,dc=com
      - ou=groups,dc=example,dc=com
      - ou=services,dc=example,dc=com

    # Profondeur maximale
    max_depth: 5

    # Naming conventions
    naming_patterns:
      users: "uid=*,ou=users,*"
      groups: "cn=*,ou=groups,*"
```

**Vérifications :**

- Présence des OUs requises
- Respect des conventions de nommage
- Profondeur de l'arborescence
- Organisation logique

### Security Audit (Audit Sécurité)

Analyse les aspects de sécurité de l'annuaire.

```yaml
audit:
  checks:
    - security

  security:
    check_password_policies: true
    alert_on_admin_creation: true
    alert_on_mass_delete: true
    mass_delete_threshold: 10
    check_privileged_accounts: true

    privileged_groups:
      - cn=admins,ou=groups,dc=example,dc=com
      - cn=domain admins,ou=groups,dc=example,dc=com
```

**Détails dans** [Audit de Sécurité](#audit-de-sécurité)

### Consistency Audit (Audit Cohérence)

Vérifie la cohérence globale des données.

```yaml
audit:
  checks:
    - consistency

  consistency:
    check_referential_integrity: true
    check_schema_compliance: true
    check_data_integrity: true
```

**Vérifications :**

- Intégrité référentielle (liens entre objets)
- Conformité au schéma LDAP
- Cohérence des données
- Validité des attributs

## Configuration des Checks

### Activation/Désactivation

```yaml
# Tous les checks
audit:
  checks:
    - health
    - users
    - groups
    - structure
    - security
    - consistency

# Checks minimaux (production)
audit:
  checks:
    - health
    - security

# Checks complets (hebdomadaire)
audit:
  checks:
    - health
    - users
    - groups
    - structure
    - security
    - consistency
```

### Configuration par Check

```yaml
audit:
  checks:
    - health
    - users
    - groups

  # Configuration spécifique par check
  health:
    enabled: true
    interval: 300  # secondes
    timeout: 10

  users:
    enabled: true
    interval: 21600  # 6 heures
    batch_size: 1000
    detailed_report: true

  groups:
    enabled: true
    interval: 21600
    check_membership: true
```

## Seuils et Thresholds

### Configuration Globale

```yaml
audit:
  thresholds:
    # Utilisateurs
    inactive_days: 90
    password_expiry_warning_days: 30
    max_password_age_days: 180
    min_password_length: 12

    # Groupes
    max_empty_groups: 5
    max_group_size: 100
    min_group_size: 1
    max_nested_depth: 3

    # Performance
    response_time_warning_ms: 500
    response_time_critical_ms: 2000
    max_query_time_ms: 5000

    # Sécurité
    ssl_cert_expiry_warning_days: 30
    max_failed_auth_attempts: 5
    password_complexity_score: 3
```

### Thresholds par Environnement

**Développement :**

```yaml
audit:
  thresholds:
    inactive_days: 30
    max_empty_groups: 20
    max_group_size: 50
    response_time_warning_ms: 1000
    response_time_critical_ms: 5000
```

**Staging :**

```yaml
audit:
  thresholds:
    inactive_days: 60
    max_empty_groups: 10
    max_group_size: 200
    response_time_warning_ms: 800
    response_time_critical_ms: 3000
```

**Production :**

```yaml
audit:
  thresholds:
    inactive_days: 90
    max_empty_groups: 5
    max_group_size: 100
    response_time_warning_ms: 500
    response_time_critical_ms: 2000
```

### Thresholds Personnalisés par Contexte

```yaml
audit:
  thresholds:
    # Défaut
    default:
      inactive_days: 90

    # Par OU
    per_ou:
      "ou=contractors,dc=example,dc=com":
        inactive_days: 30  # Plus strict pour contractuels
      "ou=services,dc=example,dc=com":
        inactive_days: 365  # Plus permissif pour services

    # Par groupe
    per_group:
      "cn=admins,ou=groups,dc=example,dc=com":
        max_group_size: 10  # Limiter les admins
        alert_on_change: true
```

## Attributs Obligatoires

### Configuration de Base

```yaml
audit:
  required_user_attributes:
    - cn
    - sn
    - mail
    - uid

  required_group_attributes:
    - cn
    - member
```

### Configuration Avancée

```yaml
audit:
  # Attributs utilisateurs
  required_user_attributes:
    mandatory:
      - cn          # Common Name
      - sn          # Surname
      - uid         # User ID
      - mail        # Email
    recommended:
      - telephoneNumber
      - departmentNumber
      - employeeNumber
    conditional:
      # Si employeeType = "employee"
      - condition: "employeeType == 'employee'"
        attributes:
          - employeeNumber
          - manager

  # Attributs groupes
  required_group_attributes:
    mandatory:
      - cn
      - member
    recommended:
      - description
      - owner
```

### Validation de Format

```yaml
audit:
  attribute_validation:
    mail:
      pattern: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
      severity: critical

    telephoneNumber:
      pattern: "^\\+?[0-9]{10,}$"
      severity: warning

    employeeNumber:
      pattern: "^[0-9]{6}$"
      severity: warning
      allow_empty: false

    uid:
      pattern: "^[a-z][a-z0-9._-]{2,15}$"
      severity: critical
      unique: true
```

## Audit de Sécurité

### Configuration Complète

```yaml
audit:
  security:
    # Politiques de mots de passe
    check_password_policies: true
    password_policy:
      min_length: 12
      require_uppercase: true
      require_lowercase: true
      require_numbers: true
      require_special_chars: true
      max_age_days: 90
      history_count: 5

    # Surveillance des comptes privilégiés
    check_privileged_accounts: true
    privileged_groups:
      - cn=admins,ou=groups,dc=example,dc=com
      - cn=domain admins,ou=groups,dc=example,dc=com
      - cn=enterprise admins,ou=groups,dc=example,dc=com
      - cn=schema admins,ou=groups,dc=example,dc=com

    privileged_monitoring:
      alert_on_member_add: true
      alert_on_member_remove: true
      require_justification: true
      max_members: 10

    # Alertes de sécurité
    alert_on_admin_creation: true
    alert_on_mass_delete: true
    mass_delete_threshold: 10
    alert_on_bulk_modification: true
    bulk_modification_threshold: 50

    # Audit des permissions
    check_acls: true
    suspicious_permissions:
      - "write access to ou=users"
      - "delete access to ou=groups"

    # Détection d'anomalies
    anomaly_detection:
      enabled: true
      check_login_patterns: true
      check_access_patterns: true
      unusual_activity_threshold: 3
```

### Règles de Sécurité

```yaml
audit:
  security_rules:
    # Règle 1: Comptes sans expiration
    - name: "password_never_expires"
      check: "userAccountControl & 0x10000"
      severity: critical
      message: "Mot de passe configuré pour ne jamais expirer"
      recommendation: "Activer l'expiration des mots de passe"

    # Règle 2: Comptes avec privilèges élevés
    - name: "elevated_privileges"
      check: "memberOf contains 'admins'"
      severity: warning
      message: "Compte avec privilèges administratifs"
      action: "review_quarterly"

    # Règle 3: Mots de passe faibles
    - name: "weak_password"
      check: "password_complexity_score < 3"
      severity: critical
      message: "Mot de passe ne respecte pas la politique de complexité"

    # Règle 4: Accès non autorisé
    - name: "unauthorized_access"
      check: "failed_auth_count > 5"
      severity: warning
      message: "Tentatives d'authentification échouées"
      action: "lock_account"
```

### Comptes de Service

```yaml
audit:
  security:
    service_accounts:
      # Identifier les comptes de service
      identification:
        - ou: "ou=services,dc=example,dc=com"
        - attribute: "employeeType=service"
        - naming: "svc-*"

      # Règles spécifiques
      rules:
        allow_never_expires: true
        require_strong_password: true
        check_usage: true
        alert_on_interactive_login: true

      # Rotation
      password_rotation:
        enabled: true
        interval_days: 180
        notify_days_before: 30
```

## Règles Personnalisées

### Création de Règles

```yaml
audit:
  custom_rules:
    # Règle: Utilisateurs sans manager
    - name: "no_manager"
      description: "Détecte les utilisateurs sans attribut manager"
      type: user
      condition:
        attribute_missing: "manager"
      severity: warning
      exclude:
        - "ou=contractors,dc=example,dc=com"

    # Règle: Groupes sans propriétaire
    - name: "no_owner"
      description: "Groupes sans attribut owner"
      type: group
      condition:
        attribute_missing: "owner"
      severity: info
      recommendation: "Assigner un propriétaire à chaque groupe"

    # Règle: Email non conforme
    - name: "invalid_email_domain"
      description: "Email avec domaine non autorisé"
      type: user
      condition:
        attribute: "mail"
        not_matches: ".*@(company\\.com|example\\.com)$"
      severity: critical
      action: "require_update"

    # Règle: Groupe trop ancien sans activité
    - name: "stale_group"
      description: "Groupe non modifié depuis plus d'un an"
      type: group
      condition:
        modified_before_days: 365
        member_count: 0
      severity: warning
      recommendation: "Vérifier et supprimer si non nécessaire"
```

### Règles Complexes

```yaml
audit:
  custom_rules:
    # Règle avec conditions multiples
    - name: "inactive_privileged_account"
      description: "Compte privilégié inactif"
      type: user
      conditions:
        all:
          - memberof_contains: "cn=admins"
          - last_logon_before_days: 30
      severity: critical
      action: "disable_account"
      notification:
        - security-team@company.com

    # Règle avec script personnalisé
    - name: "custom_validation"
      type: user
      script: |
        def validate(user):
            if user.get('department') == 'IT':
                if not user.get('telephoneNumber'):
                    return False, "IT staff must have phone number"
            return True, None
      severity: warning
```

## Niveaux de Sévérité

### Définition des Niveaux

```yaml
audit:
  severity_levels:
    info:
      description: "Information, pas d'action requise"
      color: "blue"
      notify: false

    warning:
      description: "Attention requise, pas d'urgence"
      color: "orange"
      notify: true
      channels: ["email"]

    critical:
      description: "Action immédiate requise"
      color: "red"
      notify: true
      channels: ["email", "slack"]
      escalate_after_hours: 2
```

### Attribution de Sévérité

```yaml
audit:
  severity_mapping:
    # Par type de problème
    missing_attributes:
      required: critical
      recommended: warning

    duplicate_values:
      unique_constraint: critical
      other: warning

    inactive_accounts:
      privileged: critical
      standard: warning
      service: info

    # Par contexte
    privileged_groups:
      any_change: critical

    service_accounts:
      password_expiry: warning
      unauthorized_access: critical
```

## Planification des Audits

### Cron Schedule

```yaml
audit:
  schedule:
    # Health check fréquent
    health:
      enabled: true
      cron: "*/5 * * * *"  # Toutes les 5 minutes

    # Audits quotidiens
    users:
      enabled: true
      cron: "0 2 * * *"    # 2h du matin

    groups:
      enabled: true
      cron: "0 3 * * *"    # 3h du matin

    # Audit sécurité quotidien
    security:
      enabled: true
      cron: "0 1 * * *"    # 1h du matin

    # Audit complet hebdomadaire
    full:
      enabled: true
      cron: "0 4 * * 0"    # Dimanche 4h
      checks:
        - health
        - users
        - groups
        - structure
        - security
        - consistency

    # Audit mensuel approfondi
    deep:
      enabled: true
      cron: "0 5 1 * *"    # 1er du mois à 5h
      detailed: true
      generate_report: true
```

### Configuration Avancée

```yaml
audit:
  schedule:
    # Planification par environnement
    production:
      health: "*/5 * * * *"
      security: "0 * * * *"
      full: "0 2 * * *"

    staging:
      health: "*/15 * * * *"
      full: "0 3 * * *"

    # Fenêtres de maintenance
    maintenance_windows:
      - start: "02:00"
        end: "04:00"
        days: ["sunday"]
        skip_alerts: true

    # Parallélisation
    parallel_execution:
      enabled: true
      max_concurrent: 3
      timeout_minutes: 30
```

## Rapports d'Audit

### Configuration des Rapports

```yaml
reports:
  audit:
    # Génération automatique
    auto_generate: true
    formats:
      - html
      - json
      - pdf

    # Contenu
    sections:
      - executive_summary
      - detailed_findings
      - statistics
      - trends
      - recommendations

    # Distribution
    recipients:
      - ldap-admins@company.com
      - security-team@company.com

    # Rétention
    retention_days: 365
    archive_old_reports: true
```

### Structure du Rapport

```yaml
reports:
  audit:
    template:
      # En-tête
      header:
        - audit_date
        - audit_type
        - duration
        - checks_performed

      # Résumé exécutif
      executive_summary:
        - overall_score
        - critical_issues_count
        - warning_issues_count
        - info_issues_count
        - top_recommendations

      # Détails par catégorie
      details:
        health:
          - connectivity_status
          - performance_metrics
          - ssl_status

        users:
          - total_users
          - inactive_users
          - users_with_issues
          - duplicate_detection

        groups:
          - total_groups
          - empty_groups
          - orphaned_members
          - size_distribution

        security:
          - privileged_accounts
          - password_policy_compliance
          - security_violations

      # Tendances
      trends:
        - user_count_evolution
        - issue_count_evolution
        - performance_evolution

      # Recommandations
      recommendations:
        - priority: critical
        - priority: high
        - priority: medium
        - priority: low
```

## Exemples Pratiques

### Configuration Startup Simple

```yaml
audit:
  checks:
    - health
    - users

  thresholds:
    inactive_days: 90
    response_time_warning_ms: 1000

  required_user_attributes:
    - cn
    - mail
```

### Configuration PME

```yaml
audit:
  checks:
    - health
    - users
    - groups
    - security

  thresholds:
    inactive_days: 60
    max_empty_groups: 10
    max_group_size: 50
    response_time_warning_ms: 500

  required_user_attributes:
    - cn
    - sn
    - mail
    - telephoneNumber

  security:
    check_privileged_accounts: true
    privileged_groups:
      - cn=admins,ou=groups,dc=company,dc=com
    alert_on_admin_creation: true
```

### Configuration Enterprise

```yaml
audit:
  checks:
    - health
    - users
    - groups
    - structure
    - security
    - consistency

  thresholds:
    inactive_days: 90
    password_expiry_warning_days: 30
    max_empty_groups: 5
    max_group_size: 100
    max_nested_depth: 3
    response_time_warning_ms: 500
    response_time_critical_ms: 2000

  required_user_attributes:
    mandatory:
      - cn
      - sn
      - mail
      - uid
      - employeeNumber
    recommended:
      - manager
      - departmentNumber
      - telephoneNumber

  security:
    check_password_policies: true
    check_privileged_accounts: true
    alert_on_admin_creation: true
    alert_on_mass_delete: true
    mass_delete_threshold: 10

    privileged_groups:
      - cn=domain admins,ou=groups,dc=company,dc=com
      - cn=enterprise admins,ou=groups,dc=company,dc=com

    password_policy:
      min_length: 14
      max_age_days: 90
      history_count: 12

  custom_rules:
    - name: "contractor_validation"
      type: user
      condition:
        attribute: "employeeType"
        equals: "contractor"
      checks:
        - attribute_exists: "contractEndDate"
        - attribute_exists: "sponsor"
      severity: critical

  schedule:
    health:
      cron: "*/5 * * * *"
    security:
      cron: "0 1 * * *"
    full:
      cron: "0 2 * * 0"
```

## Optimisation des Performances

### Pagination et Batch

```yaml
audit:
  performance:
    # Pagination des requêtes
    page_size: 1000

    # Traitement par lot
    batch_processing:
      enabled: true
      batch_size: 500
      delay_between_batches: 100  # ms

    # Timeout
    timeout:
      query: 30
      total_audit: 3600
```

### Cache

```yaml
audit:
  cache:
    enabled: true
    ttl: 300  # 5 minutes

    # Résultats à mettre en cache
    cache_items:
      - user_list
      - group_list
      - ou_structure

    # Backend
    backend: "redis"
    redis_url: "redis://localhost:6379/0"
```

### Parallélisation

```yaml
audit:
  parallel:
    enabled: true
    max_workers: 4
    checks_in_parallel:
      - [health, structure]
      - [users, groups]
      - [security, consistency]
```

## Dépannage

### Problèmes Courants

**Audit trop lent :**

```yaml
# Optimisations
audit:
  performance:
    page_size: 500  # Réduire si nécessaire
    batch_size: 100
    enable_cache: true
    parallel_checks: true
```

**Trop d'alertes :**

```yaml
# Ajuster les seuils
audit:
  thresholds:
    inactive_days: 180  # Plus permissif
    max_empty_groups: 20

  # Filtrer les alertes
  alert_filters:
    exclude_info: true
    min_severity: warning
```

**Faux positifs :**

```yaml
# Exclusions
audit:
  exclusions:
    users:
      - "ou=test,dc=example,dc=com"
      - "cn=service-*"
    groups:
      - "cn=template-*"
```

## Liens Connexes

- [Structure du Fichier de Configuration](./Config-File-Structure.md)
- [Configuration du Monitoring](./Monitoring-Configuration.md)
- [Configuration des Alertes](./Alerts-Configuration.md)
- [Guide des Audits](../guides/Running-Audits.md)
- [Bonnes Pratiques de Sécurité](../Security-Best-Practices.md)
