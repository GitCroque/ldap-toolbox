# Opérations de Nettoyage - Guide Complet

Les opérations de nettoyage permettent de maintenir un annuaire LDAP propre et optimisé en supprimant les comptes désactivés, les groupes vides, les entrées orphelines et autres données obsolètes.

## 🎯 Objectifs du Nettoyage

- ✅ Supprimer les comptes désactivés anciens
- ✅ Nettoyer les groupes vides
- ✅ Corriger les références orphelines
- ✅ Supprimer les entrées obsolètes
- ✅ Optimiser la structure LDAP
- ✅ Réduire la taille de l'annuaire
- ✅ Améliorer les performances
- ✅ Maintenir la cohérence des données

## 🚀 Commandes de Base

### Vue d'Ensemble du Nettoyage

```bash
# Afficher ce qui peut être nettoyé (dry-run global)
ldap-monitor cleanup dry-run

# Résultat
Cleanup Analysis Report
=======================

Disabled Users:
  - Total disabled: 45
  - Disabled > 90 days: 23
  - Disabled > 180 days: 12
  - Disabled > 365 days: 8

Empty Groups:
  - Total empty: 15
  - Empty > 30 days: 10
  - Empty > 90 days: 5

Orphaned References:
  - Orphaned group members: 34
  - Orphaned group references: 8
  - Stale DN references: 12

Obsolete Entries:
  - Expired accounts: 6
  - Temporary entries: 3
  - Duplicate entries: 2

Total space that can be freed: ~2.3 MB
Estimated cleanup time: 45 seconds

# Afficher les statistiques
ldap-monitor cleanup stats

# Résultat
LDAP Directory Statistics
=========================

Users:
  Total: 1,234
  Active: 1,150
  Disabled: 84 (6.8%)

Groups:
  Total: 156
  With members: 141
  Empty: 15 (9.6%)

Health Score: 87/100
Last cleanup: 45 days ago
Recommended: Run cleanup operations
```

## 🚫 Nettoyage des Comptes Désactivés

### Lister les Comptes Désactivés

```bash
# Tous les comptes désactivés
ldap-monitor cleanup list-disabled

# Résultat
Disabled User Accounts (45 total)
=================================

Recent (< 30 days):
  1. uid=user1,ou=users,dc=example,dc=com
     Disabled: 15 days ago (2025-01-02)
     Reason: Employee departure

  2. uid=user2,ou=users,dc=example,dc=com
     Disabled: 28 days ago (2024-12-20)
     Reason: Contract ended

Old (> 90 days):
  23. uid=olduser1,ou=users,dc=example,dc=com
      Disabled: 125 days ago (2024-09-14)
      Reason: N/A

Very Old (> 365 days):
  8. uid=veryold1,ou=users,dc=example,dc=com
     Disabled: 450 days ago (2023-11-22)
     Reason: Terminated

# Filtrer par ancienneté
ldap-monitor cleanup list-disabled --days 90

# Export en CSV
ldap-monitor cleanup list-disabled --output disabled-users.csv --format csv

# Export en JSON avec détails
ldap-monitor cleanup list-disabled --output disabled-users.json --format json --detailed
```

### Supprimer les Comptes Désactivés

