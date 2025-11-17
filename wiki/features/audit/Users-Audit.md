# Audit des Utilisateurs - Guide Complet

L'audit des utilisateurs permet de détecter automatiquement les problèmes et incohérences dans vos comptes LDAP.

## 🎯 Objectifs de l'Audit Users

L'audit utilisateurs vérifie :
- ✅ Comptes désactivés ou expirés
- ✅ Comptes inactifs (sans connexion récente)
- ✅ Attributs manquants ou invalides
- ✅ Doublons (email, uid, etc.)
- ✅ Comptes orphelins (pas dans les groupes attendus)
- ✅ Incohérences de données
- ✅ Problèmes de mots de passe
- ✅ Comptes de service mal configurés

## 🚀 Utilisation de Base

### Audit Complet

```bash
# Audit complet de tous les utilisateurs
ldap-monitor audit users

# Avec output en JSON
ldap-monitor audit users --format json --output users-audit.json

# Avec output en HTML
ldap-monitor audit users --format html --output users-audit.html
```

### Audit Ciblé

```bash
# Vérifier uniquement les comptes inactifs
ldap-monitor audit users --inactive

# Vérifier uniquement les attributs manquants
ldap-monitor audit users --missing-attributes

# Combiner plusieurs checks
ldap-monitor audit users --inactive --missing-attributes
```

## 🔍 Types de Vérifications

### 1. Comptes Désactivés

**Ce qui est détecté :**
- Comptes avec flag `userAccountControl` désactivé (AD)
- Attribut `accountStatus: disabled`
- Comptes avec dates d'expiration passées

**Exemple de résultat :**
```
⚠️  5 disabled user accounts
  Found 5 disabled user accounts
  💡 Review and clean up disabled accounts

  Affected users:
  - uid=jdoe,ou=users,dc=example,dc=com
  - uid=asmith,ou=users,dc=example,dc=com
  ...
```

**Configuration :**
```yaml
audit:
  thresholds:
    max_disabled_users: 10  # Alerte si > 10
```

**Action recommandée :**
```bash
# Lister les comptes désactivés
ldap-monitor user list --filter "disabled" --output disabled-users.csv

# Supprimer après vérification
ldap-monitor cleanup disabled --days 365 --confirm
```

### 2. Attributs Manquants

**Attributs vérifiés par défaut :**
- `cn` (Common Name)
- `sn` (Surname)
- `mail` (Email)
- `uid` (User ID)

**Configuration :**
```yaml
audit:
  required_user_attributes:
    - cn
    - sn
    - mail
    - uid
    - givenName         # Prénom
    - telephoneNumber   # Téléphone
    - department        # Département
    - title             # Titre
```

**Exemple de résultat :**
```
⚠️  15 users missing required attributes
  Found 15 users with missing attributes
  💡 Complete user profiles with required attributes

  Examples:
  - uid=user1,ou=users,dc=example,dc=com
    Missing: mail, telephoneNumber

  - uid=user2,ou=users,dc=example,dc=com
    Missing: department, title
```

**Corriger les attributs manquants :**
```bash
# Voir les détails
ldap-monitor user show "uid=user1,ou=users,dc=example,dc=com"

# Ajouter un attribut
ldap-monitor user set-attribute \
  "uid=user1,ou=users,dc=example,dc=com" \
  mail \
  "user1@example.com"
```

### 3. Comptes Inactifs

**Détection basée sur :**
- `lastLogon` (Active Directory)
- `lastLogonTimestamp` (Active Directory)
- `authTimestamp` (OpenLDAP avec overlay)

**Configuration :**
```yaml
audit:
  thresholds:
    inactive_days: 90  # Inactif si pas de connexion depuis 90 jours
```

**Utilisation :**
```bash
# Détecter comptes inactifs (90 jours par défaut)
ldap-monitor audit users --inactive

# Avec seuil personnalisé (180 jours)
ldap-monitor audit users --inactive --days 180

# Exporter la liste
ldap-monitor audit users --inactive --export inactive-users.csv
```

**Exemple de résultat :**
```
⚠️  23 inactive users
  Found 23 users inactive for more than 90 days
  💡 Review and disable or remove inactive accounts

  Statistics:
  - Inactive 90-180 days: 10 users
  - Inactive 180-365 days: 8 users
  - Inactive > 1 year: 5 users

  Sample inactive users:
  - uid=old-employee,ou=users,dc=example,dc=com (inactive 456 days)
  - uid=contractor,ou=users,dc=example,dc=com (inactive 234 days)
```

