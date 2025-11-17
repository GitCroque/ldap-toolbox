# Gestion des Utilisateurs - Guide Complet

La gestion des utilisateurs LDAP permet de créer, modifier, désactiver et supprimer des comptes utilisateurs de manière sécurisée et efficace.

## 🎯 Fonctionnalités Principales

- ✅ Création de nouveaux utilisateurs
- ✅ Modification d'utilisateurs existants
- ✅ Recherche et consultation d'utilisateurs
- ✅ Désactivation/réactivation de comptes
- ✅ Suppression de comptes
- ✅ Réinitialisation de mots de passe
- ✅ Gestion des attributs utilisateurs
- ✅ Opérations en masse (bulk)
- ✅ Mode dry-run pour tester
- ✅ Sauvegardes automatiques

## 🚀 Commandes de Base

### Rechercher des Utilisateurs

```bash
# Recherche par nom, uid ou email
ldap-monitor user search "john"

# Résultat
Found 3 users:
  jdoe (John Doe) - john.doe@example.com
  jsmith (John Smith) - john.smith@example.com
  jbrown (John Brown) - john.brown@example.com

# Recherche avec wildcards
ldap-monitor user search "*admin*"

# Recherche par attribut spécifique
ldap-monitor user search --attribute mail --value "*@example.com"
```

### Afficher les Détails d'un Utilisateur

```bash
# Par DN (Distinguished Name)
ldap-monitor user show "uid=jdoe,ou=users,dc=example,dc=com"

# Résultat complet
DN: uid=jdoe,ou=users,dc=example,dc=com
UID: jdoe
CN: John Doe
Email: john.doe@example.com

All attributes:
  objectClass: ['inetOrgPerson', 'posixAccount']
  uid: jdoe
  cn: John Doe
  sn: Doe
  givenName: John
  mail: john.doe@example.com
  telephoneNumber: +33 1 23 45 67 89
  title: Développeur Senior
  department: IT
  employeeNumber: 12345
  homeDirectory: /home/jdoe
  loginShell: /bin/bash
  uidNumber: 10001
  gidNumber: 10000
```

### Lister tous les Utilisateurs

```bash
# Liste complète
ldap-monitor user list

# Limiter le nombre de résultats
ldap-monitor user list --limit 10

# Avec filtres
ldap-monitor user list --filter "department=IT"

# Export en CSV
ldap-monitor user list --output users.csv --format csv

# Export en JSON
ldap-monitor user list --output users.json --format json
```

## 👤 Création d'Utilisateurs

### Création Interactive

```bash
# Mode interactif (pose des questions)
ldap-monitor user create --interactive

# Questions posées:
# - UID (identifiant)
# - Nom complet (cn)
# - Prénom (givenName)
# - Nom de famille (sn)
# - Email
# - Mot de passe
# - Groupe principal
# - etc.
```

### Création avec Paramètres

```bash
# Création simple
ldap-monitor user create \
  --uid "jnew" \
  --cn "Jane New" \
  --sn "New" \
  --givenName "Jane" \
  --mail "jane.new@example.com" \
  --password "TempPass123!" \
  --ou "ou=users,dc=example,dc=com"

# Création avec attributs additionnels
ldap-monitor user create \
  --uid "jnew" \
  --cn "Jane New" \
  --sn "New" \
  --givenName "Jane" \
  --mail "jane.new@example.com" \
  --password "TempPass123!" \
  --ou "ou=users,dc=example,dc=com" \
  --attribute "telephoneNumber=+33 1 23 45 67 89" \
  --attribute "title=Développeuse" \
  --attribute "department=IT" \
  --attribute "employeeNumber=12346"

# Mode dry-run (test sans créer)
ldap-monitor user create \
  --uid "jtest" \
  --cn "Test User" \
  --sn "User" \
  --givenName "Test" \
  --mail "test@example.com" \
  --dry-run

# Résultat dry-run
✓ Would create user:
  DN: uid=jtest,ou=users,dc=example,dc=com
  UID: jtest
  CN: Test User
  Mail: test@example.com
  Attributes: 8 total
```

