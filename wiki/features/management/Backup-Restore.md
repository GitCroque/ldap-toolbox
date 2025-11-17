# Sauvegarde et Restauration - Guide Complet

La sauvegarde et restauration LDAP permettent de protéger vos données, faciliter les migrations, et récupérer rapidement en cas d'incident.

## 🎯 Objectifs des Sauvegardes

- ✅ Protection contre la perte de données
- ✅ Récupération après incident (disaster recovery)
- ✅ Migration entre serveurs
- ✅ Tests et développement
- ✅ Conformité réglementaire
- ✅ Historique et audit
- ✅ Rollback après modifications
- ✅ Clonage d'environnements

## 📋 Formats de Sauvegarde

### LDIF (LDAP Data Interchange Format)

```bash
# Format standard LDAP, portable, lisible
Avantages:
  ✓ Format standard LDAP
  ✓ Compatible avec tous les serveurs LDAP
  ✓ Lisible et éditable
  ✓ Prise en charge native

Inconvénients:
  ✗ Taille importante (texte)
  ✗ Plus lent pour gros volumes

Usage recommandé:
  - Migrations entre serveurs
  - Backups complets
  - Restaurations complètes
```

### JSON

```bash
# Format structuré, facile à parser
Avantages:
  ✓ Facile à parser programmatiquement
  ✓ Compatible avec outils modernes
  ✓ Structure claire
  ✓ Bon pour l'automatisation

Inconvénients:
  ✗ Non standard LDAP
  ✗ Nécessite conversion pour restauration

Usage recommandé:
  - Exports pour analyse
  - Intégration avec autres systèmes
  - Traitement de données
```

### YAML

```bash
# Format lisible, configuration
Avantages:
  ✓ Très lisible
  ✓ Bon pour la documentation
  ✓ Commentaires possibles

Inconvénients:
  ✗ Non standard LDAP
  ✗ Sensible à l'indentation
  ✗ Plus lent

Usage recommandé:
  - Documentation
  - Configuration templates
  - Révision humaine
```

## 🚀 Sauvegarde Complète

### Backup Full - LDIF

```bash
# Sauvegarde complète simple
ldap-monitor backup full --output backup.ldif

# Résultat
Creating full LDAP backup...
Exporting 1,234 entries...

Progress: [========================================] 1234/1234

✓ Backup completed: backup.ldif
  Size: 15.3 MB
  Entries: 1,234
  Duration: 8.2s

# Avec compression
ldap-monitor backup full --output backup.ldif --compress

# Résultat
✓ Backup completed: backup.ldif.gz
  Size: 2.1 MB (compressed from 15.3 MB)
  Compression ratio: 86.3%
  Entries: 1,234
  Duration: 9.5s

# Auto-nommage avec timestamp
ldap-monitor backup full

# Résultat
✓ Backup completed: backups/ldap_backup_20250117_170000.ldif.gz
```

### Backup Full - JSON

```bash
# Format JSON
ldap-monitor backup full --output backup.json --format json

# Format JSON indenté
ldap-monitor backup full --output backup.json --format json --pretty

# Exemple de sortie JSON
{
  "backup_date": "2025-01-17T17:00:00Z",
  "backup_type": "full",
  "entries_count": 1234,
  "base_dn": "dc=example,dc=com",
  "entries": [
    {
      "dn": "dc=example,dc=com",
      "attributes": {
        "objectClass": ["top", "domain"],
        "dc": "example"
      }
    },
    {
      "dn": "ou=users,dc=example,dc=com",
      "attributes": {
        "objectClass": ["top", "organizationalUnit"],
        "ou": "users",
        "description": "Users container"
      }
    }
  ]
}

# JSON compressé
ldap-monitor backup full --output backup.json --format json --compress
```

### Backup avec Filtres

```bash
# Backup d'une branche spécifique
ldap-monitor backup full \
  --output users-backup.ldif \
  --base-dn "ou=users,dc=example,dc=com"

# Backup avec filtre LDAP
ldap-monitor backup full \
  --output active-users.ldif \
  --filter "(!(accountStatus=disabled))"

# Backup de plusieurs branches
ldap-monitor backup branches \
  --output multi-backup.ldif \
  --branch "ou=users,dc=example,dc=com" \
  --branch "ou=groups,dc=example,dc=com"

# Backup excluant certaines branches
ldap-monitor backup full \
  --output backup.ldif \
  --exclude "ou=temp,dc=example,dc=com" \
  --exclude "ou=cache,dc=example,dc=com"
```

