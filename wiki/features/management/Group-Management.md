# Gestion des Groupes - Guide Complet

La gestion des groupes LDAP permet de créer, modifier et gérer les groupes ainsi que leurs membres de manière efficace et sécurisée.

## 🎯 Fonctionnalités Principales

- ✅ Création de nouveaux groupes
- ✅ Modification de groupes existants
- ✅ Recherche et consultation de groupes
- ✅ Gestion des membres (ajout/suppression)
- ✅ Gestion des sous-groupes (nested groups)
- ✅ Suppression de groupes
- ✅ Synchronisation de membres
- ✅ Opérations en masse (bulk)
- ✅ Mode dry-run pour tester
- ✅ Sauvegardes automatiques

## 🚀 Commandes de Base

### Rechercher des Groupes

```bash
# Recherche par nom
ldap-monitor group search "developers"

# Résultat
Found 3 groups:
  developers (25 members)
  senior-developers (8 members)
  junior-developers (17 members)

# Recherche avec wildcards
ldap-monitor group search "*admin*"

# Résultat
Found 5 groups:
  admins (3 members)
  system-admins (2 members)
  db-admins (4 members)
  network-admins (3 members)
  admin-assistants (6 members)

# Recherche par description
ldap-monitor group search --attribute description --value "IT department"
```

### Afficher les Détails d'un Groupe

```bash
# Par DN (Distinguished Name)
ldap-monitor group show "cn=developers,ou=groups,dc=example,dc=com"

# Résultat complet
DN: cn=developers,ou=groups,dc=example,dc=com
CN: developers
Description: Équipe de développement
Members: 25

Attributes:
  objectClass: ['groupOfNames', 'top']
  cn: developers
  description: Équipe de développement
  member: [
    uid=jdoe,ou=users,dc=example,dc=com,
    uid=jsmith,ou=users,dc=example,dc=com,
    uid=jbrown,ou=users,dc=example,dc=com,
    ...
  ]
  gidNumber: 10001
  owner: cn=admin,dc=example,dc=com
```

### Lister tous les Groupes

```bash
# Liste complète
ldap-monitor group list

# Résultat
Total groups: 45

admins: 3 members
developers: 25 members
managers: 8 members
hr: 12 members
...

# Avec détails
ldap-monitor group list --detailed

# Export en CSV
ldap-monitor group list --output groups.csv --format csv

# Export en JSON
ldap-monitor group list --output groups.json --format json
```

### Afficher les Membres d'un Groupe

```bash
# Liste des membres
ldap-monitor group members "cn=developers,ou=groups,dc=example,dc=com"

# Résultat
Members (25):
  uid=jdoe,ou=users,dc=example,dc=com
  uid=jsmith,ou=users,dc=example,dc=com
  uid=jbrown,ou=users,dc=example,dc=com
  ...

# Avec détails des utilisateurs
ldap-monitor group members "cn=developers,ou=groups,dc=example,dc=com" --details

# Résultat
Members (25):
  jdoe - John Doe (john.doe@example.com)
  jsmith - John Smith (john.smith@example.com)
  jbrown - John Brown (john.brown@example.com)
  ...

# Export en CSV
ldap-monitor group members "cn=developers,ou=groups,dc=example,dc=com" \
  --output dev-members.csv --format csv
```

## 📁 Création de Groupes

### Création Simple

```bash
# Création basique
ldap-monitor group create \
  --cn "new-team" \
  --description "Nouvelle équipe" \
  --ou "ou=groups,dc=example,dc=com"

# Résultat
✓ Group created: cn=new-team,ou=groups,dc=example,dc=com

# Création avec attributs additionnels
ldap-monitor group create \
  --cn "new-team" \
  --description "Nouvelle équipe" \
  --ou "ou=groups,dc=example,dc=com" \
  --attribute "gidNumber=20001" \
  --attribute "owner=cn=admin,dc=example,dc=com"

# Mode dry-run
ldap-monitor group create \
  --cn "test-group" \
  --description "Groupe de test" \
  --ou "ou=groups,dc=example,dc=com" \
  --dry-run

# Résultat dry-run
✓ Would create group:
  DN: cn=test-group,ou=groups,dc=example,dc=com
  CN: test-group
  Description: Groupe de test
  Members: 0
```

### Création avec Membres Initiaux