```bash
# Dry-run: voir ce qui serait supprimé
ldap-monitor cleanup disabled --days 365 --dry-run

# Résultat
Would remove 8 disabled accounts (> 365 days):

  1. uid=olduser1,ou=disabled,dc=example,dc=com
     Disabled since: 2023-11-22 (450 days)
     Last login: 2023-10-15
     Group memberships: 3

  2. uid=olduser2,ou=disabled,dc=example,dc=com
     Disabled since: 2023-09-10 (495 days)
     Last login: 2023-08-30
     Group memberships: 5

Total accounts: 8
Total group memberships to clean: 27
Estimated time: 12 seconds

# Supprimer avec confirmation
ldap-monitor cleanup disabled --days 365 --confirm --backup

# Résultat
✓ Backup created: backups/cleanup_disabled_20250117_160000.ldif
Removing disabled accounts (> 365 days)...

Progress: [========================================] 8/8

✓ Removed: uid=olduser1,ou=disabled,dc=example,dc=com
  - Removed from 3 groups

✓ Removed: uid=olduser2,ou=disabled,dc=example,dc=com
  - Removed from 5 groups

Summary:
  Accounts removed: 8
  Group memberships cleaned: 27
  Space freed: 156 KB
  Duration: 11.3s

# Supprimer avec période spécifique
ldap-monitor cleanup disabled --days 180 --confirm --backup

# Supprimer seulement dans un OU spécifique
ldap-monitor cleanup disabled \
  --days 90 \
  --ou "ou=disabled,dc=example,dc=com" \
  --confirm \
  --backup

# Avec notification par email
ldap-monitor cleanup disabled \
  --days 365 \
  --confirm \
  --backup \
  --notify admin@example.com
```

### Archiver avant Suppression

```bash
# Archiver les comptes avant suppression
ldap-monitor cleanup disabled \
  --days 180 \
  --archive /archives/ldap/users \
  --confirm

# Résultat
✓ Archived 12 accounts to: /archives/ldap/users/archive_20250117.ldif.gz
✓ Removed 12 disabled accounts

# Archive avec métadonnées
ldap-monitor cleanup disabled \
  --days 180 \
  --archive /archives/ldap/users \
  --archive-format json \
  --include-metadata \
  --confirm

# Contenu du JSON d'archive
{
  "archive_date": "2025-01-17T16:00:00Z",
  "reason": "Disabled accounts cleanup",
  "retention_days": 180,
  "accounts": [
    {
      "dn": "uid=user1,ou=disabled,dc=example,dc=com",
      "disabled_date": "2024-06-20",
      "days_disabled": 211,
      "last_login": "2024-06-15",
      "attributes": { ... }
    }
  ]
}
```

## 📁 Nettoyage des Groupes Vides

### Lister les Groupes Vides

```bash
# Tous les groupes vides
ldap-monitor cleanup list-empty-groups

# Résultat
Empty Groups (15 total)
=======================

Recent (< 30 days):
  1. cn=temp-project,ou=groups,dc=example,dc=com
     Created: 25 days ago
     Last modified: 10 days ago

  2. cn=old-team,ou=groups,dc=example,dc=com
     Created: 180 days ago
     Last modified: 5 days ago

Very Old (> 90 days):
  5. cn=abandoned-group,ou=groups,dc=example,dc=com
     Created: 345 days ago
     Last modified: 320 days ago
     Description: Project ended

# Filtrer par ancienneté
ldap-monitor cleanup list-empty-groups --days 90

# Avec raison/description
ldap-monitor cleanup list-empty-groups --show-description

# Export
ldap-monitor cleanup list-empty-groups --output empty-groups.csv
```

### Supprimer les Groupes Vides

```bash
# Dry-run
ldap-monitor cleanup empty-groups --dry-run

# Résultat
Would remove 15 empty groups:

Recent changes - Keep (< 30 days):
  - cn=temp-project,ou=groups,dc=example,dc=com
  - cn=new-team,ou=groups,dc=example,dc=com

Candidates for removal (> 30 days):
  1. cn=old-team,ou=groups,dc=example,dc=com
     Empty since: 2024-11-20 (58 days)

  2. cn=abandoned-group,ou=groups,dc=example,dc=com
     Empty since: 2024-03-15 (308 days)

Recommended: Remove 13 groups (keeping 2 recent)

# Supprimer les groupes vides de plus de 30 jours
ldap-monitor cleanup empty-groups --days 30 --confirm --backup

# Résultat
✓ Backup created: backups/cleanup_empty_groups_20250117_161000.ldif
Removing empty groups (> 30 days)...

Progress: [========================================] 13/13

✓ Removed: cn=old-team,ou=groups,dc=example,dc=com
✓ Removed: cn=abandoned-group,ou=groups,dc=example,dc=com
...

Summary:
  Groups removed: 13
  Groups kept (recent): 2
  Space freed: 45 KB
  Duration: 4.2s

# Supprimer seulement dans un OU
ldap-monitor cleanup empty-groups \
  --ou "ou=projects,ou=groups,dc=example,dc=com" \
  --days 60 \
  --confirm \
  --backup

# Avec exclusions
ldap-monitor cleanup empty-groups \
  --days 30 \
  --exclude "cn=keep-*" \
  --exclude "cn=system-*" \
  --confirm \
  --backup
```

