# Opérations en Masse - Guide Complet

Les opérations en masse (bulk) permettent de gérer efficacement de grands volumes d'utilisateurs, groupes et autres entrées LDAP via des imports CSV, des modifications groupées et des traitements par lots.

## 🎯 Objectifs des Opérations en Masse

- ✅ Import de nouveaux utilisateurs/groupes
- ✅ Modifications massives d'attributs
- ✅ Synchronisation avec systèmes RH
- ✅ Migration entre serveurs
- ✅ Gestion de projet (ajouts/suppressions groupés)
- ✅ Corrections d'erreurs en masse
- ✅ Réorganisations structurelles
- ✅ Automatisation des tâches répétitives

## 📋 Types d'Opérations Supportées

```bash
Opérations disponibles:
  - bulk-create:    Créer plusieurs entrées
  - bulk-update:    Modifier plusieurs entrées
  - bulk-delete:    Supprimer plusieurs entrées
  - bulk-move:      Déplacer plusieurs entrées
  - bulk-enable:    Activer plusieurs comptes
  - bulk-disable:   Désactiver plusieurs comptes
  - bulk-password:  Réinitialiser plusieurs mots de passe
  - bulk-attribute: Modifier un attribut pour plusieurs entrées
```

## 🚀 Import CSV d'Utilisateurs

### Template CSV Basique

```csv
# users-import.csv
uid,cn,sn,givenName,mail,telephoneNumber,title,department
jdoe,John Doe,Doe,John,john.doe@example.com,+33123456789,Developer,IT
jsmith,Jane Smith,Smith,Jane,jane.smith@example.com,+33123456790,Manager,Sales
jbrown,Bob Brown,Brown,Bob,bob.brown@example.com,+33123456791,Analyst,Marketing
mjones,Mary Jones,Jones,Mary,mary.jones@example.com,+33123456792,Director,HR
```

### Import Basique

```bash
# Import simple
ldap-monitor bulk-create users users-import.csv

# Résultat
Importing users from users-import.csv...
Validating CSV file...

✓ CSV structure valid
✓ Found 4 users to import
✓ All required fields present
✓ No duplicate UIDs detected

Progress: [========================================] 4/4

✓ Created: uid=jdoe,ou=users,dc=example,dc=com
✓ Created: uid=jsmith,ou=users,dc=example,dc=com
✓ Created: uid=jbrown,ou=users,dc=example,dc=com
✓ Created: uid=mjones,ou=users,dc=example,dc=com

Summary:
  Total: 4
  Success: 4
  Failed: 0
  Duration: 3.2s

# Import avec dry-run
ldap-monitor bulk-create users users-import.csv --dry-run

# Résultat
Dry-run mode: No changes will be made

Would create 4 users:
  1. uid=jdoe,ou=users,dc=example,dc=com
     - cn: John Doe
     - mail: john.doe@example.com
     - department: IT

  2. uid=jsmith,ou=users,dc=example,dc=com
     - cn: Jane Smith
     - mail: jane.smith@example.com
     - department: Sales

No changes made (dry-run mode)
```

### Import Avancé

```bash
# Import avec backup automatique
ldap-monitor bulk-create users users-import.csv --backup

# Import avec validation stricte
ldap-monitor bulk-create users users-import.csv \
  --validate-emails \
  --check-duplicates \
  --verify-departments

# Import avec génération de mots de passe
ldap-monitor bulk-create users users-import.csv \
  --generate-passwords \
  --send-welcome-emails

# Import avec attributs additionnels
ldap-monitor bulk-create users users-import.csv \
  --base-dn "ou=users,dc=example,dc=com" \
  --object-class inetOrgPerson \
  --object-class posixAccount \
  --default-attribute homeDirectory=/home/{uid} \
  --default-attribute loginShell=/bin/bash

# Import avec transformation
ldap-monitor bulk-create users users-import.csv \
  --transform "mail=lowercase" \
  --transform "uid=lowercase" \
  --transform "department=uppercase"
```

### Template CSV Complet