```bash
# Créer un groupe avec des membres
ldap-monitor group create \
  --cn "new-team" \
  --description "Nouvelle équipe" \
  --ou "ou=groups,dc=example,dc=com" \
  --member "uid=jdoe,ou=users,dc=example,dc=com" \
  --member "uid=jsmith,ou=users,dc=example,dc=com" \
  --member "uid=jbrown,ou=users,dc=example,dc=com"

# Créer avec membres depuis un fichier
ldap-monitor group create \
  --cn "new-team" \
  --description "Nouvelle équipe" \
  --ou "ou=groups,dc=example,dc=com" \
  --members-file initial-members.txt

# Contenu de initial-members.txt (un DN par ligne)
uid=jdoe,ou=users,dc=example,dc=com
uid=jsmith,ou=users,dc=example,dc=com
uid=jbrown,ou=users,dc=example,dc=com
```

### Création à partir d'un Template

```bash
# Template JSON
ldap-monitor group create --template group-template.json

# group-template.json
{
  "cn": "new-team",
  "description": "Nouvelle équipe de développement",
  "ou": "ou=groups,dc=example,dc=com",
  "gidNumber": 20001,
  "members": [
    "uid=jdoe,ou=users,dc=example,dc=com",
    "uid=jsmith,ou=users,dc=example,dc=com"
  ],
  "owner": "cn=admin,dc=example,dc=com"
}

# Template YAML
ldap-monitor group create --template group-template.yaml

# group-template.yaml
cn: new-team
description: Nouvelle équipe de développement
ou: ou=groups,dc=example,dc=com
gidNumber: 20001
members:
  - uid=jdoe,ou=users,dc=example,dc=com
  - uid=jsmith,ou=users,dc=example,dc=com
owner: cn=admin,dc=example,dc=com
```

## ✏️ Modification de Groupes

### Modifier les Attributs

```bash
# Modifier la description
ldap-monitor group modify "cn=developers,ou=groups,dc=example,dc=com" \
  --set description="Équipe de développement backend"

# Modifier plusieurs attributs
ldap-monitor group modify "cn=developers,ou=groups,dc=example,dc=com" \
  --set description="Équipe de développement backend" \
  --set owner="cn=new-manager,ou=users,dc=example,dc=com"

# Mode dry-run
ldap-monitor group modify "cn=developers,ou=groups,dc=example,dc=com" \
  --set description="Nouvelle description" \
  --dry-run
```

### Renommer un Groupe

```bash
# Renommer le CN
ldap-monitor group rename \
  --old-dn "cn=old-name,ou=groups,dc=example,dc=com" \
  --new-cn "new-name" \
  --backup

# Résultat
✓ Backup created: backups/group_old-name_20250117_150000.ldif
✓ Group renamed: cn=new-name,ou=groups,dc=example,dc=com
✓ Updated references in 3 other groups
```

## 👥 Gestion des Membres

### Ajouter des Membres

```bash
# Ajouter un membre
ldap-monitor group add-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  "uid=jnew,ou=users,dc=example,dc=com"

# Résultat
✓ Added member: uid=jnew,ou=users,dc=example,dc=com
✓ Group now has 26 members

# Ajouter plusieurs membres
ldap-monitor group add-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  "uid=jnew1,ou=users,dc=example,dc=com" \
  "uid=jnew2,ou=users,dc=example,dc=com" \
  "uid=jnew3,ou=users,dc=example,dc=com"

# Résultat
✓ Added 3 members
✓ Group now has 28 members

# Ajouter depuis un fichier
ldap-monitor group add-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file new-members.txt

# Contenu de new-members.txt
uid=jnew1,ou=users,dc=example,dc=com
uid=jnew2,ou=users,dc=example,dc=com
uid=jnew3,ou=users,dc=example,dc=com

# Avec backup automatique
ldap-monitor group add-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file new-members.txt \
  --backup
```

### Supprimer des Membres

```bash
# Supprimer un membre
ldap-monitor group remove-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  "uid=jold,ou=users,dc=example,dc=com"

# Résultat
✓ Removed member: uid=jold,ou=users,dc=example,dc=com
✓ Group now has 27 members

# Supprimer plusieurs membres
ldap-monitor group remove-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  "uid=jold1,ou=users,dc=example,dc=com" \
  "uid=jold2,ou=users,dc=example,dc=com"

# Supprimer depuis un fichier
ldap-monitor group remove-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file members-to-remove.txt \
  --backup

# Dry-run pour tester
ldap-monitor group remove-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file members-to-remove.txt \
  --dry-run
```

### Synchroniser les Membres

