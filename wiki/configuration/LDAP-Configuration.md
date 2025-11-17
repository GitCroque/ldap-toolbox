# Configuration LDAP - Guide Détaillé

Ce guide couvre toutes les options de configuration LDAP pour s'adapter à n'importe quel serveur LDAP ou Active Directory.

## 📋 Vue d'Ensemble

La section `ldap` du fichier `config.yaml` définit comment l'outil se connecte et interagit avec votre serveur LDAP.

## 🔌 Configuration de Connexion

### Serveur et Port

```yaml
ldap:
  server: ldap://ldap.example.com
  port: 389
```

**Options :**
- `server` : URL ou IP du serveur LDAP
  - Format : `ldap://` ou `ldaps://`
  - Exemple : `ldap://192.168.1.10`
  - Exemple : `ldaps://dc.example.com`

- `port` : Port de connexion
  - `389` : LDAP standard (non sécurisé)
  - `636` : LDAPS (SSL/TLS)
  - `3268` : Global Catalog (Active Directory)
  - `3269` : Global Catalog SSL (Active Directory)

### SSL/TLS

```yaml
ldap:
  use_ssl: true      # Utiliser LDAPS (port 636)
  use_tls: true      # Utiliser STARTTLS (port 389)
```

**Configurations recommandées :**

**Option 1 - LDAPS (Recommandé) :**
```yaml
ldap:
  server: ldaps://ldap.example.com
  port: 636
  use_ssl: true
  use_tls: false
```

**Option 2 - STARTTLS :**
```yaml
ldap:
  server: ldap://ldap.example.com
  port: 389
  use_ssl: false
  use_tls: true
```

**Option 3 - Non sécurisé (Test uniquement) :**
```yaml
ldap:
  server: ldap://ldap.example.com
  port: 389
  use_ssl: false
  use_tls: false
```

⚠️ **Attention** : N'utilisez JAMAIS de connexion non sécurisée en production !

### Authentification

```yaml
ldap:
  bind_dn: cn=admin,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
```