## 👥 Sauvegardes Sélectives

### Backup Utilisateurs Seulement

```bash
# Tous les utilisateurs
ldap-monitor backup users --output users-backup.ldif

# Résultat
Backing up users...
Found 850 users

Progress: [========================================] 850/850

✓ Backup completed: users-backup.ldif
  Entries: 850
  Size: 8.5 MB
  Duration: 4.2s

# Utilisateurs actifs uniquement
ldap-monitor backup users \
  --output active-users.ldif \
  --active-only

# Utilisateurs avec attributs spécifiques
ldap-monitor backup users \
  --output users-subset.ldif \
  --attributes "uid,cn,mail,telephoneNumber"

# Format CSV
ldap-monitor backup users --output users.csv --format csv
```

### Backup Groupes Seulement

```bash
# Tous les groupes
ldap-monitor backup groups --output groups-backup.ldif

# Groupes avec membres
ldap-monitor backup groups \
  --output groups-with-members.ldif \
  --include-members

# Groupes non vides uniquement
ldap-monitor backup groups \
  --output non-empty-groups.ldif \
  --non-empty-only
```

### Backup Incrémental

```bash
# Backup incrémental (depuis dernière sauvegarde)
ldap-monitor backup incremental --output incremental.ldif

# Résultat
Checking for changes since last backup...
Last backup: 2025-01-16 17:00:00

Found changes:
  - New entries: 12
  - Modified entries: 23
  - Deleted entries: 5

✓ Incremental backup completed: incremental.ldif
  Total changes: 40
  Size: 456 KB

# Backup différentiel (depuis backup de référence)
ldap-monitor backup differential \
  --reference backups/full_20250101.ldif \
  --output diff_20250117.ldif

# Backup des modifications depuis une date
ldap-monitor backup changes \
  --since "2025-01-15" \
  --output recent-changes.ldif
```

## 🔄 Restauration

### Restauration Complète

```bash
# Restaurer depuis un backup LDIF
ldap-monitor restore backup.ldif

# Résultat
⚠ WARNING: This will overwrite existing data!
Analyzing backup file...

Backup information:
  Date: 2025-01-17 17:00:00
  Entries: 1,234
  Base DN: dc=example,dc=com

Do you want to continue? [y/N]: y

Creating safety backup before restore...
✓ Safety backup: backups/pre-restore_20250117_171500.ldif.gz

Restoring entries...
Progress: [========================================] 1234/1234

✓ Restore completed successfully
  Entries restored: 1,234
  Duration: 15.3s

# Restauration automatique (sans confirmation)
ldap-monitor restore backup.ldif --yes --backup

# Dry-run (tester sans restaurer)
ldap-monitor restore backup.ldif --dry-run

# Résultat dry-run
Would restore 1,234 entries:
  - Would add: 45 new entries
  - Would update: 1,189 existing entries
  - Would delete: 0 entries (not in backup)

Changes preview:
  ou=users: 850 entries
  ou=groups: 156 entries
  ou=other: 228 entries

No changes made (dry-run mode)
```

### Restauration Sélective

```bash
# Restaurer seulement une branche
ldap-monitor restore backup.ldif \
  --base-dn "ou=users,dc=example,dc=com" \
  --backup

# Restaurer un utilisateur spécifique
ldap-monitor restore backup.ldif \
  --dn "uid=jdoe,ou=users,dc=example,dc=com" \
  --backup

# Restaurer plusieurs entrées
ldap-monitor restore backup.ldif \
  --filter "(department=IT)" \
  --backup

# Restaurer sans écraser les données existantes
ldap-monitor restore backup.ldif \
  --mode add-only \
  --backup

# Restaurer seulement les entrées manquantes
ldap-monitor restore backup.ldif \
  --mode missing-only \
  --backup
```

### Restauration depuis JSON

```bash
# Restaurer depuis JSON
ldap-monitor restore backup.json --format json --backup

# Convertir JSON en LDIF puis restaurer
ldap-monitor convert backup.json --to ldif --output backup.ldif
ldap-monitor restore backup.ldif --backup
```

### Restauration avec Fusion

