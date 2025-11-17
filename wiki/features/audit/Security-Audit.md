# Audit de sécurité LDAP

## Introduction

L'audit de sécurité est crucial pour protéger votre annuaire LDAP contre les accès non autorisés, les violations de données et les vulnérabilités. Ce guide couvre tous les aspects de la sécurité LDAP à auditer régulièrement.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Configuration de l'audit](#configuration-de-laudit)
3. [Comptes privilégiés](#comptes-privilégiés)
4. [Politiques de mots de passe](#politiques-de-mots-de-passe)
5. [SSL/TLS et chiffrement](#ssltls-et-chiffrement)
6. [Contrôle d'accès (ACLs)](#contrôle-daccès-acls)
7. [Authentification](#authentification)
8. [Audit des logs](#audit-des-logs)
9. [Conformité et réglementation](#conformité-et-réglementation)
10. [Exemples pratiques](#exemples-pratiques)
11. [Remédiation](#remédiation)
12. [Dépannage](#dépannage)

## Vue d'ensemble

### Qu'est-ce que l'audit de sécurité ?

L'audit de sécurité examine :
- **Comptes privilégiés** : Qui a les droits d'administration ?
- **Politiques de mots de passe** : Les mots de passe sont-ils robustes ?
- **Chiffrement** : Les communications sont-elles sécurisées ?
- **Contrôles d'accès** : Les permissions sont-elles appropriées ?
- **Configuration** : Le serveur est-il durci ?
- **Conformité** : Respecte-t-on les standards de sécurité ?

### Niveaux de sécurité

| Niveau | Description | Exemples |
|--------|-------------|----------|
| Critique | Faille majeure | Certificat expiré, admin sans mot de passe |
| Élevé | Risque important | Mots de passe faibles, pas de chiffrement |
| Moyen | Amélioration nécessaire | ACLs trop permissives, logs insuffisants |
| Faible | Bonne pratique | Configuration optimale recommandée |

### Architecture de l'audit

```
┌──────────────────┐
│ SecurityAuditor  │
└────────┬─────────┘
         │
    ┌────▼──────────────────────────────┐
    │ _check_privileged_accounts()      │
    │ _check_password_policy()          │
    │ _check_ssl_tls_config()           │
    │ _check_acls()                     │
    │ _check_authentication_methods()   │
    └────┬──────────────────────────────┘
         │
    ┌────▼─────────┐
    │ AuditIssue[] │
    └──────────────┘
```

## Configuration de l'audit

### Fichier de configuration

```yaml
audit:
  security:
    # Activer les vérifications de sécurité
    check_privileged_accounts: true
    check_password_policy: true
    check_ssl_config: true
    check_acls: true

    # Groupes privilégiés à surveiller
    privileged_groups:
      - "cn=Domain Admins,ou=Groups,dc=example,dc=com"
      - "cn=Enterprise Admins,ou=Groups,dc=example,dc=com"
      - "cn=LDAP Admins,ou=Groups,dc=example,dc=com"
      - "cn=Schema Admins,ou=Groups,dc=example,dc=com"

    # Comptes de service à exclure des vérifications
    service_accounts:
      - "cn=ldap-replicator,ou=ServiceAccounts,dc=example,dc=com"
      - "cn=monitoring,ou=ServiceAccounts,dc=example,dc=com"

    # Politique de mots de passe
    password_policy:
      min_length: 12
      require_uppercase: true
      require_lowercase: true
      require_digit: true
      require_special: true
      max_age_days: 90
      min_age_days: 1
      history_count: 5

    # Configuration SSL/TLS
    ssl_tls:
      require_ssl: true
      min_tls_version: "1.2"
      check_certificate_expiry: true
      certificate_expiry_warning_days: 30

    # Alertes
    alerts:
      email: "security@example.com"
      critical_issues_immediate: true
      daily_summary: true
```

### Commande de base

```bash
ldap-health-monitor audit security
```

**Sortie exemple :**
```
Found 3 issues

INFO: Privileged group has 5 members
  Group cn=Domain Admins,ou=Groups,dc=example,dc=com has 5 members
  💡 Regularly review privileged group membership

WARNING: Weak SSL/TLS configuration
  TLS 1.0 is enabled (should be 1.2+)
  💡 Disable legacy TLS versions

CRITICAL: Account without password expiry
  uid=admin,ou=Users,dc=example,dc=com has no password expiration
  💡 Enforce password expiration policy
```

## Comptes privilégiés

### Identification des comptes privilégiés

**Types de comptes privilégiés :**

1. **Administrateurs LDAP**
```ldif
dn: cn=admin,dc=example,dc=com
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: admin
userPassword: {SSHA}xxxxx
description: LDAP Administrator
```

2. **Administrateurs de domaine**
```bash
ldapsearch -x -b "cn=Domain Admins,ou=Groups,dc=example,dc=com" member
```

3. **Comptes de service avec privilèges**
```bash
ldapsearch -x -b "ou=ServiceAccounts,dc=example,dc=com" \
  "(&(objectClass=person)(memberOf=cn=Admins,*))"
```

### Audit des membres de groupes privilégiés

**Script de vérification :**
```bash
#!/bin/bash
# audit-privileged-accounts.sh

echo "=== Privileged Accounts Audit ==="
echo "Date: $(date)"
echo ""

# Liste des groupes privilégiés
PRIV_GROUPS=(
  "cn=Domain Admins,ou=Groups,dc=example,dc=com"
  "cn=Enterprise Admins,ou=Groups,dc=example,dc=com"
  "cn=LDAP Admins,ou=Groups,dc=example,dc=com"
  "cn=Schema Admins,ou=Groups,dc=example,dc=com"
)

for GROUP in "${PRIV_GROUPS[@]}"; do
  echo "=== $GROUP ==="

  # Compter les membres
  MEMBER_COUNT=$(ldapsearch -x -b "$GROUP" member | grep -c "^member:")

  echo "Total members: $MEMBER_COUNT"
  echo ""

  # Lister les membres avec détails
  ldapsearch -x -b "$GROUP" member | grep "^member:" | cut -d' ' -f2- | while read MEMBER_DN; do
    echo "Member: $MEMBER_DN"

    # Récupérer infos du membre
    USER_INFO=$(ldapsearch -x -b "$MEMBER_DN" -s base cn mail pwdLastSet accountExpires 2>/dev/null)

    CN=$(echo "$USER_INFO" | grep "^cn:" | cut -d' ' -f2-)
    MAIL=$(echo "$USER_INFO" | grep "^mail:" | cut -d' ' -f2-)
    LAST_PWD=$(echo "$USER_INFO" | grep "^pwdLastSet:" | cut -d' ' -f2-)

    echo "  Name: $CN"
    echo "  Email: $MAIL"
    echo "  Last password change: $LAST_PWD"

    # Vérifier si le compte est actif
    if ldapsearch -x -b "$MEMBER_DN" -s base userAccountControl 2>/dev/null | grep -q "userAccountControl:"; then
      UAC=$(ldapsearch -x -b "$MEMBER_DN" -s base userAccountControl | grep "^userAccountControl:" | cut -d' ' -f2)
      if [ $((UAC & 2)) -ne 0 ]; then
        echo "  ⚠️  Status: DISABLED"
      else
        echo "  ✓ Status: Active"
      fi
    fi

    # Vérifier la dernière connexion
    LAST_LOGON=$(ldapsearch -x -b "$MEMBER_DN" -s base lastLogon 2>/dev/null | grep "^lastLogon:" | cut -d' ' -f2-)
    if [ -n "$LAST_LOGON" ]; then
      echo "  Last logon: $LAST_LOGON"
    else
      echo "  ⚠️  Last logon: Unknown"
    fi

    echo ""
  done

  echo ""
done

# Alertes
echo "=== Alerts ==="

# Comptes admins désactivés mais toujours dans les groupes
echo "Checking for disabled admin accounts..."
# ... logique de vérification ...

# Comptes sans activité récente
echo "Checking for inactive admin accounts (90+ days)..."
# ... logique de vérification ...

# Comptes de service avec privilèges admin
echo "Checking for service accounts with admin rights..."
# ... logique de vérification ...
```

### Matrice de rôles et permissions

**Documentation des permissions :**
```yaml
# roles-matrix.yaml
privileged_roles:
  domain_admins:
    description: "Full control over domain"
    members:
      - uid=john.admin
      - uid=jane.admin
    permissions:
      - read_all
      - write_all
      - delete_all
      - modify_schema
    last_review: "2025-11-01"
    review_frequency: "monthly"

  ldap_admins:
    description: "LDAP server administration"
    members:
      - uid=ldap.admin
    permissions:
      - read_all
      - write_all
      - modify_config
    last_review: "2025-11-01"
    review_frequency: "monthly"

  security_admins:
    description: "Security policy management"
    members:
      - uid=security.admin
    permissions:
      - read_all
      - modify_acls
      - modify_password_policy
    last_review: "2025-10-15"
    review_frequency: "quarterly"
```

### Détection d'anomalies

**Comptes suspects :**
```python
#!/usr/bin/env python3
# detect-suspicious-accounts.py

from ldap3 import Server, Connection, ALL
from datetime import datetime, timedelta

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

# 1. Comptes admin récemment créés
threshold_date = datetime.now() - timedelta(days=7)
conn.search(
    'cn=Domain Admins,ou=Groups,dc=example,dc=com',
    '(objectClass=*)',
    attributes=['member']
)

print("=== Recently Added Admins (last 7 days) ===")
# Vérifier createTimestamp de chaque membre
# ...

# 2. Comptes avec privilèges mais sans email
print("\n=== Admin Accounts Without Email ===")
conn.search(
    'cn=Domain Admins,ou=Groups,dc=example,dc=com',
    '(objectClass=*)',
    attributes=['member']
)

for entry in conn.entries:
    if hasattr(entry, 'member'):
        for member_dn in entry.member:
            conn.search(member_dn, '(objectClass=*)', search_scope='BASE', attributes=['mail'])
            if not hasattr(conn.entries[0], 'mail'):
                print(f"No email: {member_dn}")

# 3. Comptes dupliqués (même nom mais différents DNs)
print("\n=== Potential Duplicate Admin Accounts ===")
# ...

conn.unbind()
```

### Notifications d'ajout aux groupes privilégiés

**Script de monitoring :**
```bash
#!/bin/bash
# monitor-admin-group-changes.sh

# Sauvegarder l'état actuel
CURRENT="/var/lib/ldap-monitor/admin-groups-current.txt"
PREVIOUS="/var/lib/ldap-monitor/admin-groups-previous.txt"

# Déplacer current vers previous
if [ -f "$CURRENT" ]; then
  mv "$CURRENT" "$PREVIOUS"
fi

# Récupérer l'état actuel
ldapsearch -x -b "cn=Domain Admins,ou=Groups,dc=example,dc=com" member | \
  grep "^member:" | cut -d' ' -f2- | sort > "$CURRENT"

# Comparer avec l'état précédent
if [ -f "$PREVIOUS" ]; then
  # Nouveaux membres
  NEW_MEMBERS=$(comm -13 "$PREVIOUS" "$CURRENT")

  if [ -n "$NEW_MEMBERS" ]; then
    echo "⚠️ NEW ADMIN MEMBERS DETECTED!" | \
      mail -s "SECURITY ALERT: Admin Group Modified" security@example.com

    echo "New members:" | \
      mail -s "Admin Group Changes" security@example.com
    echo "$NEW_MEMBERS" | \
      mail -s "Admin Group Changes" security@example.com
  fi

  # Membres supprimés
  REMOVED_MEMBERS=$(comm -23 "$PREVIOUS" "$CURRENT")

  if [ -n "$REMOVED_MEMBERS" ]; then
    echo "Members removed:" | \
      mail -s "Admin Group Changes" security@example.com
    echo "$REMOVED_MEMBERS" | \
      mail -s "Admin Group Changes" security@example.com
  fi
fi
```

**Cron toutes les heures :**
```cron
0 * * * * /usr/local/bin/monitor-admin-group-changes.sh
```

## Politiques de mots de passe

### Vérification de la politique

**Configuration OpenLDAP (ppolicy) :**
```ldif
dn: cn=default,ou=policies,dc=example,dc=com
objectClass: pwdPolicy
objectClass: person
objectClass: top
cn: default
sn: default
pwdAttribute: userPassword
pwdMinLength: 12
pwdMaxAge: 7776000
pwdMinAge: 86400
pwdInHistory: 5
pwdCheckQuality: 2
pwdMustChange: TRUE
pwdAllowUserChange: TRUE
pwdSafeModify: FALSE
pwdMaxFailure: 5
pwdFailureCountInterval: 1800
pwdLockout: TRUE
pwdLockoutDuration: 1800
pwdGraceAuthNLimit: 3
pwdExpireWarning: 604800
```

### Audit de la politique

**Script de vérification :**
```bash
#!/bin/bash
# audit-password-policy.sh

echo "=== Password Policy Audit ==="

# Récupérer la politique
POLICY_DN="cn=default,ou=policies,dc=example,dc=com"

echo "Current Password Policy:"
ldapsearch -x -b "$POLICY_DN" -s base

# Vérifier les paramètres critiques
PWD_MIN_LENGTH=$(ldapsearch -x -b "$POLICY_DN" -s base pwdMinLength | grep "^pwdMinLength:" | cut -d' ' -f2)
PWD_MAX_AGE=$(ldapsearch -x -b "$POLICY_DN" -s base pwdMaxAge | grep "^pwdMaxAge:" | cut -d' ' -f2)
PWD_IN_HISTORY=$(ldapsearch -x -b "$POLICY_DN" -s base pwdInHistory | grep "^pwdInHistory:" | cut -d' ' -f2)

echo ""
echo "=== Policy Checks ==="

# Longueur minimum
if [ "$PWD_MIN_LENGTH" -lt 12 ]; then
  echo "⚠️  WARNING: Minimum password length is $PWD_MIN_LENGTH (should be ≥12)"
else
  echo "✓ Minimum password length: $PWD_MIN_LENGTH"
fi

# Âge maximum (en secondes, 7776000 = 90 jours)
if [ "$PWD_MAX_AGE" -gt 7776000 ]; then
  DAYS=$((PWD_MAX_AGE / 86400))
  echo "⚠️  WARNING: Password expires after $DAYS days (should be ≤90)"
else
  DAYS=$((PWD_MAX_AGE / 86400))
  echo "✓ Password max age: $DAYS days"
fi

# Historique
if [ "$PWD_IN_HISTORY" -lt 5 ]; then
  echo "⚠️  WARNING: Password history is $PWD_IN_HISTORY (should be ≥5)"
else
  echo "✓ Password history: $PWD_IN_HISTORY"
fi
```

### Comptes avec mots de passe expirés

**Recherche :**
```bash
#!/bin/bash
# find-expired-passwords.sh

echo "=== Expired Passwords ==="

# Rechercher les comptes avec mots de passe expirés
ldapsearch -x -b "ou=Users,dc=example,dc=com" \
  "(&(objectClass=person)(pwdChangedTime=*))" \
  dn pwdChangedTime | \
while read LINE; do
  if [[ "$LINE" =~ ^dn: ]]; then
    CURRENT_DN=$(echo "$LINE" | cut -d' ' -f2-)
  elif [[ "$LINE" =~ ^pwdChangedTime: ]]; then
    PWD_CHANGED=$(echo "$LINE" | cut -d' ' -f2-)

    # Calculer l'âge (nécessite conversion du format LDAP)
    # Format LDAP: 20251117103045Z
    # ...calcul...

    echo "$CURRENT_DN - Last changed: $PWD_CHANGED"
  fi
done
```

### Comptes avec mots de passe faibles

**Utilisation de John the Ripper (test autorisé uniquement) :**
```bash
#!/bin/bash
# test-weak-passwords.sh

# ⚠️  À utiliser uniquement sur des environnements de test
# ⚠️  Nécessite autorisation explicite

# Export des hashes
ldapsearch -x -b "ou=Users,dc=example,dc=com" \
  "(objectClass=person)" \
  dn userPassword > /tmp/passwords.ldif

# Extraction des hashes
grep "userPassword::" /tmp/passwords.ldif | cut -d' ' -f2- | \
  base64 -d > /tmp/hashes.txt

# Test avec John (wordlist commune)
john --wordlist=/usr/share/wordlists/common-passwords.txt /tmp/hashes.txt

# Rapporter les mots de passe faibles trouvés
john --show /tmp/hashes.txt

# Nettoyage
rm /tmp/passwords.ldif /tmp/hashes.txt
```

### Politique de complexité

**Script de validation :**
```python
#!/usr/bin/env python3
# validate-password-complexity.py

import re

def check_password_complexity(password):
    """Vérifie la complexité d'un mot de passe"""
    issues = []

    if len(password) < 12:
        issues.append("Too short (minimum 12 characters)")

    if not re.search(r'[A-Z]', password):
        issues.append("Missing uppercase letter")

    if not re.search(r'[a-z]', password):
        issues.append("Missing lowercase letter")

    if not re.search(r'\d', password):
        issues.append("Missing digit")

    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Missing special character")

    # Vérifier les patterns courants
    common_patterns = [
        r'password', r'123456', r'qwerty', r'admin',
        r'(\w)\1{2,}',  # Caractères répétés (aaa, 111)
        r'(01|12|23|34|45|56|67|78|89)',  # Séquences
    ]

    for pattern in common_patterns:
        if re.search(pattern, password, re.IGNORECASE):
            issues.append(f"Contains common pattern: {pattern}")

    return issues

# Test
passwords = [
    "Password123!",  # Commun
    "Tr0ub4dor&3",   # Bon
    "correct horse battery staple",  # Passphrase
    "P@ssw0rd",      # Trop court
]

for pwd in passwords:
    issues = check_password_complexity(pwd)
    if issues:
        print(f"'{pwd}': WEAK - {', '.join(issues)}")
    else:
        print(f"'{pwd}': STRONG")
```

## SSL/TLS et chiffrement

### Configuration SSL/TLS

**Vérification de la configuration :**
```bash
#!/bin/bash
# check-ssl-config.sh

echo "=== SSL/TLS Configuration Audit ==="

# Tester la connexion SSL
echo "Testing SSL connection..."
openssl s_client -connect ldap.example.com:636 -showcerts < /dev/null 2>/dev/null | \
  openssl x509 -text -noout

# Vérifier les versions TLS supportées
echo ""
echo "=== Supported TLS Versions ==="

for VERSION in ssl3 tls1 tls1_1 tls1_2 tls1_3; do
  echo -n "Testing $VERSION: "
  if openssl s_client -connect ldap.example.com:636 -$VERSION < /dev/null 2>/dev/null | grep -q "Cipher"; then
    if [[ "$VERSION" =~ ^(ssl3|tls1|tls1_1)$ ]]; then
      echo "⚠️  ENABLED (insecure, should be disabled)"
    else
      echo "✓ ENABLED"
    fi
  else
    echo "✗ DISABLED"
  fi
done

# Vérifier les ciphers
echo ""
echo "=== Cipher Suites ==="
nmap --script ssl-enum-ciphers -p 636 ldap.example.com
```

### Audit du certificat

**Vérification détaillée :**
```bash
#!/bin/bash
# audit-certificate.sh

echo "=== Certificate Audit ==="

# Récupérer le certificat
echo | openssl s_client -connect ldap.example.com:636 2>/dev/null | \
  openssl x509 -text -noout > /tmp/cert.txt

# Extraire les informations
SUBJECT=$(grep "Subject:" /tmp/cert.txt)
ISSUER=$(grep "Issuer:" /tmp/cert.txt)
NOT_BEFORE=$(grep "Not Before:" /tmp/cert.txt)
NOT_AFTER=$(grep "Not After:" /tmp/cert.txt)
SERIAL=$(grep "Serial Number:" /tmp/cert.txt)

echo "Subject: $SUBJECT"
echo "Issuer: $ISSUER"
echo "Valid From: $NOT_BEFORE"
echo "Valid Until: $NOT_AFTER"
echo "Serial: $SERIAL"

# Vérifier l'expiration
EXPIRY_DATE=$(echo "$NOT_AFTER" | grep -oP '\w{3}\s+\d+\s+\d+:\d+:\d+\s+\d+')
EXPIRY_EPOCH=$(date -d "$EXPIRY_DATE" +%s)
NOW_EPOCH=$(date +%s)
DAYS_LEFT=$(( (EXPIRY_EPOCH - NOW_EPOCH) / 86400 ))

echo ""
echo "=== Expiration Check ==="
if [ $DAYS_LEFT -lt 0 ]; then
  echo "🔴 CRITICAL: Certificate EXPIRED ${DAYS_LEFT#-} days ago!"
elif [ $DAYS_LEFT -lt 30 ]; then
  echo "⚠️  WARNING: Certificate expires in $DAYS_LEFT days"
else
  echo "✓ Certificate valid for $DAYS_LEFT days"
fi

# Vérifier la chaîne de certification
echo ""
echo "=== Certificate Chain ==="
openssl s_client -connect ldap.example.com:636 -showcerts < /dev/null 2>/dev/null | \
  awk '/BEGIN CERTIFICATE/,/END CERTIFICATE/' | \
  grep -c "BEGIN CERTIFICATE"
echo "certificates in chain"

# Vérifier la révocation (OCSP)
echo ""
echo "=== Revocation Check (OCSP) ==="
# ... logique OCSP ...

rm /tmp/cert.txt
```

### Forcer l'utilisation de SSL/TLS

**Configuration OpenLDAP :**
```ldif
# Require STARTTLS
dn: olcDatabase={1}mdb,cn=config
changetype: modify
replace: olcSecurity
olcSecurity: ssf=1 tls=1
```

**Configuration Active Directory :**
```powershell
# Forcer LDAPS uniquement
Set-ADObject -Identity "CN=NTDS Settings,CN=ServerName,CN=Servers,CN=SiteName,CN=Sites,CN=Configuration,DC=example,DC=com" -Replace @{"options"=1}
```

### Audit des connexions non chiffrées

**Analyse des logs :**
```bash
#!/bin/bash
# detect-unencrypted-connections.sh

echo "=== Unencrypted Connection Detection ==="

# Parser les logs LDAP
LOG_FILE="/var/log/slapd/slapd.log"

# Rechercher les connexions sur le port 389 (non SSL)
grep "conn=" "$LOG_FILE" | grep "fd=" | grep -v "ssf=" | \
while read LINE; do
  # Extraire l'IP source
  IP=$(echo "$LINE" | grep -oP 'IP=\K[\d.]+')
  TIMESTAMP=$(echo "$LINE" | awk '{print $1, $2, $3}')

  echo "$TIMESTAMP - Unencrypted connection from $IP"
done | tail -100

# Statistiques
echo ""
echo "=== Statistics (last 24h) ==="
TOTAL=$(grep -c "conn=" "$LOG_FILE")
UNENCRYPTED=$(grep "conn=" "$LOG_FILE" | grep -v "ssf=" | wc -l)
PERCENTAGE=$((UNENCRYPTED * 100 / TOTAL))

echo "Total connections: $TOTAL"
echo "Unencrypted: $UNENCRYPTED ($PERCENTAGE%)"

if [ $PERCENTAGE -gt 10 ]; then
  echo "⚠️  WARNING: High percentage of unencrypted connections!"
fi
```

## Contrôle d'accès (ACLs)

### Audit des ACLs OpenLDAP

**Récupération des ACLs :**
```bash
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=config" \
  "(objectClass=olcDatabaseConfig)" \
  olcAccess
```

**Exemple de sortie :**
```
olcAccess: {0}to attrs=userPassword
  by self write
  by anonymous auth
  by * none

olcAccess: {1}to dn.subtree="ou=Users,dc=example,dc=com"
  by group.exact="cn=HR,ou=Groups,dc=example,dc=com" write
  by users read
  by * none

olcAccess: {2}to *
  by self read
  by users read
  by * none
```

### Analyse des permissions excessives

**Script de vérification :**
```bash
#!/bin/bash
# audit-acls.sh

echo "=== ACL Security Audit ==="

# Récupérer toutes les ACLs
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=config" \
  "(objectClass=olcDatabaseConfig)" \
  olcAccess > /tmp/acls.txt

# Vérifications de sécurité

echo "1. Checking for anonymous write access..."
if grep -q "by anonymous write" /tmp/acls.txt; then
  echo "⚠️  CRITICAL: Anonymous write access found!"
  grep "by anonymous write" /tmp/acls.txt
else
  echo "✓ No anonymous write access"
fi

echo ""
echo "2. Checking for world-readable sensitive attributes..."
SENSITIVE_ATTRS=("userPassword" "sshPublicKey" "sambaNTPassword")
for ATTR in "${SENSITIVE_ATTRS[@]}"; do
  if grep "to attrs=$ATTR" /tmp/acls.txt | grep -q "by \* read"; then
    echo "⚠️  WARNING: $ATTR is world-readable!"
  else
    echo "✓ $ATTR properly protected"
  fi
done

echo ""
echo "3. Checking for overly permissive group write access..."
grep "by group" /tmp/acls.txt | grep "write" | while read LINE; do
  GROUP=$(echo "$LINE" | grep -oP 'group[^"]*"\K[^"]+')
  SCOPE=$(echo "$LINE" | grep -oP 'to \K[^"]+')
  echo "⚠️  Group write access: $GROUP can write to $SCOPE"
done

rm /tmp/acls.txt
```

### ACLs recommandées

**Configuration sécurisée OpenLDAP :**
```ldif
# 1. Protection du mot de passe
olcAccess: {0}to attrs=userPassword,shadowLastChange
  by self write
  by anonymous auth
  by group.exact="cn=LDAP Admins,ou=Groups,dc=example,dc=com" write
  by * none

# 2. Protection des informations sensibles
olcAccess: {1}to attrs=sshPublicKey,homeDirectory,loginShell
  by self write
  by group.exact="cn=LDAP Admins,ou=Groups,dc=example,dc=com" write
  by * none

# 3. Informations personnelles
olcAccess: {2}to dn.subtree="ou=Users,dc=example,dc=com" attrs=mail,telephoneNumber
  by self write
  by group.exact="cn=HR,ou=Groups,dc=example,dc=com" write
  by users read
  by * none

# 4. Lecture générale
olcAccess: {3}to dn.subtree="ou=Users,dc=example,dc=com"
  by self read
  by users read
  by * none

# 5. Groupes
olcAccess: {4}to dn.subtree="ou=Groups,dc=example,dc=com"
  by group.exact="cn=Group Admins,ou=Groups,dc=example,dc=com" write
  by users read
  by * none

# 6. Défaut (le plus restrictif)
olcAccess: {5}to *
  by self read
  by group.exact="cn=LDAP Admins,ou=Groups,dc=example,dc=com" write
  by * none
```

### Test des permissions

**Script de test :**
```python
#!/usr/bin/env python3
# test-permissions.py

from ldap3 import Server, Connection, ALL

# Tester avec différents comptes
test_accounts = [
    ('anonymous', None, None),
    ('regular_user', 'uid=alice,ou=Users,dc=example,dc=com', 'password'),
    ('admin', 'cn=admin,dc=example,dc=com', 'admin_password'),
]

tests = [
    ('Read own password', 'uid=alice,ou=Users,dc=example,dc=com', 'userPassword'),
    ('Read other user password', 'uid=bob,ou=Users,dc=example,dc=com', 'userPassword'),
    ('Modify own email', 'uid=alice,ou=Users,dc=example,dc=com', 'mail'),
    ('Modify other user email', 'uid=bob,ou=Users,dc=example,dc=com', 'mail'),
]

server = Server('ldap://ldap.example.com', get_info=ALL)

for account_name, bind_dn, password in test_accounts:
    print(f"\n=== Testing as: {account_name} ===")

    if bind_dn:
        conn = Connection(server, bind_dn, password, auto_bind=True)
    else:
        conn = Connection(server, auto_bind=True)

    for test_name, target_dn, attribute in tests:
        try:
            # Essayer de lire
            conn.search(target_dn, '(objectClass=*)', attributes=[attribute])
            if conn.entries:
                print(f"  ✓ {test_name}: SUCCESS (can read)")
            else:
                print(f"  ✗ {test_name}: DENIED (cannot read)")

        except Exception as e:
            print(f"  ✗ {test_name}: ERROR - {e}")

    conn.unbind()
```

## Authentification

### Méthodes d'authentification supportées

**Vérification :**
```bash
ldapsearch -x -H ldap://ldap.example.com -b "" -s base supportedSASLMechanisms
```

**Sortie exemple :**
```
supportedSASLMechanisms: PLAIN
supportedSASLMechanisms: LOGIN
supportedSASLMechanisms: DIGEST-MD5
supportedSASLMechanisms: CRAM-MD5
supportedSASLMechanisms: GSSAPI
```

### Audit des méthodes faibles

**Vérification :**
```bash
#!/bin/bash
# audit-auth-methods.sh

echo "=== Authentication Methods Audit ==="

# Récupérer les méthodes supportées
METHODS=$(ldapsearch -x -H ldap://ldap.example.com -b "" -s base supportedSASLMechanisms | \
  grep "supportedSASLMechanisms:" | cut -d' ' -f2)

# Vérifier les méthodes faibles
WEAK_METHODS=("PLAIN" "LOGIN" "DIGEST-MD5")

echo "Supported methods:"
echo "$METHODS"

echo ""
echo "=== Security Check ==="

for METHOD in "${WEAK_METHODS[@]}"; do
  if echo "$METHODS" | grep -q "^$METHOD$"; then
    echo "⚠️  WARNING: Weak auth method enabled: $METHOD"
    echo "   Recommendation: Disable and use GSSAPI (Kerberos) or require SSL/TLS"
  fi
done

# Vérifier si SSL est requis
echo ""
echo "=== SSL/TLS Requirement Check ==="
if ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=config" "(objectClass=olcGlobal)" olcSecurity | \
   grep -q "ssf="; then
  echo "✓ SSL/TLS is enforced"
else
  echo "⚠️  WARNING: SSL/TLS is NOT enforced"
  echo "   Recommendation: Set olcSecurity: ssf=1"
fi
```

### Audit des binds anonymes

**Vérification :**
```bash
#!/bin/bash
# audit-anonymous-binds.sh

echo "=== Anonymous Bind Audit ==="

# Tester si le bind anonyme est autorisé
if ldapsearch -x -H ldap://ldap.example.com -b "dc=example,dc=com" "(objectClass=*)" dn 2>/dev/null | grep -q "^dn:"; then
  echo "⚠️  WARNING: Anonymous binds are ALLOWED"
  echo ""
  echo "Accessible data with anonymous bind:"
  ldapsearch -x -H ldap://ldap.example.com -b "dc=example,dc=com" "(objectClass=*)" dn | grep "^dn:" | head -20
else
  echo "✓ Anonymous binds are properly restricted"
fi

# Vérifier la configuration
echo ""
echo "=== Configuration Check ==="
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=config" \
  "(objectClass=olcGlobal)" \
  olcDisallows olcRequires
```

### Configuration recommandée

**Désactiver les binds anonymes :**
```ldif
dn: cn=config
changetype: modify
add: olcDisallows
olcDisallows: bind_anon

dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcRequires
olcRequires: authc
```

## Audit des logs

### Configuration du logging

**OpenLDAP :**
```ldif
dn: cn=config
changetype: modify
replace: olcLogLevel
olcLogLevel: stats sync
```

**Niveaux de log :**
- `stats` : Statistiques de connexion
- `sync` : Réplication
- `acl` : Décisions ACL (debug uniquement)
- `conns` : Gestion des connexions
- `filter` : Filtres de recherche

### Analyse des logs de sécurité

**Script d'analyse :**
```bash
#!/bin/bash
# analyze-security-logs.sh

LOG_FILE="/var/log/slapd/slapd.log"
REPORT="/var/reports/security-log-$(date +%Y%m%d).txt"

{
  echo "=== LDAP Security Log Analysis ==="
  echo "Date: $(date)"
  echo "Period: Last 24 hours"
  echo ""

  # 1. Tentatives d'authentification échouées
  echo "=== Failed Authentication Attempts ==="
  grep "BIND" "$LOG_FILE" | grep "err=49" | tail -50
  echo ""

  # 2. Connexions depuis des IPs inhabituelles
  echo "=== Unusual Source IPs ==="
  grep "conn=" "$LOG_FILE" | grep -oP 'IP=\K[\d.]+' | sort | uniq -c | sort -rn | head -20
  echo ""

  # 3. Modifications de configuration
  echo "=== Configuration Changes ==="
  grep "cn=config" "$LOG_FILE" | grep "MOD"
  echo ""

  # 4. Accès aux données sensibles
  echo "=== Sensitive Data Access ==="
  grep "userPassword\|sshPublicKey\|sambaNTPassword" "$LOG_FILE" | tail -20
  echo ""

  # 5. Opérations d'administration
  echo "=== Admin Operations ==="
  grep "cn=admin" "$LOG_FILE" | grep -E "ADD|DEL|MOD" | tail -50
  echo ""

  # 6. Erreurs ACL
  echo "=== ACL Denials ==="
  grep "err=50\|err=53" "$LOG_FILE" | tail -20
  echo ""

} > "$REPORT"

echo "Report generated: $REPORT"

# Alertes
FAILED_BINDS=$(grep -c "err=49" "$LOG_FILE")
if [ $FAILED_BINDS -gt 100 ]; then
  echo "⚠️  ALERT: $FAILED_BINDS failed authentication attempts!" | \
    mail -s "Security Alert: High Failed Bind Count" security@example.com
fi
```

### SIEM Integration

**Export vers syslog :**
```bash
# /etc/rsyslog.d/ldap.conf
# Forward LDAP logs to SIEM
if $programname == 'slapd' then @@siem.example.com:514
& stop
```

**Export vers Elasticsearch :**
```bash
#!/bin/bash
# export-logs-to-elasticsearch.sh

LOG_FILE="/var/log/slapd/slapd.log"
ES_URL="http://elasticsearch.example.com:9200"
INDEX="ldap-logs-$(date +%Y.%m.%d)"

tail -f "$LOG_FILE" | while read LINE; do
  # Parser la ligne de log
  TIMESTAMP=$(echo "$LINE" | awk '{print $1, $2, $3}')
  MESSAGE=$(echo "$LINE" | cut -d' ' -f4-)

  # Créer le document JSON
  DOC=$(cat <<EOF
{
  "@timestamp": "$TIMESTAMP",
  "message": "$MESSAGE",
  "source": "ldap-server-01",
  "facility": "authentication"
}
EOF
)

  # Envoyer à Elasticsearch
  curl -X POST "$ES_URL/$INDEX/_doc" \
    -H 'Content-Type: application/json' \
    -d "$DOC"
done
```

## Conformité et réglementation

### RGPD (GDPR)

**Vérifications requises :**

1. **Minimisation des données**
```bash
# Vérifier les attributs collectés
ldapsearch -x -b "ou=Users,dc=example,dc=com" -s base \* | \
  grep "^[a-z]" | cut -d':' -f1 | sort -u
```

2. **Droit à l'oubli**
```bash
# Capacité de suppression complète
# Vérifier les backups et archives
```

3. **Chiffrement des données sensibles**
```bash
# Vérifier que les mots de passe sont hashés
ldapsearch -x -b "ou=Users,dc=example,dc=com" userPassword | \
  grep "userPassword:" | head -5
# Devrait afficher {SSHA} ou similaire
```

4. **Audit trail**
```bash
# Log de toutes les modifications
grep "MOD\|ADD\|DEL" /var/log/slapd/slapd.log
```

### HIPAA (Santé)

**Exigences :**
- Authentification forte (MFA)
- Chiffrement en transit et au repos
- Logs d'accès détaillés
- Révision régulière des accès

### PCI-DSS (Paiement)

**Contrôles requis :**
```yaml
pci_dss_controls:
  requirement_8:
    - unique_user_ids
    - strong_passwords
    - account_lockout
    - session_timeout

  requirement_10:
    - audit_trails
    - log_retention
    - log_protection
    - time_synchronization
```

### Génération de rapport de conformité

```python
#!/usr/bin/env python3
# compliance-report.py

import json
from datetime import datetime

def generate_compliance_report():
    """Génère un rapport de conformité"""
    report = {
        "timestamp": datetime.now().isoformat(),
        "standard": "GDPR",
        "checks": []
    }

    # Vérification 1: Chiffrement
    report["checks"].append({
        "id": "CRYPTO-001",
        "name": "Data Encryption",
        "status": "PASS",
        "details": "SSL/TLS enabled, TLS 1.2+",
        "evidence": "/var/audit/ssl-config.txt"
    })

    # Vérification 2: Contrôle d'accès
    report["checks"].append({
        "id": "ACCESS-001",
        "name": "Access Control",
        "status": "PASS",
        "details": "ACLs properly configured",
        "evidence": "/var/audit/acls.txt"
    })

    # Vérification 3: Audit logging
    report["checks"].append({
        "id": "AUDIT-001",
        "name": "Audit Logging",
        "status": "PASS",
        "details": "All access logged",
        "evidence": "/var/log/slapd/access.log"
    })

    # Calculer le score de conformité
    passed = sum(1 for c in report["checks"] if c["status"] == "PASS")
    total = len(report["checks"])
    report["compliance_score"] = f"{passed}/{total} ({passed*100//total}%)"

    # Sauvegarder le rapport
    with open(f'/var/reports/compliance-{datetime.now().strftime("%Y%m%d")}.json', 'w') as f:
        json.dump(report, f, indent=2)

    print(f"Compliance Score: {report['compliance_score']}")

if __name__ == "__main__":
    generate_compliance_report()
```

## Exemples pratiques

### Exemple 1 : Audit de sécurité mensuel

```bash
#!/bin/bash
# monthly-security-audit.sh

REPORT_DIR="/var/reports/security/$(date +%Y-%m)"
mkdir -p "$REPORT_DIR"

echo "=== Monthly Security Audit - $(date) ==="

# 1. Audit complet
ldap-health-monitor audit security \
  --format json \
  --output "$REPORT_DIR/audit.json"

# 2. Comptes privilégiés
./audit-privileged-accounts.sh > "$REPORT_DIR/privileged-accounts.txt"

# 3. Politique de mots de passe
./audit-password-policy.sh > "$REPORT_DIR/password-policy.txt"

# 4. Configuration SSL/TLS
./check-ssl-config.sh > "$REPORT_DIR/ssl-config.txt"

# 5. ACLs
./audit-acls.sh > "$REPORT_DIR/acls.txt"

# 6. Analyse des logs
./analyze-security-logs.sh

# 7. Génération du rapport HTML
python3 generate-security-report.py "$REPORT_DIR"

# 8. Notification
CRITICAL=$(jq -r '[.issues[] | select(.level=="critical")] | length' "$REPORT_DIR/audit.json")

if [ "$CRITICAL" -gt 0 ]; then
  mail -s "🔴 CRITICAL: Security Audit Found $CRITICAL Critical Issues" \
    -a "$REPORT_DIR/audit-summary.html" \
    security@example.com < "$REPORT_DIR/audit.json"
else
  mail -s "Security Audit Completed" \
    -a "$REPORT_DIR/audit-summary.html" \
    security@example.com <<< "No critical issues found"
fi
```

### Exemple 2: Surveillance en temps réel

```bash
#!/bin/bash
# realtime-security-monitor.sh

# Surveiller les événements de sécurité en temps réel
tail -f /var/log/slapd/slapd.log | while read LINE; do
  # Détecter les tentatives d'authentification échouées
  if echo "$LINE" | grep -q "err=49"; then
    IP=$(echo "$LINE" | grep -oP 'IP=\K[\d.]+')
    echo "Failed auth from $IP" | logger -t ldap-security
    # Bloquer après 5 échecs
    COUNT=$(grep "$IP" /var/log/slapd/slapd.log | grep -c "err=49")
    if [ $COUNT -gt 5 ]; then
      iptables -A INPUT -s $IP -j DROP
      echo "Blocked $IP after $COUNT failed attempts" | \
        mail -s "Security: IP Blocked" security@example.com
    fi
  fi

  # Détecter les modifications d'admin
  if echo "$LINE" | grep -q "cn=admin" && echo "$LINE" | grep -qE "MOD|ADD|DEL"; then
    echo "Admin operation detected" | logger -t ldap-security
    echo "$LINE" | mail -s "Admin Operation Alert" security@example.com
  fi

  # Détecter les accès aux données sensibles
  if echo "$LINE" | grep -q "userPassword"; then
    echo "Password attribute accessed" | logger -t ldap-security
  fi
done
```

## Remédiation

### Correction des vulnérabilités

**Checklist de durcissement :**

```bash
#!/bin/bash
# harden-ldap.sh

echo "=== LDAP Security Hardening ==="

# 1. Forcer SSL/TLS
echo "1. Enforcing SSL/TLS..."
ldapmodify -Y EXTERNAL -H ldapi:/// << EOF
dn: cn=config
changetype: modify
replace: olcSecurity
olcSecurity: ssf=128 tls=1
EOF

# 2. Désactiver binds anonymes
echo "2. Disabling anonymous binds..."
ldapmodify -Y EXTERNAL -H ldapi:/// << EOF
dn: cn=config
changetype: modify
add: olcDisallows
olcDisallows: bind_anon
EOF

# 3. Activer la politique de mots de passe
echo "3. Enabling password policy..."
# ... configuration ppolicy ...

# 4. Configurer les ACLs restrictives
echo "4. Configuring restrictive ACLs..."
# ... configuration ACLs ...

# 5. Activer l'audit logging
echo "5. Enabling comprehensive logging..."
ldapmodify -Y EXTERNAL -H ldapi:/// << EOF
dn: cn=config
changetype: modify
replace: olcLogLevel
olcLogLevel: stats sync conns
EOF

# 6. Désactiver TLS 1.0/1.1
echo "6. Disabling legacy TLS versions..."
# Dépend du serveur LDAP utilisé

echo "Hardening complete!"
```

## Dépannage

### Problèmes courants

**Accès refusé après durcissement :**
```bash
# Vérifier les ACLs
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=config" olcAccess

# Tester avec différents comptes
ldapwhoami -x -D "uid=test,ou=Users,dc=example,dc=com" -W
```

**Certificat SSL invalide :**
```bash
# Régénérer le certificat
certbot renew --force-renewal

# Redémarrer le service
systemctl restart slapd
```

## Conclusion

La sécurité LDAP nécessite une vigilance constante et des audits réguliers. En automatisant les vérifications et en maintenant une documentation à jour, vous pouvez assurer la protection de votre annuaire.

**Points clés :**
- Audit mensuel obligatoire
- Surveillance des comptes privilégiés
- Chiffrement systématique
- ACLs restrictives par défaut
- Logging complet des accès
- Conformité réglementaire

Pour aller plus loin :
- [Audit de cohérence](./Consistency-Audit.md)
- [Génération de rapports](./Audit-Reports.md)
- [Vue d'ensemble](./Overview.md)
