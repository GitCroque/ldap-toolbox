# Exports de Données - Guide Complet

Les exports de données LDAP permettent d'extraire des informations pour l'analyse, les rapports, l'intégration avec d'autres systèmes et la documentation.

## 🎯 Objectifs des Exports

- ✅ Rapports et analyses
- ✅ Intégration avec systèmes tiers
- ✅ Documentation et audit
- ✅ Migration de données
- ✅ Synchronisation avec HR/CRM
- ✅ Tableaux de bord (dashboards)
- ✅ Conformité et reporting
- ✅ Data warehousing

## 📋 Formats d'Export Disponibles

### CSV (Comma-Separated Values)

```bash
Avantages:
  ✓ Compatible avec Excel/LibreOffice
  ✓ Facile à lire et éditer
  ✓ Compact
  ✓ Universel

Inconvénients:
  ✗ Perd la structure hiérarchique
  ✗ Problèmes avec caractères spéciaux
  ✗ Attributs multi-valués difficiles

Usage recommandé:
  - Rapports simples
  - Import dans Excel
  - Listes d'utilisateurs/groupes
```

### JSON

```bash
Avantages:
  ✓ Structure préservée
  ✓ Attributs multi-valués
  ✓ Compatible web/API
  ✓ Facile à parser

Inconvénients:
  ✗ Plus verbeux que CSV
  ✗ Moins lisible pour humains

Usage recommandé:
  - Intégration API
  - Applications web
  - Traitement automatisé
  - Data pipelines
```

### YAML

```bash
Avantages:
  ✓ Très lisible
  ✓ Commentaires possibles
  ✓ Structure claire

Inconvénients:
  ✗ Sensible à l'indentation
  ✗ Moins universel

Usage recommandé:
  - Configuration
  - Documentation
  - Révision humaine
```

### Excel (XLSX)

```bash
Avantages:
  ✓ Format natif Excel
  ✓ Feuilles multiples
  ✓ Formatage préservé

Inconvénients:
  ✗ Format propriétaire
  ✗ Plus complexe

Usage recommandé:
  - Rapports business
  - Présentations
  - Analyses Excel
```

## 🚀 Exports d'Utilisateurs

### Export Basique

```bash
# Export CSV simple
ldap-monitor export users --output users.csv

# Résultat
Exporting users...
Found 850 users

Progress: [========================================] 850/850

✓ Export completed: users.csv
  Entries: 850
  Size: 245 KB
  Duration: 2.3s

# Contenu du CSV (aperçu)
dn,uid,cn,sn,givenName,mail,telephoneNumber,title,department
"uid=jdoe,ou=users,dc=example,dc=com",jdoe,"John Doe",Doe,John,john.doe@example.com,+33123456789,Developer,IT
"uid=jsmith,ou=users,dc=example,dc=com",jsmith,"John Smith",Smith,John,john.smith@example.com,+33123456790,Manager,Sales

# Export JSON
ldap-monitor export users --output users.json --format json

# Contenu JSON (aperçu)
[
  {
    "dn": "uid=jdoe,ou=users,dc=example,dc=com",
    "uid": "jdoe",
    "cn": "John Doe",
    "sn": "Doe",
    "givenName": "John",
    "mail": "john.doe@example.com",
    "telephoneNumber": "+33123456789",
    "title": "Developer",
    "department": "IT"
  }
]

# Export YAML
ldap-monitor export users --output users.yaml --format yaml

# Export Excel
ldap-monitor export users --output users.xlsx --format xlsx
```

### Export avec Attributs Spécifiques

```bash
# Sélectionner des attributs spécifiques
ldap-monitor export users \
  --output users-basic.csv \
  --attributes uid,cn,mail

# Contenu
uid,cn,mail
jdoe,"John Doe",john.doe@example.com
jsmith,"John Smith",john.smith@example.com

# Export avec attributs personnalisés
ldap-monitor export users \
  --output users-detailed.csv \
  --attributes uid,cn,mail,telephoneNumber,title,department,manager,employeeNumber

# Export de tous les attributs
ldap-monitor export users \
  --output users-full.csv \
  --all-attributes

# Export avec attributs opérationnels
ldap-monitor export users \
  --output users-with-meta.csv \
  --attributes uid,cn,mail \
  --include-operational \
  --operational-attributes createTimestamp,modifyTimestamp,entryUUID
```