```bash
# Fusionner avec données existantes
ldap-monitor restore backup.ldif --merge --backup

# Résultat
Analyzing backup and current directory...

Merge plan:
  - Keep existing: 1,189 entries
  - Add from backup: 45 entries
  - Update from backup: 23 entries
  - Skip (conflicts): 12 entries

Conflicts found:
  uid=jdoe,ou=users,dc=example,dc=com
    Current: modified 2025-01-17
    Backup: modified 2025-01-16
    Action: Keep current

Proceed with merge? [y/N]: y

# Résolution automatique des conflits
ldap-monitor restore backup.ldif \
  --merge \
  --conflict-strategy newest \
  --backup

# Stratégies de résolution:
# - newest: garder la version la plus récente
# - oldest: garder la version la plus ancienne
# - current: toujours garder la version actuelle
# - backup: toujours prendre la version du backup
# - prompt: demander pour chaque conflit
```

## 📦 Compression et Chiffrement

### Compression

```bash
# Backup avec compression gzip
ldap-monitor backup full --output backup.ldif --compress

# Backup avec niveau de compression
ldap-monitor backup full \
  --output backup.ldif \
  --compress \
  --compression-level 9  # 1-9, 9 = maximum

# Résultat
✓ Backup completed: backup.ldif.gz
  Original size: 15.3 MB
  Compressed size: 1.8 MB
  Compression ratio: 88.2%
  Compression level: 9

# Backup avec bzip2 (meilleure compression)
ldap-monitor backup full \
  --output backup.ldif \
  --compress-format bzip2

# Backup avec xz (compression maximale)
ldap-monitor backup full \
  --output backup.ldif \
  --compress-format xz
```

### Chiffrement

```bash
# Backup chiffré
ldap-monitor backup full \
  --output backup.ldif \
  --encrypt \
  --password-file /secure/backup-password.txt

# Backup chiffré avec compression
ldap-monitor backup full \
  --output backup.ldif \
  --compress \
  --encrypt \
  --password-file /secure/backup-password.txt

# Résultat
✓ Backup completed: backup.ldif.gz.enc
  Size: 2.1 MB (compressed and encrypted)
  Encryption: AES-256-CBC

# Backup avec clé GPG
ldap-monitor backup full \
  --output backup.ldif \
  --encrypt-gpg \
  --recipient admin@example.com

# Restaurer un backup chiffré
ldap-monitor restore backup.ldif.gz.enc \
  --password-file /secure/backup-password.txt \
  --backup
```

## ⏰ Planification et Automatisation

### Configuration de Sauvegarde Automatique

```yaml
# config.yaml
backup:
  # Répertoire de sauvegarde
  backup_dir: /var/backups/ldap

  # Rétention
  retention_days: 90
  retention_full_backups: 10
  retention_incremental_backups: 30

  # Compression
  compress: true
  compression_format: gzip  # gzip, bzip2, xz
  compression_level: 6      # 1-9

  # Chiffrement
  encrypt: true
  encryption_method: aes-256-cbc
  password_file: /etc/ldap-monitor/backup-key.txt

  # Planification
  schedule:
    full_backup: "0 2 * * 0"      # Dimanche 2h
    incremental: "0 2 * * 1-6"    # Lun-Sam 2h
    differential: "0 14 * * *"    # Tous les jours 14h

  # Notification
  notifications:
    on_success: false
    on_failure: true
    email: admin@example.com

  # Vérification
  verify_after_backup: true
  test_restore: false  # Test de restauration périodique
```

### Script de Backup Automatique