```csv
# users-complete.csv
uid,cn,sn,givenName,mail,telephoneNumber,mobile,title,department,employeeNumber,employeeType,manager,homeDirectory,loginShell,uidNumber,gidNumber,description,ou
jdoe,John Doe,Doe,John,john.doe@example.com,+33123456789,+33612345678,Senior Developer,IT,EMP001,Regular,cn=manager1,ou=users,dc=example,dc=com,/home/jdoe,/bin/bash,10001,10000,Senior developer in backend team,ou=users,dc=example,dc=com
jsmith,Jane Smith,Smith,Jane,jane.smith@example.com,+33123456790,+33612345679,Sales Manager,Sales,EMP002,Regular,cn=director,ou=users,dc=example,dc=com,/home/jsmith,/bin/bash,10002,10000,Sales team manager,ou=users,dc=example,dc=com

# Import du template complet
ldap-monitor bulk-create users users-complete.csv \
  --all-attributes \
  --backup
```

## 👥 Import CSV de Groupes

### Template CSV Groupes

```csv
# groups-import.csv
cn,description,gidNumber,ou,members
developers,Development team,20001,ou=groups,dc=example,dc=com,"uid=jdoe,ou=users,dc=example,dc=com;uid=jsmith,ou=users,dc=example,dc=com"
managers,Management team,20002,ou=groups,dc=example,dc=com,"uid=boss1,ou=users,dc=example,dc=com;uid=boss2,ou=users,dc=example,dc=com"
admins,System administrators,20003,ou=groups,dc=example,dc=com,"uid=admin1,ou=users,dc=example,dc=com"
```

### Import de Groupes

```bash
# Import basique
ldap-monitor bulk-create groups groups-import.csv

# Résultat
Importing groups from groups-import.csv...
Validating CSV file...

✓ CSV structure valid
✓ Found 3 groups to import
✓ All required fields present

Processing groups...
Progress: [========================================] 3/3

✓ Created: cn=developers,ou=groups,dc=example,dc=com (2 members)
✓ Created: cn=managers,ou=groups,dc=example,dc=com (2 members)
✓ Created: cn=admins,ou=groups,dc=example,dc=com (1 member)

Summary:
  Total: 3
  Success: 3
  Failed: 0
  Total members added: 5

# Import avec vérification des membres
ldap-monitor bulk-create groups groups-import.csv \
  --verify-members \
  --skip-invalid-members

# Import sans membres (ajouter plus tard)
ldap-monitor bulk-create groups groups-import.csv \
  --no-members
```

## ✏️ Modifications en Masse

### Template CSV Modifications

```csv
# users-update.csv
dn,operation,attribute,value
uid=jdoe,ou=users,dc=example,dc=com,replace,title,Lead Developer
uid=jdoe,ou=users,dc=example,dc=com,replace,telephoneNumber,+33123456799
uid=jsmith,ou=users,dc=example,dc=com,replace,department,Marketing
uid=jbrown,ou=users,dc=example,dc=com,add,mobile,+33612345678
uid=mjones,ou=users,dc=example,dc=com,delete,mobile,
```

### Modifications Basiques

```bash
# Appliquer les modifications
ldap-monitor bulk-update users-update.csv

# Résultat
Processing bulk updates from users-update.csv...
Analyzing operations...

Operations to perform:
  - Replace: 3 operations
  - Add: 1 operation
  - Delete: 1 operation

Progress: [========================================] 5/5

✓ Updated: uid=jdoe,ou=users,dc=example,dc=com (2 changes)
✓ Updated: uid=jsmith,ou=users,dc=example,dc=com (1 change)
✓ Updated: uid=jbrown,ou=users,dc=example,dc=com (1 change)
✓ Updated: uid=mjones,ou=users,dc=example,dc=com (1 change)

Summary:
  Total operations: 5
  Success: 5
  Failed: 0
  Entries modified: 4

# Avec dry-run
ldap-monitor bulk-update users-update.csv --dry-run

# Avec backup
ldap-monitor bulk-update users-update.csv --backup
```

