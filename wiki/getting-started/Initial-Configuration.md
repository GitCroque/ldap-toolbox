# Configuration Initiale

Guide complet pour configurer LDAP Health Monitor pour la première fois.

## 📋 Prérequis

Avant de commencer, assurez-vous d'avoir :

- ✅ Python 3.10 ou supérieur installé
- ✅ Accès à un serveur LDAP (OpenLDAP, Active Directory, FreeIPA)
- ✅ Credentials d'un compte avec permissions de lecture
- ✅ Informations de connexion (server, port, base DN)

## 🔧 Étape 1 : Installation

### Via Make (Recommandé)

```bash
make install
```

### Installation Manuelle

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# ou
venv\Scripts\activate  # Windows

# Installer les dépendances
pip install -e .
```

### Vérifier l'Installation

```bash
ldap-monitor --version
```

## 📁 Étape 2 : Fichiers de Configuration

### Structure des Fichiers

LDAP Health Monitor utilise deux fichiers principaux :

```
ldap-health-monitor/
├── config.yaml          # Configuration principale (gitignored)
├── .env                 # Variables sensibles (gitignored)
├── config.example.yaml  # Template de configuration
└── .env.example         # Template d'environnement
```

### Créer les Fichiers

```bash
# Copier les templates
cp config.example.yaml config.yaml
cp .env.example .env
```

⚠️ **IMPORTANT** : Ces fichiers sont automatiquement exclus de Git pour éviter de commiter des informations sensibles.

## ⚙️ Étape 3 : Configuration du Serveur LDAP

### 3.1 Variables d'Environnement (.env)

Éditer le fichier `.env` avec vos credentials :

```bash
# Credentials LDAP
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BIND_PASSWORD=VotreMotDePasseSecurise

# Alerting (optionnel)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/XXX/YYY/ZZZ
EMAIL_PASSWORD=mot_de_passe_email

# Monitoring (optionnel)
PROMETHEUS_PORT=9090
```

### 3.2 Configuration LDAP (config.yaml)

#### Configuration de Base

```yaml
ldap:
  # Serveur LDAP
  server: "ldap.example.com"
  port: 636  # 636 pour LDAPS, 389 pour LDAP
  use_ssl: true
  use_tls: false

  # Authentification
  bind_dn: "${LDAP_BIND_DN}"
  bind_password: "${LDAP_BIND_PASSWORD}"

  # Base de recherche
  base_dn: "dc=example,dc=com"

  # Options de connexion
  timeout: 30
  page_size: 1000

  # Retry logic
  retry_max: 3
  retry_delay: 2
```

#### Configuration du Schéma

Adapter selon votre annuaire LDAP :

```yaml
schema:
  # Configuration des utilisateurs
  users:
    object_class: "inetOrgPerson"  # ou "user" pour AD
    base_ou: "ou=users,dc=example,dc=com"

    attributes:
      username: "uid"  # ou "sAMAccountName" pour AD
      email: "mail"
      first_name: "givenName"
      last_name: "sn"
      display_name: "cn"
      telephone: "telephoneNumber"
      disabled: "nsAccountLock"  # ou "userAccountControl" pour AD
      last_login: "loginTime"
      password_changed: "pwdChangedTime"
      groups: "memberOf"

    filters:
      all: "(objectClass=inetOrgPerson)"
      active: "(&(objectClass=inetOrgPerson)(!(nsAccountLock=TRUE)))"
      disabled: "(&(objectClass=inetOrgPerson)(nsAccountLock=TRUE))"

  # Configuration des groupes
  groups:
    object_class: "groupOfNames"  # ou "group" pour AD
    base_ou: "ou=groups,dc=example,dc=com"

    attributes:
      name: "cn"
      description: "description"
      members: "member"
      owner: "owner"

    filters:
      all: "(objectClass=groupOfNames)"
```

### 3.3 Configuration Spécifique par Type de LDAP

#### Pour Active Directory

```yaml
schema:
  users:
    object_class: "user"
    attributes:
      username: "sAMAccountName"
      disabled: "userAccountControl"
      email: "userPrincipalName"
    filters:
      all: "(&(objectClass=user)(objectCategory=person))"
      active: "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
      disabled: "(&(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=2))"

  groups:
    object_class: "group"
    attributes:
      members: "member"
```

#### Pour OpenLDAP

```yaml
schema:
  users:
    object_class: "inetOrgPerson"
    attributes:
      username: "uid"
      disabled: "nsAccountLock"

  groups:
    object_class: "groupOfNames"
    attributes:
      members: "member"
```

#### Pour FreeIPA

```yaml
schema:
  users:
    object_class: "inetOrgPerson"
    base_ou: "cn=users,cn=accounts,dc=example,dc=com"
    attributes:
      username: "uid"
      disabled: "nsAccountLock"

  groups:
    object_class: "groupOfNames"
    base_ou: "cn=groups,cn=accounts,dc=example,dc=com"
```

## 🧪 Étape 4 : Tester la Configuration

### Test de Connexion

```bash
ldap-monitor health
```

**Résultat attendu** :
```
✅ LDAP Health Check Results
────────────────────────────────────
Server: ldap.example.com:636
Status: ✓ Healthy
Response Time: 45ms
SSL Certificate: Valid (expires in 287 days)
Total Entries: 1,234
Version: 3
```

### Test d'Accès aux Données

```bash
# Lister quelques utilisateurs
ldap-monitor export users --limit 5