```bash
#!/bin/bash
# auto-backup.sh

CONFIG_FILE="/etc/ldap-monitor/config.yaml"
BACKUP_DIR="/var/backups/ldap"
LOG_FILE="/var/log/ldap-backup.log"
DATE=$(date +"%Y%m%d_%H%M%S")
DAY=$(date +"%u")  # 1=Lundi, 7=Dimanche

# Fonction de logging
log() {
    echo "[$(date +"%Y-%m-%d %H:%M:%S")] $1" | tee -a "$LOG_FILE"
}

# Fonction de notification
notify() {
    local subject=$1
    local message=$2
    echo "$message" | mail -s "$subject" admin@example.com
}

log "Starting LDAP backup..."

# Backup complet le dimanche, incrémental les autres jours
if [ "$DAY" -eq 7 ]; then
    log "Running full backup..."

    ldap-monitor backup full \
        --output "$BACKUP_DIR/full_$DATE.ldif" \
        --compress \
        --encrypt \
        --password-file /secure/backup-password.txt \
        >> "$LOG_FILE" 2>&1

    RESULT=$?

    if [ $RESULT -eq 0 ]; then
        log "Full backup completed successfully"

        # Vérifier le backup
        log "Verifying backup..."
        ldap-monitor backup verify "$BACKUP_DIR/full_$DATE.ldif.gz.enc" \
            --password-file /secure/backup-password.txt \
            >> "$LOG_FILE" 2>&1

        if [ $? -eq 0 ]; then
            log "Backup verification successful"
        else
            log "ERROR: Backup verification failed"
            notify "LDAP Backup Verification Failed" "Full backup verification failed. Check logs."
        fi
    else
        log "ERROR: Full backup failed"
        notify "LDAP Backup Failed" "Full backup failed with error code $RESULT. Check logs."
        exit 1
    fi
else
    log "Running incremental backup..."

    ldap-monitor backup incremental \
        --output "$BACKUP_DIR/incr_$DATE.ldif" \
        --compress \
        --encrypt \
        --password-file /secure/backup-password.txt \
        >> "$LOG_FILE" 2>&1

    if [ $? -eq 0 ]; then
        log "Incremental backup completed successfully"
    else
        log "ERROR: Incremental backup failed"
        notify "LDAP Backup Failed" "Incremental backup failed. Check logs."
        exit 1
    fi
fi

# Nettoyer les vieux backups
log "Cleaning old backups..."
ldap-monitor backup cleanup --days 90 >> "$LOG_FILE" 2>&1

# Statistiques
log "Backup statistics:"
du -sh "$BACKUP_DIR" | tee -a "$LOG_FILE"
ls -lh "$BACKUP_DIR" | tail -5 | tee -a "$LOG_FILE"

log "Backup process completed"
```

### Cron Jobs

```bash
# Crontab entries

# Backup complet tous les dimanches à 2h
0 2 * * 0 /usr/local/bin/auto-backup.sh full

# Backup incrémental du lundi au samedi à 2h
0 2 * * 1-6 /usr/local/bin/auto-backup.sh incremental

# Backup différentiel tous les jours à 14h (sécurité)
0 14 * * * /usr/local/bin/auto-backup.sh differential

# Vérification des backups tous les lundis à 10h
0 10 * * 1 ldap-monitor backup verify-all --email-report admin@example.com

# Nettoyage des vieux backups tous les 1er du mois à 3h
0 3 1 * * ldap-monitor backup cleanup --days 90 --confirm

# Test de restauration mensuel (environnement de test)
0 4 1 * * /usr/local/bin/test-restore.sh
```

### Systemd Timer

```ini
# /etc/systemd/system/ldap-backup.timer
[Unit]
Description=LDAP Backup Timer
Requires=ldap-backup.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target

# /etc/systemd/system/ldap-backup.service
[Unit]
Description=LDAP Backup Service
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/auto-backup.sh
User=ldap-backup
Group=ldap-backup
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target

# Activer
systemctl enable ldap-backup.timer
systemctl start ldap-backup.timer

# Vérifier
systemctl status ldap-backup.timer
systemctl list-timers ldap-backup.timer
```

## 🔍 Vérification et Tests

### Vérifier un Backup

```bash
# Vérifier l'intégrité d'un backup
ldap-monitor backup verify backup.ldif

# Résultat
Verifying backup file...

File information:
  Path: backup.ldif.gz
  Size: 2.1 MB
  Format: LDIF (gzip compressed)
  Created: 2025-01-17 17:00:00

Verification checks:
  ✓ File is readable
  ✓ Compression is valid
  ✓ LDIF syntax is valid
  ✓ All DNs are valid
  ✓ All attributes are valid
  ✓ No duplicate entries
  ✓ Structure is consistent

Entries: 1,234
Base DNs: dc=example,dc=com
Object classes: 15 types

✓ Backup verification passed

# Vérifier un backup chiffré
ldap-monitor backup verify backup.ldif.gz.enc \
  --password-file /secure/backup-password.txt

# Vérifier tous les backups
ldap-monitor backup verify-all --directory /var/backups/ldap

# Résultat
Verifying all backups in /var/backups/ldap...

[1/15] full_20250110_020000.ldif.gz: ✓ OK
[2/15] full_20250103_020000.ldif.gz: ✓ OK
[3/15] incr_20250116_020000.ldif.gz: ✓ OK
...
[15/15] incr_20250117_020000.ldif.gz: ✓ OK

Summary:
  Total: 15
  Valid: 15
  Invalid: 0
  Corrupted: 0
```

### Test de Restauration