### Export avec Filtres

```bash
# Utilisateurs d'un département
ldap-monitor export users \
  --output it-users.csv \
  --filter "(department=IT)"

# Utilisateurs actifs uniquement
ldap-monitor export users \
  --output active-users.csv \
  --filter "(!(accountStatus=disabled))"

# Utilisateurs avec email
ldap-monitor export users \
  --output users-with-email.csv \
  --filter "(mail=*)"

# Filtres complexes
ldap-monitor export users \
  --output filtered-users.csv \
  --filter "(&(department=IT)(title=*Developer*)(mail=*))"

# Utilisateurs créés récemment
ldap-monitor export users \
  --output new-users.csv \
  --filter "(createTimestamp>=20250101000000Z)"

# Combinaison de filtres
ldap-monitor export users \
  --output complex-filter.csv \
  --filter "(&(|(department=IT)(department=Sales))(!(accountStatus=disabled)))"
```

## 📁 Exports de Groupes

### Export Basique de Groupes

```bash
# Export CSV simple
ldap-monitor export groups --output groups.csv

# Contenu
dn,cn,description,memberCount,members
"cn=developers,ou=groups,dc=example,dc=com",developers,"Development team",25,"uid=jdoe,...;uid=jsmith,..."
"cn=managers,ou=groups,dc=example,dc=com",managers,"Management team",8,"uid=boss1,...;uid=boss2,..."

# Export JSON
ldap-monitor export groups --output groups.json --format json

# Contenu JSON
[
  {
    "dn": "cn=developers,ou=groups,dc=example,dc=com",
    "cn": "developers",
    "description": "Development team",
    "members": [
      "uid=jdoe,ou=users,dc=example,dc=com",
      "uid=jsmith,ou=users,dc=example,dc=com"
    ]
  }
]

# Export avec compte de membres
ldap-monitor export groups \
  --output groups-with-count.csv \
  --include-member-count

# Export sans les membres (plus léger)
ldap-monitor export groups \
  --output groups-no-members.csv \
  --exclude-members
```

### Export Détaillé de Groupes

```bash
# Groupes avec détails des membres
ldap-monitor export groups \
  --output groups-detailed.csv \
  --expand-members

# Contenu (avec informations membres)
group_dn,group_cn,member_uid,member_cn,member_mail,member_title
"cn=developers,ou=groups,dc=example,dc=com",developers,jdoe,"John Doe",john.doe@example.com,Developer
"cn=developers,ou=groups,dc=example,dc=com",developers,jsmith,"John Smith",john.smith@example.com,Developer

# Matrice groupe-utilisateur
ldap-monitor export groups \
  --output group-matrix.csv \
  --format matrix

# Contenu
uid,developers,managers,admins,hr
jdoe,1,0,0,0
jsmith,1,1,0,0
jbrown,0,0,1,0

# Hierarchie des groupes imbriqués
ldap-monitor export groups \
  --output group-hierarchy.json \
  --format json \
  --include-nested \
  --expand-nested
```

## 📊 Exports Spécialisés

### Export d'Appartenances

```bash
# Appartenance aux groupes par utilisateur
ldap-monitor export memberships --output memberships.csv

# Contenu
user_dn,user_uid,user_cn,group_dn,group_cn,membership_type
"uid=jdoe,ou=users,dc=example,dc=com",jdoe,"John Doe","cn=developers,ou=groups,dc=example,dc=com",developers,direct
"uid=jdoe,ou=users,dc=example,dc=com",jdoe,"John Doe","cn=all-staff,ou=groups,dc=example,dc=com",all-staff,nested

# Export avec groupes directs uniquement
ldap-monitor export memberships \
  --output direct-memberships.csv \
  --direct-only

# Export avec groupes imbriqués
ldap-monitor export memberships \
  --output all-memberships.csv \
  --include-nested
```

### Export de Contacts

