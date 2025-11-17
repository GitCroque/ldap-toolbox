# Guide Active Directory

Configuration et utilisation de LDAP Health Monitor avec Microsoft Active Directory.

## 🎯 Spécificités Active Directory

Active Directory a des différences importantes par rapport à OpenLDAP :

- **Schéma** : Object classes et attributs différents
- **Authentification** : Support UPN et DOMAIN\user
- **Global Catalog** : Ports 3268/3269
- **Pagination** : Limite de 1000 entrées par page
- **Attributs propriétaires** : userAccountControl, sAMAccountName, etc.

## ⚙️ Configuration pour Active Directory

### Configuration Minimale

```yaml
ldap:
  # Connexion
  server: ldaps://dc01.corp.example.com
  port: 636
  use_ssl: true
  use_tls: false

  # Authentification (plusieurs formats possibles)
  bind_dn: serviceaccount@corp.example.com  # Format UPN (recommandé)
  # OU bind_dn: CORP\serviceaccount         # Format DOMAIN\user
  # OU bind_dn: cn=Service Account,ou=Service Accounts,dc=corp,dc=example,dc=com  # Format DN
  bind_password: ${LDAP_PASSWORD}

  # Base DN
  base_dn: dc=corp,dc=example,dc=com

  # Structure (adapter à votre organisation)
  users_ou: cn=Users,dc=corp,dc=example,dc=com
  groups_ou: cn=Groups,dc=corp,dc=example,dc=com

  # Schéma Active Directory
  user_objectclass: user
  group_objectclass: group
  user_uid_attribute: sAMAccountName
  group_member_attribute: member

  # Performance (important pour AD)
  timeout: 15
  retry_max: 3
  retry_delay: 3
  page_size: 1000  # Maximum pour AD
  search_scope: SUBTREE
```

### Configuration Avancée

```yaml
ldap:
  server: ldaps://dc01.corp.example.com
  port: 636
  use_ssl: true
  use_tls: false

  # Global Catalog (pour multi-domaines)
  # server: ldaps://dc01.corp.example.com
  # port: 3269

  bind_dn: svc-ldapmonitor@corp.example.com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=corp,dc=example,dc=com

  users_ou: ou=Corporate Users,dc=corp,dc=example,dc=com
  groups_ou: ou=Security Groups,dc=corp,dc=example,dc=com

  user_objectclass: user
  group_objectclass: group
  user_uid_attribute: sAMAccountName
  group_member_attribute: member

  timeout: 20
  retry_max: 5
  retry_delay: 5
  page_size: 1000
  search_scope: SUBTREE

# Audit spécifique AD
audit:
  required_user_attributes:
    - sAMAccountName
    - userPrincipalName
    - displayName
    - mail
    - department
    - title
    - manager

  thresholds:
    inactive_days: 90
    password_expiry_warning_days: 14

  security:
    check_password_policies: true
    alert_on_admin_creation: true
    privileged_groups:
      - cn=Domain Admins,cn=Users,dc=corp,dc=example,dc=com
      - cn=Enterprise Admins,cn=Users,dc=corp,dc=example,dc=com
      - cn=Schema Admins,cn=Users,dc=corp,dc=example,dc=com
      - cn=Account Operators,cn=Builtin,dc=corp,dc=example,dc=com
```

## 🔐 Création du Compte de Service

### Via PowerShell

```powershell
# Créer l'utilisateur
New-ADUser -Name "svc-ldapmonitor" `
  -SamAccountName "svc-ldapmonitor" `
  -UserPrincipalName "svc-ldapmonitor@corp.example.com" `
  -Path "OU=Service Accounts,DC=corp,DC=example,DC=com" `
  -AccountPassword (ConvertTo-SecureString "YourSecurePassword123!" -AsPlainText -Force) `
  -Enabled $true `
  -PasswordNeverExpires $true `
  -CannotChangePassword $true `
  -Description "LDAP Health Monitor Service Account (Read-Only)"

# Ajouter aux groupes si nécessaire (pour lecture)
Add-ADGroupMember -Identity "Domain Users" -Members "svc-ldapmonitor"

# Vérifier
Get-ADUser svc-ldapmonitor -Properties *
```

### Permissions Minimales

Le compte de service a besoin de :

**Pour l'audit (read-only) :**
- ✅ Read sur tous les objets du domaine
- ✅ Read sur les attributs : userAccountControl, lastLogon, pwdLastSet
- ❌ PAS de droits d'écriture
- ❌ PAS membre de Domain Admins