```bash
# Test de restauration (environnement de test)
ldap-monitor restore backup.ldif \
  --test-mode \
  --test-server "ldap://test.example.com" \
  --test-bind-dn "cn=admin,dc=test,dc=com"

# Résultat
Testing restore on test server...

✓ Connected to test server
✓ Cleared test directory
✓ Restored 1,234 entries

Verification:
  ✓ Entry count matches (1,234)
  ✓ All DNs present
  ✓ Sample entries valid

Test restore successful!
Test environment ready for validation.

# Test de restauration automatisé
#!/bin/bash
# test-restore.sh

# 1. Prendre un backup récent
BACKUP_FILE=$(ls -t /var/backups/ldap/full_*.ldif.gz | head -1)

# 2. Restaurer sur serveur de test
ldap-monitor restore "$BACKUP_FILE" \
    --test-server "ldap://test.example.com" \
    --test-bind-dn "cn=admin,dc=test,dc=com" \
    --password-file /secure/test-admin-password.txt

# 3. Vérifier
ldap-monitor test connection --config test-config.yaml
ldap-monitor audit all --config test-config.yaml

# 4. Rapport
if [ $? -eq 0 ]; then
    echo "Test restore successful" | \
        mail -s "LDAP Restore Test: PASSED" admin@example.com
else
    echo "Test restore failed" | \
        mail -s "LDAP Restore Test: FAILED" admin@example.com
fi
```

## 📊 Gestion des Backups

### Lister les Backups

```bash
# Lister tous les backups
ldap-monitor backup list

# Résultat
LDAP Backups in /var/backups/ldap
==================================

Full Backups:
  1. full_20250117_020000.ldif.gz.enc
     Date: 2025-01-17 02:00:00
     Size: 2.1 MB
     Entries: 1,234
     Type: Full, Compressed, Encrypted

  2. full_20250110_020000.ldif.gz.enc
     Date: 2025-01-10 02:00:00
     Size: 2.0 MB
     Entries: 1,189
     Type: Full, Compressed, Encrypted

Incremental Backups (last 7 days):
  3. incr_20250117_020000.ldif.gz
     Date: 2025-01-17 02:00:00
     Size: 156 KB
     Changes: 40
     Type: Incremental, Compressed

Total backups: 15
Total size: 28.5 MB
Oldest: 2024-10-19 02:00:00 (90 days)
Newest: 2025-01-17 02:00:00 (today)

# Lister avec filtres
ldap-monitor backup list --type full --days 30

# Export de la liste
ldap-monitor backup list --output backups.csv --format csv
```

### Informations sur un Backup

```bash
# Informations détaillées
ldap-monitor backup info backup.ldif.gz.enc

# Résultat
Backup Information
==================

File:
  Path: /var/backups/ldap/full_20250117_020000.ldif.gz.enc
  Size: 2.1 MB
  Created: 2025-01-17 02:00:15
  Modified: 2025-01-17 02:00:15
  Permissions: -rw-------

Format:
  Type: Full backup
  Format: LDIF
  Compression: gzip (level 6)
  Encryption: AES-256-CBC
  Checksum (SHA256): a1b2c3d4...

Content:
  Base DN: dc=example,dc=com
  Entries: 1,234
  Object classes:
    - inetOrgPerson: 850
    - groupOfNames: 156
    - organizationalUnit: 45
    - domain: 1
    - other: 182

Branches:
  ou=users,dc=example,dc=com: 850 entries
  ou=groups,dc=example,dc=com: 156 entries
  ou=services,dc=example,dc=com: 45 entries

Metadata:
  Created by: ldap-monitor v1.0.0
  Server: ldap.example.com
  Backup duration: 8.2s
  Verified: Yes (2025-01-17 02:05:00)

# Comparer deux backups
ldap-monitor backup diff backup1.ldif backup2.ldif

# Résultat
Comparing backups...

Differences:
  New entries: 12
  Modified entries: 23
  Deleted entries: 5

New entries:
  - uid=newuser1,ou=users,dc=example,dc=com
  - uid=newuser2,ou=users,dc=example,dc=com
  ...

Modified entries:
  - uid=jdoe,ou=users,dc=example,dc=com
    Changed: mail (old@example.com → new@example.com)
  ...

Deleted entries:
  - uid=olduser,ou=users,dc=example,dc=com
  ...
```

### Nettoyer les Vieux Backups

