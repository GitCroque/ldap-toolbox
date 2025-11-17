# Guide de Stratégie de Sauvegarde

Guide complet pour les stratégies de sauvegarde LDAP, planification, tests et récupération après sinistre.

## 🎯 Vue d'Ensemble

Ce guide couvre :

- Stratégies de sauvegarde LDAP
- Types de sauvegardes
- Planification et automatisation
- Tests de restauration
- Disaster Recovery (DR)
- Archivage long terme
- Conformité et rétention

## 📋 Types de Sauvegardes

### Sauvegarde Complète (Full Backup)

```bash
#!/bin/bash
# scripts/full-backup.sh

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backups/ldap/full"
RETENTION_DAYS=30

mkdir -p "$BACKUP_DIR"

# OpenLDAP: slapcat
slapcat -v -l "$BACKUP_DIR/ldap-full-$DATE.ldif"

# Compresser
gzip "$BACKUP_DIR/ldap-full-$DATE.ldif"

# Checksum
sha256sum "$BACKUP_DIR/ldap-full-$DATE.ldif.gz" > "$BACKUP_DIR/ldap-full-$DATE.ldif.gz.sha256"

# Nettoyage anciennes sauvegardes
find "$BACKUP_DIR" -name "ldap-full-*.ldif.gz" -mtime +$RETENTION_DAYS -delete

echo "✓ Full backup completed: $BACKUP_DIR/ldap-full-$DATE.ldif.gz"
```

### Sauvegarde Incrémentale

```bash
#!/bin/bash
# scripts/incremental-backup.sh

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backups/ldap/incremental"
LAST_BACKUP_FILE="/var/lib/ldap-backup/last-backup-timestamp"

mkdir -p "$BACKUP_DIR"

# Obtenir timestamp dernière sauvegarde
if [ -f "$LAST_BACKUP_FILE" ]; then
    LAST_BACKUP=$(cat "$LAST_BACKUP_FILE")
else
    LAST_BACKUP="19700101000000Z"
fi

# Export entrées modifiées depuis dernière sauvegarde
ldapsearch -x -LLL -H ldapi:/// \
    -D "cn=admin,dc=example,dc=com" \
    -w "password" \
    -b "dc=example,dc=com" \
    "(modifyTimestamp>=$LAST_BACKUP)" \
    > "$BACKUP_DIR/ldap-incremental-$DATE.ldif"

# Compresser
gzip "$BACKUP_DIR/ldap-incremental-$DATE.ldif"

# Mettre à jour timestamp
date -u +%Y%m%d%H%M%SZ > "$LAST_BACKUP_FILE"

echo "✓ Incremental backup completed: $BACKUP_DIR/ldap-incremental-$DATE.ldif.gz"
```

### Sauvegarde en Ligne (Hot Backup)

```bash
#!/bin/bash
# scripts/hot-backup.sh

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backups/ldap/hot"

mkdir -p "$BACKUP_DIR"

# Backup avec serveur en ligne (ldapsearch)
ldapsearch -x -LLL -H ldaps://ldap.example.com \
    -D "cn=admin,dc=example,dc=com" \
    -w "password" \
    -b "dc=example,dc=com" \
    "(objectClass=*)" \
    "*" "+" \
    > "$BACKUP_DIR/ldap-hot-$DATE.ldif"

# Compresser
gzip "$BACKUP_DIR/ldap-hot-$DATE.ldif"

echo "✓ Hot backup completed: $BACKUP_DIR/ldap-hot-$DATE.ldif.gz"
```

### Sauvegarde des Fichiers

```bash
#!/bin/bash
# scripts/filesystem-backup.sh

DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_DIR="/backups/ldap/filesystem"

mkdir -p "$BACKUP_DIR"

# Arrêter service (hors ligne)
systemctl stop slapd

# Backup répertoires LDAP
tar czf "$BACKUP_DIR/ldap-data-$DATE.tar.gz" \
    /var/lib/ldap \
    /etc/ldap/slapd.d \
    /etc/ldap/schema

# Redémarrer service
systemctl start slapd

# Checksum
sha256sum "$BACKUP_DIR/ldap-data-$DATE.tar.gz" > "$BACKUP_DIR/ldap-data-$DATE.tar.gz.sha256"

echo "✓ Filesystem backup completed: $BACKUP_DIR/ldap-data-$DATE.tar.gz"
```

