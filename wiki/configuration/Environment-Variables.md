# Variables d'Environnement

## Table des Matières

- [Introduction](#introduction)
- [Variables Requises](#variables-requises)
- [Variables Optionnelles](#variables-optionnelles)
- [Configuration par Environnement](#configuration-par-environnement)
- [Méthodes de Configuration](#méthodes-de-configuration)
- [Sécurité et Bonnes Pratiques](#sécurité-et-bonnes-pratiques)
- [Gestion des Secrets](#gestion-des-secrets)
- [Intégrations](#intégrations)
- [Exemples Complets](#exemples-complets)
- [Dépannage](#dépannage)

## Introduction

Les variables d'environnement permettent de configurer LDAP Health Monitor sans exposer les informations sensibles dans les fichiers de configuration. Cette approche est essentielle pour la sécurité et la portabilité de l'application.

### Pourquoi Utiliser des Variables d'Environnement ?

1. **Sécurité** : Les secrets ne sont pas stockés dans le code source
2. **Flexibilité** : Configuration différente par environnement
3. **Conformité** : Respect des bonnes pratiques DevSecOps
4. **CI/CD** : Facilite les déploiements automatisés
5. **Rotation** : Changement facile des credentials

### Syntaxe dans config.yaml

```yaml
# Référence à une variable d'environnement
bind_password: ${LDAP_PASSWORD}

# Avec valeur par défaut (si variable non définie)
bind_password: ${LDAP_PASSWORD:-default_password}

# Variable obligatoire (erreur si non définie)
bind_password: ${LDAP_PASSWORD:?Variable LDAP_PASSWORD requise}
```

## Variables Requises

Ces variables doivent être définies pour le fonctionnement de base.

### LDAP_PASSWORD

Mot de passe pour l'authentification LDAP.

```bash
export LDAP_PASSWORD="VotreMotDePasseSecurise123!"
```

**Utilisé dans :**
```yaml
ldap:
  bind_password: ${LDAP_PASSWORD}
```

**Bonnes pratiques :**
- Minimum 16 caractères
- Caractères spéciaux, majuscules, minuscules, chiffres
- Rotation tous les 90 jours
- Stockage sécurisé (vault, gestionnaire de secrets)

**Exemple sécurisé :**
```bash
# Génération d'un mot de passe fort
LDAP_PASSWORD=$(openssl rand -base64 32)
export LDAP_PASSWORD

# Vérification
echo "Mot de passe défini: ${LDAP_PASSWORD:0:4}****"
```

### LDAP_BIND_DN (Optionnel mais recommandé)

Distinguished Name pour l'authentification.

```bash
export LDAP_BIND_DN="cn=svc-monitor,ou=services,dc=example,dc=com"
```

**Utilisé dans :**
```yaml
ldap:
  bind_dn: ${LDAP_BIND_DN}
```

### LDAP_SERVER

Serveur LDAP à monitorer.

```bash
export LDAP_SERVER="ldaps://ldap.example.com"
```

**Exemples :**
```bash
# LDAP standard
export LDAP_SERVER="ldap://192.168.1.100"

# LDAPS (recommandé)
export LDAP_SERVER="ldaps://ldap.company.com"

# Avec port personnalisé
export LDAP_SERVER="ldaps://ldap.company.com:3636"

# Active Directory
export LDAP_SERVER="ldaps://dc01.domain.local"
```

## Variables Optionnelles

### Variables SMTP (Email)

Configuration pour l'envoi d'emails.

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="alerts@example.com"
export SMTP_PASSWORD="MotDePasseApplication123"
export SMTP_FROM="ldap-monitor@example.com"
export SMTP_TO="admin@example.com,team@example.com"
```

**Configuration Gmail :**
```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT="587"
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="xxxx xxxx xxxx xxxx"  # App password
```

**Configuration Office 365 :**
```bash
export SMTP_HOST="smtp.office365.com"
export SMTP_PORT="587"
export SMTP_USER="alerts@company.onmicrosoft.com"
export SMTP_PASSWORD="YourPassword123!"
```

**Configuration SMTP personnalisé :**
```bash
export SMTP_HOST="mail.company.com"
export SMTP_PORT="465"
export SMTP_USE_SSL="true"
export SMTP_USER="ldap-alerts"
export SMTP_PASSWORD="SecurePass123!"
```

### Variables Slack

Configuration pour les alertes Slack.

```bash
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN"
export SLACK_CHANNEL="#ldap-alerts"
export SLACK_USERNAME="LDAP Monitor"
```

**Obtenir un Webhook Slack :**

1. Aller sur : https://api.slack.com/apps
2. Créer une nouvelle app ou sélectionner existante
3. Activer "Incoming Webhooks"
4. Créer un nouveau webhook
5. Copier l'URL du webhook

**Exemples de configuration :**
```bash
# Production
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKENabc123"
export SLACK_CHANNEL="#prod-ldap-alerts"
export SLACK_MENTION_CRITICAL="@oncall"

# Développement
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKENdef456"
export SLACK_CHANNEL="#dev-alerts"
export SLACK_MENTION_CRITICAL=""
```

### Variables Webhook Générique

Pour les intégrations personnalisées (n8n, Zapier, etc.).

```bash
export WEBHOOK_URL="https://n8n.company.com/webhook/ldap-alerts"
export WEBHOOK_METHOD="POST"
export WEBHOOK_AUTH_TOKEN="Bearer xyz123abc456"
```

**Exemples :**

**n8n :**
```bash
export N8N_WEBHOOK="https://n8n.example.com/webhook/ldap-monitor"
export N8N_AUTH_TOKEN="your-secret-token"
```

**Zapier :**
```bash
export ZAPIER_WEBHOOK="https://hooks.zapier.com/hooks/catch/123456/abcdef/"
```

**Custom API :**
```bash
export CUSTOM_WEBHOOK="https://api.company.com/webhooks/ldap"
export CUSTOM_WEBHOOK_TOKEN="sk_live_abc123def456"
export CUSTOM_WEBHOOK_HEADER="X-API-Key: ${CUSTOM_WEBHOOK_TOKEN}"
```

### Variables Prometheus

Configuration pour l'export de métriques Prometheus.

```bash
export PROMETHEUS_PORT="9090"
export PROMETHEUS_HOST="0.0.0.0"
export PROMETHEUS_PATH="/metrics"
```

**Configuration complète :**
```bash
# Port d'écoute
export PROMETHEUS_PORT="9090"

# Interface (0.0.0.0 = toutes, 127.0.0.1 = local uniquement)
export PROMETHEUS_HOST="0.0.0.0"

# Chemin des métriques
export PROMETHEUS_PATH="/metrics"

# Authentification (optionnel)
export PROMETHEUS_AUTH_USER="prometheus"
export PROMETHEUS_AUTH_PASSWORD="SecurePass123!"
```

### Variables de Backup

Configuration des chemins de sauvegarde.

```bash
export BACKUP_DIR="/var/backups/ldap-monitor"
export BACKUP_RETENTION_DAYS="90"
export BACKUP_S3_BUCKET="s3://company-backups/ldap"
```

**Backup local :**
```bash
export BACKUP_DIR="/opt/ldap-monitor/backups"
export BACKUP_COMPRESS="true"
export BACKUP_FORMAT="ldif"
```

**Backup S3 :**
```bash
export BACKUP_S3_BUCKET="my-company-backups"
export BACKUP_S3_PREFIX="ldap-monitor/"
export AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"
export AWS_SECRET_ACCESS_KEY="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
export AWS_DEFAULT_REGION="eu-west-1"
```

**Backup Azure :**
```bash
export AZURE_STORAGE_ACCOUNT="companybackups"
export AZURE_STORAGE_KEY="YourStorageKey=="
export AZURE_CONTAINER="ldap-backups"
```

## Configuration par Environnement

### Fichiers .env par Environnement

Créez des fichiers `.env` séparés pour chaque environnement.

**Structure recommandée :**
```
.env.development
.env.staging
.env.production
.env.local (pour tests locaux, gitignored)
```

### .env.development

```bash
# LDAP
LDAP_SERVER="ldap://localhost:389"
LDAP_BIND_DN="cn=admin,dc=example,dc=com"
LDAP_PASSWORD="admin"
LDAP_BASE_DN="dc=example,dc=com"

# Monitoring
MONITORING_ENABLED="true"
MONITORING_INTERVAL="600"

# Alerts (désactivées en dev)
SLACK_ENABLED="false"
EMAIL_ENABLED="false"

# Logging
LOG_LEVEL="DEBUG"
LOG_FILE="./logs/dev.log"

# Backup
BACKUP_DIR="./backups/dev"
BACKUP_ENABLED="false"
```

### .env.staging

```bash
# LDAP
LDAP_SERVER="ldaps://ldap-staging.company.com"
LDAP_BIND_DN="cn=svc-monitor-stg,ou=services,dc=company,dc=com"
LDAP_PASSWORD="${STAGING_LDAP_PASSWORD}"
LDAP_BASE_DN="dc=company,dc=com"

# Monitoring
MONITORING_ENABLED="true"
MONITORING_INTERVAL="300"

# Alerts
SLACK_ENABLED="true"
SLACK_WEBHOOK="${STAGING_SLACK_WEBHOOK}"
SLACK_CHANNEL="#staging-alerts"

EMAIL_ENABLED="true"
SMTP_HOST="smtp.company.com"
SMTP_USER="${STAGING_SMTP_USER}"
SMTP_PASSWORD="${STAGING_SMTP_PASSWORD}"
SMTP_TO="dev-team@company.com"

# Logging
LOG_LEVEL="INFO"
LOG_FILE="/var/log/ldap-monitor/staging.log"

# Backup
BACKUP_DIR="/backups/ldap-monitor/staging"
BACKUP_ENABLED="true"
BACKUP_RETENTION_DAYS="30"
```

### .env.production

```bash
# LDAP
LDAP_SERVER="ldaps://ldap.company.com"
LDAP_BIND_DN="cn=svc-ldap-monitor,ou=services,dc=company,dc=com"
LDAP_PASSWORD="${VAULT_LDAP_PASSWORD}"
LDAP_BASE_DN="dc=company,dc=com"

# Monitoring
MONITORING_ENABLED="true"
MONITORING_INTERVAL="60"
MONITORING_RETENTION_DAYS="365"

# Alerts
SLACK_ENABLED="true"
SLACK_WEBHOOK="${PROD_SLACK_WEBHOOK}"
SLACK_CHANNEL="#prod-ldap-alerts"
SLACK_MENTION_CRITICAL="@oncall"

EMAIL_ENABLED="true"
SMTP_HOST="smtp.company.com"
SMTP_USER="${PROD_SMTP_USER}"
SMTP_PASSWORD="${PROD_SMTP_PASSWORD}"
SMTP_TO="ops-team@company.com,ldap-admins@company.com"

# Logging
LOG_LEVEL="WARNING"
LOG_FILE="/var/log/ldap-monitor/production.log"
LOG_MAX_BYTES="52428800"  # 50MB
LOG_BACKUP_COUNT="20"

# Backup
BACKUP_DIR="/var/backups/ldap-monitor"
BACKUP_ENABLED="true"
BACKUP_RETENTION_DAYS="90"
BACKUP_S3_ENABLED="true"
BACKUP_S3_BUCKET="company-prod-backups"

# Prometheus
PROMETHEUS_ENABLED="true"
PROMETHEUS_PORT="9090"
PROMETHEUS_HOST="127.0.0.1"
```

## Méthodes de Configuration

### Méthode 1 : Fichier .env

Le plus simple pour le développement local.

```bash
# Créer le fichier .env
cat > .env << 'EOF'
LDAP_SERVER="ldap://localhost"
LDAP_PASSWORD="admin"
SLACK_WEBHOOK="https://hooks.slack.com/..."
EOF

# Charger les variables
export $(cat .env | xargs)

# Ou avec direnv (recommandé)
echo "export LDAP_PASSWORD='secret'" > .envrc
direnv allow
```

### Méthode 2 : Export Direct

Pour les tests rapides.

```bash
export LDAP_PASSWORD="MonMotDePasse123!"
export SLACK_WEBHOOK="https://hooks.slack.com/services/..."

# Vérifier
echo $LDAP_PASSWORD
```

### Méthode 3 : Script de Configuration

Créer un script `env.sh` :

```bash
#!/bin/bash
# env.sh - Configuration des variables d'environnement

# LDAP Configuration
export LDAP_SERVER="ldaps://ldap.company.com"
export LDAP_BIND_DN="cn=monitor,dc=company,dc=com"
export LDAP_PASSWORD="${VAULT_LDAP_PASSWORD:-changeme}"

# Alerts
export SLACK_WEBHOOK="${SLACK_WEBHOOK:-}"
export SMTP_PASSWORD="${SMTP_PASSWORD:-}"

# Source depuis un vault si disponible
if [ -f "/etc/secrets/ldap-monitor.env" ]; then
    source /etc/secrets/ldap-monitor.env
fi

echo "Variables d'environnement chargées"
```

**Utilisation :**
```bash
source env.sh
ldap-health-monitor audit
```

### Méthode 4 : Docker / Docker Compose

**Fichier docker-compose.yml :**

```yaml
version: '3.8'

services:
  ldap-monitor:
    image: ldap-health-monitor:latest
    environment:
      - LDAP_SERVER=${LDAP_SERVER}
      - LDAP_PASSWORD=${LDAP_PASSWORD}
      - SLACK_WEBHOOK=${SLACK_WEBHOOK}
    env_file:
      - .env.production
    volumes:
      - ./config.yaml:/app/config.yaml:ro
      - ./backups:/app/backups
```

**Avec secrets Docker :**

```yaml
version: '3.8'

services:
  ldap-monitor:
    image: ldap-health-monitor:latest
    environment:
      - LDAP_SERVER=ldaps://ldap.company.com
    secrets:
      - ldap_password
      - slack_webhook
    env_file:
      - .env

secrets:
  ldap_password:
    file: ./secrets/ldap_password.txt
  slack_webhook:
    file: ./secrets/slack_webhook.txt
```

### Méthode 5 : Kubernetes Secrets

**Secret Kubernetes :**

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ldap-monitor-secrets
type: Opaque
stringData:
  ldap-password: "VotreMotDePasse123!"
  slack-webhook: "https://hooks.slack.com/services/..."
  smtp-password: "SmtpPassword123!"
```

**Déploiement :**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ldap-monitor
spec:
  template:
    spec:
      containers:
      - name: ldap-monitor
        image: ldap-health-monitor:latest
        env:
        - name: LDAP_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ldap-monitor-secrets
              key: ldap-password
        - name: SLACK_WEBHOOK
          valueFrom:
            secretKeyRef:
              name: ldap-monitor-secrets
              key: slack-webhook
```

### Méthode 6 : Gestionnaires de Secrets

**HashiCorp Vault :**

```bash
# Stocker dans Vault
vault kv put secret/ldap-monitor \
    ldap_password="SecurePassword123!" \
    slack_webhook="https://hooks.slack.com/..."

# Récupérer et exporter
export LDAP_PASSWORD=$(vault kv get -field=ldap_password secret/ldap-monitor)
export SLACK_WEBHOOK=$(vault kv get -field=slack_webhook secret/ldap-monitor)
```

**AWS Secrets Manager :**

```bash
# Créer le secret
aws secretsmanager create-secret \
    --name ldap-monitor/prod \
    --secret-string '{"ldap_password":"Secret123!","slack_webhook":"https://..."}'

# Script pour charger
#!/bin/bash
SECRET=$(aws secretsmanager get-secret-value \
    --secret-id ldap-monitor/prod \
    --query SecretString \
    --output text)

export LDAP_PASSWORD=$(echo $SECRET | jq -r '.ldap_password')
export SLACK_WEBHOOK=$(echo $SECRET | jq -r '.slack_webhook')
```

**Azure Key Vault :**

```bash
# Créer les secrets
az keyvault secret set --vault-name ldap-monitor-kv \
    --name ldap-password --value "SecurePassword123!"

# Récupérer
export LDAP_PASSWORD=$(az keyvault secret show \
    --vault-name ldap-monitor-kv \
    --name ldap-password \
    --query value -o tsv)
```

## Sécurité et Bonnes Pratiques

### Protection des Variables

**1. Permissions Fichiers**

```bash
# Fichier .env lisible uniquement par le propriétaire
chmod 600 .env
chown ldap-monitor:ldap-monitor .env

# Vérification
ls -la .env
# Output: -rw------- 1 ldap-monitor ldap-monitor
```

**2. .gitignore**

```gitignore
# Ne jamais commiter ces fichiers
.env
.env.local
.env.*.local
config.yaml
secrets/
*.key
*.pem
```

**3. Rotation des Secrets**

```bash
#!/bin/bash
# rotate-secrets.sh - Rotation automatique des secrets

OLD_PASSWORD=$LDAP_PASSWORD
NEW_PASSWORD=$(openssl rand -base64 32)

# Changer dans LDAP
ldappasswd -H $LDAP_SERVER \
    -D "$LDAP_BIND_DN" \
    -w "$OLD_PASSWORD" \
    -s "$NEW_PASSWORD"

# Mettre à jour le secret
vault kv put secret/ldap-monitor ldap_password="$NEW_PASSWORD"

echo "Secret rotated successfully"
```

### Validation des Variables

**Script de validation :**

```bash
#!/bin/bash
# validate-env.sh - Valide les variables requises

REQUIRED_VARS=(
    "LDAP_SERVER"
    "LDAP_PASSWORD"
    "LDAP_BIND_DN"
)

MISSING=()

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING+=("$var")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo "ERREUR: Variables manquantes:"
    printf '  - %s\n' "${MISSING[@]}"
    exit 1
fi

echo "Toutes les variables requises sont définies"
```

### Masquage dans les Logs

```python
# Exemple de masquage dans le code
import re

def mask_sensitive_data(log_message):
    """Masque les données sensibles dans les logs."""
    # Masquer les mots de passe
    log_message = re.sub(
        r'(password["\s:=]+)([^\s"]+)',
        r'\1****',
        log_message,
        flags=re.IGNORECASE
    )
    # Masquer les tokens
    log_message = re.sub(
        r'(token["\s:=]+)([^\s"]+)',
        r'\1****',
        log_message,
        flags=re.IGNORECASE
    )
    return log_message
```

## Gestion des Secrets

### Approche par Niveau

**Niveau 1 : Développement Local**
- Fichier `.env.local`
- Secrets en clair (acceptable pour dev)
- Non commité dans Git

**Niveau 2 : CI/CD**
- Variables d'environnement dans CI
- Secrets chiffrés dans le pipeline
- Rotation manuelle

**Niveau 3 : Staging**
- Gestionnaire de secrets (Vault, AWS Secrets Manager)
- Rotation semi-automatique
- Audit logs

**Niveau 4 : Production**
- Gestionnaire de secrets centralisé
- Rotation automatique
- Audit complet
- Alertes sur accès

### Template de Secrets

**secrets.template.env :**

```bash
# LDAP Configuration
LDAP_SERVER="ldaps://your-ldap-server.com"
LDAP_BIND_DN="cn=service-account,dc=example,dc=com"
LDAP_PASSWORD="CHANGEME"

# Email Configuration
SMTP_HOST="smtp.example.com"
SMTP_USER="alerts@example.com"
SMTP_PASSWORD="CHANGEME"

# Slack Configuration
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Instructions:
# 1. Copier ce fichier: cp secrets.template.env .env
# 2. Remplacer les valeurs CHANGEME
# 3. Ne jamais commiter .env
```

## Intégrations

### CI/CD GitLab

**.gitlab-ci.yml :**

```yaml
variables:
  LDAP_SERVER: "ldaps://ldap.company.com"

deploy:
  stage: deploy
  script:
    - export LDAP_PASSWORD="$CI_LDAP_PASSWORD"
    - export SLACK_WEBHOOK="$CI_SLACK_WEBHOOK"
    - ./deploy.sh
  only:
    - main
```

### CI/CD GitHub Actions

**.github/workflows/deploy.yml :**

```yaml
name: Deploy LDAP Monitor

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Configure environment
        env:
          LDAP_PASSWORD: ${{ secrets.LDAP_PASSWORD }}
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        run: |
          echo "LDAP_SERVER=ldaps://ldap.company.com" >> $GITHUB_ENV
          ./deploy.sh
```

### Terraform

```hcl
# variables.tf
variable "ldap_password" {
  type      = string
  sensitive = true
}

# main.tf
resource "kubernetes_secret" "ldap_monitor" {
  metadata {
    name = "ldap-monitor-secrets"
  }

  data = {
    ldap-password = var.ldap_password
    slack-webhook = var.slack_webhook
  }
}
```

## Exemples Complets

### Exemple Production Complète

```bash
#!/bin/bash
# production-env.sh

# LDAP Configuration
export LDAP_SERVER="ldaps://ldap.company.com:636"
export LDAP_BIND_DN="cn=svc-ldap-monitor,ou=services,dc=company,dc=com"
export LDAP_PASSWORD="$(vault kv get -field=password secret/ldap/monitor)"
export LDAP_BASE_DN="dc=company,dc=com"
export LDAP_USERS_OU="ou=users,dc=company,dc=com"
export LDAP_GROUPS_OU="ou=groups,dc=company,dc=com"

# Monitoring
export MONITORING_ENABLED="true"
export MONITORING_INTERVAL="60"
export MONITORING_RETENTION_DAYS="365"

# Alerts - Slack
export SLACK_ENABLED="true"
export SLACK_WEBHOOK="$(vault kv get -field=webhook secret/slack/ldap-alerts)"
export SLACK_CHANNEL="#prod-ldap-alerts"
export SLACK_USERNAME="LDAP Monitor"
export SLACK_MENTION_CRITICAL="@oncall"

# Alerts - Email
export EMAIL_ENABLED="true"
export SMTP_HOST="smtp.company.com"
export SMTP_PORT="587"
export SMTP_USE_TLS="true"
export SMTP_USER="ldap-alerts@company.com"
export SMTP_PASSWORD="$(vault kv get -field=password secret/smtp/ldap-alerts)"
export SMTP_FROM="ldap-monitor@company.com"
export SMTP_TO="ops-team@company.com,ldap-admins@company.com"

# Backup
export BACKUP_ENABLED="true"
export BACKUP_DIR="/var/backups/ldap-monitor"
export BACKUP_RETENTION_DAYS="90"
export BACKUP_S3_ENABLED="true"
export BACKUP_S3_BUCKET="company-prod-backups"
export AWS_ACCESS_KEY_ID="$(vault kv get -field=access_key secret/aws/backups)"
export AWS_SECRET_ACCESS_KEY="$(vault kv get -field=secret_key secret/aws/backups)"
export AWS_DEFAULT_REGION="eu-west-1"

# Prometheus
export PROMETHEUS_ENABLED="true"
export PROMETHEUS_PORT="9090"
export PROMETHEUS_HOST="127.0.0.1"

# Logging
export LOG_LEVEL="INFO"
export LOG_FILE="/var/log/ldap-monitor/production.log"
export LOG_MAX_BYTES="52428800"
export LOG_BACKUP_COUNT="20"

echo "Production environment configured"
```

## Dépannage

### Variables Non Définies

```bash
# Vérifier si une variable est définie
if [ -z "$LDAP_PASSWORD" ]; then
    echo "ERREUR: LDAP_PASSWORD non définie"
    exit 1
fi

# Lister toutes les variables LDAP
env | grep LDAP

# Afficher (masqué)
echo "Password: ${LDAP_PASSWORD:0:4}****"
```

### Problèmes d'Expansion

```bash
# Problème: Variable non expandée
bind_password: ${LDAP_PASSWORD}  # Reste littéral

# Solution 1: Utiliser envsubst
envsubst < config.template.yaml > config.yaml

# Solution 2: Script Python
python3 << 'EOF'
import os
import yaml

with open('config.template.yaml') as f:
    config = yaml.safe_load(f)

# Expand environment variables
config['ldap']['bind_password'] = os.getenv('LDAP_PASSWORD')

with open('config.yaml', 'w') as f:
    yaml.dump(config, f)
EOF
```

### Debug Variables

```bash
# Mode debug
set -x
export LDAP_PASSWORD="test"
ldap-health-monitor audit
set +x

# Voir toutes les variables utilisées
ldap-health-monitor config show --redact
```

## Liens Connexes

- [Structure du Fichier de Configuration](./Config-File-Structure.md)
- [Configuration de Sécurité](../Security-Best-Practices.md)
- [Déploiement Docker](../deployment/Docker-Deployment.md)
- [Déploiement Kubernetes](../deployment/Kubernetes-Deployment.md)
- [Guide de Production](../guides/Production-Deployment.md)