```bash
# Dry-run
ldap-monitor backup cleanup --days 90 --dry-run

# Résultat
Would delete 8 old backups (> 90 days):

  1. full_20241019_020000.ldif.gz.enc (90 days old, 2.0 MB)
  2. full_20241012_020000.ldif.gz.enc (97 days old, 1.9 MB)
  ...

Total space to free: 15.2 MB
Keeping 7 recent backups

# Nettoyer avec confirmation
ldap-monitor backup cleanup --days 90 --confirm

# Résultat
✓ Deleted 8 old backups
✓ Freed 15.2 MB

# Nettoyer en gardant un nombre minimum
ldap-monitor backup cleanup \
  --days 90 \
  --keep-minimum 5 \
  --confirm

# Nettoyer selon la stratégie
ldap-monitor backup cleanup --strategy smart --confirm

# Stratégie smart:
# - Garder tous les backups < 7 jours
# - Garder 1 backup/semaine pour le dernier mois
# - Garder 1 backup/mois pour la dernière année
# - Supprimer tout le reste
```

## 📋 Meilleures Pratiques

### 1. Stratégie 3-2-1

```bash
# 3 copies des données
# 2 types de médias différents
# 1 copie hors site

# Local (primaire)
ldap-monitor backup full --output /var/backups/ldap/backup.ldif

# Local (secondaire - NAS)
ldap-monitor backup full --output /mnt/nas/ldap-backups/backup.ldif

# Distant (cloud)
ldap-monitor backup full --output /tmp/backup.ldif
aws s3 cp /tmp/backup.ldif.gz s3://my-ldap-backups/
```

### 2. Planification Optimale

```bash
# Quotidien: Backup incrémental
# Hebdomadaire: Backup complet
# Mensuel: Test de restauration
# Trimestriel: Revue de la stratégie

Daily (2h):
  - Incremental backup
  - Verify backup
  - Clean temp files

Weekly (Sunday 2h):
  - Full backup
  - Verify all backups
  - Update documentation

Monthly (1st, 4h):
  - Test restore
  - Clean old backups
  - Generate reports

Quarterly:
  - Review backup strategy
  - Update retention policy
  - Disaster recovery drill
```

### 3. Sécurité

```bash
# Toujours chiffrer
backup:
  encrypt: true
  encryption_method: aes-256-cbc

# Permissions strictes
chmod 600 /var/backups/ldap/*.ldif.gz.enc
chown ldap-backup:ldap-backup /var/backups/ldap/

# Backups hors site
# - Cloud storage (S3, Azure Blob, etc.)
# - Datacenter secondaire
# - Bandes magnétiques (pour long terme)
```

### 4. Tests Réguliers

```bash
# Tester la restauration régulièrement
# - Mensuel: Restauration complète sur environnement de test
# - Trimestriel: Exercice de disaster recovery
# - Annuel: Test de restauration à partir de backup ancien

# Script de test mensuel
#!/bin/bash
# monthly-restore-test.sh

BACKUP=$(ls -t /var/backups/ldap/full_*.ldif.gz.enc | head -1)

ldap-monitor restore "$BACKUP" \
    --test-server ldap://test.example.com \
    --verify \
    --email-report admin@example.com
```

### 5. Documentation

```bash
# Documenter:
# - Stratégie de backup
# - Procédures de restauration
# - Contacts d'urgence
# - Historique des restaurations
# - Leçons apprises

# Maintenir un runbook
/docs/backup-restore-runbook.md:
  - Backup procedure
  - Restore procedure
  - Emergency contacts
  - Common issues
  - Test results history
```

## 🔧 Dépannage

### Problèmes Courants

**Erreur: Backup file corrupted**
```bash
# Vérifier l'intégrité
ldap-monitor backup verify backup.ldif.gz

# Si corrompu, utiliser un backup antérieur
ldap-monitor backup list
ldap-monitor restore previous_backup.ldif.gz --backup
```

**Erreur: Insufficient space**
```bash
# Vérifier l'espace
df -h /var/backups/ldap

# Nettoyer les vieux backups
ldap-monitor backup cleanup --days 30 --confirm

# Ou utiliser une compression plus forte
ldap-monitor backup full --compress-format xz
```

**Erreur: Cannot decrypt backup**
```bash
# Vérifier le fichier de mot de passe
cat /secure/backup-password.txt

# Tester le déchiffrement
openssl enc -aes-256-cbc -d \
    -in backup.ldif.gz.enc \
    -out backup.ldif.gz \
    -pass file:/secure/backup-password.txt
```

## 📚 Voir Aussi

- [Gestion des Utilisateurs](User-Management.md)
- [Gestion des Groupes](Group-Management.md)
- [Opérations de Nettoyage](Cleanup-Operations.md)
- [Exports de Données](Data-Exports.md)