### Modification d'un Attribut pour Plusieurs Utilisateurs

```bash
# Template simple pour modification groupée
# set-department.csv
dn
uid=user1,ou=users,dc=example,dc=com
uid=user2,ou=users,dc=example,dc=com
uid=user3,ou=users,dc=example,dc=com

# Appliquer un attribut à tous
ldap-monitor bulk-attribute \
  --file set-department.csv \
  --attribute department \
  --value "IT" \
  --operation replace \
  --backup

# Résultat
Setting attribute 'department' to 'IT' for 3 users...

✓ Updated: uid=user1,ou=users,dc=example,dc=com
✓ Updated: uid=user2,ou=users,dc=example,dc=com
✓ Updated: uid=user3,ou=users,dc=example,dc=com

Summary:
  Total: 3
  Success: 3
  Failed: 0

# Avec filtre LDAP (sans CSV)
ldap-monitor bulk-attribute \
  --filter "(department=OldDept)" \
  --attribute department \
  --value "NewDept" \
  --operation replace \
  --dry-run

# Résultat
Would update 15 users matching filter: (department=OldDept)

Preview:
  uid=user1,ou=users,dc=example,dc=com
  uid=user2,ou=users,dc=example,dc=com
  ...
```

## 🔄 Gestion des Membres de Groupe en Masse

### Template Ajout de Membres

```csv
# add-members.csv
group_dn,member_dn
cn=developers,ou=groups,dc=example,dc=com,uid=jdoe,ou=users,dc=example,dc=com
cn=developers,ou=groups,dc=example,dc=com,uid=jsmith,ou=users,dc=example,dc=com
cn=managers,ou=groups,dc=example,dc=com,uid=jsmith,ou=users,dc=example,dc=com
cn=admins,ou=groups,dc=example,dc=com,uid=jbrown,ou=users,dc=example,dc=com
```

### Ajout de Membres

```bash
# Ajouter des membres
ldap-monitor bulk-add-members add-members.csv

# Résultat
Adding members from add-members.csv...

Processing 4 membership operations...
Progress: [========================================] 4/4

✓ Added to cn=developers: uid=jdoe (1/2)
✓ Added to cn=developers: uid=jsmith (2/2)
✓ Added to cn=managers: uid=jsmith (1/1)
✓ Added to cn=admins: uid=jbrown (1/1)

Summary:
  Total operations: 4
  Success: 4
  Failed: 0
  Groups modified: 3

# Avec vérification
ldap-monitor bulk-add-members add-members.csv \
  --verify-users \
  --skip-existing \
  --backup
```

### Template Suppression de Membres

```csv
# remove-members.csv
group_dn,member_dn
cn=developers,ou=groups,dc=example,dc=com,uid=olddev1,ou=users,dc=example,dc=com
cn=developers,ou=groups,dc=example,dc=com,uid=olddev2,ou=users,dc=example,dc=com
cn=managers,ou=groups,dc=example,dc=com,uid=oldmgr,ou=users,dc=example,dc=com
```

### Suppression de Membres

```bash
# Supprimer des membres
ldap-monitor bulk-remove-members remove-members.csv --backup

# Résultat
Removing members from remove-members.csv...

✓ Removed from cn=developers: uid=olddev1
✓ Removed from cn=developers: uid=olddev2
✓ Removed from cn=managers: uid=oldmgr

Summary:
  Total operations: 3
  Success: 3
  Failed: 0
  Groups modified: 2
```

## 🗑️ Suppressions en Masse

### Template Suppressions

```csv
# users-delete.csv
dn
uid=olduser1,ou=users,dc=example,dc=com
uid=olduser2,ou=users,dc=example,dc=com
uid=tempuser,ou=users,dc=example,dc=com
```

### Suppressions Basiques