### Création à partir d'un Template

```bash
# Utiliser un template JSON
ldap-monitor user create --template user-template.json

# Template: user-template.json
{
  "uid": "jnew",
  "cn": "Jane New",
  "sn": "New",
  "givenName": "Jane",
  "mail": "jane.new@example.com",
  "telephoneNumber": "+33 1 23 45 67 89",
  "title": "Développeuse",
  "department": "IT",
  "employeeNumber": "12346",
  "homeDirectory": "/home/jnew",
  "loginShell": "/bin/bash",
  "uidNumber": 10002,
  "gidNumber": 10000
}

# Template YAML
ldap-monitor user create --template user-template.yaml

# Template: user-template.yaml
uid: jnew
cn: Jane New
sn: New
givenName: Jane
mail: jane.new@example.com
telephoneNumber: "+33 1 23 45 67 89"
title: Développeuse
department: IT
employeeNumber: "12346"
homeDirectory: /home/jnew
loginShell: /bin/bash
uidNumber: 10002
gidNumber: 10000
```

## ✏️ Modification d'Utilisateurs

### Modifier un Attribut

```bash
# Modifier un attribut simple
ldap-monitor user modify "uid=jdoe,ou=users,dc=example,dc=com" \
  --set mail="new.email@example.com"

# Modifier plusieurs attributs
ldap-monitor user modify "uid=jdoe,ou=users,dc=example,dc=com" \
  --set mail="new.email@example.com" \
  --set telephoneNumber="+33 9 87 65 43 21" \
  --set title="Architecte Senior"

# Ajouter un attribut multi-valué
ldap-monitor user modify "uid=jdoe,ou=users,dc=example,dc=com" \
  --add mobile="+33 6 12 34 56 78"

# Supprimer un attribut
ldap-monitor user modify "uid=jdoe,ou=users,dc=example,dc=com" \
  --delete mobile

# Mode dry-run
ldap-monitor user modify "uid=jdoe,ou=users,dc=example,dc=com" \
  --set mail="new.email@example.com" \
  --dry-run
```

### Modifier avec Sauvegarde Automatique

```bash
# Avec backup avant modification
ldap-monitor user modify "uid=jdoe,ou=users,dc=example,dc=com" \
  --set mail="new.email@example.com" \
  --backup

# Le backup est créé automatiquement
✓ Backup created: backups/user_jdoe_20250117_143022.ldif
✓ User modified successfully

# Restaurer si nécessaire
ldap-monitor backup restore backups/user_jdoe_20250117_143022.ldif
```

### Renommer un Utilisateur

```bash
# Changer le UID (avec déplacement)
ldap-monitor user rename \
  --old-dn "uid=jdoe,ou=users,dc=example,dc=com" \
  --new-uid "john.doe" \
  --backup

# Résultat
✓ Backup created: backups/user_jdoe_20250117_143500.ldif
✓ User renamed: uid=john.doe,ou=users,dc=example,dc=com
✓ Updated 3 group memberships
```

## 🔒 Gestion des Mots de Passe

### Réinitialiser un Mot de Passe

```bash
# Réinitialisation interactive (demande le nouveau mot de passe)
ldap-monitor user reset-password "uid=jdoe,ou=users,dc=example,dc=com"

# Avec mot de passe fourni
ldap-monitor user reset-password "uid=jdoe,ou=users,dc=example,dc=com" \
  --password "NewSecurePass123!"

# Générer un mot de passe aléatoire
ldap-monitor user reset-password "uid=jdoe,ou=users,dc=example,dc=com" \
  --generate

# Résultat
✓ Password reset successfully
✓ Generated password: xK9$mP2#vL7@wR4
⚠ Please save this password securely and provide it to the user

# Forcer le changement au prochain login
ldap-monitor user reset-password "uid=jdoe,ou=users,dc=example,dc=com" \
  --generate \
  --must-change

# Envoyer par email (si configuré)
ldap-monitor user reset-password "uid=jdoe,ou=users,dc=example,dc=com" \
  --generate \
  --send-email
```