```bash
# Annuaire de contacts
ldap-monitor export contacts --output contacts.csv

# Contenu
uid,displayName,mail,telephoneNumber,mobile,title,department,manager
jdoe,"John Doe",john.doe@example.com,+33123456789,+33612345678,Developer,IT,"cn=manager,ou=users,dc=example,dc=com"

# Format vCard pour import dans clients email
ldap-monitor export contacts \
  --output contacts.vcf \
  --format vcard

# Contenu vCard
BEGIN:VCARD
VERSION:3.0
FN:John Doe
N:Doe;John;;;
EMAIL:john.doe@example.com
TEL;TYPE=WORK:+33123456789
TEL;TYPE=CELL:+33612345678
TITLE:Developer
ORG:Example Corp;IT
END:VCARD
```

### Export d'Organigramme

```bash
# Hiérarchie organisationnelle
ldap-monitor export org-chart --output org-chart.json --format json

# Contenu JSON
{
  "root": {
    "dn": "cn=ceo,ou=users,dc=example,dc=com",
    "uid": "ceo",
    "cn": "CEO Name",
    "title": "Chief Executive Officer",
    "children": [
      {
        "dn": "cn=cto,ou=users,dc=example,dc=com",
        "uid": "cto",
        "cn": "CTO Name",
        "title": "Chief Technology Officer",
        "children": [
          {
            "dn": "uid=dev1,ou=users,dc=example,dc=com",
            "uid": "dev1",
            "cn": "Developer 1",
            "title": "Senior Developer",
            "children": []
          }
        ]
      }
    ]
  }
}

# Format CSV plat avec niveaux
ldap-monitor export org-chart --output org-chart.csv --format csv

# Contenu
uid,cn,title,department,manager_uid,level,path
ceo,"CEO Name","Chief Executive Officer",Executive,,0,/ceo
cto,"CTO Name","Chief Technology Officer",IT,ceo,1,/ceo/cto
dev1,"Developer 1","Senior Developer",IT,cto,2,/ceo/cto/dev1

# Export pour visualisation (Graphviz DOT)
ldap-monitor export org-chart --output org-chart.dot --format dot

# Générer l'image
dot -Tpng org-chart.dot -o org-chart.png
```

### Export de Statistiques

```bash
# Statistiques par département
ldap-monitor export stats-by-department --output dept-stats.csv

# Contenu
department,user_count,active_count,disabled_count,avg_groups_per_user
IT,125,118,7,4.2
Sales,89,85,4,3.1
HR,34,34,0,2.8
Marketing,67,65,2,3.5

# Statistiques des groupes
ldap-monitor export group-stats --output group-stats.csv

# Contenu
group_cn,member_count,empty,last_modified,days_since_modified
developers,25,no,2025-01-15,2
old-team,0,yes,2024-06-20,211
managers,8,no,2025-01-10,7

# Export pour dashboard
ldap-monitor export dashboard-data \
  --output dashboard.json \
  --format json \
  --include-metrics

# Contenu JSON
{
  "generated": "2025-01-17T18:00:00Z",
  "metrics": {
    "total_users": 850,
    "active_users": 805,
    "disabled_users": 45,
    "total_groups": 156,
    "empty_groups": 5,
    "avg_groups_per_user": 3.4
  },
  "by_department": { ... },
  "by_location": { ... },
  "trends": { ... }
}
```

## 🎨 Formatage et Personnalisation

### Options de Format CSV

```bash
# Délimiteur personnalisé
ldap-monitor export users \
  --output users.csv \
  --csv-delimiter ";" \
  --csv-quote '"'

# Sans en-têtes
ldap-monitor export users \
  --output users.csv \
  --no-header

# Avec BOM UTF-8 (pour Excel Windows)
ldap-monitor export users \
  --output users.csv \
  --utf8-bom

# Encodage spécifique
ldap-monitor export users \
  --output users.csv \
  --encoding "iso-8859-1"

# Format Excel direct (avec mise en forme)
ldap-monitor export users \
  --output users.xlsx \
  --format xlsx \
  --excel-autofit \
  --excel-freeze-header
```

### Options de Format JSON