```bash
# Dry-run obligatoire pour suppressions
ldap-monitor bulk-delete users users-delete.csv --dry-run

# Résultat
Dry-run mode: No deletions will be performed

Would delete 3 users:

  1. uid=olduser1,ou=users,dc=example,dc=com
     - Member of: 3 groups
     - Last modified: 2024-06-15

  2. uid=olduser2,ou=users,dc=example,dc=com
     - Member of: 5 groups
     - Last modified: 2024-03-20

  3. uid=tempuser,ou=users,dc=example,dc=com
     - Member of: 0 groups
     - Last modified: 2025-01-10

Total group memberships to clean: 8

# Suppression avec confirmation
ldap-monitor bulk-delete users users-delete.csv \
  --confirm \
  --backup

# Résultat
⚠ WARNING: This will delete 3 users permanently!

Creating backup...
✓ Backup created: backups/bulk_delete_20250117_190000.ldif

Deleting users...
Progress: [========================================] 3/3

✓ Deleted: uid=olduser1,ou=users,dc=example,dc=com
  - Removed from 3 groups

✓ Deleted: uid=olduser2,ou=users,dc=example,dc=com
  - Removed from 5 groups

✓ Deleted: uid=tempuser,ou=users,dc=example,dc=com

Summary:
  Total: 3
  Success: 3
  Failed: 0
  Group memberships cleaned: 8
```

## 🔐 Opérations de Sécurité en Masse

### Réinitialisation de Mots de Passe

```csv
# password-reset.csv
dn,new_password
uid=user1,ou=users,dc=example,dc=com,TempPass123!
uid=user2,ou=users,dc=example,dc=com,TempPass456!
uid=user3,ou=users,dc=example,dc=com,TempPass789!
```

```bash
# Réinitialiser les mots de passe
ldap-monitor bulk-password password-reset.csv \
  --must-change \
  --send-emails

# Résultat
Resetting passwords for 3 users...

✓ Password reset: uid=user1 (email sent to user1@example.com)
✓ Password reset: uid=user2 (email sent to user2@example.com)
✓ Password reset: uid=user3 (email sent to user3@example.com)

Summary:
  Total: 3
  Success: 3
  Emails sent: 3

# Générer des mots de passe aléatoires
ldap-monitor bulk-password \
  --file users-list.csv \
  --generate \
  --output generated-passwords.csv \
  --must-change \
  --send-emails
```

### Activation/Désactivation en Masse

```csv
# users-disable.csv
dn,reason
uid=departed1,ou=users,dc=example,dc=com,Employee departure - 2025-01-15
uid=departed2,ou=users,dc=example,dc=com,Contract ended - 2025-01-10
uid=suspended1,ou=users,dc=example,dc=com,Temporary suspension
```

```bash
# Désactiver des comptes
ldap-monitor bulk-disable users-disable.csv --backup

# Résultat
Disabling 3 user accounts...

✓ Disabled: uid=departed1
  Reason: Employee departure - 2025-01-15

✓ Disabled: uid=departed2
  Reason: Contract ended - 2025-01-10

✓ Disabled: uid=suspended1
  Reason: Temporary suspension

Summary:
  Total: 3
  Success: 3
  Failed: 0

# Activer des comptes
ldap-monitor bulk-enable users-enable.csv --backup

# Avec déplacement vers OU spécifique
ldap-monitor bulk-disable users-disable.csv \
  --move-to "ou=disabled,dc=example,dc=com" \
  --backup
```

## 📦 Templates et Modèles

### Créer des Templates Réutilisables

```bash
# Créer un template pour nouveaux développeurs
# templates/new-developer.yaml
type: user
base_dn: ou=users,dc=example,dc=com
object_classes:
  - inetOrgPerson
  - posixAccount
  - organizationalPerson

attributes:
  department: IT
  employeeType: Regular
  homeDirectory: /home/{uid}
  loginShell: /bin/bash
  gidNumber: 10000

required_attributes:
  - uid
  - cn
  - sn
  - givenName
  - mail

groups:
  - cn=developers,ou=groups,dc=example,dc=com
  - cn=all-staff,ou=groups,dc=example,dc=com
  - cn=git-users,ou=groups,dc=example,dc=com

post_create:
  - generate_ssh_key
  - send_welcome_email
  - create_home_directory

# Utiliser le template
ldap-monitor bulk-create-from-template \
  --template templates/new-developer.yaml \
  --data new-developers.csv

# new-developers.csv (champs minimum requis)
uid,cn,sn,givenName,mail
dev1,Dev One,One,Dev,dev1@example.com
dev2,Dev Two,Two,Dev,dev2@example.com
```