### Vérifier la Politique de Mots de Passe

```bash
# Tester si un mot de passe est conforme
ldap-monitor user validate-password --password "MyPassword123!"

# Résultat
✓ Password meets requirements:
  - Length: 16 (min: 8)
  - Uppercase: Yes
  - Lowercase: Yes
  - Numbers: Yes
  - Special chars: Yes
  - Not in common list: Yes

# Afficher les exigences
ldap-monitor user password-policy

# Résultat
Password Policy:
  Minimum length: 8 characters
  Maximum length: 128 characters
  Required character types: 3 of 4
    - Uppercase letters (A-Z)
    - Lowercase letters (a-z)
    - Numbers (0-9)
    - Special characters (!@#$%^&*)
  Password expiry: 90 days
  History: Last 5 passwords
  Max attempts: 5
```

## 🚫 Désactivation et Suppression

### Désactiver un Utilisateur

```bash
# Désactiver un compte (conserve les données)
ldap-monitor user disable "uid=jdoe,ou=users,dc=example,dc=com"

# Avec raison
ldap-monitor user disable "uid=jdoe,ou=users,dc=example,dc=com" \
  --reason "Départ de l'entreprise - 2025-01-17"

# Désactiver avec déplacement vers OU spéciale
ldap-monitor user disable "uid=jdoe,ou=users,dc=example,dc=com" \
  --move-to "ou=disabled,dc=example,dc=com"

# Désactiver plusieurs utilisateurs
ldap-monitor user disable \
  --file disabled-users.txt \
  --backup

# Contenu de disabled-users.txt (un DN par ligne)
uid=user1,ou=users,dc=example,dc=com
uid=user2,ou=users,dc=example,dc=com
uid=user3,ou=users,dc=example,dc=com
```

### Réactiver un Utilisateur

```bash
# Réactiver un compte
ldap-monitor user enable "uid=jdoe,ou=disabled,dc=example,dc=com"

# Réactiver et déplacer vers OU active
ldap-monitor user enable "uid=jdoe,ou=disabled,dc=example,dc=com" \
  --move-to "ou=users,dc=example,dc=com"

# Réactiver avec réinitialisation du mot de passe
ldap-monitor user enable "uid=jdoe,ou=disabled,dc=example,dc=com" \
  --reset-password \
  --generate
```

### Supprimer un Utilisateur

```bash
# Supprimer avec confirmation
ldap-monitor user delete "uid=jdoe,ou=users,dc=example,dc=com" \
  --confirm

# Dry-run (voir ce qui sera supprimé)
ldap-monitor user delete "uid=jdoe,ou=users,dc=example,dc=com" \
  --dry-run

# Résultat dry-run
⚠ Would delete:
  User: uid=jdoe,ou=users,dc=example,dc=com
  Group memberships: 5
  Files: /home/jdoe (if configured)

Use --confirm to actually delete

# Supprimer avec backup automatique
ldap-monitor user delete "uid=jdoe,ou=users,dc=example,dc=com" \
  --backup \
  --confirm

# Résultat
✓ Backup created: backups/user_jdoe_20250117_144500.ldif
✓ Removed from 5 groups
✓ User deleted successfully

# Supprimer plusieurs utilisateurs
ldap-monitor user delete --file users-to-delete.txt --backup --confirm
```

## 📊 Opérations en Masse (Bulk)

### Import CSV

```bash
# Template CSV pour création d'utilisateurs
# users-import.csv
uid,cn,sn,givenName,mail,telephoneNumber,title,department
jnew1,Jane New1,New1,Jane,jane.new1@example.com,+33123456789,Développeuse,IT
jnew2,Jane New2,New2,Jane,jane.new2@example.com,+33123456790,Analyste,IT
jnew3,Jane New3,New3,Jane,jane.new3@example.com,+33123456791,Chef de projet,Marketing

# Import avec dry-run
ldap-monitor user import users-import.csv --dry-run

# Import réel
ldap-monitor user import users-import.csv --backup

# Résultat
✓ Backup created: backups/bulk_import_20250117_145000.ldif
Processing 3 users...
✓ Created: uid=jnew1,ou=users,dc=example,dc=com
✓ Created: uid=jnew2,ou=users,dc=example,dc=com
✓ Created: uid=jnew3,ou=users,dc=example,dc=com

Summary:
  Total: 3
  Success: 3
  Failed: 0
  Duration: 2.3s
```