```bash
# JSON indenté (pretty print)
ldap-monitor export users \
  --output users.json \
  --format json \
  --pretty

# JSON compact (une ligne)
ldap-monitor export users \
  --output users.json \
  --format json \
  --compact

# JSON avec métadonnées
ldap-monitor export users \
  --output users.json \
  --format json \
  --include-metadata

# Contenu avec métadonnées
{
  "metadata": {
    "export_date": "2025-01-17T18:00:00Z",
    "export_type": "users",
    "server": "ldap.example.com",
    "base_dn": "dc=example,dc=com",
    "filter": "(objectClass=inetOrgPerson)",
    "entry_count": 850
  },
  "data": [ ... ]
}

# JSON Lines (un objet par ligne)
ldap-monitor export users \
  --output users.jsonl \
  --format jsonlines
```

### Templates Personnalisés

```bash
# Utiliser un template
ldap-monitor export users \
  --output users.csv \
  --template user-export-template.yaml

# user-export-template.yaml
format: csv
attributes:
  - name: uid
    header: "User ID"
  - name: cn
    header: "Full Name"
  - name: mail
    header: "Email Address"
  - name: telephoneNumber
    header: "Phone"
  - name: department
    header: "Department"
    transform: uppercase
  - name: title
    header: "Job Title"
filter: "(department=IT)"
sort_by: cn
output_options:
  delimiter: ","
  quote: '"'
  include_header: true
  utf8_bom: true

# Template avec transformations
# user-transform-template.yaml
transforms:
  - attribute: mail
    type: lowercase
  - attribute: telephoneNumber
    type: format
    format: "+33 X XX XX XX XX"
  - attribute: createTimestamp
    type: date_format
    format: "%Y-%m-%d"
  - attribute: department
    type: map
    mapping:
      "IT": "Information Technology"
      "HR": "Human Resources"
      "R&D": "Research and Development"
```

## 📦 Exports Groupés et Batch

### Export Multiple

```bash
# Exporter plusieurs datasets
ldap-monitor export all \
  --output-dir /exports/ldap-$(date +%Y%m%d)

# Résultat
Creating exports in /exports/ldap-20250117...

[1/5] Exporting users...
✓ users.csv (850 entries, 245 KB)

[2/5] Exporting groups...
✓ groups.csv (156 entries, 45 KB)

[3/5] Exporting memberships...
✓ memberships.csv (2,890 entries, 178 KB)

[4/5] Exporting contacts...
✓ contacts.csv (850 entries, 189 KB)

[5/5] Exporting statistics...
✓ statistics.json (1 entry, 12 KB)

✓ Export completed
  Total files: 5
  Total size: 669 KB
  Duration: 12.5s

# Export avec formats multiples
ldap-monitor export users \
  --output users \
  --formats csv,json,xlsx

# Résultat
✓ users.csv (850 entries, 245 KB)
✓ users.json (850 entries, 512 KB)
✓ users.xlsx (850 entries, 156 KB)
```

### Export Planifié

```bash
# Configuration pour exports réguliers
# export-config.yaml
exports:
  schedule:
    daily:
      - name: users-export
        type: users
        output: /exports/daily/users-{date}.csv
        format: csv
        filter: "(!(accountStatus=disabled))"

    weekly:
      - name: full-export
        type: all
        output: /exports/weekly/full-{date}
        formats: [csv, json]

    monthly:
      - name: audit-export
        type: users
        output: /exports/monthly/audit-{date}.xlsx
        format: xlsx
        include-metadata: true
        attributes:
          - uid
          - cn
          - mail
          - department
          - createTimestamp
          - modifyTimestamp

# Exécuter selon la configuration
ldap-monitor export scheduled --config export-config.yaml
```

## 🔄 Intégrations

### Export pour Systèmes Tiers

```bash
# Format Salesforce
ldap-monitor export users \
  --output salesforce-import.csv \
  --template templates/salesforce.yaml

# Format Active Directory (import)
ldap-monitor export users \
  --output ad-import.csv \
  --template templates/active-directory.yaml

# Format Google Workspace
ldap-monitor export users \
  --output google-workspace.csv \
  --template templates/google-workspace.yaml

# Contenu template Google Workspace
format: csv
attributes:
  - name: givenName
    header: "First Name [Required]"
  - name: sn
    header: "Last Name [Required]"
  - name: mail
    header: "Email Address [Required]"
  - name: userPassword
    header: "Password [Required]"
    transform: generate_random
  - name: ou
    header: "Org Unit Path [Required]"
    default: "/"
```