### Templates pour Différents Types d'Utilisateurs

```yaml
# templates/contractor.yaml
type: user
base_dn: ou=contractors,dc=example,dc=com
attributes:
  employeeType: Contractor
  accountExpires: +90days  # Expiration automatique
  homeDirectory: /tmp/contractors/{uid}
groups:
  - cn=contractors,ou=groups,dc=example,dc=com

# templates/manager.yaml
type: user
base_dn: ou=users,dc=example,dc=com
attributes:
  employeeType: Manager
  title: Manager
groups:
  - cn=managers,ou=groups,dc=example,dc=com
  - cn=all-staff,ou=groups,dc=example,dc=com
permissions:
  - can_manage_team
  - can_approve_leave

# templates/service-account.yaml
type: user
base_dn: ou=services,dc=example,dc=com
object_classes:
  - account
  - simpleSecurityObject
attributes:
  employeeType: Service
  description: Service account for {service_name}
security:
  password_never_expires: true
  cannot_be_disabled: true
```

## 🔄 Traitement par Lots (Batch Processing)

### Configuration de Batch

```yaml
# batch-config.yaml
batch:
  size: 100              # Traiter 100 entrées à la fois
  parallel: 4            # 4 threads parallèles
  delay: 100             # 100ms entre chaque lot
  retry_on_error: 3      # Réessayer 3 fois en cas d'erreur
  continue_on_error: true # Continuer si erreur sur une entrée

  backoff:
    initial_delay: 1s
    max_delay: 30s
    multiplier: 2

  monitoring:
    progress_bar: true
    log_each_entry: false
    log_errors_only: true

# Exécuter avec config batch
ldap-monitor bulk-create users large-import.csv \
  --batch-config batch-config.yaml
```

### Traitement de Gros Volumes

```bash
# Import de 10,000 utilisateurs
ldap-monitor bulk-create users huge-import.csv \
  --batch-size 500 \
  --parallel 4 \
  --delay 100 \
  --backup

# Résultat
Importing 10,000 users in batches of 500...

Batch 1/20: [========================================] 500/500 (2.3s)
Batch 2/20: [========================================] 500/500 (2.1s)
Batch 3/20: [========================================] 500/500 (2.4s)
...
Batch 20/20: [========================================] 500/500 (2.2s)

Summary:
  Total: 10,000
  Success: 9,987
  Failed: 13
  Duration: 8m 45s
  Average: 19 entries/second

Failed entries saved to: failed-entries.csv

# Réimporter les entrées échouées
ldap-monitor bulk-create users failed-entries.csv \
  --retry \
  --backup
```

### Chunking et Pagination

```bash
# Diviser un gros fichier en chunks
ldap-monitor bulk-split large-import.csv \
  --chunk-size 1000 \
  --output-dir chunks/

# Résultat
Splitting large-import.csv into chunks...

✓ Created: chunks/import-001.csv (1,000 entries)
✓ Created: chunks/import-002.csv (1,000 entries)
✓ Created: chunks/import-003.csv (1,000 entries)
✓ Created: chunks/import-004.csv (876 entries)

Total: 3,876 entries in 4 chunks

# Traiter chunk par chunk
for file in chunks/import-*.csv; do
    echo "Processing $file..."
    ldap-monitor bulk-create users "$file" --backup
    sleep 5
done
```

## 📊 Validation et Vérification

### Validation Avant Import