### Groupes Presque Vides

```bash
# Lister les groupes avec très peu de membres
ldap-monitor cleanup list-small-groups --max-members 2

# Résultat
Small Groups (<= 2 members)
============================

  1. cn=tiny-team,ou=groups,dc=example,dc=com
     Members: 1
     Last modified: 120 days ago

  2. cn=duo-group,ou=groups,dc=example,dc=com
     Members: 2
     Last modified: 45 days ago

# Dry-run pour supprimer
ldap-monitor cleanup small-groups \
  --max-members 2 \
  --days 90 \
  --dry-run
```

## 🔗 Nettoyage des Références Orphelines

### Détecter les Orphelins

```bash
# Scanner toutes les références orphelines
ldap-monitor cleanup scan-orphans

# Résultat
Orphaned References Report
==========================

Orphaned Group Members (34 total):
  Groups with orphaned members: 12

  1. cn=developers,ou=groups,dc=example,dc=com
     Orphaned members: 3
     - uid=deleted1,ou=users,dc=example,dc=com (not found)
     - uid=deleted2,ou=users,dc=example,dc=com (not found)
     - uid=deleted3,ou=users,dc=example,dc=com (not found)

  2. cn=managers,ou=groups,dc=example,dc=com
     Orphaned members: 2
     - uid=oldmgr1,ou=users,dc=example,dc=com (not found)
     - uid=oldmgr2,ou=users,dc=example,dc=com (not found)

Orphaned Nested Groups (8 total):
  3. cn=all-staff,ou=groups,dc=example,dc=com
     Orphaned group members: 2
     - cn=deleted-team,ou=groups,dc=example,dc=com (not found)

Stale Manager References (12 total):
  Users with non-existent managers:
  - uid=user1,ou=users,dc=example,dc=com
    Manager: cn=oldmgr,ou=users,dc=example,dc=com (not found)

Total orphaned references: 54

# Scan détaillé avec rapport
ldap-monitor cleanup scan-orphans --detailed --output orphans-report.json
```

### Nettoyer les Orphelins

```bash
# Dry-run
ldap-monitor cleanup orphans --dry-run

# Résultat
Would fix 54 orphaned references:

Group Members:
  Would remove 34 orphaned member references from 12 groups

Nested Groups:
  Would remove 8 orphaned group references from 3 groups

Manager Attributes:
  Would clear 12 stale manager references

# Nettoyer avec confirmation
ldap-monitor cleanup orphans --confirm --backup

# Résultat
✓ Backup created: backups/cleanup_orphans_20250117_162000.ldif
Cleaning up orphaned references...

Group Members:
Progress: [========================================] 12/12 groups

✓ cn=developers,ou=groups,dc=example,dc=com
  Removed 3 orphaned members

✓ cn=managers,ou=groups,dc=example,dc=com
  Removed 2 orphaned members

Nested Groups:
✓ Removed 8 orphaned group references

Manager Attributes:
✓ Cleared 12 stale manager references

Summary:
  Group member orphans fixed: 34
  Nested group orphans fixed: 8
  Manager references fixed: 12
  Total fixed: 54
  Duration: 8.7s

# Nettoyer seulement les membres de groupe
ldap-monitor cleanup orphans --type group-members --confirm --backup

# Nettoyer seulement les références manager
ldap-monitor cleanup orphans --type manager-refs --confirm --backup
```

### Orphelins dans Attributs Spécifiques