# Lister quelques groupes
ldap-monitor export groups --limit 5
```

### Déboguer les Problèmes de Connexion

Si la connexion échoue, augmenter le niveau de verbosité :

```bash
ldap-monitor --verbose health
```

Voir aussi : [Troubleshooting - Problèmes de Connexion](../troubleshooting/Connection-Issues.md)

## 📊 Étape 5 : Configuration des Audits

### 5.1 Configuration des Seuils d'Audit

```yaml
audit:
  # Critères pour détecter des comptes inactifs
  inactive_days: 90

  # Critères pour détecter des mots de passe anciens
  password_max_age: 180

  # Groupes vides à ignorer
  ignore_empty_groups:
    - "cn=temp,ou=groups,dc=example,dc=com"

  # Patterns d'attributs requis
  required_user_attributes:
    - mail
    - telephoneNumber

  # Validation d'email
  email_domains:
    - "example.com"
    - "example.org"
```

### 5.2 Premier Audit

```bash
# Audit complet
ldap-monitor audit all

# Audit avec rapport HTML
ldap-monitor audit all --format html --output audit-$(date +%Y%m%d).html
```

## 📈 Étape 6 : Configuration du Monitoring (Optionnel)

### 6.1 Configuration des Métriques

```yaml
monitoring:
  enabled: true
  interval: 300  # Collecte toutes les 5 minutes

  metrics:
    # Métriques à collecter
    collect_users: true
    collect_groups: true
    collect_health: true
    collect_performance: true

  # Exposition Prometheus
  prometheus:
    enabled: true
    port: 9090
    path: "/metrics"
```

### 6.2 Démarrer le Monitoring

```bash
ldap-monitor monitor start --interval 300
```

## 🔔 Étape 7 : Configuration des Alertes (Optionnel)

### 7.1 Alertes Slack

```yaml
alerts:
  enabled: true

  # Canaux de notification
  channels:
    - type: slack
      webhook_url: "${SLACK_WEBHOOK_URL}"
      enabled: true
      min_severity: warning

  # Règles d'alerting
  rules:
    - name: "server_down"
      condition: "health_status == 'down'"
      severity: critical
      message: "🚨 LDAP Server is DOWN!"

    - name: "high_response_time"
      condition: "response_time > 1000"
      severity: warning
      message: "⚠️ LDAP response time is high: {response_time}ms"

    - name: "many_disabled_accounts"
      condition: "disabled_users > 50"
      severity: warning
      message: "⚠️ {disabled_users} disabled accounts detected"
```

### 7.2 Alertes Email

```yaml
alerts:
  channels:
    - type: email
      smtp_host: "smtp.gmail.com"
      smtp_port: 587
      smtp_user: "alerts@example.com"
      smtp_password: "${EMAIL_PASSWORD}"
      from_addr: "ldap-monitor@example.com"
      to_addrs:
        - "admin@example.com"
        - "team@example.com"
      enabled: true
      min_severity: critical
```

## 🔒 Étape 8 : Sécurisation

### Permissions des Fichiers

```bash
# Restreindre l'accès aux fichiers sensibles
chmod 600 .env
chmod 600 config.yaml
```

### Vérifier le .gitignore

S'assurer que les fichiers sensibles sont exclus :

```bash
# Vérifier que config.yaml n'est PAS tracké
git status

# Les fichiers suivants ne doivent JAMAIS apparaître
# - config.yaml
# - .env
# - *.ldif
# - backup*.json
# - users*.csv
```

### Credentials en Lecture Seule

⚠️ **BEST PRACTICE** : Utiliser un compte LDAP avec permissions en **lecture seule** :

```bash
# Active Directory
dsacls "dc=example,dc=com" /G "LDAP-Monitor:GR"

# OpenLDAP (slapd.conf)
access to *
  by dn="cn=monitor,dc=example,dc=com" read
  by * none
```

## 🚀 Étape 9 : Automatisation

### Scripts d'Automatisation

Voir les scripts fournis dans `examples/scripts/` :

```bash
# Configurer les tâches automatisées
cd examples/scripts
./setup-cron.sh
```

Cela configure :
- ✅ Audit quotidien à 6h00
- ✅ Backup quotidien à 2h00
- ✅ Cleanup hebdomadaire (dimanche 3h00)

## ✅ Checklist de Configuration

- [ ] Python 3.10+ installé
- [ ] Dépendances installées (`make install`)
- [ ] Fichier `config.yaml` créé et édité
- [ ] Fichier `.env` créé avec credentials
- [ ] Test de connexion réussi (`ldap-monitor health`)
- [ ] Schéma LDAP configuré correctement
- [ ] Premier audit effectué
- [ ] Permissions des fichiers sécurisées (chmod 600)
- [ ] .gitignore vérifié
- [ ] Monitoring configuré (optionnel)
- [ ] Alertes configurées (optionnel)
- [ ] Automatisation mise en place (optionnel)

## 🎯 Prochaines Étapes

Maintenant que votre configuration initiale est terminée :

1. **Personnaliser les audits** : [Configuration des Audits](../configuration/Audit-Configuration.md)
2. **Mettre en production** : [Production Monitoring](../guides/Production-Monitoring.md)
3. **Automatiser** : [Cron Automation](../guides/Cron-Automation.md)
4. **Optimiser** : [Performance Tuning](../guides/Performance-Tuning.md)

## 🆘 Besoin d'Aide ?

- [FAQ](../troubleshooting/FAQ.md)
- [Problèmes de Connexion](../troubleshooting/Connection-Issues.md)
- [Erreurs Courantes](../troubleshooting/Common-Errors.md)
- [Guide Active Directory](../guides/Active-Directory.md)
- [Guide OpenLDAP](../guides/OpenLDAP.md)

---

**Configuration terminée ?** Passez au [Guide de Démarrage Rapide](Quick-Start.md) pour commencer à utiliser l'outil.