### Modification en Masse

```bash
# Template CSV pour modifications
# users-update.csv
dn,attribute,value
uid=jdoe,ou=users,dc=example,dc=com,title,Architecte Senior
uid=jsmith,ou=users,dc=example,dc=com,title,Lead Développeur
uid=jbrown,ou=users,dc=example,dc=com,department,DevOps

# Appliquer les modifications
ldap-monitor user bulk-update users-update.csv --backup

# Modifier un attribut pour tous les utilisateurs d'un département
ldap-monitor user bulk-modify \
  --filter "department=IT" \
  --set "manager=cn=John Manager,ou=users,dc=example,dc=com" \
  --backup \
  --dry-run
```

## 🔐 Fonctionnalités de Sécurité

### Sauvegarde Automatique

Configuration dans `config.yaml`:

```yaml
management:
  users:
    auto_backup: true              # Backup automatique avant modifications
    backup_retention_days: 30      # Conserver les backups 30 jours
    require_confirmation: true     # Demander confirmation pour suppressions
    allow_delete: false            # Interdire les suppressions (mode sécurisé)
```

### Mode Dry-Run

```bash
# Toutes les commandes supportent --dry-run
ldap-monitor user create [...] --dry-run
ldap-monitor user modify [...] --dry-run
ldap-monitor user delete [...] --dry-run
ldap-monitor user import [...] --dry-run

# Le mode dry-run:
# - N'effectue AUCUNE modification
# - Affiche ce qui serait fait
# - Valide les paramètres
# - Teste la connectivité LDAP
```

### Validation et Vérifications

```bash
# Valider avant création
ldap-monitor user validate --template user.json

# Vérifications effectuées:
✓ UID unique
✓ Email unique
✓ Attributs requis présents
✓ Format email valide
✓ Longueur des champs
✓ Caractères autorisés
✓ OU de destination existe
✓ Groupe principal existe

# Vérifier les doublons avant import
ldap-monitor user check-duplicates users-import.csv

# Résultat
⚠ Found 2 potential duplicates:
  - jdoe: Email already exists (john.doe@example.com)
  - jsmith: UID already exists
```

## 🤖 Automatisation

### Scripts de Création Automatique

```bash
#!/bin/bash
# create-user-automated.sh

# Fonction de création avec tous les paramètres
create_user() {
  local uid=$1
  local firstname=$2
  local lastname=$3
  local email=$4
  local department=$5

  ldap-monitor user create \
    --uid "$uid" \
    --cn "$firstname $lastname" \
    --sn "$lastname" \
    --givenName "$firstname" \
    --mail "$email" \
    --attribute "department=$department" \
    --attribute "employeeType=Regular" \
    --attribute "homeDirectory=/home/$uid" \
    --generate-password \
    --must-change \
    --send-email \
    --backup
}

# Créer plusieurs utilisateurs
create_user "jnew1" "Jane" "New1" "jane.new1@example.com" "IT"
create_user "jnew2" "Jane" "New2" "jane.new2@example.com" "Marketing"
create_user "jnew3" "Jane" "New3" "jane.new3@example.com" "Sales"
```

### Intégration avec HR System

```bash
#!/bin/bash
# sync-from-hr.sh

# Exporter depuis le système RH (exemple)
curl -s https://hr.example.com/api/new-employees > new-employees.json

# Convertir en CSV
jq -r '.[] | [.username, .first_name, .last_name, .email, .department] | @csv' \
  new-employees.json > new-users.csv

# Import dans LDAP
ldap-monitor user import new-users.csv \
  --backup \
  --send-welcome-email \
  --log-file /var/log/ldap-sync.log
```