```bash
# Nettoyer les attributs manager obsolètes
ldap-monitor cleanup orphan-attribute \
  --attribute manager \
  --confirm \
  --backup

# Nettoyer les attributs secretary obsolètes
ldap-monitor cleanup orphan-attribute \
  --attribute secretary \
  --confirm \
  --backup

# Nettoyer tous les attributs DN
ldap-monitor cleanup orphan-attributes \
  --all-dn-attributes \
  --confirm \
  --backup
```

## 🗑️ Nettoyage d'Entrées Obsolètes

### Comptes Expirés

```bash
# Lister les comptes expirés
ldap-monitor cleanup list-expired

# Résultat
Expired Accounts (6 total)
===========================

  1. uid=contractor1,ou=users,dc=example,dc=com
     Expired: 45 days ago (2024-12-03)
     Type: Contractor
     Last login: 2024-11-28

  2. uid=temp1,ou=users,dc=example,dc=com
     Expired: 120 days ago (2024-09-19)
     Type: Temporary
     Last login: 2024-09-15

# Supprimer les comptes expirés
ldap-monitor cleanup expired --confirm --backup

# Résultat
✓ Backup created: backups/cleanup_expired_20250117_163000.ldif
✓ Removed 6 expired accounts
✓ Cleaned 18 group memberships

# Désactiver au lieu de supprimer
ldap-monitor cleanup expired --disable --confirm

# Résultat
✓ Disabled 6 expired accounts
✓ Moved to: ou=expired,dc=example,dc=com
```

### Entrées Temporaires

```bash
# Lister les entrées temporaires obsolètes
ldap-monitor cleanup list-temporary

# Résultat
Temporary Entries (3 total)
============================

  1. cn=temp-session-12345,ou=temp,dc=example,dc=com
     Created: 15 days ago
     Expires: Already expired

  2. cn=cache-entry-67890,ou=temp,dc=example,dc=com
     Created: 30 days ago
     Expires: 25 days ago

# Supprimer les entrées temporaires expirées
ldap-monitor cleanup temporary --confirm

# Résultat
✓ Removed 3 expired temporary entries
✓ Space freed: 12 KB
```

### Entrées Dupliquées

```bash
# Détecter les doublons
ldap-monitor cleanup scan-duplicates

# Résultat
Duplicate Entries Detected (2 groups)
=====================================

Email Duplicates:
  Email: john.doe@example.com (2 occurrences)
  - uid=jdoe,ou=users,dc=example,dc=com (created: 2024-01-15)
  - uid=john.doe,ou=users,dc=example,dc=com (created: 2024-06-20)
  Recommendation: Keep uid=john.doe (newer)

UID Number Duplicates:
  uidNumber: 10001 (2 occurrences)
  - uid=user1,ou=users,dc=example,dc=com
  - uid=olduser1,ou=users,dc=example,dc=com
  Recommendation: Reassign uidNumber for one entry

# Résoudre automatiquement (avec validation)
ldap-monitor cleanup duplicates --auto-resolve --dry-run

# Résoudre avec confirmation
ldap-monitor cleanup duplicates --auto-resolve --confirm --backup
```

## 🧹 Nettoyage Complet (Full Cleanup)

### Mode Automatique

```bash
# Nettoyage complet en mode automatique
ldap-monitor cleanup auto --dry-run

# Résultat
Automatic Cleanup Plan
======================

Will perform:
  1. Remove disabled accounts (> 365 days): 8 accounts
  2. Remove empty groups (> 90 days): 5 groups
  3. Clean orphaned references: 54 references
  4. Remove expired accounts: 6 accounts
  5. Remove temporary entries: 3 entries

Total operations: 76
Estimated duration: 45 seconds
Estimated space freed: 2.3 MB

# Exécuter le nettoyage automatique
ldap-monitor cleanup auto --confirm --backup

# Résultat
✓ Backup created: backups/cleanup_full_20250117_164000.ldif

Running automatic cleanup...

[1/5] Removing disabled accounts...
✓ Removed 8 disabled accounts (> 365 days)

[2/5] Removing empty groups...
✓ Removed 5 empty groups (> 90 days)

[3/5] Cleaning orphaned references...
✓ Fixed 54 orphaned references

[4/5] Removing expired accounts...
✓ Removed 6 expired accounts

[5/5] Removing temporary entries...
✓ Removed 3 temporary entries

Summary:
  Total operations: 76
  Success: 76
  Failed: 0
  Space freed: 2.3 MB
  Duration: 42.8s

Cleanup completed successfully!
```