```bash
# Synchroniser avec une liste (remplace tous les membres)
ldap-monitor group sync-members \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file desired-members.txt \
  --backup

# Résultat
✓ Backup created: backups/group_developers_20250117_151000.ldif
Analyzing changes...
  - Will add: 5 members
  - Will remove: 3 members
  - Will keep: 20 members

✓ Added 5 new members
✓ Removed 3 old members
✓ Group synchronized (25 members total)

# Dry-run pour voir les changements
ldap-monitor group sync-members \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file desired-members.txt \
  --dry-run

# Résultat
Would make the following changes:
  + uid=new1,ou=users,dc=example,dc=com
  + uid=new2,ou=users,dc=example,dc=com
  - uid=old1,ou=users,dc=example,dc=com
  - uid=old2,ou=users,dc=example,dc=com
  = 23 members unchanged
```

### Vérifier l'Appartenance

```bash
# Vérifier si un utilisateur est membre
ldap-monitor group is-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  "uid=jdoe,ou=users,dc=example,dc=com"

# Résultat
✓ Yes, uid=jdoe is a member of cn=developers

# Lister tous les groupes d'un utilisateur
ldap-monitor group memberships "uid=jdoe,ou=users,dc=example,dc=com"

# Résultat
User uid=jdoe is member of 5 groups:
  cn=developers,ou=groups,dc=example,dc=com
  cn=senior-developers,ou=groups,dc=example,dc=com
  cn=project-alpha,ou=groups,dc=example,dc=com
  cn=all-staff,ou=groups,dc=example,dc=com
  cn=linux-users,ou=groups,dc=example,dc=com
```

## 🔗 Groupes Imbriqués (Nested Groups)

### Créer des Sous-Groupes

```bash
# Ajouter un groupe comme membre d'un autre groupe
ldap-monitor group add-member \
  "cn=all-developers,ou=groups,dc=example,dc=com" \
  "cn=frontend-developers,ou=groups,dc=example,dc=com"

# Résultat
✓ Added group member: cn=frontend-developers,ou=groups,dc=example,dc=com
✓ This is a nested group structure

# Structure:
# all-developers
#   ├── frontend-developers (sous-groupe)
#   │   ├── user1
#   │   └── user2
#   ├── backend-developers (sous-groupe)
#   │   ├── user3
#   │   └── user4
#   └── user5 (membre direct)
```

### Afficher la Hiérarchie

```bash
# Afficher l'arbre des groupes
ldap-monitor group tree "cn=all-developers,ou=groups,dc=example,dc=com"

# Résultat
cn=all-developers (30 total members)
├── cn=frontend-developers (12 members)
│   ├── uid=user1,ou=users,dc=example,dc=com
│   ├── uid=user2,ou=users,dc=example,dc=com
│   └── ...
├── cn=backend-developers (15 members)
│   ├── uid=user3,ou=users,dc=example,dc=com
│   ├── uid=user4,ou=users,dc=example,dc=com
│   └── ...
└── uid=user5,ou=users,dc=example,dc=com (direct member)

# Lister tous les membres récursivement
ldap-monitor group members \
  "cn=all-developers,ou=groups,dc=example,dc=com" \
  --recursive

# Résultat
Direct members: 1
Nested members: 29
Total unique members: 30

All members:
  uid=user1,ou=users,dc=example,dc=com (via frontend-developers)
  uid=user2,ou=users,dc=example,dc=com (via frontend-developers)
  uid=user3,ou=users,dc=example,dc=com (via backend-developers)
  ...
  uid=user5,ou=users,dc=example,dc=com (direct)
```

## 🗑️ Suppression de Groupes

### Supprimer un Groupe

```bash
# Suppression avec confirmation
ldap-monitor group delete "cn=old-group,ou=groups,dc=example,dc=com" \
  --confirm

# Dry-run (voir ce qui sera supprimé)
ldap-monitor group delete "cn=old-group,ou=groups,dc=example,dc=com" \
  --dry-run

# Résultat dry-run
⚠ Would delete:
  Group: cn=old-group,ou=groups,dc=example,dc=com
  Members: 15
  Referenced in: 2 parent groups

Parent groups:
  - cn=all-staff,ou=groups,dc=example,dc=com
  - cn=department-it,ou=groups,dc=example,dc=com

Use --confirm to actually delete

# Supprimer avec backup automatique
ldap-monitor group delete "cn=old-group,ou=groups,dc=example,dc=com" \
  --backup \
  --confirm

# Résultat
✓ Backup created: backups/group_old-group_20250117_152000.ldif
✓ Removed from 2 parent groups
✓ Group deleted successfully

# Supprimer un groupe vide uniquement
ldap-monitor group delete "cn=empty-group,ou=groups,dc=example,dc=com" \
  --only-if-empty \
  --confirm

# Résultat si non vide
✗ Error: Group has 5 members, cannot delete with --only-if-empty
```