### Tâche Cron pour Nettoyage

```bash
# Crontab entry
# Désactiver les comptes inactifs tous les lundis à 2h
0 2 * * 1 /usr/local/bin/disable-inactive-users.sh

# disable-inactive-users.sh
#!/bin/bash

# Trouver les utilisateurs inactifs (> 90 jours)
ldap-monitor audit users --inactive --days 90 --output inactive.json --format json

# Extraire les DNs
jq -r '.[] | .dn' inactive.json > inactive-dns.txt

# Désactiver avec backup
ldap-monitor user disable --file inactive-dns.txt --backup \
  --reason "Inactif depuis plus de 90 jours - $(date +%Y-%m-%d)"

# Envoyer rapport
mail -s "Comptes inactifs désactivés" admin@example.com < inactive-dns.txt
```

## 📋 Meilleures Pratiques

### 1. Toujours Sauvegarder

```bash
# Utiliser --backup pour toutes les opérations importantes
ldap-monitor user modify [...] --backup
ldap-monitor user delete [...] --backup
ldap-monitor user import [...] --backup
```

### 2. Tester avec Dry-Run

```bash
# Toujours tester avant de modifier en production
ldap-monitor user modify [...] --dry-run
# Vérifier le résultat
# Puis exécuter sans --dry-run
ldap-monitor user modify [...]
```

### 3. Utiliser des Templates

```bash
# Créer des templates réutilisables
templates/
  ├── developer.json
  ├── manager.json
  ├── contractor.json
  └── service-account.json

# Utiliser les templates
ldap-monitor user create --template templates/developer.json \
  --override uid=newdev \
  --override mail=newdev@example.com
```

### 4. Documenter les Changements

```bash
# Ajouter des commentaires/raisons
ldap-monitor user disable [...] --reason "Départ - 2025-01-17"
ldap-monitor user modify [...] --comment "Promotion - nouveau titre"

# Tenir un journal des modifications
ldap-monitor user modify [...] | tee -a /var/log/ldap-changes.log
```

### 5. Valider les Entrées

```bash
# Valider les fichiers avant import
ldap-monitor user validate-csv users-import.csv

# Vérifier les doublons
ldap-monitor user check-duplicates users-import.csv

# Tester la syntaxe
ldap-monitor user validate --template user.json
```

### 6. Sécuriser les Mots de Passe

```bash
# Ne jamais mettre de mots de passe en clair dans les commandes
# Mauvais:
ldap-monitor user create --password "secret123"

# Bon:
ldap-monitor user create --generate-password
# ou
ldap-monitor user create --password-stdin < password.txt
# ou
export LDAP_USER_PASSWORD="secret123"
ldap-monitor user create --password-env LDAP_USER_PASSWORD
```

## 🔧 Dépannage

### Problèmes Courants

**Erreur: UID already exists**
```bash
# Vérifier si l'utilisateur existe
ldap-monitor user search "uid=jdoe"

# Utiliser un autre UID ou supprimer l'ancien
ldap-monitor user delete "uid=jdoe,ou=users,dc=example,dc=com" --backup --confirm
```

**Erreur: Email already in use**
```bash
# Trouver qui utilise l'email
ldap-monitor user search --attribute mail --value "john@example.com"

# Modifier l'email existant ou utiliser un autre
ldap-monitor user modify "uid=olduser,ou=users,dc=example,dc=com" \
  --set mail="old.email@example.com"
```

**Erreur: Permission denied**
```bash
# Vérifier les permissions dans config.yaml
management:
  allow_create: true
  allow_modify: true
  allow_delete: true  # Doit être true

# Vérifier les droits LDAP de l'utilisateur bind
ldap-monitor test connection --verbose
```

## 📚 Voir Aussi

- [Gestion des Groupes](Group-Management.md)
- [Opérations de Nettoyage](Cleanup-Operations.md)
- [Sauvegarde et Restauration](Backup-Restore.md)
- [Exports de Données](Data-Exports.md)
- [Opérations en Masse](Bulk-Operations.md)