### Mode Personnalisé

```bash
# Nettoyage personnalisé avec options
ldap-monitor cleanup custom \
  --disabled-days 180 \
  --empty-groups-days 60 \
  --include-orphans \
  --include-expired \
  --exclude-temporary \
  --dry-run

# Configuration dans un fichier
# cleanup-config.yaml
cleanup:
  disabled_accounts:
    enabled: true
    days: 180
    ou: "ou=disabled,dc=example,dc=com"
  empty_groups:
    enabled: true
    days: 60
    exclude_patterns:
      - "cn=system-*"
      - "cn=keep-*"
  orphaned_references:
    enabled: true
    types:
      - group_members
      - manager_refs
  expired_accounts:
    enabled: true
    action: disable  # or delete
  temporary_entries:
    enabled: false

# Exécuter avec config
ldap-monitor cleanup custom --config cleanup-config.yaml --confirm --backup
```

## 📊 Rapports et Statistiques

### Générer un Rapport de Nettoyage

```bash
# Rapport complet
ldap-monitor cleanup report --output cleanup-report.html --format html

# Rapport JSON pour automatisation
ldap-monitor cleanup report --output cleanup-report.json --format json

# Rapport avec historique
ldap-monitor cleanup report --include-history --days 30

# Contenu du rapport
Cleanup Report - 2025-01-17
============================

Directory Health:
  Total entries: 1,234
  Healthy entries: 1,158 (93.8%)
  Issues found: 76 (6.2%)

Issues Breakdown:
  - Disabled accounts (old): 8
  - Empty groups: 5
  - Orphaned references: 54
  - Expired accounts: 6
  - Temporary entries: 3

Cleanup History (Last 30 days):
  2025-01-17: Auto cleanup (76 items)
  2024-12-20: Manual cleanup (12 items)
  2024-12-05: Orphans cleanup (23 items)

Recommendations:
  1. Schedule automatic cleanup weekly
  2. Monitor orphaned references daily
  3. Review disabled accounts monthly
  4. Implement stricter temporary entry TTL
```

### Statistiques de Nettoyage

```bash
# Statistiques globales
ldap-monitor cleanup stats --detailed

# Résultat
Cleanup Statistics
==================

Last 30 days:
  Operations performed: 3
  Entries removed: 111
  Space freed: 5.8 MB

Last 90 days:
  Operations performed: 12
  Entries removed: 456
  Space freed: 24.3 MB

Last 365 days:
  Operations performed: 52
  Entries removed: 1,847
  Space freed: 98.7 MB

By Category:
  Disabled accounts: 234 (12.7%)
  Empty groups: 89 (4.8%)
  Orphaned references: 1,402 (75.9%)
  Expired accounts: 67 (3.6%)
  Temporary entries: 55 (3.0%)

Average cleanup frequency: Weekly
Last cleanup: 3 days ago
Next recommended: In 4 days
```

## 🔐 Sécurité et Validation

### Configuration de Sécurité

