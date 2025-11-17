# Personnalisation du Schéma LDAP

## Table des Matières

- [Introduction](#introduction)
- [Configuration de Base](#configuration-de-base)
- [ObjectClass Mapping](#objectclass-mapping)
- [Mapping des Attributs](#mapping-des-attributs)
- [Schémas par Type de Serveur](#schémas-par-type-de-serveur)
- [Attributs Personnalisés](#attributs-personnalisés)
- [Validation du Schéma](#validation-du-schéma)
- [Extensions de Schéma](#extensions-de-schéma)
- [Migration entre Schémas](#migration-entre-schémas)
- [Exemples Pratiques](#exemples-pratiques)
- [Dépannage](#dépannage)

## Introduction

LDAP Health Monitor supporte différents types de serveurs LDAP avec des schémas variés. La personnalisation du schéma permet d'adapter l'outil à votre infrastructure spécifique.

### Serveurs LDAP Supportés

- **OpenLDAP** : Serveur LDAP open source
- **Active Directory** : Microsoft AD
- **FreeIPA** : Identity management pour Linux
- **389 Directory Server** : Red Hat Directory Server
- **OpenDJ / ForgeRock DS** : Directory Server Java
- **ApacheDS** : Apache Directory Server
- **Schémas personnalisés** : Votre propre schéma

### Concepts Clés

**ObjectClass**
- Définit le type d'objet (utilisateur, groupe, etc.)
- Détermine les attributs obligatoires et optionnels
- Peut hériter d'autres objectClass

**Attribut**
- Propriété d'un objet LDAP
- Type de données défini (string, integer, etc.)
- Peut être mono-valué ou multi-valué

**DN (Distinguished Name)**
- Identifiant unique d'un objet
- Hiérarchique (ex: uid=jdupont,ou=users,dc=company,dc=com)

## Configuration de Base

### Structure de Configuration

```yaml
ldap:
  # ObjectClasses
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames

  # Attributs principaux
  user_uid_attribute: uid
  group_member_attribute: member

  # Structure
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com
```

### Configuration Complète

```yaml
ldap:
  # Classes d'objets
  schema:
    # Utilisateurs
    user:
      objectclass: inetOrgPerson
      auxiliary_classes:
        - posixAccount
        - shadowAccount

    # Groupes
    group:
      objectclass: groupOfNames
      auxiliary_classes:
        - posixGroup

    # Unités organisationnelles
    ou:
      objectclass: organizationalUnit

  # Mapping des attributs
  attributes:
    # Utilisateurs
    user:
      uid: uid
      cn: cn
      surname: sn
      givenname: givenName
      email: mail
      phone: telephoneNumber
      employee_id: employeeNumber
      department: departmentNumber
      title: title
      manager: manager

    # Groupes
    group:
      name: cn
      members: member
      description: description
      owner: owner

  # Attributs multi-valués
  multivalued_attributes:
    - member
    - memberOf
    - objectClass
    - mail  # Peut avoir plusieurs emails
```

## ObjectClass Mapping

### Utilisateurs

**OpenLDAP Standard :**

```yaml
ldap:
  user_objectclass: inetOrgPerson

  # ObjectClasses liés
  user_objectclasses:
    required:
      - inetOrgPerson
      - organizationalPerson
      - person
      - top
    optional:
      - posixAccount
      - shadowAccount
```

**Active Directory :**

```yaml
ldap:
  user_objectclass: user

  user_objectclasses:
    required:
      - user
      - organizationalPerson
      - person
      - top
```

**FreeIPA :**

```yaml
ldap:
  user_objectclass: person

  user_objectclasses:
    required:
      - ipaobject
      - person
      - top
      - ipasshuser
      - inetorgperson
      - organizationalperson
      - krbticketpolicyaux
      - krbprincipalaux
      - inetuser
      - posixaccount
```

### Groupes

**OpenLDAP avec groupOfNames :**

```yaml
ldap:
  group_objectclass: groupOfNames
  group_member_attribute: member

  # groupOfNames nécessite au moins un membre
  allow_empty_groups: false
  dummy_member: cn=dummy,dc=example,dc=com
```

**OpenLDAP avec groupOfUniqueNames :**

```yaml
ldap:
  group_objectclass: groupOfUniqueNames
  group_member_attribute: uniqueMember
```

**Active Directory :**

```yaml
ldap:
  group_objectclass: group
  group_member_attribute: member

  # Types de groupes AD
  group_types:
    security: true
    distribution: true
  group_scopes:
    - global
    - universal
    - domain_local
```

**POSIX Groups :**

```yaml
ldap:
  group_objectclass: posixGroup
  group_member_attribute: memberUid  # UIDs au lieu de DNs

  # Configuration spécifique POSIX
  posix:
    gid_attribute: gidNumber
    next_gid: 10000
```

## Mapping des Attributs

### Attributs Utilisateur Standard

```yaml
ldap:
  attributes:
    user:
      # Identifiants
      uid: uid
      uidnumber: uidNumber
      gidnumber: gidNumber

      # Nom
      cn: cn
      sn: sn
      givenname: givenName
      displayname: displayName

      # Contact
      mail: mail
      telephone: telephoneNumber
      mobile: mobile

      # Organisation
      title: title
      department: departmentNumber
      company: o
      manager: manager

      # Système
      home: homeDirectory
      shell: loginShell

      # Dates
      created: createTimestamp
      modified: modifyTimestamp
```

### Attributs Active Directory

```yaml
ldap:
  attributes:
    user:
      # Identifiants AD
      samaccountname: sAMAccountName
      userprincipalname: userPrincipalName
      objectguid: objectGUID
      objectsid: objectSid

      # Contrôle de compte
      useraccountcontrol: userAccountControl
      accountexpires: accountExpires
      pwdlastset: pwdLastSet
      lastlogon: lastLogon
      lastlogontimestamp: lastLogonTimestamp
      badpwdcount: badPwdCount

      # Organisation AD
      ou: ou
      distinguishedname: distinguishedName
      canonicalname: canonicalName

      # Groupes
      memberof: memberOf
      primarygroupid: primaryGroupID
```

### Attributs FreeIPA

```yaml
ldap:
  attributes:
    user:
      # IPA spécifique
      ipauniqueid: ipaUniqueID
      krbprincipalname: krbPrincipalName
      krbpasswordexpiration: krbPasswordExpiration
      krblastpwdchange: krbLastPwdChange

      # SSH
      ipasshpubkey: ipaSSHPubKey

      # Sudo
      memberof: memberOf

      # Certificats
      usercertificate: userCertificate
```

### Attributs Personnalisés

```yaml
ldap:
  custom_attributes:
    # Attributs métier
    cost_center: customCostCenter
    employee_type: customEmployeeType
    contract_end_date: customContractEndDate
    badge_number: customBadgeNumber

    # Attributs techniques
    last_audit_date: customLastAudit
    compliance_status: customComplianceStatus
    data_classification: customDataClass

  # Validation des attributs personnalisés
  custom_validation:
    customCostCenter:
      type: string
      pattern: "^CC[0-9]{4}$"
      required: false

    customEmployeeType:
      type: string
      enum: [employee, contractor, intern, service]
      required: true

    customContractEndDate:
      type: date
      format: "%Y-%m-%d"
      required_if: "employeeType == 'contractor'"
```

## Schémas par Type de Serveur

### OpenLDAP

**Configuration Complète :**

```yaml
ldap:
  server_type: openldap

  schema:
    # Utilisateurs
    user:
      objectclass: inetOrgPerson
      required_objectclasses:
        - inetOrgPerson
        - organizationalPerson
        - person
        - top

      optional_objectclasses:
        - posixAccount
        - shadowAccount
        - inetLocalMailRecipient

      # Attributs obligatoires
      required_attributes:
        - cn
        - sn

      # Attributs recommandés
      recommended_attributes:
        - mail
        - uid
        - userPassword

    # Groupes
    group:
      objectclass: groupOfNames

      required_objectclasses:
        - groupOfNames
        - top

      optional_objectclasses:
        - posixGroup

      required_attributes:
        - cn
        - member

  # Mapping des attributs
  attributes:
    user:
      uid: uid
      cn: cn
      sn: sn
      givenName: givenName
      mail: mail
      telephoneNumber: telephoneNumber
      employeeNumber: employeeNumber
      title: title
      departmentNumber: departmentNumber
      manager: manager
      userPassword: userPassword
      homeDirectory: homeDirectory
      loginShell: loginShell
      uidNumber: uidNumber
      gidNumber: gidNumber

    group:
      cn: cn
      member: member
      description: description
      gidNumber: gidNumber
```

### Active Directory

**Configuration Complète :**

```yaml
ldap:
  server_type: activedirectory

  schema:
    user:
      objectclass: user

      required_objectclasses:
        - user
        - organizationalPerson
        - person
        - top

      required_attributes:
        - cn
        - sAMAccountName

      # Attributs AD spécifiques
      ad_attributes:
        - userAccountControl
        - userPrincipalName
        - objectGUID
        - objectSid
        - whenCreated
        - whenChanged
        - pwdLastSet
        - lastLogon
        - lastLogonTimestamp
        - memberOf
        - primaryGroupID

    group:
      objectclass: group

      required_objectclasses:
        - group
        - top

      required_attributes:
        - cn
        - sAMAccountName

      ad_attributes:
        - groupType
        - member
        - memberOf

  attributes:
    user:
      # Identifiant
      uid: sAMAccountName
      upn: userPrincipalName
      guid: objectGUID
      sid: objectSid

      # Nom
      cn: cn
      sn: sn
      givenName: givenName
      displayName: displayName

      # Contact
      mail: mail
      telephoneNumber: telephoneNumber
      mobile: mobile

      # Organisation
      title: title
      department: department
      company: company
      manager: manager
      employeeID: employeeID

      # Contrôle de compte
      userAccountControl: userAccountControl
      accountExpires: accountExpires
      pwdLastSet: pwdLastSet
      lastLogon: lastLogon
      badPwdCount: badPwdCount

      # Groupes
      memberOf: memberOf
      primaryGroupID: primaryGroupID

    group:
      cn: cn
      name: sAMAccountName
      member: member
      description: description
      groupType: groupType

  # Flags userAccountControl
  user_account_control:
    ACCOUNTDISABLE: 0x0002
    NORMAL_ACCOUNT: 0x0200
    DONT_EXPIRE_PASSWORD: 0x10000
    PASSWORD_EXPIRED: 0x800000

  # Types de groupes
  group_types:
    GLOBAL_GROUP: 0x00000002
    DOMAIN_LOCAL_GROUP: 0x00000004
    UNIVERSAL_GROUP: 0x00000008
    SECURITY_ENABLED: 0x80000000
```

### FreeIPA

**Configuration Complète :**

```yaml
ldap:
  server_type: freeipa

  schema:
    user:
      objectclass: person

      required_objectclasses:
        - ipaobject
        - person
        - top
        - ipasshuser
        - inetorgperson
        - organizationalperson
        - krbticketpolicyaux
        - krbprincipalaux
        - inetuser
        - posixaccount

      ipa_attributes:
        - ipaUniqueID
        - krbPrincipalName
        - krbCanonicalName
        - krbPasswordExpiration
        - krbLastPwdChange
        - krbLastSuccessfulAuth
        - krbLastFailedAuth
        - krbLoginFailedCount
        - ipaSSHPubKey
        - memberOf

    group:
      objectclass: groupofnames

      required_objectclasses:
        - ipaobject
        - ipausergroup
        - groupofnames
        - nestedgroup
        - top
        - posixgroup

      ipa_attributes:
        - ipaUniqueID
        - member
        - memberOf
        - gidNumber

  attributes:
    user:
      # IPA
      uid: uid
      unique_id: ipaUniqueID
      kerberos: krbPrincipalName

      # Standard
      cn: cn
      sn: sn
      givenName: givenName
      mail: mail
      telephoneNumber: telephoneNumber

      # POSIX
      uidNumber: uidNumber
      gidNumber: gidNumber
      homeDirectory: homeDirectory
      loginShell: loginShell

      # SSH
      sshPublicKey: ipaSSHPubKey

      # Kerberos
      krbPasswordExpiration: krbPasswordExpiration
      krbLastPwdChange: krbLastPwdChange

    group:
      cn: cn
      unique_id: ipaUniqueID
      member: member
      gidNumber: gidNumber
```

### 389 Directory Server

```yaml
ldap:
  server_type: 389ds

  schema:
    user:
      objectclass: inetOrgPerson

      required_objectclasses:
        - inetOrgPerson
        - organizationalPerson
        - person
        - top

      optional_objectclasses:
        - posixAccount
        - nsMemberOf

    group:
      objectclass: groupOfUniqueNames

      required_objectclasses:
        - groupOfUniqueNames
        - top

  attributes:
    user:
      uid: uid
      cn: cn
      sn: sn
      mail: mail
      nsAccountLock: nsAccountLock  # 389ds specific
      passwordExpirationTime: passwordExpirationTime

    group:
      cn: cn
      uniqueMember: uniqueMember
      description: description
```

## Attributs Personnalisés

### Définition d'Attributs Custom

```yaml
ldap:
  custom_schema:
    # Définir de nouveaux attributs
    attributes:
      - name: customCostCenter
        oid: 1.3.6.1.4.1.99999.1.1.1
        syntax: 1.3.6.1.4.1.1466.115.121.1.15  # DirectoryString
        single_value: true
        description: "Cost center code"

      - name: customEmployeeType
        oid: 1.3.6.1.4.1.99999.1.1.2
        syntax: 1.3.6.1.4.1.1466.115.121.1.15
        single_value: true
        description: "Employee type"

      - name: customProjectCodes
        oid: 1.3.6.1.4.1.99999.1.1.3
        syntax: 1.3.6.1.4.1.1466.115.121.1.15
        single_value: false  # Multi-valué
        description: "Assigned project codes"

    # Définir de nouvelles objectClasses
    objectclasses:
      - name: customEmployee
        oid: 1.3.6.1.4.1.99999.2.1.1
        sup: inetOrgPerson  # Hérite de
        structural: false   # Auxiliary
        must:
          - customEmployeeType
        may:
          - customCostCenter
          - customProjectCodes
```

### Utilisation des Attributs Custom

```yaml
ldap:
  # Inclure l'objectClass custom
  user_objectclass: inetOrgPerson

  user_auxiliary_classes:
    - customEmployee

  # Mapping
  attributes:
    user:
      cost_center: customCostCenter
      employee_type: customEmployeeType
      project_codes: customProjectCodes

  # Validation
  attribute_validation:
    customCostCenter:
      pattern: "^CC[0-9]{4}$"
      required: true

    customEmployeeType:
      enum: [FTE, contractor, intern, vendor]
      required: true
```

### Installation du Schéma Custom

**OpenLDAP :**

```ldif
# custom-schema.ldif

dn: cn=custom,cn=schema,cn=config
objectClass: olcSchemaConfig
cn: custom

# Attributs
olcAttributeTypes: ( 1.3.6.1.4.1.99999.1.1.1
  NAME 'customCostCenter'
  DESC 'Cost center code'
  EQUALITY caseIgnoreMatch
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.15
  SINGLE-VALUE )

olcAttributeTypes: ( 1.3.6.1.4.1.99999.1.1.2
  NAME 'customEmployeeType'
  DESC 'Employee type'
  EQUALITY caseIgnoreMatch
  SYNTAX 1.3.6.1.4.1.1466.115.121.1.15
  SINGLE-VALUE )

# ObjectClass
olcObjectClasses: ( 1.3.6.1.4.1.99999.2.1.1
  NAME 'customEmployee'
  DESC 'Custom employee attributes'
  SUP inetOrgPerson
  AUXILIARY
  MUST ( customEmployeeType )
  MAY ( customCostCenter ) )
```

**Commande d'installation :**

```bash
ldapadd -Y EXTERNAL -H ldapi:/// -f custom-schema.ldif
```

**Active Directory :**

```powershell
# Étendre le schéma AD (nécessite privilèges Schema Admin)

# Créer attribut
$attr = New-Object DirectoryServices.ActiveDirectory.ActiveDirectorySchemaProperty
$attr.Name = "customCostCenter"
$attr.CommonName = "customCostCenter"
$attr.Syntax = "String"
$attr.IsSingleValued = $true
$attr.Save()

# Ajouter à objectClass
$class = [DirectoryServices.ActiveDirectory.ActiveDirectorySchemaClass]::FindByName(
    [DirectoryServices.ActiveDirectory.DirectoryContext]::new("Forest"),
    "user"
)
$class.OptionalProperties.Add($attr)
$class.Save()
```

## Validation du Schéma

### Configuration de la Validation

```yaml
ldap:
  schema_validation:
    enabled: true

    # Vérifications
    checks:
      - objectclass_exists
      - required_attributes
      - attribute_syntax
      - attribute_values

    # Strictness
    strict_mode: false  # true = erreur, false = warning

    # Cache
    cache_schema: true
    cache_ttl: 3600
```

### Tests de Validation

```bash
# Valider le schéma configuré
ldap-health-monitor schema validate

# Tester un objet
ldap-health-monitor schema test-object \
  --dn "uid=test,ou=users,dc=example,dc=com"

# Vérifier la compatibilité
ldap-health-monitor schema check-compatibility \
  --server-type activedirectory
```

### Détection Automatique du Schéma

```yaml
ldap:
  schema_detection:
    enabled: true

    # Détection du type de serveur
    auto_detect_server: true

    # Détection des attributs
    discover_attributes: true

    # Suggestions
    suggest_mapping: true
```

**Commande :**

```bash
# Détecter le schéma automatiquement
ldap-health-monitor schema detect

# Output:
# Serveur détecté: OpenLDAP
# ObjectClass utilisateurs: inetOrgPerson
# ObjectClass groupes: groupOfNames
# Attributs disponibles: 156
#
# Configuration suggérée:
# ldap:
#   user_objectclass: inetOrgPerson
#   group_objectclass: groupOfNames
#   ...
```

## Extensions de Schéma

### Extensions Communes

**Email Routing (Postfix) :**

```yaml
ldap:
  extensions:
    mail_routing:
      enabled: true
      objectclass: inetLocalMailRecipient

      attributes:
        mail_local_address: mailLocalAddress
        mail_routing_address: mailRoutingAddress
        mail_host: mailHost
```

**Quota Disk :**

```yaml
ldap:
  extensions:
    quota:
      enabled: true
      objectclass: customQuota

      attributes:
        disk_quota: diskQuota
        disk_usage: diskUsage
```

**Authentication :**

```yaml
ldap:
  extensions:
    authentication:
      enabled: true

      # RADIUS
      radius:
        objectclass: radiusprofile
        attributes:
          radius_group_name: radiusGroupName

      # Two-Factor
      2fa:
        objectclass: custom2FA
        attributes:
          totp_secret: totpSecret
          backup_codes: backupCodes
```

## Migration entre Schémas

### Planification de Migration

```yaml
migration:
  # Source
  source:
    server_type: openldap
    user_objectclass: inetOrgPerson
    group_objectclass: groupOfNames

  # Destination
  target:
    server_type: freeipa
    user_objectclass: person
    group_objectclass: groupofnames

  # Mapping
  attribute_mapping:
    uid: uid  # Identique
    cn: cn    # Identique
    mail: mail  # Identique
    telephoneNumber: telephoneNumber  # Identique

  # Transformations
  transformations:
    # Ajouter attributs IPA
    add_attributes:
      - krbPrincipalName: "{uid}@EXAMPLE.COM"
      - ipaUniqueID: "auto-generate"

    # Ajouter objectClasses
    add_objectclasses:
      - ipaobject
      - ipasshuser
      - krbprincipalaux

  # Validation
  validation:
    test_before: true
    dry_run_first: true
    backup_source: true
```

### Outil de Migration

```bash
# Analyser la migration
ldap-health-monitor migrate analyze \
  --source-type openldap \
  --target-type freeipa

# Générer le plan de migration
ldap-health-monitor migrate plan \
  --output migration-plan.yaml

# Exécuter la migration (dry-run)
ldap-health-monitor migrate execute \
  --plan migration-plan.yaml \
  --dry-run

# Exécuter réellement
ldap-health-monitor migrate execute \
  --plan migration-plan.yaml \
  --execute
```

## Exemples Pratiques

### Configuration Hybride

```yaml
ldap:
  # Support multi-objectClass
  user_objectclass: inetOrgPerson

  user_objectclasses:
    required:
      - inetOrgPerson
      - organizationalPerson
      - person
      - top
    optional:
      - posixAccount  # Pour intégration Unix/Linux
      - customEmployee  # Attributs custom

  attributes:
    user:
      # Standard LDAP
      uid: uid
      cn: cn
      sn: sn
      mail: mail

      # POSIX
      uidNumber: uidNumber
      gidNumber: gidNumber
      homeDirectory: homeDirectory
      loginShell: loginShell

      # Custom
      cost_center: customCostCenter
      employee_type: customEmployeeType
```

### Configuration Multi-Sites

```yaml
ldap:
  # Sites multiples
  sites:
    paris:
      base_dn: dc=paris,dc=company,dc=com
      users_ou: ou=users,dc=paris,dc=company,dc=com
      groups_ou: ou=groups,dc=paris,dc=company,dc=com
      schema: openldap

    london:
      base_dn: dc=london,dc=company,dc=com
      users_ou: ou=users,dc=london,dc=company,dc=com
      groups_ou: ou=groups,dc=london,dc=company,dc=com
      schema: activedirectory

    tokyo:
      base_dn: dc=tokyo,dc=company,dc=com
      users_ou: ou=users,dc=tokyo,dc=company,dc=com
      groups_ou: ou=groups,dc=tokyo,dc=company,dc=com
      schema: 389ds
```

## Dépannage

### Erreurs de Schéma

**Attribut non reconnu :**

```bash
# Erreur
Error: Attribute 'customCostCenter' not found in schema

# Solution 1: Vérifier le schéma
ldap-health-monitor schema list-attributes

# Solution 2: Installer le schéma custom
ldapadd -Y EXTERNAL -H ldapi:/// -f custom-schema.ldif

# Solution 3: Désactiver la validation
ldap:
  schema_validation:
    enabled: false
```

**ObjectClass non valide :**

```bash
# Erreur
Error: ObjectClass 'customEmployee' not found

# Vérifier les objectClasses disponibles
ldapsearch -Y EXTERNAL -H ldapi:/// \
  -b "cn=schema,cn=config" \
  "(objectClass=olcSchemaConfig)" \
  olcObjectClasses

# Lister dans la config
ldap-health-monitor schema list-objectclasses
```

### Problèmes de Compatibilité

```bash
# Tester la compatibilité
ldap-health-monitor schema test \
  --server-type activedirectory

# Comparer les schémas
ldap-health-monitor schema compare \
  --source openldap \
  --target freeipa
```

### Debug du Mapping

```yaml
ldap:
  debug:
    log_attribute_access: true
    show_mapping: true
    validate_on_read: true

logging:
  level: DEBUG
  file: ./logs/schema-debug.log
```

## Liens Connexes

- [Structure du Fichier de Configuration](./Config-File-Structure.md)
- [Configuration LDAP](./LDAP-Configuration.md)
- [Configuration des Audits](./Audit-Configuration.md)
- [Guide des Schémas LDAP](../reference/LDAP-Schemas.md)
- [Migration de Schémas](../guides/Schema-Migration.md)
- [RFC 4519 - LDAP Schema](https://tools.ietf.org/html/rfc4519)