## 🔄 Stratégies de Sauvegarde

### Stratégie 3-2-1

```yaml
# config/backup-strategy.yaml

backup_strategy:
  name: "3-2-1 Strategy"
  description: "3 copies, 2 different media, 1 offsite"

  # 3 Copies
  copies:
    - type: production
      location: /var/lib/ldap
      description: "Données en production"

    - type: local_backup
      location: /backups/ldap
      description: "Sauvegarde locale"
      schedule:
        full: "0 2 * * 0"  # Dimanche 2h
        incremental: "0 2 * * 1-6"  # Lundi-Samedi 2h

    - type: remote_backup
      location: "s3://backups/ldap"
      description: "Sauvegarde distante"
      schedule:
        sync: "0 4 * * *"  # Tous les jours 4h

  # 2 Médias différents
  media:
    - type: disk
      locations: ["/backups/ldap", "/mnt/backup-disk"]

    - type: cloud
      provider: aws_s3
      bucket: backups
      prefix: ldap/

  # 1 Hors site
  offsite:
    enabled: true
    provider: aws_s3
    region: eu-west-1
    encryption: AES256

  # Rétention
  retention:
    daily: 7    # 7 jours de sauvegardes quotidiennes
    weekly: 4   # 4 semaines de sauvegardes hebdomadaires
    monthly: 12 # 12 mois de sauvegardes mensuelles
    yearly: 7   # 7 ans de sauvegardes annuelles
```

### Script de Stratégie Complète