```yaml
# config.yaml
management:
  cleanup:
    require_confirmation: true      # Demander confirmation
    auto_backup: true               # Backup automatique
    backup_retention_days: 90       # Conserver backups 90 jours
    allow_auto_cleanup: false       # Désactiver auto-cleanup par défaut

    disabled_accounts:
      min_days: 90                  # Minimum 90 jours avant suppression
      require_archive: true         # Archiver avant suppression

    empty_groups:
      min_days: 30                  # Minimum 30 jours avant suppression
      exclude_patterns:             # Patterns à exclure
        - "cn=system-*"
        - "cn=admin-*"
        - "cn=keep-*"

    orphaned_references:
      auto_fix: true                # Correction automatique autorisée
      verify_before_remove: true    # Vérifier avant suppression

    safety:
      max_deletions_per_run: 100    # Max suppressions par exécution
      max_percentage: 5             # Max 5% de l'annuaire par run
      require_manual_approval: true # Approbation manuelle si > seuils
```

### Validation et Vérification

```bash
# Valider avant nettoyage
ldap-monitor cleanup validate --type disabled --days 365

# Résultat
Validation Report
=================

✓ All 8 accounts to be removed are truly disabled
✓ All accounts are older than threshold (365 days)
✓ No recent login activity detected
✓ Backup directory is writable
✓ Sufficient permissions for deletion
⚠ 2 accounts have important group memberships
  - uid=oldadmin1: member of cn=admins
  - uid=olduser2: member of 12 groups

Recommendations:
  - Review accounts with important memberships manually
  - Verify group memberships before deletion
  - Consider archiving instead of deleting

Safe to proceed: Yes (with caution)

# Vérifier l'intégrité après nettoyage
ldap-monitor cleanup verify

# Résultat
Post-Cleanup Verification
=========================

✓ No broken references detected
✓ All group memberships are valid
✓ No orphaned entries created
✓ Directory structure intact
✓ Replication is functioning

Integrity check: PASSED
```

## 🤖 Automatisation

### Script de Nettoyage Automatique

```bash
#!/bin/bash
# auto-cleanup.sh

LOG_FILE="/var/log/ldap-cleanup.log"
DATE=$(date +"%Y-%m-%d %H:%M:%S")

echo "[$DATE] Starting LDAP cleanup..." >> "$LOG_FILE"

# 1. Nettoyage des comptes désactivés (> 365 jours)
echo "Cleaning disabled accounts..." >> "$LOG_FILE"
ldap-monitor cleanup disabled --days 365 --confirm --backup >> "$LOG_FILE" 2>&1

# 2. Nettoyage des groupes vides (> 90 jours)
echo "Cleaning empty groups..." >> "$LOG_FILE"
ldap-monitor cleanup empty-groups --days 90 --confirm --backup >> "$LOG_FILE" 2>&1

# 3. Nettoyage des orphelins
echo "Cleaning orphaned references..." >> "$LOG_FILE"
ldap-monitor cleanup orphans --confirm --backup >> "$LOG_FILE" 2>&1

# 4. Générer rapport
echo "Generating cleanup report..." >> "$LOG_FILE"
ldap-monitor cleanup report --output "/reports/cleanup-$(date +%Y%m%d).html" >> "$LOG_FILE" 2>&1

# 5. Envoyer notification
if [ $? -eq 0 ]; then
    echo "Cleanup completed successfully" | \
        mail -s "LDAP Cleanup Success - $(date +%Y-%m-%d)" admin@example.com
else
    echo "Cleanup failed - check logs" | \
        mail -s "LDAP Cleanup FAILED - $(date +%Y-%m-%d)" admin@example.com
fi

echo "[$DATE] Cleanup completed." >> "$LOG_FILE"
```

### Tâches Cron

```bash
# Crontab entries

# Nettoyage automatique complet tous les dimanches à 3h
0 3 * * 0 /usr/local/bin/auto-cleanup.sh

# Nettoyage des orphelins tous les jours à 2h
0 2 * * * ldap-monitor cleanup orphans --confirm --backup

# Nettoyage des entrées temporaires toutes les heures
0 * * * * ldap-monitor cleanup temporary --confirm

# Rapport hebdomadaire le lundi à 8h
0 8 * * 1 ldap-monitor cleanup report --output /reports/weekly-$(date +\%Y\%m\%d).html --email admin@example.com

# Vérification d'intégrité quotidienne à 6h
0 6 * * * ldap-monitor cleanup verify --email-on-error admin@example.com
```