### Supprimer Plusieurs Groupes

```bash
# Supprimer depuis un fichier
ldap-monitor group delete --file groups-to-delete.txt --backup --confirm

# Contenu de groups-to-delete.txt
cn=old-group1,ou=groups,dc=example,dc=com
cn=old-group2,ou=groups,dc=example,dc=com
cn=old-group3,ou=groups,dc=example,dc=com

# Résultat
✓ Backup created: backups/bulk_delete_groups_20250117_152500.ldif
Processing 3 groups...
✓ Deleted: cn=old-group1,ou=groups,dc=example,dc=com
✓ Deleted: cn=old-group2,ou=groups,dc=example,dc=com
✓ Deleted: cn=old-group3,ou=groups,dc=example,dc=com

Summary:
  Total: 3
  Success: 3
  Failed: 0
```

## 📊 Opérations en Masse (Bulk)

### Import CSV de Groupes

```bash
# Template CSV pour création de groupes
# groups-import.csv
cn,description,gidNumber,members
team-alpha,Équipe Alpha,20001,"uid=user1,ou=users,dc=example,dc=com;uid=user2,ou=users,dc=example,dc=com"
team-beta,Équipe Beta,20002,"uid=user3,ou=users,dc=example,dc=com;uid=user4,ou=users,dc=example,dc=com"
team-gamma,Équipe Gamma,20003,"uid=user5,ou=users,dc=example,dc=com"

# Import avec dry-run
ldap-monitor group import groups-import.csv --dry-run

# Import réel
ldap-monitor group import groups-import.csv --backup

# Résultat
✓ Backup created: backups/bulk_import_groups_20250117_153000.ldif
Processing 3 groups...
✓ Created: cn=team-alpha,ou=groups,dc=example,dc=com (2 members)
✓ Created: cn=team-beta,ou=groups,dc=example,dc=com (2 members)
✓ Created: cn=team-gamma,ou=groups,dc=example,dc=com (1 member)

Summary:
  Total: 3
  Success: 3
  Failed: 0
  Total members added: 5
```

### Modification en Masse

```bash
# Template CSV pour modifications
# groups-update.csv
dn,attribute,value
cn=team-alpha,ou=groups,dc=example,dc=com,description,Équipe Alpha - Backend
cn=team-beta,ou=groups,dc=example,dc=com,description,Équipe Beta - Frontend
cn=team-gamma,ou=groups,dc=example,dc=com,owner,cn=manager,ou=users,dc=example,dc=com

# Appliquer les modifications
ldap-monitor group bulk-update groups-update.csv --backup

# Résultat
✓ Backup created: backups/bulk_update_groups_20250117_153500.ldif
Processing 3 updates...
✓ Updated: cn=team-alpha,ou=groups,dc=example,dc=com
✓ Updated: cn=team-beta,ou=groups,dc=example,dc=com
✓ Updated: cn=team-gamma,ou=groups,dc=example,dc=com

Summary:
  Total: 3
  Success: 3
  Failed: 0
```

### Ajout de Membres en Masse

```bash
# Template CSV pour ajout de membres
# bulk-add-members.csv
group_dn,member_dn
cn=developers,ou=groups,dc=example,dc=com,uid=new1,ou=users,dc=example,dc=com
cn=developers,ou=groups,dc=example,dc=com,uid=new2,ou=users,dc=example,dc=com
cn=managers,ou=groups,dc=example,dc=com,uid=new3,ou=users,dc=example,dc=com

# Ajouter les membres
ldap-monitor group bulk-add-members bulk-add-members.csv --backup

# Alternative: ajouter plusieurs utilisateurs à un groupe
ldap-monitor group add-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file users-list.txt
```

## 🔐 Fonctionnalités de Sécurité

### Sauvegarde Automatique

Configuration dans `config.yaml`:

```yaml
management:
  groups:
    auto_backup: true              # Backup automatique avant modifications
    backup_retention_days: 30      # Conserver les backups 30 jours
    require_confirmation: true     # Demander confirmation pour suppressions
    allow_delete: false            # Interdire les suppressions (mode sécurisé)
    prevent_empty_groups: true     # Empêcher création de groupes vides
```