```python
#!/usr/bin/env python3
# scripts/backup-manager.py

import os
import subprocess
import datetime
import gzip
import shutil
import hashlib
import boto3
from pathlib import Path

class LDAPBackupManager:
    """Gestionnaire de sauvegardes LDAP"""

    def __init__(self, config):
        self.config = config
        self.backup_dir = Path(config['backup_dir'])
        self.retention = config['retention']

        # Créer répertoires
        for backup_type in ['full', 'incremental', 'hot']:
            (self.backup_dir / backup_type).mkdir(parents=True, exist_ok=True)

    def create_full_backup(self):
        """Créer sauvegarde complète"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_file = self.backup_dir / 'full' / f'ldap-full-{timestamp}.ldif'

        print(f"Creating full backup: {backup_file}")

        # Export LDAP
        result = subprocess.run(
            ['slapcat', '-v', '-l', str(backup_file)],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            raise Exception(f"slapcat failed: {result.stderr}")

        # Compresser
        compressed_file = self.compress_file(backup_file)

        # Checksum
        self.create_checksum(compressed_file)

        # Nettoyer fichier non compressé
        backup_file.unlink()

        print(f"✓ Full backup created: {compressed_file}")
        return compressed_file

    def create_incremental_backup(self):
        """Créer sauvegarde incrémentale"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
        backup_file = self.backup_dir / 'incremental' / f'ldap-incr-{timestamp}.ldif'

        # Obtenir timestamp dernière sauvegarde
        last_backup_ts = self.get_last_backup_timestamp()

        print(f"Creating incremental backup since: {last_backup_ts}")

        # Export entrées modifiées
        ldap_filter = f'(modifyTimestamp>={last_backup_ts})'

        result = subprocess.run([
            'ldapsearch', '-x', '-LLL',
            '-H', self.config['ldap_uri'],
            '-D', self.config['bind_dn'],
            '-w', self.config['bind_password'],
            '-b', self.config['base_dn'],
            ldap_filter
        ], capture_output=True, text=True)

        if result.returncode != 0:
            raise Exception(f"ldapsearch failed: {result.stderr}")

        # Écrire résultats
        backup_file.write_text(result.stdout)

        # Compresser
        compressed_file = self.compress_file(backup_file)

        # Checksum
        self.create_checksum(compressed_file)

        # Nettoyer
        backup_file.unlink()

        # Mettre à jour timestamp
        self.update_last_backup_timestamp()

        print(f"✓ Incremental backup created: {compressed_file}")
        return compressed_file

    def compress_file(self, file_path):
        """Compresser fichier"""
        compressed_path = Path(str(file_path) + '.gz')

        with open(file_path, 'rb') as f_in:
            with gzip.open(compressed_path, 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)

        return compressed_path

    def create_checksum(self, file_path):
        """Créer checksum SHA256"""
        sha256_hash = hashlib.sha256()

        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        checksum_file = Path(str(file_path) + '.sha256')
        checksum_file.write_text(
            f"{sha256_hash.hexdigest()}  {file_path.name}\n"
        )

        return checksum_file

    def verify_checksum(self, file_path):
        """Vérifier checksum"""
        checksum_file = Path(str(file_path) + '.sha256')

        if not checksum_file.exists():
            return False

        # Calculer checksum actuel
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)

        actual_checksum = sha256_hash.hexdigest()

        # Lire checksum enregistré
        stored_checksum = checksum_file.read_text().split()[0]

        return actual_checksum == stored_checksum

    def upload_to_s3(self, file_path):
        """Upload vers S3"""
        if not self.config.get('s3_enabled'):
            return

        s3 = boto3.client('s3')
        bucket = self.config['s3_bucket']
        key = f"{self.config['s3_prefix']}/{file_path.name}"

        print(f"Uploading to S3: s3://{bucket}/{key}")

        s3.upload_file(
            str(file_path),
            bucket,
            key,
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )

        # Upload checksum aussi
        checksum_file = Path(str(file_path) + '.sha256')
        if checksum_file.exists():
            s3.upload_file(
                str(checksum_file),
                bucket,
                f"{key}.sha256"
            )

        print(f"✓ Uploaded to S3")

    def apply_retention_policy(self):
        """Appliquer politique de rétention"""
        now = datetime.datetime.now()

        for backup_type in ['full', 'incremental']:
            backup_dir = self.backup_dir / backup_type
            retention_days = self.retention.get(backup_type, 30)

            print(f"Applying retention policy for {backup_type} ({retention_days} days)")

            for backup_file in backup_dir.glob('*.ldif.gz'):
                # Obtenir âge du fichier
                file_age = now - datetime.datetime.fromtimestamp(
                    backup_file.stat().st_mtime
                )

                if file_age.days > retention_days:
                    print(f"  Deleting old backup: {backup_file.name}")
                    backup_file.unlink()

                    # Supprimer checksum aussi
                    checksum_file = Path(str(backup_file) + '.sha256')
                    if checksum_file.exists():
                        checksum_file.unlink()

    def get_last_backup_timestamp(self):
        """Obtenir timestamp dernière sauvegarde"""
        timestamp_file = self.backup_dir / 'last-backup-timestamp'

        if timestamp_file.exists():
            return timestamp_file.read_text().strip()
        else:
            # Valeur par défaut (epoch)
            return '19700101000000Z'

    def update_last_backup_timestamp(self):
        """Mettre à jour timestamp dernière sauvegarde"""
        timestamp_file = self.backup_dir / 'last-backup-timestamp'
        current_ts = datetime.datetime.utcnow().strftime('%Y%m%d%H%M%SZ')
        timestamp_file.write_text(current_ts)

    def run_backup(self, backup_type='full'):
        """Exécuter sauvegarde"""
        try:
            if backup_type == 'full':
                backup_file = self.create_full_backup()
            elif backup_type == 'incremental':
                backup_file = self.create_incremental_backup()
            else:
                raise ValueError(f"Unknown backup type: {backup_type}")

            # Upload vers S3
            self.upload_to_s3(backup_file)

            # Appliquer rétention
            self.apply_retention_policy()

            return True

        except Exception as e:
            print(f"✗ Backup failed: {e}")
            return False

# Configuration
config = {
    'backup_dir': '/backups/ldap',
    'ldap_uri': 'ldaps://ldap.example.com',
    'bind_dn': 'cn=admin,dc=example,dc=com',
    'bind_password': 'password',
    'base_dn': 'dc=example,dc=com',
    'retention': {
        'full': 30,
        'incremental': 7
    },
    's3_enabled': True,
    's3_bucket': 'my-backups',
    's3_prefix': 'ldap'
}

# Usage
manager = LDAPBackupManager(config)

# Sauvegarde complète
manager.run_backup('full')

# Sauvegarde incrémentale
manager.run_backup('incremental')
```