**Actions recommandées :**
```bash
# 1. Générer rapport
ldap-monitor audit users --inactive --format html --output inactive-report.html

# 2. Désactiver les comptes
ldap-monitor user disable "uid=old-employee,ou=users,dc=example,dc=com"

# 3. Ou supprimer après backup
ldap-monitor backup full --output before-cleanup.ldif
ldap-monitor cleanup inactive --days 365 --confirm
```

### 4. Doublons

**Types de doublons détectés :**

#### Email en Double
```
🔴 3 duplicate email addresses
  Found 3 email addresses used by multiple users
  💡 Ensure email addresses are unique

  Duplicates:
  - john.doe@example.com:
    * uid=jdoe,ou=users,dc=example,dc=com
    * uid=john.doe,ou=users,dc=example,dc=com

  - admin@example.com:
    * uid=admin,ou=users,dc=example,dc=com
    * uid=administrator,ou=users,dc=example,dc=com
```

#### UID en Double
```
🔴 1 duplicate UIDs
  Found 1 UIDs used by multiple users
  💡 Ensure UIDs are unique

  Duplicates:
  - testuser:
    * uid=testuser,ou=employees,dc=example,dc=com
    * uid=testuser,ou=contractors,dc=example,dc=com
```

**Configuration :**
```yaml
audit:
  check_duplicates:
    - mail
    - uid
    - sAMAccountName    # Active Directory
    - employeeNumber
    - telephoneNumber
```

**Résolution :**
```bash
# 1. Identifier les doublons
ldap-monitor audit users --duplicates --output duplicates.json

# 2. Corriger manuellement
ldap-monitor user set-attribute \
  "uid=jdoe,ou=users,dc=example,dc=com" \
  mail \
  "john.doe2@example.com"

# 3. Vérifier
ldap-monitor audit users --duplicates
```

### 5. Incohérences de Format

**Validations effectuées :**

#### Emails Invalides
```bash
# Détecte :
- Email sans @
- Domaine invalide
- Caractères spéciaux
```

**Configuration :**
```yaml
audit:
  validation:
    email_regex: "^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$"
    allowed_email_domains:
      - example.com
      - corp.example.com
```

#### Téléphones Invalides
```yaml
audit:
  validation:
    phone_regex: "^\\+?[0-9]{10,15}$"
```

**Exemple de résultat :**
```
⚠️  8 users with invalid attributes
  - 5 invalid email addresses
  - 3 invalid phone numbers

  Examples:
  - uid=user1: email "notanemail" (invalid format)
  - uid=user2: phone "abc123" (invalid format)
```

### 6. Mots de Passe

**Vérifications (si attributs disponibles) :**
- Mots de passe expirés
- Mots de passe n'expirant jamais
- Dernière modification du mot de passe
- Politique de complexité

**Configuration :**
```yaml
audit:
  security:
    check_password_policies: true
    password_expiry_warning_days: 30
    password_max_age_days: 90
```

**Exemple :**
```
⚠️  Password issues detected
  - 5 users with expired passwords
  - 12 users with passwords expiring in < 30 days
  - 3 users with passwords set to never expire

  Attention required:
  - uid=admin: password never expires (SECURITY RISK)
  - uid=jdoe: password expired 15 days ago
```

## 📊 Rapports d'Audit

### Format Console (Par Défaut)

```bash
ldap-monitor audit users
```

Affiche un résumé coloré avec :
- Nombre total d'issues
- Détails par catégorie
- Exemples d'entrées affectées
- Recommandations

### Format JSON

```bash
ldap-monitor audit users --format json --output audit.json
```

**Structure JSON :**
```json
{
  "timestamp": "2025-01-15T10:30:00",
  "total_users": 150,
  "issues": [
    {
      "level": "warning",
      "category": "users",
      "title": "15 users missing required attributes",
      "description": "...",
      "recommendation": "Complete user profiles",
      "affected_count": 15,
      "affected_dns": ["uid=user1,...", "..."],
      "details": {...}
    }
  ],
  "statistics": {
    "total_issues": 45,
    "critical": 2,
    "warning": 38,
    "info": 5
  }
}
```

### Format HTML

```bash
ldap-monitor audit users --format html --output users-audit.html
```

Génère un rapport HTML avec :
- Graphiques interactifs
- Tableau triable des issues
- Export CSV intégré
- Impression-friendly

### Format CSV

```bash
ldap-monitor audit users --format csv --output users-issues.csv
```