### Validation des Opérations

```bash
# Valider avant d'ajouter un membre
ldap-monitor group validate-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  "uid=jnew,ou=users,dc=example,dc=com"

# Vérifications effectuées:
✓ Group exists
✓ User exists
✓ User not already a member
✓ No circular references (for nested groups)
✓ User account is active

# Valider un fichier de membres
ldap-monitor group validate-members \
  "cn=developers,ou=groups,dc=example,dc=com" \
  --file members.txt

# Résultat
Validating 50 members...
✓ 47 valid members
⚠ 2 users already members (will skip)
✗ 1 user does not exist

Details:
  - uid=invalid,ou=users,dc=example,dc=com: User not found
```

### Auditer les Groupes

```bash
# Vérifier l'intégrité des groupes
ldap-monitor audit groups

# Résultat
Checking 45 groups...
✓ 40 groups are healthy
⚠ 5 groups have issues:

Issues found:
  1. cn=old-team,ou=groups,dc=example,dc=com
     - Empty group (0 members)
     - Last modified: 345 days ago

  2. cn=project-x,ou=groups,dc=example,dc=com
     - 3 orphaned members (users deleted but still in group)
     - Member: uid=deleted1,ou=users,dc=example,dc=com (not found)

  3. cn=circular,ou=groups,dc=example,dc=com
     - Circular reference detected
     - This group is member of cn=parent which is member of this group

# Corriger automatiquement
ldap-monitor audit groups --auto-fix --backup
```

## 🤖 Automatisation

### Scripts de Synchronisation

```bash
#!/bin/bash
# sync-groups-from-hr.sh

# Exporter les équipes depuis le système RH
curl -s https://hr.example.com/api/teams > teams.json

# Convertir en CSV pour import
jq -r '.[] | [.team_name, .description, .gid, (.members | join(";"))] | @csv' \
  teams.json > teams-import.csv

# Synchroniser avec LDAP
ldap-monitor group import teams-import.csv \
  --backup \
  --update-existing \
  --log-file /var/log/ldap-group-sync.log

# Envoyer un rapport par email
if [ $? -eq 0 ]; then
  echo "Synchronisation réussie" | mail -s "LDAP Groups Sync Success" admin@example.com
else
  echo "Erreur de synchronisation" | mail -s "LDAP Groups Sync FAILED" admin@example.com
fi
```

### Synchronisation Automatique des Membres

```bash
#!/bin/bash
# auto-sync-group-members.sh

GROUP_DN="cn=developers,ou=groups,dc=example,dc=com"
USERS_FILE="/data/current-developers.txt"

# Synchroniser les membres du groupe avec la liste
ldap-monitor group sync-members "$GROUP_DN" \
  --file "$USERS_FILE" \
  --backup \
  --log-file /var/log/ldap-sync.log

# Résultat
✓ Backup created: backups/group_developers_20250117_154000.ldif
Analyzing changes...
  - Added: 2 new members
  - Removed: 1 former member
  - Unchanged: 24 members

✓ Group synchronized successfully
```

### Nettoyage Automatique

```bash
#!/bin/bash
# cleanup-empty-groups.sh

# Trouver les groupes vides
ldap-monitor group list --filter "memberCount=0" --output empty-groups.txt

# Supprimer avec backup (après 90 jours sans activité)
ldap-monitor cleanup empty-groups \
  --days 90 \
  --backup \
  --confirm

# Envoyer rapport
echo "Nettoyage effectué: $(wc -l < empty-groups.txt) groupes supprimés" \
  | mail -s "LDAP Empty Groups Cleanup" admin@example.com
```

### Cron Jobs

```bash
# Crontab entries

# Synchroniser les groupes depuis le système RH tous les jours à 3h
0 3 * * * /usr/local/bin/sync-groups-from-hr.sh

# Nettoyer les groupes vides tous les lundis à 4h
0 4 * * 1 /usr/local/bin/cleanup-empty-groups.sh

# Auditer les groupes toutes les semaines
0 5 * * 0 /usr/local/bin/audit-groups-weekly.sh

# Backup complet des groupes tous les jours
0 2 * * * ldap-monitor backup groups --output /backups/groups-$(date +\%Y\%m\%d).ldif
```

## 📋 Meilleures Pratiques

### 1. Organisation Hiérarchique