## 🔄 Restauration

### Restauration Complète

```bash
#!/bin/bash
# scripts/restore-full.sh

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "Restoring from: $BACKUP_FILE"

# Vérifier checksum
CHECKSUM_FILE="${BACKUP_FILE}.sha256"
if [ -f "$CHECKSUM_FILE" ]; then
    echo "Verifying checksum..."
    sha256sum -c "$CHECKSUM_FILE" || exit 1
    echo "✓ Checksum verified"
fi

# Arrêter service
echo "Stopping LDAP service..."
systemctl stop slapd

# Sauvegarder données actuelles
BACKUP_DATE=$(date +%Y%m%d-%H%M%S)
echo "Backing up current data..."
tar czf "/backups/ldap/pre-restore-$BACKUP_DATE.tar.gz" \
    /var/lib/ldap \
    /etc/ldap/slapd.d

# Nettoyer données actuelles
echo "Cleaning current data..."
rm -rf /var/lib/ldap/*
rm -rf /etc/ldap/slapd.d/*

# Décompresser backup
echo "Decompressing backup..."
TEMP_LDIF="/tmp/restore-$BACKUP_DATE.ldif"
gunzip -c "$BACKUP_FILE" > "$TEMP_LDIF"

# Restaurer avec slapadd
echo "Restoring data..."
slapadd -v -l "$TEMP_LDIF"

# Permissions
chown -R openldap:openldap /var/lib/ldap
chown -R openldap:openldap /etc/ldap/slapd.d

# Redémarrer service
echo "Starting LDAP service..."
systemctl start slapd

# Vérifier
sleep 5
if systemctl is-active --quiet slapd; then
    echo "✓ Restore completed successfully"

    # Test connexion
    ldapsearch -x -b "dc=example,dc=com" -s base "(objectClass=*)" && \
        echo "✓ LDAP server is responding"
else
    echo "✗ LDAP service failed to start"
    exit 1
fi

# Nettoyer fichier temporaire
rm -f "$TEMP_LDIF"
```

### Restauration Sélective

```python
#!/usr/bin/env python3
# scripts/selective-restore.py

import ldap
import ldif
import sys
from io import StringIO

class SelectiveRestore:
    """Restauration sélective d'entrées LDAP"""

    def __init__(self, ldap_uri, bind_dn, bind_pw):
        self.conn = ldap.initialize(ldap_uri)
        self.conn.simple_bind_s(bind_dn, bind_pw)

    def restore_entry(self, dn, attrs):
        """Restaurer une entrée"""
        try:
            # Vérifier si entrée existe
            try:
                self.conn.search_s(dn, ldap.SCOPE_BASE)
                # Entrée existe, modifier
                print(f"Updating existing entry: {dn}")

                modlist = []
                for attr, values in attrs.items():
                    if attr != 'dn':
                        modlist.append((ldap.MOD_REPLACE, attr, values))

                self.conn.modify_s(dn, modlist)

            except ldap.NO_SUCH_OBJECT:
                # Entrée n'existe pas, ajouter
                print(f"Adding new entry: {dn}")

                # Convertir format pour ldap.add_s
                add_attrs = [
                    (attr, values)
                    for attr, values in attrs.items()
                    if attr != 'dn'
                ]

                self.conn.add_s(dn, add_attrs)

            return True

        except ldap.LDAPError as e:
            print(f"Error restoring {dn}: {e}")
            return False

    def restore_from_ldif(self, ldif_file, filter_func=None):
        """Restaurer depuis fichier LDIF avec filtre optionnel"""

        class LDIFParser(ldif.LDIFParser):
            def __init__(self, input_file, restore_obj, filter_func):
                ldif.LDIFParser.__init__(self, input_file)
                self.restore_obj = restore_obj
                self.filter_func = filter_func
                self.count = 0
                self.success = 0
                self.failed = 0

            def handle(self, dn, entry):
                # Appliquer filtre si fourni
                if self.filter_func and not self.filter_func(dn, entry):
                    return

                self.count += 1

                if self.restore_obj.restore_entry(dn, entry):
                    self.success += 1
                else:
                    self.failed += 1

        # Parser LDIF
        with open(ldif_file, 'r') as f:
            parser = LDIFParser(f, self, filter_func)
            parser.parse()

            print(f"\nRestore summary:")
            print(f"  Total processed: {parser.count}")
            print(f"  Success: {parser.success}")
            print(f"  Failed: {parser.failed}")

    def restore_user(self, backup_file, uid):
        """Restaurer un utilisateur spécifique"""

        def user_filter(dn, entry):
            # Filtrer sur uid
            uid_values = entry.get('uid', [])
            return uid.encode() in uid_values

        self.restore_from_ldif(backup_file, user_filter)

    def restore_ou(self, backup_file, ou):
        """Restaurer une OU spécifique"""

        def ou_filter(dn, entry):
            # Filtrer sur DN contenant OU
            return ou in dn

        self.restore_from_ldif(backup_file, ou_filter)

# Usage
if __name__ == '__main__':
    restore = SelectiveRestore(
        'ldaps://ldap.example.com',
        'cn=admin,dc=example,dc=com',
        'password'
    )

    # Restaurer utilisateur spécifique
    restore.restore_user('/backups/ldap-full.ldif', 'jdoe')

    # Restaurer OU spécifique
    restore.restore_ou('/backups/ldap-full.ldif', 'ou=IT')
```

