# Configuration de la Gestion

## Table des Matières

- [Introduction](#introduction)
- [Paramètres de Sécurité](#paramètres-de-sécurité)
- [Opérations sur les Utilisateurs](#opérations-sur-les-utilisateurs)
- [Opérations sur les Groupes](#opérations-sur-les-groupes)
- [Opérations en Lot](#opérations-en-lot)
- [Sauvegardes Automatiques](#sauvegardes-automatiques)
- [Mode Dry-Run](#mode-dry-run)
- [Confirmations et Validations](#confirmations-et-validations)
- [Politiques de Nettoyage](#politiques-de-nettoyage)
- [Logs d'Audit des Opérations](#logs-daudit-des-opérations)
- [Templates et Automatisation](#templates-et-automatisation)
- [Limites et Quotas](#limites-et-quotas)
- [Exemples Pratiques](#exemples-pratiques)
- [Dépannage](#dépannage)

## Introduction

La configuration de gestion définit comment LDAP Health Monitor effectue les opérations de modification sur l'annuaire LDAP. Ces paramètres sont cruciaux pour la sécurité et l'intégrité de vos données.

### Philosophie de Sécurité

Le système suit le principe de **sécurité par défaut** :

1. **Conservateur** : Par défaut, les opérations dangereuses sont désactivées
2. **Explicite** : Toute modification nécessite une configuration explicite
3. **Traçable** : Toutes les opérations sont loggées et auditables
4. **Réversible** : Sauvegardes automatiques avant modification
5. **Validé** : Confirmations requises pour les opérations critiques

### Architecture des Opérations

```
┌──────────────┐
│  Commande    │
│  Utilisateur │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Validation  │◄──── Configuration
│  Sécurité    │      Limites
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Dry-Run?    │
└──────┬───────┘
       │
       ├─── OUI ──► Simulation
       │
       └─── NON
            │
            ▼
       ┌──────────────┐
       │  Sauvegarde  │
       │  Pré-opération│
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │  Exécution   │
       └──────┬───────┘
              │
              ▼
       ┌──────────────┐
       │  Audit Log   │
       └──────────────┘
```

## Paramètres de Sécurité

### Configuration de Base

```yaml
management:
  # Sécurité
  allow_delete: false
  allow_bulk_operations: true
  require_confirmation: true
  backup_before_modify: true
  dry_run_by_default: true
```

### Description des Paramètres

**allow_delete** (défaut: false)

```yaml
management:
  allow_delete: false  # Interdit toute suppression

# Pour autoriser les suppressions
management:
  allow_delete: true

  # Avec restrictions
  delete_restrictions:
    require_admin: true
    max_per_operation: 10
    backup_required: true
    confirmation_required: true
```

**allow_bulk_operations** (défaut: true)

```yaml
management:
  allow_bulk_operations: true

  # Configuration des opérations en lot
  bulk_operations:
    max_size: 1000  # Maximum d'objets par opération
    require_approval: true
    approval_threshold: 50  # Approbation si > 50 objets
```

**require_confirmation** (défaut: true)

```yaml
management:
  require_confirmation: true

  # Confirmation par type d'opération
  confirmations:
    create: false      # Pas de confirmation pour création
    modify: true       # Confirmation pour modification
    delete: true       # Confirmation pour suppression
    bulk: true         # Confirmation pour opérations en lot

    # Bypass pour opérations automatisées
    bypass_on_automation: true
```

**backup_before_modify** (défaut: true)

```yaml
management:
  backup_before_modify: true

  # Configuration des sauvegardes
  operation_backup:
    enabled: true
    path: ./backups/operations
    format: ldif
    compress: true
    keep_days: 30
```

**dry_run_by_default** (défaut: true)

```yaml
management:
  dry_run_by_default: true

  # Forcer dry-run pour certaines opérations
  force_dry_run:
    - delete
    - bulk_delete
    - bulk_modify

  # Désactiver dry-run (production uniquement)
  allow_disable_dry_run: false
```

### Niveaux de Sécurité Prédéfinis

**Niveau 1 : Développement**

```yaml
management:
  allow_delete: true
  require_confirmation: false
  backup_before_modify: false
  dry_run_by_default: false
```

**Niveau 2 : Staging**

```yaml
management:
  allow_delete: true
  require_confirmation: true
  backup_before_modify: true
  dry_run_by_default: true
```

**Niveau 3 : Production (recommandé)**

```yaml
management:
  allow_delete: false  # Suppressions interdites
  allow_bulk_operations: true
  require_confirmation: true
  backup_before_modify: true
  dry_run_by_default: true

  # Restrictions supplémentaires
  restrictions:
    max_modifications_per_hour: 100
    require_approval_for:
      - bulk_operations
      - privileged_accounts
    audit_all_operations: true
```

## Opérations sur les Utilisateurs

### Création d'Utilisateurs

```yaml
management:
  users:
    create:
      enabled: true

      # Template par défaut
      default_template: standard_user

      # Attributs obligatoires
      required_attributes:
        - cn
        - sn
        - uid
        - mail

      # Attributs par défaut
      default_attributes:
        objectClass:
          - inetOrgPerson
          - organizationalPerson
          - person
        userPassword: "{SSHA}changeme"
        loginShell: /bin/bash

      # Validation
      validation:
        uid:
          pattern: "^[a-z][a-z0-9._-]{2,15}$"
          unique: true
        mail:
          pattern: "^[a-zA-Z0-9._%+-]+@company\\.com$"
          unique: true

      # Auto-génération
      auto_generate:
        uid: true
        uid_format: "{firstname}.{lastname}"
        mail: true
        mail_format: "{uid}@company.com"
```

**Exemple d'utilisation :**

```bash
# Créer un utilisateur avec template
ldap-health-monitor user create \
  --template standard_user \
  --cn "Jean Dupont" \
  --sn "Dupont" \
  --givenName "Jean" \
  --mail "jean.dupont@company.com"

# Avec auto-génération
ldap-health-monitor user create \
  --cn "Marie Martin" \
  --sn "Martin" \
  --givenName "Marie" \
  --auto-generate
```

### Modification d'Utilisateurs

```yaml
management:
  users:
    modify:
      enabled: true

      # Attributs modifiables
      allowed_attributes:
        - telephoneNumber
        - mail
        - description
        - title
        - departmentNumber

      # Attributs protégés
      protected_attributes:
        - uid
        - uidNumber
        - gidNumber
        - userPassword  # Utiliser commande spécifique

      # Validation des modifications
      validate_before_modify: true

      # Backup avant modification
      backup_before: true
```

### Désactivation/Activation

```yaml
management:
  users:
    disable:
      enabled: true
      method: userAccountControl  # ou attribut custom

      # Actions lors de désactivation
      on_disable:
        - remove_from_groups: false
        - set_description: "Account disabled on {date}"
        - notify: true

    enable:
      enabled: true
      require_password_reset: true
```

### Suppression d'Utilisateurs

```yaml
management:
  users:
    delete:
      enabled: false  # Désactivé par défaut

      # Si activé
      when_enabled:
        # Backup obligatoire
        require_backup: true

        # Actions avant suppression
        pre_delete:
          - remove_from_all_groups: true
          - backup_user_data: true
          - log_deletion: true

        # Soft delete (recommandé)
        soft_delete:
          enabled: true
          move_to_ou: "ou=deleted,dc=example,dc=com"
          add_deletion_timestamp: true

        # Hard delete
        hard_delete:
          enabled: false
          require_admin: true
          require_reason: true
```

## Opérations sur les Groupes

### Création de Groupes

```yaml
management:
  groups:
    create:
      enabled: true

      # Attributs par défaut
      default_attributes:
        objectClass:
          - groupOfNames
          - top

      # Validation
      validation:
        cn:
          pattern: "^[a-zA-Z][a-zA-Z0-9_-]{2,63}$"
          unique: true

      # Naming convention
      naming:
        prefix: ""
        suffix: ""
        format: "{name}"

      # Groupe vide interdit par défaut (groupOfNames nécessite au moins un membre)
      allow_empty: false
      dummy_member: "cn=dummy,ou=system,dc=example,dc=com"
```

### Gestion des Membres

```yaml
management:
  groups:
    members:
      # Ajout de membres
      add:
        enabled: true
        validate_member_exists: true
        check_duplicate: true
        max_members_per_operation: 100

      # Suppression de membres
      remove:
        enabled: true
        validate_member_in_group: true

      # Remplacement
      replace:
        enabled: true
        backup_before: true

      # Synchronisation
      sync:
        enabled: true
        source: file  # file, database, api
        format: csv   # csv, json, ldif
        dry_run: true
```

### Suppression de Groupes

```yaml
management:
  groups:
    delete:
      enabled: false

      when_enabled:
        # Vérifications préalables
        checks:
          - is_empty: true  # Vérifier que le groupe est vide
          - not_in_use: true  # Pas référencé ailleurs
          - not_privileged: true

        # Actions avant suppression
        pre_delete:
          - remove_all_members: true
          - backup_group: true

        # Soft delete
        soft_delete:
          enabled: true
          move_to_ou: "ou=deleted-groups,dc=example,dc=com"
```

## Opérations en Lot

### Configuration Générale

```yaml
management:
  batch:
    # Activation
    enabled: true

    # Limites
    max_size: 1000
    max_concurrent: 5

    # Performance
    batch_size: 100
    batch_delay: 1  # secondes entre lots

    # Sécurité
    require_confirmation: true
    confirmation_threshold: 50
    backup_before: true

    # Gestion d'erreurs
    on_error:
      action: stop  # stop, skip, continue
      rollback: true
      max_failures: 10
```

### Opérations Batch Supportées

```yaml
management:
  batch:
    operations:
      # Création en masse
      bulk_create:
        enabled: true
        max_items: 500

      # Modification en masse
      bulk_modify:
        enabled: true
        max_items: 1000
        allowed_attributes:
          - description
          - telephoneNumber
          - title

      # Suppression en masse (dangereux)
      bulk_delete:
        enabled: false
        require_admin: true
        max_items: 100

      # Import
      import:
        enabled: true
        formats: [csv, ldif, json]
        validate_before: true
        dry_run_first: true

      # Export
      export:
        enabled: true
        formats: [csv, ldif, json, yaml]
```

### Import depuis CSV

```yaml
management:
  batch:
    import:
      csv:
        enabled: true

        # Mapping des colonnes
        column_mapping:
          cn: "Full Name"
          sn: "Last Name"
          givenName: "First Name"
          mail: "Email"
          telephoneNumber: "Phone"

        # Options
        has_header: true
        delimiter: ","
        encoding: utf-8

        # Validation
        validate_rows: true
        skip_invalid: false

        # Gestion des doublons
        on_duplicate:
          action: skip  # skip, update, error
```

**Exemple CSV :**

```csv
Full Name,Last Name,First Name,Email,Phone
Jean Dupont,Dupont,Jean,jean.dupont@company.com,+33123456789
Marie Martin,Martin,Marie,marie.martin@company.com,+33123456790
```

**Commande :**

```bash
ldap-health-monitor user import \
  --file users.csv \
  --format csv \
  --dry-run
```

### Import depuis LDIF

```yaml
management:
  batch:
    import:
      ldif:
        enabled: true

        # Validation
        validate_syntax: true
        validate_schema: true

        # Options
        skip_existing: false
        update_existing: true

        # Filtres
        exclude_dns:
          - "ou=deleted,*"
        include_only:
          - "ou=users,*"
          - "ou=groups,*"
```

## Sauvegardes Automatiques

### Configuration des Sauvegardes

```yaml
management:
  operation_backup:
    enabled: true

    # Répertoire
    backup_dir: ./backups/operations

    # Format
    format: ldif
    compress: true

    # Naming
    naming_pattern: "{operation}_{timestamp}_{user}.ldif.gz"

    # Rétention
    retention_days: 30
    max_backups: 100

    # Métadonnées
    include_metadata: true
    metadata_format: json
```

### Types de Sauvegardes

**Backup avant modification :**

```yaml
management:
  operation_backup:
    pre_operation:
      enabled: true

      # Backup de l'objet avant modification
      backup_original: true

      # Backup de tous les objets affectés
      backup_affected: true

      # Pour opérations en lot
      batch_backup:
        single_file: false
        separate_files: true
```

**Backup différentiel :**

```yaml
management:
  operation_backup:
    differential:
      enabled: true

      # Sauvegarder seulement les attributs modifiés
      only_changed_attributes: true

      # Format
      format: json
      include_before_after: true
```

**Exemple de backup différentiel :**

```json
{
  "operation": "modify",
  "timestamp": "2025-11-17T10:30:00Z",
  "dn": "uid=jdupont,ou=users,dc=example,dc=com",
  "changes": [
    {
      "attribute": "telephoneNumber",
      "before": "+33123456789",
      "after": "+33987654321"
    },
    {
      "attribute": "title",
      "before": "Developer",
      "after": "Senior Developer"
    }
  ]
}
```

### Restauration

```yaml
management:
  restore:
    enabled: true

    # Validation avant restauration
    validate_backup: true

    # Confirmation
    require_confirmation: true

    # Options
    overwrite_existing: true
    merge_attributes: false
```

**Commande de restauration :**

```bash
# Lister les backups
ldap-health-monitor backup list

# Restaurer un backup spécifique
ldap-health-monitor backup restore \
  --file backups/operations/modify_20251117_103000_admin.ldif.gz \
  --confirm

# Restaurer en dry-run
ldap-health-monitor backup restore \
  --file backup.ldif.gz \
  --dry-run
```

## Mode Dry-Run

### Configuration

```yaml
management:
  dry_run:
    # Par défaut pour toutes les opérations
    by_default: true

    # Forcer dry-run (ne peut pas être désactivé)
    force_for:
      - bulk_delete
      - mass_operations

    # Output
    output:
      format: detailed  # summary, detailed
      show_diff: true
      highlight_changes: true

    # Simulation
    simulate_errors: false
    simulate_duration: true
```

### Utilisation

```bash
# Dry-run activé par défaut
ldap-health-monitor user modify uid=jdupont --mail new@email.com

# Forcer l'exécution réelle
ldap-health-monitor user modify uid=jdupont --mail new@email.com --execute

# Dry-run explicite
ldap-health-monitor user create --cn "Test User" --dry-run
```

### Output Dry-Run

```
=== DRY-RUN MODE ===
Aucune modification ne sera effectuée

Opération: MODIFY
DN: uid=jdupont,ou=users,dc=example,dc=com

Modifications prévues:
  ✎ telephoneNumber: "+33123456789" → "+33987654321"
  ✎ title: "Developer" → "Senior Developer"

Objets affectés: 1
Durée estimée: 0.5s

Pour exécuter réellement, ajouter --execute
```

## Confirmations et Validations

### Confirmations Interactives

```yaml
management:
  confirmations:
    enabled: true

    # Mode
    mode: interactive  # interactive, automatic

    # Timeout
    timeout: 60  # secondes

    # Messages personnalisés
    messages:
      delete: "Êtes-vous sûr de vouloir supprimer {dn} ?"
      bulk_operation: "Modifier {count} objets. Continuer ?"

    # Bypass pour scripts
    bypass_on_non_interactive: true
```

**Exemple de confirmation :**

```
⚠️  CONFIRMATION REQUISE

Opération: SUPPRESSION
DN: uid=jdupont,ou=users,dc=example,dc=com

Cette action est irréversible.
Backup sera créé: backups/operations/delete_20251117_103000.ldif.gz

Taper 'yes' pour confirmer, 'no' pour annuler: _
```

### Validations

```yaml
management:
  validation:
    # Validation pré-opération
    pre_operation:
      enabled: true

      checks:
        - syntax: true
        - schema: true
        - permissions: true
        - dependencies: true

    # Validation post-opération
    post_operation:
      enabled: true

      checks:
        - verify_changes: true
        - test_access: true

    # Actions sur échec de validation
    on_validation_failure:
      action: abort  # abort, warn, ignore
      log: true
      notify: true
```

## Politiques de Nettoyage

### Nettoyage Automatique

```yaml
management:
  cleanup:
    enabled: true

    # Planification
    schedule:
      cron: "0 3 * * 0"  # Dimanche 3h

    # Politiques
    policies:
      # Comptes inactifs
      inactive_accounts:
        enabled: true
        threshold_days: 90
        action: disable  # disable, delete, move

      # Groupes vides
      empty_groups:
        enabled: true
        threshold_days: 30  # Vide depuis 30 jours
        action: delete

      # Membres orphelins
      orphaned_members:
        enabled: true
        action: remove

      # Comptes expirés
      expired_accounts:
        enabled: true
        check_attribute: accountExpires
        action: disable
```

### Nettoyage Manuel

```bash
# Identifier les objets à nettoyer
ldap-health-monitor cleanup scan

# Nettoyer les comptes inactifs (dry-run)
ldap-health-monitor cleanup inactive-accounts --dry-run

# Nettoyer les groupes vides
ldap-health-monitor cleanup empty-groups --execute

# Nettoyer tout
ldap-health-monitor cleanup all --dry-run
```

## Logs d'Audit des Opérations

### Configuration

```yaml
management:
  audit_log:
    enabled: true

    # Fichier de log
    file: ./logs/operations-audit.log

    # Format
    format: json  # json, text, syslog

    # Niveau de détail
    detail_level: full  # minimal, standard, full

    # Informations à logger
    log_items:
      - timestamp
      - user
      - operation
      - dn
      - changes
      - result
      - duration

    # Rotation
    rotation:
      max_size: 100MB
      max_files: 10
      compress: true
```

### Format des Logs

**Format JSON :**

```json
{
  "timestamp": "2025-11-17T10:30:00Z",
  "level": "INFO",
  "operation": "modify",
  "user": "admin",
  "source_ip": "192.168.1.100",
  "dn": "uid=jdupont,ou=users,dc=example,dc=com",
  "changes": [
    {
      "attribute": "telephoneNumber",
      "action": "replace",
      "old_value": "+33123456789",
      "new_value": "+33987654321"
    }
  ],
  "result": "success",
  "duration_ms": 145,
  "backup_file": "backups/operations/modify_20251117_103000.ldif.gz"
}
```

### Recherche dans les Logs

```bash
# Rechercher par utilisateur
ldap-health-monitor audit search --user admin

# Rechercher par opération
ldap-health-monitor audit search --operation delete

# Rechercher par date
ldap-health-monitor audit search --since "2025-11-17"

# Rechercher par DN
ldap-health-monitor audit search --dn "uid=jdupont,*"
```

## Templates et Automatisation

### Templates d'Objets

```yaml
management:
  templates:
    users:
      standard_user:
        objectClass:
          - inetOrgPerson
          - organizationalPerson
          - person
        userPassword: "{SSHA}changeme"
        loginShell: /bin/bash
        homeDirectory: "/home/{uid}"

      contractor:
        objectClass:
          - inetOrgPerson
          - organizationalPerson
          - person
        employeeType: contractor
        description: "External contractor"

      service_account:
        objectClass:
          - inetOrgPerson
          - organizationalPerson
          - person
        employeeType: service
        description: "Service account"
        userPassword: "{SSHA}generated"

    groups:
      standard_group:
        objectClass:
          - groupOfNames
          - top
        description: "Standard group"

      privileged_group:
        objectClass:
          - groupOfNames
          - top
        description: "Privileged group - require approval"
```

### Workflows Automatisés

```yaml
management:
  workflows:
    # Onboarding nouvel employé
    employee_onboarding:
      trigger: api_call
      steps:
        - create_user:
            template: standard_user
        - set_password:
            method: generate
            notify: true
        - add_to_groups:
            - cn=employees,ou=groups,dc=example,dc=com
        - send_welcome_email:
            template: welcome

    # Offboarding
    employee_offboarding:
      trigger: manual
      steps:
        - disable_account
        - remove_from_groups:
            except:
              - cn=former-employees,ou=groups,dc=example,dc=com
        - move_to_ou:
            target: ou=disabled,dc=example,dc=com
        - notify_it_team
```

## Limites et Quotas

### Configuration des Limites

```yaml
management:
  limits:
    # Limites par opération
    per_operation:
      create:
        max_per_hour: 100
        max_per_day: 500

      modify:
        max_per_hour: 500
        max_per_day: 2000

      delete:
        max_per_hour: 10
        max_per_day: 50

    # Limites par utilisateur
    per_user:
      admin:
        unlimited: true

      operator:
        max_operations_per_hour: 100

      readonly:
        allowed_operations: [read]

    # Limites globales
    global:
      max_concurrent_operations: 10
      rate_limit: 100  # opérations/minute
```

### Quotas

```yaml
management:
  quotas:
    # Quota d'objets
    objects:
      users:
        max: 10000
        warn_at: 8000

      groups:
        max: 1000
        warn_at: 800

    # Quota de stockage (backups)
    storage:
      max_size: 10GB
      warn_at: 8GB
```

## Exemples Pratiques

### Configuration Développement

```yaml
management:
  allow_delete: true
  allow_bulk_operations: true
  require_confirmation: false
  backup_before_modify: false
  dry_run_by_default: false

  batch:
    max_size: 100
```

### Configuration Production

```yaml
management:
  # Sécurité maximale
  allow_delete: false
  allow_bulk_operations: true
  require_confirmation: true
  backup_before_modify: true
  dry_run_by_default: true

  # Batch
  batch:
    enabled: true
    max_size: 1000
    require_confirmation: true
    backup_before: true

  # Backup
  operation_backup:
    enabled: true
    backup_dir: /var/backups/ldap-operations
    retention_days: 90
    compress: true

  # Audit
  audit_log:
    enabled: true
    file: /var/log/ldap-monitor/operations-audit.log
    format: json
    detail_level: full

  # Cleanup
  cleanup:
    enabled: true
    schedule:
      cron: "0 3 * * 0"
    policies:
      inactive_accounts:
        enabled: true
        threshold_days: 90
        action: disable

  # Limites
  limits:
    per_operation:
      delete:
        max_per_day: 10
```

## Dépannage

### Opération Refusée

```bash
# Vérifier la configuration
ldap-health-monitor config show --section management

# Vérifier les permissions
ldap-health-monitor user permissions --dn "uid=admin,dc=example,dc=com"

# Forcer avec dry-run
ldap-health-monitor user delete uid=test --dry-run
```

### Backup Échoué

```bash
# Vérifier l'espace disque
df -h

# Vérifier les permissions
ls -la backups/operations/

# Tester la création de backup
ldap-health-monitor backup test
```

### Opération Lente

```yaml
# Optimiser les batch
management:
  batch:
    batch_size: 50  # Réduire
    batch_delay: 2  # Augmenter

  # Désactiver certaines validations
  validation:
    post_operation:
      verify_changes: false
```

## Liens Connexes

- [Structure du Fichier de Configuration](./Config-File-Structure.md)
- [Configuration des Audits](./Audit-Configuration.md)
- [Guide de Gestion des Utilisateurs](../guides/User-Management.md)
- [Guide de Gestion des Groupes](../guides/Group-Management.md)
- [Sauvegardes et Restauration](../guides/Backup-Restore.md)
