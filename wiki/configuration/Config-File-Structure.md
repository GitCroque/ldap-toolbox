# Structure du Fichier de Configuration

## Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Structure Générale](#structure-générale)
- [Section LDAP](#section-ldap)
- [Section Audit](#section-audit)
- [Section Monitoring](#section-monitoring)
- [Section Alerts](#section-alerts)
- [Section Management](#section-management)
- [Section Backup](#section-backup)
- [Section Reports](#section-reports)
- [Section Integrations](#section-integrations)
- [Section Logging](#section-logging)
- [Section Advanced](#section-advanced)
- [Exemples Complets](#exemples-complets)
- [Validation et Bonnes Pratiques](#validation-et-bonnes-pratiques)
- [Dépannage](#dépannage)

## Vue d'ensemble

Le fichier `config.yaml` est le fichier de configuration principal du LDAP Health Monitor. Il définit tous les paramètres nécessaires pour se connecter à votre serveur LDAP, configurer les audits, le monitoring, les alertes et les opérations de gestion.

### Localisation du Fichier

Le fichier de configuration doit être placé à la racine du projet :

```
/home/user/ldap-toolbox/config.yaml
```

### Création Initiale

Pour créer votre fichier de configuration :

```bash
# Copier le fichier d'exemple
cp config.example.yaml config.yaml

# Éditer avec vos paramètres
nano config.yaml
```

**IMPORTANT** : Ne jamais commiter le fichier `config.yaml` dans Git car il contient des informations sensibles. Utilisez `config.example.yaml` comme référence.

## Structure Générale

Le fichier de configuration est organisé en sections logiques :

```yaml
ldap:           # Configuration de la connexion LDAP
audit:          # Configuration des audits
monitoring:     # Configuration du monitoring
alerts:         # Configuration des alertes
management:     # Configuration des opérations de gestion
backup:         # Configuration des sauvegardes
reports:        # Configuration des rapports
integrations:   # Intégrations tierces (Prometheus, n8n)
logging:        # Configuration des logs
advanced:       # Paramètres avancés
```

## Section LDAP

La section `ldap` définit les paramètres de connexion au serveur LDAP.

### Paramètres de Connexion

```yaml
ldap:
  # Serveur LDAP
  server: ldap://ldap.example.com
  port: 389
  use_ssl: true
  use_tls: true
```

#### Détails des Paramètres

- **server** (obligatoire) : URL du serveur LDAP
  - Format : `ldap://hostname` ou `ldaps://hostname`
  - Exemples :
    - `ldap://192.168.1.100`
    - `ldaps://ldap.entreprise.com`
    - `ldap://dc01.domain.local`

- **port** (défaut: 389) : Port de connexion
  - `389` : LDAP standard
  - `636` : LDAPS (LDAP over SSL)
  - `3268` : Global Catalog (Active Directory)

- **use_ssl** (défaut: true) : Utiliser SSL/TLS
  - `true` : Connexion chiffrée (recommandé)
  - `false` : Connexion non chiffrée (déconseillé)

- **use_tls** (défaut: true) : Utiliser STARTTLS
  - `true` : Upgrade la connexion vers TLS
  - `false` : Pas de TLS

### Authentication

```yaml
ldap:
  # Authentification
  bind_dn: cn=admin,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
```

**IMPORTANT** : Utilisez toujours des variables d'environnement pour les mots de passe.

#### Exemples de bind_dn

```yaml
# OpenLDAP
bind_dn: cn=admin,dc=example,dc=com

# Active Directory
bind_dn: CN=ServiceAccount,CN=Users,DC=domain,DC=com

# FreeIPA
bind_dn: uid=admin,cn=users,cn=accounts,dc=example,dc=com

# 389 Directory Server
bind_dn: cn=Directory Manager
```

### Base DN et Structure

```yaml
ldap:
  # Base DN pour les recherches
  base_dn: dc=example,dc=com

  # Unités organisationnelles
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com
```

#### Exemples de Structures Organisationnelles

**Structure Simple :**
```yaml
base_dn: dc=company,dc=com
users_ou: ou=People,dc=company,dc=com
groups_ou: ou=Groups,dc=company,dc=com
```

**Structure Complexe (Multi-Sites) :**
```yaml
base_dn: dc=global,dc=company,dc=com
users_ou: ou=employees,ou=paris,dc=global,dc=company,dc=com
groups_ou: ou=teams,ou=paris,dc=global,dc=company,dc=com
```

**Active Directory :**
```yaml
base_dn: DC=corp,DC=domain,DC=com
users_ou: CN=Users,DC=corp,DC=domain,DC=com
groups_ou: CN=Groups,DC=corp,DC=domain,DC=com
```

### Timeout et Retry

```yaml
ldap:
  # Timeout et retry
  timeout: 10
  retry_max: 3
  retry_delay: 2
```

- **timeout** : Délai d'attente en secondes avant timeout
- **retry_max** : Nombre maximum de tentatives en cas d'échec
- **retry_delay** : Délai en secondes entre chaque tentative

**Recommandations par Environnement :**

```yaml
# Production (réseau fiable)
timeout: 5
retry_max: 3
retry_delay: 1

# Environnement WAN (connexion distante)
timeout: 15
retry_max: 5
retry_delay: 3

# Développement local
timeout: 3
retry_max: 2
retry_delay: 1
```

### Paramètres de Recherche

```yaml
ldap:
  # Paramètres de recherche
  page_size: 1000
  search_scope: SUBTREE
```

- **page_size** : Nombre d'entrées par page (pagination)
  - Recommandé : 500-1000 pour la plupart des serveurs
  - Active Directory : max 1000
  - OpenLDAP : configurable

- **search_scope** : Portée de la recherche
  - `BASE` : Seulement l'entrée de base
  - `ONELEVEL` : Un niveau sous la base
  - `SUBTREE` : Tous les niveaux (défaut)

## Section Audit

Configuration des audits et vérifications LDAP.

### Checks à Effectuer

```yaml
audit:
  checks:
    - health        # Santé du serveur LDAP
    - users         # Audit des utilisateurs
    - groups        # Audit des groupes
    - structure     # Vérification de la structure
    - security      # Audit de sécurité
    - consistency   # Vérification de cohérence
```

#### Description des Checks

- **health** : Vérifie la connectivité et les performances du serveur
- **users** : Vérifie les comptes utilisateurs (inactifs, attributs manquants, doublons)
- **groups** : Vérifie les groupes (vides, orphelins, doublons)
- **structure** : Vérifie la structure de l'arborescence LDAP
- **security** : Audit de sécurité (comptes privilégiés, politiques)
- **consistency** : Cohérence des données (références cassées, etc.)

### Seuils d'Alerte (Thresholds)

```yaml
audit:
  thresholds:
    inactive_days: 90
    password_expiry_warning_days: 30
    max_empty_groups: 5
    max_group_size: 100
    max_nested_depth: 3
    response_time_warning_ms: 500
    response_time_critical_ms: 2000
    ssl_cert_expiry_warning_days: 30
```

#### Configuration Détaillée des Seuils

**Seuils Utilisateurs :**

```yaml
audit:
  thresholds:
    # Compte inactif après X jours
    inactive_days: 90  # 90 jours par défaut

    # Alerte expiration mot de passe
    password_expiry_warning_days: 30

    # Longueur minimale du mot de passe
    min_password_length: 12

    # Âge maximum du mot de passe (jours)
    max_password_age: 90
```

**Seuils Groupes :**

```yaml
audit:
  thresholds:
    # Nombre maximum de groupes vides tolérés
    max_empty_groups: 5

    # Taille maximale d'un groupe avant alerte
    max_group_size: 100

    # Profondeur maximale d'imbrication des groupes
    max_nested_depth: 3

    # Nombre minimum de membres pour un groupe critique
    min_critical_group_members: 2
```

**Seuils Performance :**

```yaml
audit:
  thresholds:
    # Temps de réponse WARNING (ms)
    response_time_warning_ms: 500

    # Temps de réponse CRITICAL (ms)
    response_time_critical_ms: 2000

    # Nombre de connexions simultanées max
    max_concurrent_connections: 50
```

### Attributs Obligatoires

```yaml
audit:
  # Attributs obligatoires pour les utilisateurs
  required_user_attributes:
    - cn
    - sn
    - mail
    - uid
    - employeeNumber
    - departmentNumber

  # Attributs obligatoires pour les groupes
  required_group_attributes:
    - cn
    - member
    - description
```

**Exemples par Type d'Annuaire :**

**OpenLDAP :**
```yaml
required_user_attributes:
  - uid
  - cn
  - sn
  - mail
  - userPassword
```

**Active Directory :**
```yaml
required_user_attributes:
  - sAMAccountName
  - cn
  - sn
  - mail
  - userPrincipalName
  - distinguishedName
```

**FreeIPA :**
```yaml
required_user_attributes:
  - uid
  - cn
  - sn
  - mail
  - krbPrincipalName
```

### Configuration de Sécurité

```yaml
audit:
  security:
    check_password_policies: true
    alert_on_admin_creation: true
    alert_on_mass_delete: true
    mass_delete_threshold: 10
    check_privileged_accounts: true

    # Groupes privilégiés à surveiller
    privileged_groups:
      - cn=admins,ou=groups,dc=example,dc=com
      - cn=domain admins,ou=groups,dc=example,dc=com
      - cn=enterprise admins,ou=groups,dc=example,dc=com
```

## Section Monitoring

Configuration du monitoring continu.

```yaml
monitoring:
  enabled: true
  interval: 300  # secondes entre chaque vérification
  retention_days: 90

  # Métriques à collecter
  metrics:
    - users_count
    - groups_count
    - response_time
    - auth_failures
    - modifications
    - connections

  # Configuration des alertes
  alerts:
    enabled: true
    channels:
      - slack
      - email

    # Seuils d'alerte
    response_time_threshold: 2000  # ms
    auth_failure_threshold: 10
    connection_error_threshold: 3
```

### Intervalles de Monitoring Recommandés

```yaml
# Production critique
monitoring:
  interval: 60  # 1 minute
  retention_days: 365

# Production standard
monitoring:
  interval: 300  # 5 minutes
  retention_days: 90

# Développement
monitoring:
  interval: 600  # 10 minutes
  retention_days: 30
```

## Section Alerts

Configuration complète dans [Alerts-Configuration.md](./Alerts-Configuration.md)

```yaml
alerts:
  # Slack
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    mention_on_critical: "@channel"
    username: "LDAP Monitor"
    icon_emoji: ":warning:"

  # Email
  email:
    enabled: true
    smtp_host: smtp.example.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    from: ldap-monitor@example.com
    to:
      - admin@example.com
      - team@example.com

  # Niveaux d'alertes à envoyer
  levels:
    info: true
    warning: true
    critical: true
```

## Section Management

```yaml
management:
  # Paramètres de sécurité
  allow_delete: false
  allow_bulk_operations: true
  require_confirmation: true
  backup_before_modify: true
  dry_run_by_default: true

  # Limites des opérations par lot
  batch_size: 100
  batch_delay: 1  # secondes entre les lots

  # Sauvegarde des opérations
  operation_backup_enabled: true
  operation_backup_dir: ./backups/operations
```

## Section Backup

```yaml
backup:
  auto_backup: true
  backup_dir: ./backups
  retention_days: 30
  compress: true
  format: ldif  # ldif, json, yaml

  # Sauvegarde incrémentale
  incremental_enabled: true
  incremental_base_dir: ./backups/incremental

  # Planification (format cron)
  schedule:
    enabled: false
    cron: "0 2 * * *"  # Quotidien à 2h du matin
```

## Section Reports

```yaml
reports:
  output_dir: ./reports
  default_format: html  # html, json, csv, pdf, yaml
  include_graphs: true
  include_recommendations: true

  templates_dir: ./templates
  custom_logo: null

  sections:
    - summary
    - health
    - users
    - groups
    - security
    - recommendations
```

## Section Integrations

```yaml
integrations:
  # Prometheus
  prometheus:
    enabled: false
    port: 9090
    host: 0.0.0.0
    path: /metrics

  # n8n
  n8n:
    enabled: false
    webhook_url: ${N8N_WEBHOOK}
    events:
      - alert
      - audit_complete
      - backup_complete
```

## Section Logging

```yaml
logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: ./logs/ldap-monitor.log
  max_bytes: 10485760  # 10MB
  backup_count: 5
  console: true
```

### Niveaux de Log

- **DEBUG** : Tous les détails (développement uniquement)
- **INFO** : Informations normales d'opération
- **WARNING** : Avertissements non critiques
- **ERROR** : Erreurs nécessitant attention
- **CRITICAL** : Erreurs critiques

## Section Advanced

```yaml
advanced:
  # Optimisation des performances
  connection_pool_size: 5
  max_concurrent_operations: 10

  # Cache
  cache_enabled: true
  cache_ttl: 300  # secondes

  # Rate limiting
  rate_limit_enabled: false
  rate_limit_requests: 100
  rate_limit_period: 60  # secondes
```

## Exemples Complets

### Configuration Production

```yaml
ldap:
  server: ldaps://ldap.prod.company.com
  port: 636
  use_ssl: true
  use_tls: true
  bind_dn: cn=svc-monitor,ou=services,dc=company,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=company,dc=com
  timeout: 10
  retry_max: 3
  retry_delay: 2
  users_ou: ou=users,dc=company,dc=com
  groups_ou: ou=groups,dc=company,dc=com
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
  user_uid_attribute: uid
  group_member_attribute: member
  page_size: 1000
  search_scope: SUBTREE

audit:
  checks:
    - health
    - users
    - groups
    - security
    - consistency
  thresholds:
    inactive_days: 90
    password_expiry_warning_days: 30
    max_empty_groups: 5
    max_group_size: 500
    response_time_warning_ms: 500
    response_time_critical_ms: 2000
  required_user_attributes:
    - cn
    - sn
    - mail
    - uid
  security:
    check_password_policies: true
    alert_on_admin_creation: true
    privileged_groups:
      - cn=admins,ou=groups,dc=company,dc=com

monitoring:
  enabled: true
  interval: 300
  retention_days: 365
  metrics:
    - users_count
    - groups_count
    - response_time
    - auth_failures
  alerts:
    enabled: true
    channels:
      - slack
      - email
    response_time_threshold: 2000

alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#prod-alerts"
    mention_on_critical: "@oncall"
  email:
    enabled: true
    smtp_host: smtp.company.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    from: ldap-monitor@company.com
    to:
      - ops-team@company.com
  levels:
    info: false
    warning: true
    critical: true

management:
  allow_delete: false
  allow_bulk_operations: true
  require_confirmation: true
  backup_before_modify: true
  dry_run_by_default: true

backup:
  auto_backup: true
  backup_dir: /var/backups/ldap-monitor
  retention_days: 90
  compress: true
  format: ldif
  schedule:
    enabled: true
    cron: "0 2 * * *"

logging:
  level: INFO
  file: /var/log/ldap-monitor/monitor.log
  max_bytes: 52428800  # 50MB
  backup_count: 10
  console: false
```

### Configuration Développement

```yaml
ldap:
  server: ldap://localhost
  port: 389
  use_ssl: false
  use_tls: false
  bind_dn: cn=admin,dc=example,dc=com
  bind_password: admin
  base_dn: dc=example,dc=com
  timeout: 5
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com

audit:
  checks:
    - health
    - users
  thresholds:
    inactive_days: 30
    max_empty_groups: 10

monitoring:
  enabled: true
  interval: 600
  retention_days: 7

alerts:
  slack:
    enabled: false
  email:
    enabled: false

logging:
  level: DEBUG
  console: true
  file: ./logs/dev.log
```

## Validation et Bonnes Pratiques

### Validation du Fichier

Utilisez la commande de validation :

```bash
ldap-health-monitor validate-config
```

### Bonnes Pratiques

1. **Sécurité**
   - Toujours utiliser des variables d'environnement pour les secrets
   - Activer SSL/TLS en production
   - Limiter les permissions du fichier : `chmod 600 config.yaml`

2. **Performance**
   - Ajuster `page_size` selon votre serveur LDAP
   - Configurer des timeouts appropriés
   - Activer le cache pour les grands annuaires

3. **Monitoring**
   - Commencer avec un interval de 5 minutes
   - Ajuster selon la charge et les besoins
   - Conserver les métriques au moins 90 jours

4. **Alertes**
   - Ne pas alerter sur INFO en production
   - Configurer plusieurs canaux pour la redondance
   - Tester les alertes régulièrement

## Dépannage

### Problèmes Courants

**Erreur de connexion :**
```
Vérifier :
- server et port
- use_ssl/use_tls
- Pare-feu et connectivité réseau
```

**Timeout :**
```yaml
# Augmenter les valeurs de timeout
ldap:
  timeout: 30
  retry_max: 5
```

**Erreurs d'authentification :**
```
Vérifier :
- bind_dn (format correct)
- bind_password (variable d'environnement définie)
- Permissions du compte de service
```

**Métriques non collectées :**
```yaml
# Vérifier que les checks sont activés
monitoring:
  metrics:
    - users_count  # Doit correspondre aux checks
```

## Liens Connexes

- [Variables d'Environnement](./Environment-Variables.md)
- [Configuration des Audits](./Audit-Configuration.md)
- [Configuration du Monitoring](./Monitoring-Configuration.md)
- [Configuration des Alertes](./Alerts-Configuration.md)
- [Personnalisation du Schéma](./Schema-Customization.md)
- [Guide de Démarrage Rapide](../getting-started/Quick-Start.md)