```bash
# Valider un fichier CSV
ldap-monitor bulk-validate users-import.csv

# Résultat
Validating users-import.csv...

File structure:
  ✓ Valid CSV format
  ✓ Header row present
  ✓ 1,234 data rows

Required fields:
  ✓ uid: present in all rows
  ✓ cn: present in all rows
  ✓ sn: present in all rows
  ✓ mail: present in all rows

Data validation:
  ✓ All UIDs unique
  ✓ All emails valid format
  ⚠ 5 potential email duplicates found
  ✓ No invalid characters

LDAP validation:
  ✓ No existing UIDs conflict
  ⚠ 3 emails already exist in LDAP
  ✓ All managers exist
  ✓ All departments valid

Warnings (8 total):
  1. Row 45: Email duplicate with row 78
  2. Row 123: Email already exists (uid=olduser)
  3. Row 456: Unusual department name "R&D"

Recommendation: Fix warnings before import

# Validation stricte (arrêt si problèmes)
ldap-monitor bulk-validate users-import.csv --strict

# Correction automatique
ldap-monitor bulk-validate users-import.csv \
  --fix-duplicates \
  --output users-import-fixed.csv
```

### Vérification Après Import

```bash
# Vérifier les imports
ldap-monitor bulk-verify import-log.json

# Résultat
Verifying import from import-log.json...

Import information:
  Date: 2025-01-17 19:00:00
  Total entries: 1,234
  Success: 1,230
  Failed: 4

Verification:
  ✓ 1,230 entries exist in LDAP
  ✓ All attributes match import data
  ✓ All group memberships applied
  ✗ 4 entries not found

Missing entries:
  1. uid=user1,ou=users,dc=example,dc=com
     Reason: Import failed - duplicate UID
  2. uid=user2,ou=users,dc=example,dc=com
     Reason: Import failed - invalid email

Recommendation: Review failed entries

# Export des entrées manquantes pour réimport
ldap-monitor bulk-verify import-log.json \
  --export-missing missing-entries.csv
```

## 🤖 Automatisation Avancée

### Pipeline d'Import Automatisé

```bash
#!/bin/bash
# auto-import-pipeline.sh

SOURCE_FILE="/data/hr-export/employees.csv"
WORK_DIR="/tmp/ldap-import-$(date +%Y%m%d)"
LOG_FILE="/var/log/ldap-import.log"

mkdir -p "$WORK_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting import pipeline..."

# 1. Transformer le fichier source
log "Step 1: Transforming data..."
python3 /scripts/transform-hr-data.py \
    "$SOURCE_FILE" \
    "$WORK_DIR/transformed.csv"

# 2. Valider
log "Step 2: Validating..."
ldap-monitor bulk-validate "$WORK_DIR/transformed.csv" \
    --fix-duplicates \
    --output "$WORK_DIR/validated.csv" \
    >> "$LOG_FILE" 2>&1

if [ $? -ne 0 ]; then
    log "ERROR: Validation failed"
    exit 1
fi

# 3. Dry-run
log "Step 3: Dry-run..."
ldap-monitor bulk-create users "$WORK_DIR/validated.csv" \
    --dry-run \
    --output "$WORK_DIR/dry-run-report.txt" \
    >> "$LOG_FILE" 2>&1

# 4. Import réel
log "Step 4: Importing..."
ldap-monitor bulk-create users "$WORK_DIR/validated.csv" \
    --backup \
    --batch-size 100 \
    --output-log "$WORK_DIR/import-log.json" \
    >> "$LOG_FILE" 2>&1

IMPORT_STATUS=$?

# 5. Vérification
log "Step 5: Verifying..."
ldap-monitor bulk-verify "$WORK_DIR/import-log.json" \
    --export-missing "$WORK_DIR/failed-entries.csv" \
    >> "$LOG_FILE" 2>&1

# 6. Rapport
log "Step 6: Generating report..."
ldap-monitor bulk-report "$WORK_DIR/import-log.json" \
    --output "$WORK_DIR/report.html" \
    --format html

# 7. Notification
if [ $IMPORT_STATUS -eq 0 ]; then
    log "Import completed successfully"
    echo "Import successful. See attached report." | \
        mail -s "LDAP Import Success" \
        -a "$WORK_DIR/report.html" \
        admin@example.com
else
    log "ERROR: Import failed"
    echo "Import failed. Check logs: $LOG_FILE" | \
        mail -s "LDAP Import FAILED" admin@example.com
fi

# 8. Cleanup
log "Cleaning up..."
find /tmp/ldap-import-* -mtime +7 -exec rm -rf {} \;

log "Pipeline completed"
```