**Paramètres :**
- `bind_dn` : Distinguished Name de l'utilisateur de connexion
- `bind_password` : Mot de passe (TOUJOURS via variable d'environnement)

**Exemples selon le type de serveur :**

**OpenLDAP :**
```yaml
bind_dn: cn=admin,dc=example,dc=com
```

**Active Directory :**
```yaml
# Format DN
bind_dn: cn=Service Account,ou=Service Accounts,dc=corp,dc=example,dc=com

# Ou format UPN
bind_dn: serviceaccount@corp.example.com

# Ou format DOMAIN\user
bind_dn: CORP\serviceaccount
```

**FreeIPA :**
```yaml
bind_dn: uid=admin,cn=users,cn=accounts,dc=example,dc=com
```

### Base DN

```yaml
ldap:
  base_dn: dc=example,dc=com
```

Le Base DN est la racine de votre arborescence LDAP.

**Exemples :**
- `dc=example,dc=com` - Standard
- `dc=corp,dc=example,dc=com` - Sous-domaine
- `o=organization` - Format alternatif

Pour trouver votre Base DN :
```bash
# OpenLDAP
ldapsearch -x -LLL -b "" -s base namingContexts

# Active Directory
dsquery * -scope base -attr defaultNamingContext
```

## 🗂️ Configuration de Structure

### Organizational Units

```yaml
ldap:
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com
```

**Adaptation selon votre structure :**

**Structure simple :**
```yaml
users_ou: ou=People,dc=example,dc=com
groups_ou: ou=Groups,dc=example,dc=com
```

**Structure complexe (Active Directory) :**
```yaml
users_ou: ou=Employees,ou=Users,dc=corp,dc=example,dc=com
groups_ou: ou=Security Groups,ou=Groups,dc=corp,dc=example,dc=com
```

**Multiple OUs (à venir) :**
```yaml
users_ou:
  - ou=Employees,dc=example,dc=com
  - ou=Contractors,dc=example,dc=com
groups_ou:
  - ou=Security Groups,dc=example,dc=com
  - ou=Distribution Lists,dc=example,dc=com
```

## 🏷️ Configuration du Schéma

### Object Classes

```yaml
ldap:
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
```

**Par type de serveur :**

**OpenLDAP :**
```yaml
user_objectclass: inetOrgPerson
group_objectclass: groupOfNames
# Ou posixGroup pour groupes Unix
```

**Active Directory :**
```yaml
user_objectclass: user
group_objectclass: group
```

**FreeIPA :**
```yaml
user_objectclass: inetOrgPerson
group_objectclass: groupOfNames
```

### Attributs

```yaml
ldap:
  user_uid_attribute: uid
  group_member_attribute: member
```

**Configurations courantes :**

**OpenLDAP :**
```yaml
user_uid_attribute: uid
group_member_attribute: member
```

**Active Directory :**
```yaml
user_uid_attribute: sAMAccountName
group_member_attribute: member
# Alternative :
# user_uid_attribute: userPrincipalName
```

**FreeIPA :**
```yaml
user_uid_attribute: uid
group_member_attribute: member
```

## 🔧 Paramètres de Performance

### Timeouts

```yaml
ldap:
  timeout: 10          # Timeout de connexion (secondes)
  retry_max: 3         # Nombre de tentatives
  retry_delay: 2       # Délai entre tentatives (secondes)
```

**Adaptation selon votre réseau :**

**Réseau local rapide :**
```yaml
timeout: 5
retry_max: 2
retry_delay: 1
```

**Réseau distant/lent :**
```yaml
timeout: 30
retry_max: 5
retry_delay: 5
```

**VPN/connexion instable :**
```yaml
timeout: 60
retry_max: 10
retry_delay: 10
```

### Pagination

```yaml
ldap:
  page_size: 1000       # Taille des pages
  search_scope: SUBTREE # Profondeur de recherche
```

**page_size :**
- Petites bases (< 1000 entrées) : `500`
- Bases moyennes : `1000`
- Grandes bases (> 100k entrées) : `1500-2000`
- Active Directory : max `1000` (limitation serveur)

**search_scope :**
- `BASE` : Seulement l'objet de base
- `ONELEVEL` : Un niveau de profondeur
- `SUBTREE` : Tous les niveaux (défaut, recommandé)

## 📝 Exemples de Configurations Complètes

### OpenLDAP Standard

```yaml
ldap:
  # Connexion
  server: ldap://ldap.example.com
  port: 389
  use_ssl: false
  use_tls: true

  # Authentification
  bind_dn: cn=readonly,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com

  # Structure
  users_ou: ou=people,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com

  # Schéma
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
  user_uid_attribute: uid
  group_member_attribute: member

  # Performance
  timeout: 10
  retry_max: 3
  retry_delay: 2
  page_size: 1000
  search_scope: SUBTREE
```

### Active Directory

```yaml
ldap:
  # Connexion
  server: ldaps://dc01.corp.example.com
  port: 636
  use_ssl: true
  use_tls: false

  # Authentification
  bind_dn: serviceaccount@corp.example.com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=corp,dc=example,dc=com

  # Structure
  users_ou: ou=Users,dc=corp,dc=example,dc=com
  groups_ou: ou=Groups,dc=corp,dc=example,dc=com

  # Schéma Active Directory
  user_objectclass: user
  group_objectclass: group
  user_uid_attribute: sAMAccountName
  group_member_attribute: member

  # Performance (AD a des limites)
  timeout: 15
  retry_max: 3
  retry_delay: 3
  page_size: 1000  # Max pour AD
  search_scope: SUBTREE
```

### FreeIPA

```yaml
ldap:
  # Connexion
  server: ldaps://ipa.example.com
  port: 636
  use_ssl: true
  use_tls: false

  # Authentification
  bind_dn: uid=ldap-monitor,cn=users,cn=accounts,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com

  # Structure FreeIPA
  users_ou: cn=users,cn=accounts,dc=example,dc=com
  groups_ou: cn=groups,cn=accounts,dc=example,dc=com

  # Schéma
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
  user_uid_attribute: uid
  group_member_attribute: member

  # Performance
  timeout: 10
  retry_max: 3
  retry_delay: 2
  page_size: 1000
  search_scope: SUBTREE
```

### 389 Directory Server

```yaml
ldap:
  # Connexion
  server: ldaps://ds.example.com
  port: 636
  use_ssl: true
  use_tls: false

  # Authentification
  bind_dn: cn=Directory Manager
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com

  # Structure
  users_ou: ou=People,dc=example,dc=com
  groups_ou: ou=Groups,dc=example,dc=com

  # Schéma
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfUniqueNames
  user_uid_attribute: uid
  group_member_attribute: uniqueMember

  # Performance
  timeout: 10
  retry_max: 3
  retry_delay: 2
  page_size: 1500
  search_scope: SUBTREE
```

## 🧪 Test de Configuration

### Tester la connexion

```bash
# Test basique
ldap-monitor test connection

# Avec verbose
ldap-monitor --verbose test connection

# Avec config personnalisée
ldap-monitor --config /path/to/config.yaml test connection
```

### Valider la configuration

```bash
# Valider config.yaml
ldap-monitor config validate

# Afficher la config chargée
ldap-monitor config show
```

### Tester les recherches

```bash
# Compter les users
ldap-monitor user list --limit 10

# Compter les groups
ldap-monitor group list

# Audit rapide
ldap-monitor audit health
```

## 🔍 Trouver les Bonnes Valeurs

### Découvrir le Base DN

```bash
# Avec ldapsearch
ldapsearch -x -H ldap://server -b "" -s base namingContexts

# Avec l'outil
ldap-monitor test connection --discover
```

### Trouver les OUs

```bash
# Lister les OUs
ldapsearch -x -H ldap://server -D "bind_dn" -W \
  -b "dc=example,dc=com" "(objectClass=organizationalUnit)" dn

# Avec l'outil
ldap-monitor audit structure --tree
```

### Identifier les Object Classes

```bash
# Pour users
ldapsearch -x -H ldap://server -D "bind_dn" -W \
  -b "ou=users,dc=example,dc=com" \
  "(uid=*)" objectClass | grep objectClass

# Pour groups
ldapsearch -x -H ldap://server -D "bind_dn" -W \
  -b "ou=groups,dc=example,dc=com" \
  "(cn=*)" objectClass | grep objectClass
```

## 🔒 Sécurité

### Créer un Compte de Service Read-Only

**OpenLDAP :**
```ldif
dn: cn=ldap-monitor,ou=services,dc=example,dc=com
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: ldap-monitor
userPassword: {SSHA}generated-hash
description: Read-only account for LDAP Health Monitor
```

**Active Directory :**
1. Créer utilisateur "svc-ldap-monitor"
2. Permissions : Read sur tout le domaine
3. Ne PAS ajouter à Domain Admins

### ACLs OpenLDAP

```ldif
# Donner accès en lecture
access to *
  by dn="cn=ldap-monitor,ou=services,dc=example,dc=com" read
  by * none
```

## 📚 Voir Aussi

- [Variables d'Environnement](Environment-Variables.md)
- [Schema Customization](Schema-Customization.md)
- [Security Best Practices](Security-Best-Practices.md)
- [Active Directory Guide](../guides/Active-Directory.md)
- [OpenLDAP Guide](../guides/OpenLDAP.md)
