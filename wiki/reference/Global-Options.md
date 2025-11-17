# Options Globales et Variables d'Environnement

Guide complet des options globales CLI et de la configuration par variables d'environnement pour LDAP Health Monitor.

## 📑 Table des Matières

- [Options Globales CLI](#options-globales-cli)
- [Variables d'Environnement](#variables-denvironnement)
- [Fichiers de Configuration](#fichiers-de-configuration)
- [Ordre de Priorité](#ordre-de-priorité)
- [Exemples d'Usage](#exemples-dusage)
- [Meilleures Pratiques](#meilleures-pratiques)

## Options Globales CLI

Les options globales peuvent être utilisées avec n'importe quelle commande et doivent être placées **avant** le nom de la commande.

### --config, -c

Spécifie le chemin vers le fichier de configuration.

**Syntaxe** :
```bash
ldap-monitor --config PATH COMMAND
ldap-monitor -c PATH COMMAND
```

**Description** :
- Par défaut, l'outil recherche `config.yaml` dans le répertoire courant
- Permet d'utiliser plusieurs configurations (prod, dev, test)
- Le fichier doit exister et être accessible en lecture
- Support des formats YAML et JSON

**Exemples** :

```bash
# Configuration par défaut (./config.yaml)
ldap-monitor audit health

# Configuration personnalisée
ldap-monitor --config /etc/ldap-monitor/config.yaml audit health

# Configuration de production
ldap-monitor -c config.prod.yaml audit all

# Configuration de développement
ldap-monitor -c config.dev.yaml test connection

# Configuration absolue
ldap-monitor --config /home/user/ldap/prod-config.yaml monitor start

# Configuration relative
ldap-monitor --config ../configs/ldap.yaml audit users
```

**Cas d'Usage** :

```bash
# Environnements multiples
ldap-monitor -c config.prod.yaml audit all > audit-prod.json
ldap-monitor -c config.staging.yaml audit all > audit-staging.json
ldap-monitor -c config.dev.yaml audit all > audit-dev.json

# Tests avec différentes configurations
for config in configs/*.yaml; do
    echo "Testing $config..."
    ldap-monitor -c "$config" test connection
done

# Backup multi-environnements
ldap-monitor -c config.prod.yaml backup full -o prod-backup.ldif
ldap-monitor -c config.dev.yaml backup full -o dev-backup.ldif
```

**Erreurs Courantes** :

```bash
# ❌ Fichier inexistant
ldap-monitor --config nonexistent.yaml audit health
# Error: Path 'nonexistent.yaml' does not exist

# ❌ Permissions insuffisantes
ldap-monitor --config /root/secure-config.yaml audit health
# Error: Permission denied

# ✅ Vérifier l'existence avant
if [ -f config.prod.yaml ]; then
    ldap-monitor -c config.prod.yaml audit all
fi
```

---

### --verbose, -v

Active la sortie détaillée pour le débogage.

**Syntaxe** :
```bash
ldap-monitor --verbose COMMAND
ldap-monitor -v COMMAND
```

**Description** :
- Affiche des informations de débogage détaillées
- Utile pour diagnostiquer les problèmes de connexion
- Montre les requêtes LDAP envoyées
- Affiche les temps de réponse pour chaque opération
- Inclut les stack traces en cas d'erreur

**Exemples** :

```bash
# Mode verbeux simple
ldap-monitor --verbose audit health

# Mode verbeux avec configuration
ldap-monitor -v -c config.prod.yaml test connection

# Combinaison d'options
ldap-monitor --config /etc/ldap-monitor/config.yaml --verbose audit all

# Redirection du debug vers fichier
ldap-monitor -v audit users 2> debug.log

# Debug avec timestamp
ldap-monitor -v monitor metrics 2>&1 | ts '[%Y-%m-%d %H:%M:%S]'
```

**Sortie Standard (sans --verbose)** :
```
✅ Connection successful (42ms)
```

**Sortie Verbose (avec --verbose)** :
```
[DEBUG] Loading configuration from: config.yaml
[DEBUG] Connecting to: ldap.example.com:636
[DEBUG] Using SSL/TLS: True
[DEBUG] Bind DN: cn=admin,dc=example,dc=com
[DEBUG] Attempting connection...
[DEBUG] Connection established in 38ms
[DEBUG] Performing bind operation...
[DEBUG] Bind successful in 4ms
[DEBUG] Testing search operation...
[DEBUG] Search completed in 12ms
[DEBUG] Total response time: 42ms
✅ Connection successful (42ms)
[DEBUG] Closing connection...
[DEBUG] Connection closed
```

**Cas d'Usage** :

```bash
# Diagnostiquer un problème de connexion
ldap-monitor -v test connection 2>&1 | grep -i error

# Analyser les performances
ldap-monitor -v audit all 2>&1 | grep "completed in"

# Log complet d'une opération
ldap-monitor -v --config config.prod.yaml monitor start &> monitor.log

# Debug d'un audit spécifique
ldap-monitor -v audit users --inactive 2>&1 | tee debug-users.log
```

---

### --help

Affiche l'aide pour une commande.

**Syntaxe** :
```bash
ldap-monitor --help
ldap-monitor COMMAND --help
ldap-monitor COMMAND SUBCOMMAND --help
```

**Description** :
- Affiche la syntaxe et les options disponibles
- Fonctionne à tous les niveaux (global, commande, sous-commande)
- Inclut des exemples d'usage
- Liste toutes les options et leurs valeurs par défaut

**Exemples** :

```bash
# Aide globale
ldap-monitor --help

# Aide pour une commande principale
ldap-monitor audit --help
ldap-monitor monitor --help
ldap-monitor backup --help

# Aide pour une sous-commande
ldap-monitor audit users --help
ldap-monitor config init --help
ldap-monitor group search --help

# Aide sur les options globales
ldap-monitor --help | grep -A 10 "Global Options"
```

**Sortie Exemple** :
```
Usage: ldap-monitor [OPTIONS] COMMAND [ARGS]...

  LDAP Health Monitor - Audit, monitor, and manage LDAP servers.

Options:
  --config, -c PATH  Path to configuration file
  --verbose, -v      Verbose output
  --help             Show this message and exit

Commands:
  audit    Audit LDAP directory
  backup   Backup and export commands
  cleanup  Cleanup and maintenance commands
  config   Configuration management commands
  export   Export data commands
  group    Group management commands
  monitor  Monitor LDAP server
  test     Test commands
  user     User management commands
  version  Show version information
```

---

## Variables d'Environnement

Les variables d'environnement permettent de configurer des valeurs sensibles sans les inclure dans les fichiers de configuration.

### Variables de Configuration LDAP

#### LDAP_BIND_DN

Distinguished Name pour l'authentification LDAP.

**Syntaxe** :
```bash
export LDAP_BIND_DN="cn=admin,dc=example,dc=com"
```

**Usage dans config.yaml** :
```yaml
ldap:
  bind_dn: "${LDAP_BIND_DN}"
```

**Exemples** :

```bash
# Configuration simple
export LDAP_BIND_DN="cn=admin,dc=example,dc=com"
ldap-monitor test connection

# Configuration avec utilisateur de lecture seule
export LDAP_BIND_DN="cn=readonly,dc=example,dc=com"
ldap-monitor audit all

# Configuration pour Active Directory
export LDAP_BIND_DN="CN=Service Account,OU=Service Accounts,DC=domain,DC=com"
ldap-monitor monitor start
```

---

#### LDAP_BIND_PASSWORD

Mot de passe pour l'authentification LDAP.

**Syntaxe** :
```bash
export LDAP_BIND_PASSWORD="votre_mot_de_passe_securise"
```

**Usage dans config.yaml** :
```yaml
ldap:
  bind_password: "${LDAP_BIND_PASSWORD}"
```

**Exemples** :

```bash
# Configuration directe (déconseillé en production)
export LDAP_BIND_PASSWORD="MyPassword123!"

# Lecture depuis fichier sécurisé
export LDAP_BIND_PASSWORD=$(cat /secure/ldap-password.txt)

# Lecture depuis vault (exemple avec HashiCorp Vault)
export LDAP_BIND_PASSWORD=$(vault kv get -field=password secret/ldap)

# Demande interactive
read -sp "LDAP Password: " LDAP_BIND_PASSWORD
export LDAP_BIND_PASSWORD

# Avec AWS Secrets Manager
export LDAP_BIND_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id ldap-password \
    --query SecretString \
    --output text)
```

**Sécurité** :

```bash
# ⚠️ DANGER : Ne jamais faire
echo "export LDAP_BIND_PASSWORD=secret123" >> ~/.bashrc

# ✅ RECOMMANDÉ : Utiliser un fichier .env gitignored
cat > .env << 'EOF'
LDAP_BIND_PASSWORD=secret123
EOF
chmod 600 .env
source .env

# ✅ Vérifier que la variable n'est pas dans l'historique
export HISTCONTROL=ignorespace
 export LDAP_BIND_PASSWORD="secret"  # Note l'espace au début
```

---

#### LDAP_SERVER

Adresse du serveur LDAP.

**Syntaxe** :
```bash
export LDAP_SERVER="ldap.example.com"
```

**Exemples** :

```bash
# Serveur simple
export LDAP_SERVER="ldap.example.com"

# Avec IP
export LDAP_SERVER="192.168.1.100"

# Active Directory
export LDAP_SERVER="ad.domain.local"

# Multiple servers (failover)
export LDAP_SERVER="ldap1.example.com,ldap2.example.com"
```

---

#### LDAP_PORT

Port du serveur LDAP.

**Syntaxe** :
```bash
export LDAP_PORT="636"
```

**Valeurs courantes** :
- `389` : LDAP non sécurisé (déconseillé)
- `636` : LDAPS (LDAP over SSL)
- `3268` : Active Directory Global Catalog
- `3269` : Active Directory Global Catalog (SSL)

**Exemples** :

```bash
# LDAPS (recommandé)
export LDAP_PORT="636"

# LDAP with StartTLS
export LDAP_PORT="389"

# Active Directory Global Catalog
export LDAP_PORT="3268"
```

---

#### LDAP_BASE_DN

Base DN pour les recherches LDAP.

**Syntaxe** :
```bash
export LDAP_BASE_DN="dc=example,dc=com"
```

**Exemples** :

```bash
# Organisation simple
export LDAP_BASE_DN="dc=example,dc=com"

# Sous-organisation
export LDAP_BASE_DN="ou=company,dc=example,dc=com"

# Active Directory
export LDAP_BASE_DN="DC=domain,DC=local"

# Multi-domaine
export LDAP_BASE_DN="DC=child,DC=parent,DC=com"
```

---

### Variables d'Alertes

#### SLACK_WEBHOOK_URL

URL du webhook Slack pour les alertes.

**Syntaxe** :
```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

**Usage dans config.yaml** :
```yaml
alerts:
  slack:
    enabled: true
    webhook_url: "${SLACK_WEBHOOK_URL}"
    channel: "#ldap-alerts"
```

**Exemples** :

```bash
# Configuration simple
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN"

# Lecture depuis fichier
export SLACK_WEBHOOK_URL=$(cat /secure/slack-webhook.txt)

# Test de webhook
curl -X POST "$SLACK_WEBHOOK_URL" \
    -H 'Content-Type: application/json' \
    -d '{"text":"Test alert from LDAP Monitor"}'
```

---

#### SMTP_PASSWORD

Mot de passe pour l'authentification SMTP (alertes email).

**Syntaxe** :
```bash
export SMTP_PASSWORD="votre_mot_de_passe_email"
```

**Usage dans config.yaml** :
```yaml
alerts:
  email:
    enabled: true
    smtp_password: "${SMTP_PASSWORD}"
```

**Exemples** :

```bash
# Gmail App Password
export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"

# Office 365
export SMTP_PASSWORD="your-o365-password"

# Depuis AWS Secrets Manager
export SMTP_PASSWORD=$(aws secretsmanager get-secret-value \
    --secret-id smtp-password \
    --query SecretString \
    --output text)
```

---

### Variables d'Intégration

#### N8N_WEBHOOK_URL

URL du webhook n8n pour les intégrations.

**Syntaxe** :
```bash
export N8N_WEBHOOK_URL="https://n8n.example.com/webhook/ldap-monitor"
```

**Usage dans config.yaml** :
```yaml
integrations:
  n8n:
    enabled: true
    webhook_url: "${N8N_WEBHOOK_URL}"
```

---

#### PROMETHEUS_PORT

Port pour le serveur de métriques Prometheus.

**Syntaxe** :
```bash
export PROMETHEUS_PORT="9090"
```

**Usage dans config.yaml** :
```yaml
integrations:
  prometheus:
    enabled: true
    port: "${PROMETHEUS_PORT}"
```

---

## Fichiers de Configuration

### Fichier .env

Le fichier `.env` permet de définir toutes les variables d'environnement en un seul endroit.

**Emplacement** :
- `./.env` (répertoire courant)
- `~/.config/ldap-monitor/.env` (configuration utilisateur)
- `/etc/ldap-monitor/.env` (configuration système)

**Exemple de fichier .env** :

```bash
# Configuration LDAP
LDAP_SERVER=ldap.example.com
LDAP_PORT=636
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BIND_PASSWORD=VotreMotDePasseSecurise123!
LDAP_BASE_DN=dc=example,dc=com

# Alertes Slack
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN
SLACK_CHANNEL=#ldap-alerts

# Alertes Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@example.com
SMTP_PASSWORD=your-app-password

# Intégrations
N8N_WEBHOOK_URL=https://n8n.example.com/webhook/ldap
PROMETHEUS_PORT=9090

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/ldap-monitor/monitor.log
```

**Chargement du fichier .env** :

```bash
# Méthode 1 : source direct
source .env
ldap-monitor audit health

# Méthode 2 : avec export explicite
set -a
source .env
set +a
ldap-monitor monitor start

# Méthode 3 : dotenv dans script Python
# Automatiquement chargé si python-dotenv est installé

# Méthode 4 : avec docker-compose
docker-compose --env-file .env up
```

**Sécurité du fichier .env** :

```bash
# ✅ Permissions restrictives
chmod 600 .env
chown $USER:$USER .env

# ✅ Vérifier qu'il est dans .gitignore
grep "^\.env$" .gitignore

# ✅ Template pour l'équipe (sans secrets)
cp .env .env.example
# Éditer .env.example et supprimer les valeurs sensibles
```

---

## Ordre de Priorité

Les valeurs de configuration sont résolues dans l'ordre suivant (du plus prioritaire au moins prioritaire) :

1. **Options CLI** : `--config`, `--verbose`
2. **Variables d'environnement** : `LDAP_SERVER`, `LDAP_PASSWORD`, etc.
3. **Fichier .env** : Variables chargées depuis `.env`
4. **Fichier de configuration** : `config.yaml`
5. **Valeurs par défaut** : Valeurs codées en dur

**Exemple** :

```yaml
# config.yaml
ldap:
  server: "default-ldap.example.com"
  port: 389
  bind_dn: "${LDAP_BIND_DN}"
```

```bash
# Fichier .env
LDAP_SERVER=env-ldap.example.com
LDAP_PORT=636
```

```bash
# Ligne de commande
export LDAP_BIND_DN="cn=admin,dc=example,dc=com"
ldap-monitor --config custom-config.yaml test connection

# Résolution finale :
# - server: "env-ldap.example.com" (depuis .env)
# - port: 636 (depuis .env)
# - bind_dn: "cn=admin,dc=example,dc=com" (depuis export)
# - config file: custom-config.yaml (depuis --config)
```

---

## Exemples d'Usage

### Configuration Multi-Environnement

```bash
#!/bin/bash
# deploy-multi-env.sh

# Fonction pour charger l'environnement
load_env() {
    local env=$1
    source ".env.${env}"
    export LDAP_ENV=$env
}

# Production
load_env "prod"
ldap-monitor -c config.prod.yaml audit all \
    --format html \
    --output reports/audit-prod-$(date +%Y%m%d).html

# Staging
load_env "staging"
ldap-monitor -c config.staging.yaml audit all \
    --format html \
    --output reports/audit-staging-$(date +%Y%m%d).html

# Development
load_env "dev"
ldap-monitor -c config.dev.yaml test connection
```

### Script avec Variables d'Environnement

```bash
#!/bin/bash
# ldap-monitor-wrapper.sh

# Vérifier les variables requises
required_vars=(
    "LDAP_SERVER"
    "LDAP_BIND_DN"
    "LDAP_BIND_PASSWORD"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set"
        exit 1
    fi
done

# Charger la configuration
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Exécuter avec options
ldap-monitor \
    --config "${LDAP_CONFIG:-config.yaml}" \
    ${LDAP_VERBOSE:+--verbose} \
    "$@"
```

### Configuration avec Vault

```bash
#!/bin/bash
# vault-ldap-monitor.sh

# Authentification Vault
vault login -method=token token="$VAULT_TOKEN"

# Récupérer les secrets
export LDAP_BIND_DN=$(vault kv get -field=bind_dn secret/ldap)
export LDAP_BIND_PASSWORD=$(vault kv get -field=password secret/ldap)
export SLACK_WEBHOOK_URL=$(vault kv get -field=webhook secret/slack)

# Exécuter l'audit
ldap-monitor audit all --format json --output audit-$(date +%Y%m%d).json

# Nettoyer les variables
unset LDAP_BIND_DN LDAP_BIND_PASSWORD SLACK_WEBHOOK_URL
```

---

## Meilleures Pratiques

### Sécurité

```bash
# ✅ Utiliser des fichiers .env avec permissions restrictives
chmod 600 .env

# ✅ Ne jamais commiter les secrets
echo ".env" >> .gitignore
echo "config.yaml" >> .gitignore

# ✅ Utiliser un gestionnaire de secrets
# HashiCorp Vault, AWS Secrets Manager, Azure Key Vault

# ✅ Rotation régulière des mots de passe
# Automatiser avec scripts ou outils de gestion

# ❌ Ne jamais logger les mots de passe
# Même en mode verbose
```

### Organisation

```bash
# Structure recommandée
project/
├── .env                    # Gitignored, local uniquement
├── .env.example           # Template pour l'équipe
├── config.yaml            # Gitignored, configuration locale
├── config.example.yaml    # Template de configuration
├── configs/
│   ├── prod.yaml         # Références aux variables d'env
│   ├── staging.yaml
│   └── dev.yaml
└── scripts/
    ├── load-env.sh       # Helper pour charger .env
    └── run-audit.sh      # Wrapper avec variables
```

### Variables d'Environnement Recommandées

```bash
# Définir dans ~/.bashrc ou ~/.zshrc pour usage fréquent
export LDAP_MONITOR_CONFIG_DIR="${HOME}/.config/ldap-monitor"
export LDAP_MONITOR_DATA_DIR="${HOME}/.local/share/ldap-monitor"
export LDAP_MONITOR_CACHE_DIR="${HOME}/.cache/ldap-monitor"

# Alias utiles
alias ldap-prod='ldap-monitor -c $LDAP_MONITOR_CONFIG_DIR/prod.yaml'
alias ldap-dev='ldap-monitor -c $LDAP_MONITOR_CONFIG_DIR/dev.yaml'
alias ldap-test='ldap-monitor -c $LDAP_MONITOR_CONFIG_DIR/test.yaml'
```

---

## Voir Aussi

- [Commandes CLI](CLI-Commands.md) - Référence complète des commandes
- [Formats d'Export](Export-Formats.md) - Spécifications des formats
- [Codes de Sortie](Exit-Codes.md) - Codes de retour
- [Configuration](../configuration/Config-File-Structure.md) - Structure YAML
- [Sécurité](../../docs/SECURITY.md) - Guide de sécurité

---

**Note de Sécurité** : Ne jamais exposer les variables d'environnement contenant des secrets dans les logs, l'historique de commandes, ou les commits Git. Utilisez toujours des gestionnaires de secrets pour la production.