### Monitoring et Alertes

```bash
#!/bin/bash
# cleanup-monitor.sh

# Vérifier les seuils
DISABLED_COUNT=$(ldap-monitor cleanup list-disabled --days 365 --count)
EMPTY_GROUPS=$(ldap-monitor cleanup list-empty-groups --days 90 --count)
ORPHANS=$(ldap-monitor cleanup scan-orphans --count)

# Alertes si dépassement de seuils
if [ "$DISABLED_COUNT" -gt 50 ]; then
    echo "Warning: $DISABLED_COUNT old disabled accounts" | \
        mail -s "LDAP Alert: Too many disabled accounts" admin@example.com
fi

if [ "$EMPTY_GROUPS" -gt 20 ]; then
    echo "Warning: $EMPTY_GROUPS empty groups" | \
        mail -s "LDAP Alert: Too many empty groups" admin@example.com
fi

if [ "$ORPHANS" -gt 100 ]; then
    echo "Warning: $ORPHANS orphaned references" | \
        mail -s "LDAP Alert: Too many orphaned references" admin@example.com
fi
```

## 📋 Meilleures Pratiques

### 1. Planification du Nettoyage

```bash
# Créer un calendrier de nettoyage
Daily:
  - Orphaned references
  - Temporary entries
  - Expired sessions

Weekly:
  - Empty groups (> 30 days)
  - Disabled accounts (> 180 days)
  - Integrity verification

Monthly:
  - Disabled accounts (> 365 days)
  - Comprehensive audit
  - Performance optimization

Quarterly:
  - Full cleanup review
  - Policy adjustment
  - Archive old backups
```

### 2. Toujours Sauvegarder

```bash
# Backup avant chaque opération de nettoyage
ldap-monitor cleanup [...] --backup

# Configuration
backup:
  auto_backup: true
  backup_dir: /var/backups/ldap
  retention_days: 90
  compress: true
```

### 3. Tester avec Dry-Run

```bash
# Toujours dry-run d'abord
ldap-monitor cleanup auto --dry-run

# Vérifier les résultats
# Puis exécuter
ldap-monitor cleanup auto --confirm --backup
```

### 4. Monitorer et Alerter

```bash
# Configurer des alertes
alerts:
  cleanup:
    high_orphan_count:
      threshold: 100
      action: email

    high_disabled_count:
      threshold: 50
      action: email

    failed_cleanup:
      action: email_and_log
```

### 5. Documenter les Opérations

```bash
# Logger toutes les opérations
ldap-monitor cleanup [...] | tee -a /var/log/ldap-cleanup.log

# Générer des rapports réguliers
ldap-monitor cleanup report --weekly --email admin@example.com
```

## 🔧 Dépannage

### Problèmes Courants

**Erreur: Too many entries to delete**
```bash
# Configuration de sécurité activée
# Augmenter les seuils ou procéder par lots

# Option 1: Augmenter le seuil (avec précaution)
ldap-monitor cleanup disabled --days 365 --max-deletions 200 --confirm

# Option 2: Procéder par lots
ldap-monitor cleanup disabled --days 365 --batch-size 50 --confirm
```

**Erreur: Cannot delete, entry has references**
```bash
# Nettoyer d'abord les références
ldap-monitor cleanup orphans --confirm --backup

# Puis supprimer l'entrée
ldap-monitor cleanup disabled --days 365 --confirm --backup
```

**Erreur: Permission denied**
```bash
# Vérifier les permissions LDAP
ldap-monitor test connection --verbose

# Vérifier la configuration
cat config.yaml | grep -A 5 "management:"
```

## 📚 Voir Aussi

- [Gestion des Utilisateurs](User-Management.md)
- [Gestion des Groupes](Group-Management.md)
- [Sauvegarde et Restauration](Backup-Restore.md)
- [Audit de Sécurité](../audit/Security-Audit.md)