## 🧪 Tests de Restauration

### Script de Test Automatisé

```bash
#!/bin/bash
# scripts/test-restore.sh

set -euo pipefail

echo "=== LDAP Restore Test ==="

# Configuration
BACKUP_FILE="${1:-/backups/ldap/full/latest.ldif.gz}"
TEST_SERVER="ldap-test.example.com"
TEST_PORT=389
TEST_BASE_DN="dc=test,dc=example,dc=com"

# 1. Préparer environnement de test
echo "1. Preparing test environment..."

# Arrêter serveur test si actif
docker stop ldap-test 2>/dev/null || true
docker rm ldap-test 2>/dev/null || true

# Démarrer serveur LDAP de test
docker run -d \
    --name ldap-test \
    -p 389:389 \
    -e LDAP_ORGANISATION="Test" \
    -e LDAP_DOMAIN="test.example.com" \
    -e LDAP_ADMIN_PASSWORD="testpassword" \
    osixia/openldap:latest

# Attendre démarrage
sleep 10

# 2. Restaurer backup
echo "2. Restoring backup..."

gunzip -c "$BACKUP_FILE" | \
    ldapadd -x -H ldap://$TEST_SERVER:$TEST_PORT \
    -D "cn=admin,$TEST_BASE_DN" \
    -w testpassword

# 3. Vérifier données
echo "3. Verifying restored data..."

# Compter entrées
ENTRY_COUNT=$(ldapsearch -x -H ldap://$TEST_SERVER:$TEST_PORT \
    -D "cn=admin,$TEST_BASE_DN" \
    -w testpassword \
    -b "$TEST_BASE_DN" \
    "(objectClass=*)" dn | grep -c "^dn:")

echo "  Restored entries: $ENTRY_COUNT"

# Vérifier utilisateurs
USER_COUNT=$(ldapsearch -x -H ldap://$TEST_SERVER:$TEST_PORT \
    -D "cn=admin,$TEST_BASE_DN" \
    -w testpassword \
    -b "$TEST_BASE_DN" \
    "(objectClass=inetOrgPerson)" dn | grep -c "^dn:")

echo "  Users: $USER_COUNT"

# Vérifier groupes
GROUP_COUNT=$(ldapsearch -x -H ldap://$TEST_SERVER:$TEST_PORT \
    -D "cn=admin,$TEST_BASE_DN" \
    -w testpassword \
    -b "$TEST_BASE_DN" \
    "(objectClass=groupOfNames)" dn | grep -c "^dn:")

echo "  Groups: $GROUP_COUNT"

# 4. Tests fonctionnels
echo "4. Running functional tests..."

# Test recherche
if ldapsearch -x -H ldap://$TEST_SERVER:$TEST_PORT \
    -D "cn=admin,$TEST_BASE_DN" \
    -w testpassword \
    -b "$TEST_BASE_DN" \
    "(uid=*)" uid > /dev/null; then
    echo "  ✓ Search test passed"
else
    echo "  ✗ Search test failed"
fi

# Test bind
if ldapwhoami -x -H ldap://$TEST_SERVER:$TEST_PORT \
    -D "cn=admin,$TEST_BASE_DN" \
    -w testpassword > /dev/null; then
    echo "  ✓ Bind test passed"
else
    echo "  ✗ Bind test failed"
fi

# 5. Cleanup
echo "5. Cleaning up..."
docker stop ldap-test
docker rm ldap-test

echo ""
echo "=== Restore Test Complete ==="
echo "  Total entries: $ENTRY_COUNT"
echo "  Users: $USER_COUNT"
echo "  Groups: $GROUP_COUNT"
```