```bash
# Créer une structure claire
ou=groups
├── ou=departments      # Groupes par département
│   ├── cn=dept-it
│   ├── cn=dept-hr
│   └── cn=dept-sales
├── ou=projects         # Groupes par projet
│   ├── cn=project-alpha
│   ├── cn=project-beta
│   └── cn=project-gamma
├── ou=roles           # Groupes par rôle
│   ├── cn=developers
│   ├── cn=managers
│   └── cn=admins
└── ou=locations       # Groupes par localisation
    ├── cn=office-paris
    ├── cn=office-london
    └── cn=office-remote
```

### 2. Conventions de Nommage

```bash
# Utiliser des préfixes cohérents
cn=dept-it              # Départements: dept-*
cn=role-developer       # Rôles: role-*
cn=proj-alpha          # Projets: proj-*
cn=loc-paris           # Localisations: loc-*
cn=team-backend        # Équipes: team-*

# Éviter les caractères spéciaux
cn=my-group            # Bon: tirets
cn=my_group            # Bon: underscores
cn=my.group            # À éviter: points
cn=my group            # À éviter: espaces
```

### 3. Documentation des Groupes

```bash
# Toujours ajouter une description claire
ldap-monitor group create \
  --cn "developers" \
  --description "Équipe de développement - Accès aux repos Git et serveurs de dev"

# Ajouter des métadonnées utiles
ldap-monitor group modify "cn=developers,ou=groups,dc=example,dc=com" \
  --set owner="cn=tech-lead,ou=users,dc=example,dc=com" \
  --set businessCategory="IT Development" \
  --set ou="Engineering Department"
```

### 4. Gestion des Membres

```bash
# Utiliser la synchronisation plutôt que des ajouts/suppressions manuels
ldap-monitor group sync-members [...] --file members.txt --backup

# Auditer régulièrement les membres orphelins
ldap-monitor audit groups --check-orphans --auto-fix

# Documenter les changements
ldap-monitor group add-member [...] | tee -a /var/log/group-changes.log
```

### 5. Sécurité et Backups

```bash
# Toujours utiliser --backup pour les opérations importantes
ldap-monitor group delete [...] --backup --confirm
ldap-monitor group sync-members [...] --backup

# Tester avec dry-run
ldap-monitor group sync-members [...] --dry-run
# Vérifier le résultat
# Puis exécuter sans --dry-run

# Conserver les backups
# Configuration dans config.yaml:
backup:
  backup_dir: /var/backups/ldap
  retention_days: 90
  compress: true
```

## 🔧 Dépannage

### Problèmes Courants

**Erreur: Group already exists**
```bash
# Vérifier si le groupe existe
ldap-monitor group search "group-name"

# Utiliser un autre nom ou supprimer l'ancien
ldap-monitor group delete "cn=group-name,ou=groups,dc=example,dc=com" --backup --confirm
```

**Erreur: Member already exists**
```bash
# Vérifier l'appartenance
ldap-monitor group is-member \
  "cn=developers,ou=groups,dc=example,dc=com" \
  "uid=jdoe,ou=users,dc=example,dc=com"

# Utiliser --skip-existing lors de l'import
ldap-monitor group add-member [...] --skip-existing
```

**Erreur: Circular reference detected**
```bash
# Afficher la hiérarchie pour comprendre le problème
ldap-monitor group tree "cn=problematic-group,ou=groups,dc=example,dc=com"

# Supprimer la référence circulaire
ldap-monitor group remove-member \
  "cn=child-group,ou=groups,dc=example,dc=com" \
  "cn=parent-group,ou=groups,dc=example,dc=com"
```

**Erreur: Cannot delete non-empty group**
```bash
# Supprimer d'abord tous les membres
ldap-monitor group remove-member \
  "cn=group,ou=groups,dc=example,dc=com" \
  --all \
  --backup

# Puis supprimer le groupe
ldap-monitor group delete "cn=group,ou=groups,dc=example,dc=com" --confirm

# Ou forcer la suppression (avec confirmation)
ldap-monitor group delete "cn=group,ou=groups,dc=example,dc=com" \
  --force \
  --backup \
  --confirm
```

## 📚 Voir Aussi

- [Gestion des Utilisateurs](User-Management.md)
- [Opérations de Nettoyage](Cleanup-Operations.md)
- [Sauvegarde et Restauration](Backup-Restore.md)
- [Exports de Données](Data-Exports.md)
- [Opérations en Masse](Bulk-Operations.md)