### Export API

```bash
# Export pour API REST
ldap-monitor export users \
  --output users-api.json \
  --format json \
  --api-compatible

# Résultat
{
  "users": [ ... ],
  "pagination": {
    "total": 850,
    "page": 1,
    "per_page": 100,
    "total_pages": 9
  }
}

# Export paginé
ldap-monitor export users \
  --output users-page-{page}.json \
  --format json \
  --paginate \
  --page-size 100
```

### Synchronisation avec Base de Données

```bash
# Export pour PostgreSQL
ldap-monitor export users \
  --output users.sql \
  --format sql \
  --table users \
  --database postgresql

# Contenu SQL
CREATE TABLE IF NOT EXISTS users (
  dn VARCHAR(255) PRIMARY KEY,
  uid VARCHAR(100) UNIQUE,
  cn VARCHAR(200),
  mail VARCHAR(200),
  department VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO users (dn, uid, cn, mail, department) VALUES
('uid=jdoe,ou=users,dc=example,dc=com', 'jdoe', 'John Doe', 'john.doe@example.com', 'IT'),
...;

# Export pour MySQL
ldap-monitor export users \
  --output users.sql \
  --format sql \
  --table users \
  --database mysql

# Export pour MongoDB
ldap-monitor export users \
  --output users.json \
  --format mongodb

# Import direct dans MongoDB
mongoimport --db mydb --collection users --file users.json --jsonArray
```

## 📊 Rapports et Analyses

### Rapports Prédéfinis

```bash
# Rapport d'audit complet
ldap-monitor export report-audit --output audit-report.xlsx

# Contenu (plusieurs feuilles)
Feuille 1 - Summary:
  Total Users: 850
  Active: 805
  Disabled: 45
  Total Groups: 156
  ...

Feuille 2 - Users by Department:
  IT: 125 users
  Sales: 89 users
  ...

Feuille 3 - Inactive Users:
  uid, cn, last_login, days_inactive
  ...

# Rapport de conformité
ldap-monitor export report-compliance --output compliance.xlsx

# Rapport d'activité
ldap-monitor export report-activity \
  --output activity-report.xlsx \
  --period last-30-days
```

### Analyses Personnalisées

```bash
# Utilisateurs sans email
ldap-monitor export users \
  --output no-email.csv \
  --filter "(!(mail=*))" \
  --attributes uid,cn,department

# Groupes avec plus de N membres
ldap-monitor export groups \
  --output large-groups.csv \
  --filter-expression "memberCount > 50"

# Utilisateurs créés récemment
ldap-monitor export users \
  --output new-users.csv \
  --filter "(createTimestamp>=20250101000000Z)" \
  --attributes uid,cn,mail,createTimestamp,department

# Distribution par département
ldap-monitor export analyze department-distribution \
  --output dept-distribution.csv

# Contenu
department,count,percentage
IT,125,14.7%
Sales,89,10.5%
HR,34,4.0%
...
```

## 🤖 Automatisation

### Scripts d'Export Automatique

```bash
#!/bin/bash
# auto-export.sh

EXPORT_DIR="/exports/ldap/$(date +%Y%m%d)"
mkdir -p "$EXPORT_DIR"

# Export quotidien des utilisateurs actifs
ldap-monitor export users \
    --output "$EXPORT_DIR/active-users.csv" \
    --filter "(!(accountStatus=disabled))"

# Export des groupes
ldap-monitor export groups \
    --output "$EXPORT_DIR/groups.csv"

# Export des statistiques
ldap-monitor export stats \
    --output "$EXPORT_DIR/statistics.json" \
    --format json

# Compresser
tar -czf "$EXPORT_DIR.tar.gz" "$EXPORT_DIR"

# Upload vers S3
aws s3 cp "$EXPORT_DIR.tar.gz" s3://my-ldap-exports/

# Nettoyer les exports > 30 jours
find /exports/ldap -type f -mtime +30 -delete

# Notification
echo "Export completed: $EXPORT_DIR" | \
    mail -s "LDAP Daily Export Success" admin@example.com
```

### Cron Jobs