## 📅 Planification Automatique

### Configuration Cron

```bash
# /etc/cron.d/ldap-backup

# Variables
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=admin@example.com

# Sauvegarde complète hebdomadaire (Dimanche 2h)
0 2 * * 0 root /usr/local/bin/ldap-backup.sh full

# Sauvegarde incrémentale quotidienne (Lundi-Samedi 2h)
0 2 * * 1-6 root /usr/local/bin/ldap-backup.sh incremental

# Upload vers S3 (tous les jours 4h)
0 4 * * * root /usr/local/bin/ldap-backup-sync-s3.sh

# Test de restauration mensuel (1er du mois 3h)
0 3 1 * * root /usr/local/bin/test-restore.sh

# Nettoyage anciennes sauvegardes (tous les jours 5h)
0 5 * * * root /usr/local/bin/ldap-backup-cleanup.sh
```

### Service Systemd

```ini
# /etc/systemd/system/ldap-backup.service
[Unit]
Description=LDAP Backup Service
After=network-online.target slapd.service
Wants=network-online.target

[Service]
Type=oneshot
User=root
ExecStart=/usr/local/bin/ldap-backup.sh full
StandardOutput=journal
StandardError=journal
```

```ini
# /etc/systemd/system/ldap-backup.timer
[Unit]
Description=LDAP Backup Timer
Requires=ldap-backup.service

[Timer]
OnCalendar=Sun 02:00
Persistent=true
Unit=ldap-backup.service

[Install]
WantedBy=timers.target
```

## 🗄️ Archivage Long Terme

### Script d'Archivage

```bash
#!/bin/bash
# scripts/archive-longterm.sh

YEAR=$(date +%Y)
MONTH=$(date +%m)
ARCHIVE_DIR="/archives/ldap/$YEAR"
BACKUP_DIR="/backups/ldap/full"

mkdir -p "$ARCHIVE_DIR"

# Créer archive mensuelle
ARCHIVE_FILE="$ARCHIVE_DIR/ldap-archive-$YEAR-$MONTH.tar.gz"

# Trouver toutes les sauvegardes du mois
find "$BACKUP_DIR" -name "ldap-full-$YEAR$MONTH*.ldif.gz" \
    -exec tar czf "$ARCHIVE_FILE" {} +

# Encryption (GPG)
gpg --encrypt \
    --recipient admin@example.com \
    --output "$ARCHIVE_FILE.gpg" \
    "$ARCHIVE_FILE"

# Checksum
sha256sum "$ARCHIVE_FILE.gpg" > "$ARCHIVE_FILE.gpg.sha256"

# Upload vers archive glacier (AWS)
aws s3 cp "$ARCHIVE_FILE.gpg" \
    s3://long-term-archives/ldap/$YEAR/ \
    --storage-class GLACIER

echo "✓ Long-term archive created: $ARCHIVE_FILE.gpg"
```

## 📖 Voir Aussi

- [Production Monitoring](Production-Monitoring.md)
- [Multi-Server Setup](Multi-Server.md)
- [Docker Deployment](Docker-Deployment.md)
- [Disaster Recovery](../troubleshooting/Disaster-Recovery.md)