### Synchronisation Bidirectionnelle

```bash
#!/bin/bash
# bi-directional-sync.sh

# Export depuis LDAP
ldap-monitor export users --output ldap-users.csv

# Export depuis système RH
curl -s https://hr.example.com/api/employees > hr-users.json
python3 convert-hr-to-csv.py hr-users.json > hr-users.csv

# Comparer et générer les différences
ldap-monitor bulk-compare \
    ldap-users.csv \
    hr-users.csv \
    --output-create users-to-create.csv \
    --output-update users-to-update.csv \
    --output-delete users-to-delete.csv

# Appliquer les changements
ldap-monitor bulk-create users users-to-create.csv --backup
ldap-monitor bulk-update users-to-update.csv --backup
ldap-monitor bulk-delete users users-to-delete.csv --backup --confirm

# Mettre à jour le système RH avec les changements LDAP
python3 sync-to-hr.py ldap-users.csv
```

## 📋 Meilleures Pratiques

### 1. Toujours Valider

```bash
# Workflow recommandé
1. ldap-monitor bulk-validate import.csv
2. ldap-monitor bulk-create users import.csv --dry-run
3. Review dry-run output
4. ldap-monitor bulk-create users import.csv --backup
5. ldap-monitor bulk-verify import-log.json
```

### 2. Utiliser des Backups

```bash
# Backup avant toute opération
ldap-monitor bulk-* --backup

# Configuration automatique
config:
  bulk:
    auto_backup: true
    backup_before_delete: true  # Obligatoire pour suppressions
```

### 3. Traiter par Lots

```bash
# Pour gros volumes (> 1000)
ldap-monitor bulk-create users large.csv \
    --batch-size 500 \
    --parallel 4 \
    --delay 100
```

### 4. Gérer les Erreurs

```bash
# Continuer en cas d'erreur
ldap-monitor bulk-create users import.csv \
    --continue-on-error \
    --output-failed failed.csv

# Réimporter les échecs
ldap-monitor bulk-create users failed.csv --retry
```

### 5. Logger et Auditer

```bash
# Logger toutes les opérations
ldap-monitor bulk-create users import.csv \
    --output-log import-log.json \
    --verbose | tee -a /var/log/ldap-bulk.log

# Audit trail
config:
  audit:
    log_bulk_operations: true
    log_file: /var/log/ldap-audit.log
```

## 🔧 Dépannage

### Problèmes Courants

**Erreur: CSV parsing failed**
```bash
# Vérifier l'encodage
file -i import.csv

# Convertir si nécessaire
iconv -f ISO-8859-1 -t UTF-8 import.csv > import-utf8.csv

# Vérifier les délimiteurs
head import.csv
```

**Erreur: Import too slow**
```bash
# Augmenter parallélisme
ldap-monitor bulk-create users import.csv \
    --batch-size 500 \
    --parallel 8

# Optimiser le serveur LDAP
# - Augmenter les limites de connexion
# - Désactiver temporairement certains contrôles
# - Utiliser des connexions persistantes
```

**Erreur: Some entries failed**
```bash
# Export des échecs
ldap-monitor bulk-create users import.csv \
    --continue-on-error \
    --output-failed failed.csv

# Analyser les échecs
ldap-monitor bulk-analyze-failures failed.csv

# Corriger et réimporter
ldap-monitor bulk-create users failed-corrected.csv --retry
```

## 📚 Voir Aussi

- [Gestion des Utilisateurs](User-Management.md)
- [Gestion des Groupes](Group-Management.md)
- [Exports de Données](Data-Exports.md)
- [Sauvegarde et Restauration](Backup-Restore.md)
- [Opérations de Nettoyage](Cleanup-Operations.md)