```bash
# Crontab entries

# Export quotidien à 1h
0 1 * * * /usr/local/bin/auto-export.sh

# Export hebdomadaire complet (dimanche 3h)
0 3 * * 0 ldap-monitor export all --output-dir /exports/weekly/$(date +\%Y\%m\%d)

# Rapport mensuel (1er du mois à 8h)
0 8 1 * * ldap-monitor export report-audit --output /reports/monthly/$(date +\%Y\%m).xlsx

# Synchronisation avec HR system (tous les jours à 6h)
0 6 * * * /usr/local/bin/sync-to-hr.sh
```

### Monitoring des Exports

```bash
#!/bin/bash
# monitor-exports.sh

LAST_EXPORT=$(ls -t /exports/ldap/*.tar.gz | head -1)
LAST_EXPORT_DATE=$(stat -c %Y "$LAST_EXPORT")
NOW=$(date +%s)
HOURS_AGO=$(( ($NOW - $LAST_EXPORT_DATE) / 3600 ))

if [ $HOURS_AGO -gt 26 ]; then
    echo "WARNING: Last export is $HOURS_AGO hours old" | \
        mail -s "LDAP Export Alert: Overdue" admin@example.com
fi

# Vérifier la taille
SIZE=$(du -sh /exports/ldap/$(date +%Y%m%d) | cut -f1)
echo "Today's export size: $SIZE" | \
    mail -s "LDAP Export Status" admin@example.com
```

## 📋 Meilleures Pratiques

### 1. Sécurité des Exports

```bash
# Chiffrer les exports sensibles
ldap-monitor export users \
    --output users.csv \
    --encrypt \
    --password-file /secure/export-key.txt

# Permissions strictes
chmod 600 /exports/ldap/*.csv
chown ldap-export:ldap-export /exports/ldap/

# Pas de mots de passe dans les exports
export_config:
  exclude_attributes:
    - userPassword
    - sambaNTPassword
    - sambaLMPassword
```

### 2. Performance

```bash
# Utiliser des filtres pour limiter les données
ldap-monitor export users \
    --filter "(department=IT)" \
    --attributes uid,cn,mail

# Paginer les gros exports
ldap-monitor export users \
    --output users-{page}.csv \
    --paginate \
    --page-size 1000

# Compression pour gros volumes
ldap-monitor export users --output users.csv --compress
```

### 3. Documentation

```bash
# Inclure les métadonnées
ldap-monitor export users \
    --output users.json \
    --include-metadata

# README automatique
ldap-monitor export all \
    --output-dir /exports/full \
    --generate-readme

# Contenu README.md
# LDAP Export - 2025-01-17

## Files
- users.csv: 850 users
- groups.csv: 156 groups
- memberships.csv: 2,890 memberships

## Generated
Date: 2025-01-17 18:00:00
Server: ldap.example.com
Base DN: dc=example,dc=com
```

### 4. Validation

```bash
# Valider avant export
ldap-monitor export users \
    --validate \
    --output users.csv

# Vérifier après export
ldap-monitor export verify users.csv

# Test d'intégrité
wc -l users.csv  # Compter les lignes
file users.csv   # Vérifier le type
head users.csv   # Aperçu
```

## 🔧 Dépannage

### Problèmes Courants

**Erreur: Special characters in CSV**
```bash
# Utiliser l'encodage UTF-8 avec BOM
ldap-monitor export users --output users.csv --utf8-bom

# Ou changer l'encodage
ldap-monitor export users --output users.csv --encoding iso-8859-1
```

**Erreur: File too large**
```bash
# Paginer l'export
ldap-monitor export users --output users-{page}.csv --paginate --page-size 1000

# Ou compresser
ldap-monitor export users --output users.csv --compress
```

**Erreur: Timeout**
```bash
# Augmenter le timeout
ldap-monitor export users --output users.csv --timeout 300

# Ou exporter par lots
ldap-monitor export users --filter "(department=IT)" --output it-users.csv
ldap-monitor export users --filter "(department=Sales)" --output sales-users.csv
```

## 📚 Voir Aussi

- [Gestion des Utilisateurs](User-Management.md)
- [Gestion des Groupes](Group-Management.md)
- [Sauvegarde et Restauration](Backup-Restore.md)
- [Opérations en Masse](Bulk-Operations.md)