**Colonnes CSV :**
```csv
DN,Issue Type,Severity,Description,Recommendation
"uid=user1,ou=users,dc=example,dc=com",Missing Attribute,Warning,"Missing: mail",Add email address
...
```

## 🎨 Personnalisation de l'Audit

### Définir les Attributs Requis

```yaml
audit:
  required_user_attributes:
    # Attributs de base
    - cn
    - sn
    - uid
    - mail

    # Attributs métier
    - employeeNumber
    - department
    - title
    - manager

    # Contact
    - telephoneNumber
    - mobile

    # Localisation
    - l            # Ville
    - st           # État/Province
    - co           # Pays

    # Active Directory
    - sAMAccountName
    - userPrincipalName
```

### Configurer les Seuils

```yaml
audit:
  thresholds:
    # Inactivité
    inactive_days: 90

    # Alertes
    max_disabled_users: 10
    max_users_without_email: 5
    max_users_without_manager: 20

    # Mots de passe
    password_expiry_warning_days: 30
    password_max_age_days: 90
```

### Exclure des Utilisateurs

```yaml
audit:
  exclude_users:
    # Par DN
    - uid=admin,ou=users,dc=example,dc=com
    - uid=root,ou=users,dc=example,dc=com

    # Par pattern (regex)
    - "uid=svc-.*"      # Tous les comptes de service
    - "uid=test.*"      # Tous les comptes de test
```

## 🔄 Automatisation

### Audit Quotidien

```bash
#!/bin/bash
# /usr/local/bin/daily-user-audit.sh

# Audit avec rapport HTML
ldap-monitor audit users \
  --format html \
  --output /var/reports/user-audit-$(date +%Y%m%d).html

# Si issues critiques, envoyer alerte
if ldap-monitor audit users --format json | jq -r '.statistics.critical' | grep -v '^0$'; then
  # Envoyer notification
  echo "Critical user issues detected" | mail -s "LDAP Audit Alert" admin@example.com
fi
```

**Cron :**
```cron
# Tous les jours à 6h00
0 6 * * * /usr/local/bin/daily-user-audit.sh
```

### CI/CD Integration

```yaml
# .github/workflows/ldap-audit.yml
name: LDAP User Audit

on:
  schedule:
    - cron: '0 6 * * *'  # Tous les jours à 6h

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Run LDAP user audit
        run: |
          ldap-monitor audit users \
            --format json \
            --output audit-results.json
        env:
          LDAP_PASSWORD: ${{ secrets.LDAP_PASSWORD }}

      - name: Upload results
        uses: actions/upload-artifact@v2
        with:
          name: audit-results
          path: audit-results.json

      - name: Check for critical issues
        run: |
          CRITICAL=$(jq -r '.statistics.critical' audit-results.json)
          if [ "$CRITICAL" -gt 0 ]; then
            echo "::error::Found $CRITICAL critical issues"
            exit 1
          fi
```

## 📚 Exemples Pratiques

### Scénario 1: Nettoyage Annuel

```bash
# 1. Audit complet
ldap-monitor audit users --format html --output annual-audit.html

# 2. Identifier comptes inactifs > 1 an
ldap-monitor audit users --inactive --days 365 --export inactive-1year.csv

# 3. Backup avant nettoyage
ldap-monitor backup full --output before-cleanup-$(date +%Y%m%d).ldif

# 4. Désactiver (pas supprimer immédiatement)
while read dn; do
  ldap-monitor user disable "$dn"
done < inactive-1year.csv

# 5. Audit de vérification
ldap-monitor audit users
```

### Scénario 2: Onboarding Vérification

```bash
# Vérifier nouveaux employés du mois
ldap-monitor user list --created-since "2025-01-01" \
  | while read dn; do
      ldap-monitor user show "$dn"
    done \
  | ldap-monitor audit users --missing-attributes
```

### Scénario 3: Compliance Check

```bash
# Rapport de compliance
ldap-monitor audit users \
  --check-all \
  --format html \
  --output compliance-report-$(date +%Y-%m).html

# Vérifier règles spécifiques
ldap-monitor audit users \
  --required-attributes "mail,telephoneNumber,manager,department" \
  --format csv \
  --output compliance-gaps.csv
```

## 📖 Voir Aussi

- [Audit de Groupes](Groups-Audit.md)
- [Audit de Sécurité](Security-Audit.md)
- [Rapports d'Audit](Audit-Reports.md)
- [Gestion des Utilisateurs](../management/User-Management.md)
- [Cleanup Operations](../management/Cleanup-Operations.md)