**Pour la gestion (optionnel) :**
- ✅ Write sur attributs spécifiques
- ✅ Create/Delete dans OUs spécifiques
- ⚠️ À limiter au strict nécessaire

### Délégation de Contrôle

```powershell
# Donner permissions de lecture sur le domaine
$acl = Get-Acl "AD:\DC=corp,DC=example,DC=com"
$user = Get-ADUser svc-ldapmonitor
$sid = [System.Security.Principal.SecurityIdentifier] $user.SID

# Ajout permission Read
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule `
  $sid, "GenericRead", "Allow", "All"

$acl.AddAccessRule($ace)
Set-Acl -Path "AD:\DC=corp,DC=example,DC=com" -AclObject $acl
```

## 🔍 Audit Spécifique AD

### Attributs Active Directory

**Attributs utilisateurs importants :**
```yaml
audit:
  required_user_attributes:
    # Identité
    - sAMAccountName
    - userPrincipalName
    - displayName
    - cn
    - sn
    - givenName

    # Contact
    - mail
    - telephoneNumber
    - mobile

    # Organisation
    - department
    - title
    - company
    - manager
    - employeeID

    # Technique
    - userAccountControl
    - pwdLastSet
    - lastLogon
    - lastLogonTimestamp
```

### UserAccountControl Flags

L'outil peut détecter :

```
0x0002 : ACCOUNTDISABLE (compte désactivé)
0x0010 : LOCKOUT (compte verrouillé)
0x0020 : PASSWD_NOTREQD (pas de mot de passe requis)
0x0040 : PASSWD_CANT_CHANGE (ne peut pas changer le mot de passe)
0x0080 : ENCRYPTED_TEXT_PWD_ALLOWED
0x0100 : TEMP_DUPLICATE_ACCOUNT
0x0200 : NORMAL_ACCOUNT
0x10000 : DONT_EXPIRE_PASSWORD (mot de passe n'expire jamais)
0x20000 : SMARTCARD_REQUIRED
0x40000 : TRUSTED_FOR_DELEGATION
0x80000 : NOT_DELEGATED
0x100000 : USE_DES_KEY_ONLY
0x200000 : DONT_REQ_PREAUTH
0x400000 : PASSWORD_EXPIRED
```

### Audit des Comptes Privilégiés

```bash
# Auditer Domain Admins
ldap-monitor audit security \
  --check-group "cn=Domain Admins,cn=Users,dc=corp,dc=example,dc=com"

# Lister tous les admins
ldap-monitor group members \
  "cn=Domain Admins,cn=Users,dc=corp,dc=example,dc=com"

# Trouver comptes avec "ne jamais expirer"
ldap-monitor audit users --never-expire-password
```

### Comptes Inactifs (lastLogon)

Active Directory stocke plusieurs attributs de connexion :

- **lastLogon** : Dernière connexion sur CE DC (non répliqué)
- **lastLogonTimestamp** : Répliqué mais mis à jour tous les 9-14 jours
- **pwdLastSet** : Dernière modification du mot de passe

```bash
# Utiliser lastLogonTimestamp (recommandé)
ldap-monitor audit users --inactive --days 90

# Export pour analyse
ldap-monitor audit users --inactive --format csv --output inactive-ad.csv
```

### Groupes Imbriqués

AD supporte les groupes imbriqués :

```bash
# Vérifier profondeur d'imbrication
ldap-monitor audit groups --nested-depth

# Détecter les boucles
ldap-monitor audit groups --circular-check
```

## 🏢 Multi-Domaines et Forêts

### Global Catalog

Pour interroger plusieurs domaines :

```yaml
ldap:
  server: ldaps://dc01.corp.example.com
  port: 3269  # Global Catalog SSL
  base_dn: dc=corp,dc=example,dc=com
```

### Plusieurs Domaines

```yaml
# Configuration pour domaine parent
ldap:
  base_dn: dc=example,dc=com
  users_ou: dc=example,dc=com  # Recherche dans tout le domaine

# Ou domaine enfant
ldap:
  base_dn: dc=subsidiary,dc=example,dc=com
```

## 📊 Rapports Active Directory

### Rapport de Compliance AD

```bash
# Rapport complet
ldap-monitor audit all \
  --format html \
  --output ad-compliance-report.html

# Vérifications spécifiques AD
ldap-monitor audit security \
  --check-password-policies \
  --check-privileged-accounts \
  --check-service-accounts
```

### Export pour Excel

```bash
# Users avec tous les attributs AD
ldap-monitor export users \
  --format csv \
  --attributes "sAMAccountName,userPrincipalName,displayName,mail,department,title,manager,lastLogonTimestamp" \
  --output ad-users-export.csv

# Groupes avec membres
ldap-monitor export groups \
  --format csv \
  --include-members \
  --output ad-groups-export.csv
```

## 🔄 Synchronisation et Monitoring

### Monitoring AD en Continu

```bash
# Démarrer monitoring
ldap-monitor monitor start --daemon

# Métriques AD spécifiques
ldap-monitor monitor metrics \
  --metrics users_total,groups_total,response_time,domain_controllers
```

### Alertes AD

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ad-alerts"

monitoring:
  alerts:
    - name: "New Domain Admin"
      condition: "new_member_in_group"
      group: "cn=Domain Admins,cn=Users,dc=corp,dc=example,dc=com"
      level: critical

    - name: "Account Lockouts"
      condition: "lockout_count_increase"
      threshold: 5
      level: warning
```

## 🛠️ Opérations de Gestion AD

### Désactiver des Comptes

```bash
# Désactiver un compte
ldap-monitor user disable \
  "cn=John Doe,ou=Users,dc=corp,dc=example,dc=com"

# Désactiver en masse (inactifs > 1 an)
ldap-monitor cleanup inactive \
  --days 365 \
  --dry-run  # Vérifier d'abord

ldap-monitor cleanup inactive \
  --days 365 \
  --confirm  # Exécuter
```

### Gestion des Groupes

```bash
# Ajouter membre à groupe
ldap-monitor group add-member \
  "cn=IT Team,ou=Groups,dc=corp,dc=example,dc=com" \
  "cn=John Doe,ou=Users,dc=corp,dc=example,dc=com"

# Retirer membre
ldap-monitor group remove-member \
  "cn=IT Team,ou=Groups,dc=corp,dc=example,dc=com" \
  "cn=John Doe,ou=Users,dc=corp,dc=example,dc=com"
```

## 🐛 Troubleshooting AD

### Problème de Connexion

```bash
# Test basique
ldap-monitor test connection

# Test avec verbose
ldap-monitor --verbose test connection

# Vérifier la résolution DNS
nslookup dc01.corp.example.com

# Vérifier les ports
telnet dc01.corp.example.com 636
```

### Erreurs Courantes

**"Server not operational"**
- Vérifier que le DC est accessible
- Vérifier les credentials
- Vérifier le bind DN format

**"Size limit exceeded"**
- Réduire page_size
- Filtrer la recherche
- Utiliser Global Catalog

**"Referral"**
- Suivre les referrals
- Ou se connecter directement au bon DC

### Debug

```bash
# Mode debug complet
ldap-monitor --verbose --config config.yaml audit health 2>&1 | tee debug.log

# Tester requête LDAP directe
ldapsearch -H ldaps://dc01.corp.example.com \
  -D "svc-ldapmonitor@corp.example.com" \
  -W \
  -b "dc=corp,dc=example,dc=com" \
  "(objectClass=user)" sAMAccountName
```

## 📚 Scripts PowerShell Utiles

### Export pour Comparaison

```powershell
# Export AD natif
Get-ADUser -Filter * -Properties * |
  Export-Csv -Path "ad-export-powershell.csv" -NoTypeInformation

# Puis comparer avec ldap-monitor
ldap-monitor export users --output ldap-monitor-export.csv

# Comparer
Compare-Object `
  (Import-Csv ad-export-powershell.csv) `
  (Import-Csv ldap-monitor-export.csv) `
  -Property sAMAccountName
```

### Vérification Post-Audit

```powershell
# Vérifier comptes inactifs détectés
$inactiveUsers = Import-Csv "inactive-users.csv"

foreach ($user in $inactiveUsers) {
    Get-ADUser -Filter {sAMAccountName -eq $user.sAMAccountName} `
      -Properties lastLogonTimestamp |
      Select sAMAccountName,
        @{N='LastLogon';E={[DateTime]::FromFileTime($_.lastLogonTimestamp)}}
}
```

## 📖 Voir Aussi

- [Configuration LDAP](../configuration/LDAP-Configuration.md)
- [Security Best Practices](../configuration/Security-Best-Practices.md)
- [User Audit](../features/audit/Users-Audit.md)
- [OpenLDAP Guide](OpenLDAP.md) (comparaison)
