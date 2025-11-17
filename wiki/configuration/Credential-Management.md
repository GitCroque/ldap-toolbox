# Gestion des Identifiants et Secrets

## Table des Matières

- [Introduction](#introduction)
- [Principes de Gestion des Secrets](#principes-de-gestion-des-secrets)
- [Stockage des Identifiants](#stockage-des-identifiants)
- [Gestionnaires de Secrets](#gestionnaires-de-secrets)
- [Rotation des Credentials](#rotation-des-credentials)
- [Variables d'Environnement](#variables-denvironnement)
- [Certificats et Clés](#certificats-et-clés)
- [Intégration HashiCorp Vault](#intégration-hashicorp-vault)
- [Intégration Cloud Secrets](#intégration-cloud-secrets)
- [Bonnes Pratiques](#bonnes-pratiques)
- [Audit et Conformité](#audit-et-conformité)
- [Récupération d'Urgence](#récupération-durgence)

## Introduction

La gestion sécurisée des identifiants et secrets est critique pour LDAP Health Monitor. Ce guide couvre les meilleures pratiques pour stocker, gérer et utiliser les credentials de manière sécurisée.

### Architecture de Gestion des Secrets

```
┌─────────────────────────────────────────────────────────┐
│                   APPLICATION                            │
└────────────────────┬────────────────────────────────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
          ▼                     ▼
┌──────────────────┐  ┌──────────────────┐
│  Secret Provider │  │  Fallback Store  │
│    Interface     │  │   (Encrypted)    │
└────────┬─────────┘  └──────────────────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    │         │        │        │        │
    ▼         ▼        ▼        ▼        ▼
┌───────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐
│ Vault │ │ AWS  │ │Azure │ │ GCP  │ │ Env  │
│       │ │Secret│ │KeyVlt│ │Secret│ │ Vars │
└───────┘ └──────┘ └──────┘ └──────┘ └──────┘
```

### Types de Secrets

```yaml
secrets_taxonomy:
  # Identifiants LDAP
  ldap_credentials:
    - bind_dn
    - bind_password
    - admin_password

  # Certificats et Clés
  certificates:
    - tls_certificate
    - tls_private_key
    - ca_certificate

  # Tokens et API Keys
  tokens:
    - api_tokens
    - webhook_secrets
    - oauth_tokens

  # Clés de Chiffrement
  encryption_keys:
    - data_encryption_key
    - backup_encryption_key
    - signing_key

  # Identifiants d'Intégration
  integration_credentials:
    - slack_webhook
    - email_password
    - prometheus_token
```

## Principes de Gestion des Secrets

### 1. Séparation des Secrets

Ne jamais mélanger secrets et code.

```yaml
# ❌ MAUVAIS - Secrets en clair dans la config
ldap:
  bind_dn: "cn=admin,dc=example,dc=com"
  bind_password: "SuperSecret123!"  # JAMAIS ÇA!

# ✅ BON - Référence vers un secret
ldap:
  bind_dn: "cn=admin,dc=example,dc=com"
  bind_password:
    secret_ref: "vault:secret/ldap/admin#password"
```

### 2. Chiffrement Obligatoire

Tous les secrets au repos doivent être chiffrés.

```yaml
encryption:
  # Chiffrement des secrets stockés localement
  local_secrets:
    enabled: true
    algorithm: "aes-256-gcm"
    key_derivation: "pbkdf2"
    iterations: 100000

  # Chiffrement des secrets en transit
  transit:
    tls_version: "1.3"
    verify_certificates: true
```

### 3. Principe du Moindre Privilège

Accordez uniquement les accès nécessaires.

```yaml
access_control:
  # Par rôle
  roles:
    - name: "reader"
      secrets_access:
        - "ldap:read_only_password"

    - name: "operator"
      secrets_access:
        - "ldap:bind_password"
        - "monitoring:api_token"

    - name: "admin"
      secrets_access:
        - "*"
```

### 4. Rotation Régulière

Changez régulièrement les secrets.

```yaml
rotation_policy:
  # Rotation automatique
  automatic:
    enabled: true
    schedules:
      - secret_type: "ldap_password"
        frequency: "90d"

      - secret_type: "api_token"
        frequency: "30d"

      - secret_type: "encryption_key"
        frequency: "180d"

  # Notification avant expiration
  notifications:
    enabled: true
    days_before: [30, 14, 7, 1]
```

## Stockage des Identifiants

### Fichiers de Secrets Chiffrés

#### Utilisation de SOPS (Secrets OPerationS)

```bash
# Installation de SOPS
curl -LO https://github.com/mozilla/sops/releases/download/v3.7.3/sops-v3.7.3.linux
chmod +x sops-v3.7.3.linux
sudo mv sops-v3.7.3.linux /usr/local/bin/sops

# Générer une clé Age
age-keygen -o /opt/ldap-monitor/secrets/age-key.txt

# Configuration SOPS
cat > .sops.yaml <<EOF
creation_rules:
  - path_regex: secrets/.*\.yml$
    age: age1xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
EOF

# Créer un fichier de secrets
cat > secrets/ldap-credentials.yml <<EOF
ldap:
  servers:
    production:
      bind_dn: "cn=admin,dc=example,dc=com"
      bind_password: "SuperSecretPassword123!"
      admin_password: "AdminPassword456!"
EOF

# Chiffrer le fichier
sops -e -i secrets/ldap-credentials.yml

# Le fichier est maintenant chiffré
cat secrets/ldap-credentials.yml
```

#### Déchiffrement et Utilisation

```bash
# Déchiffrer pour utilisation
sops -d secrets/ldap-credentials.yml

# Utiliser dans l'application
export SOPS_AGE_KEY_FILE=/opt/ldap-monitor/secrets/age-key.txt
ldap-health-monitor audit health --config <(sops -d secrets/ldap-credentials.yml)
```

### Utilisation de GNU Privacy Guard (GPG)

```bash
# Générer une paire de clés GPG
gpg --full-generate-key
# Choisir: RSA 4096 bits, pas d'expiration

# Lister les clés
gpg --list-keys

# Chiffrer les identifiants
cat > secrets.txt <<EOF
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BIND_PASSWORD=SuperSecret123!
EOF

gpg --encrypt --recipient "admin@example.com" secrets.txt

# Déchiffrer
gpg --decrypt secrets.txt.gpg
```

### Base de Données Chiffrée

```yaml
# config/secrets-db.yml
secrets_database:
  type: "sqlite"
  path: "/opt/ldap-monitor/secrets/secrets.db"

  # Chiffrement de la base
  encryption:
    enabled: true
    algorithm: "aes-256-gcm"
    key_file: "/opt/ldap-monitor/secrets/db.key"

  # Schéma
  schema:
    tables:
      - name: "credentials"
        columns:
          - name: "id"
            type: "TEXT"
            primary_key: true
          - name: "secret_type"
            type: "TEXT"
          - name: "encrypted_value"
            type: "BLOB"
          - name: "created_at"
            type: "TIMESTAMP"
          - name: "expires_at"
            type: "TIMESTAMP"
```

## Gestionnaires de Secrets

### HashiCorp Vault

#### Configuration de Base

```yaml
# config/vault.yml
vault:
  enabled: true

  # Connexion
  address: "https://vault.example.com:8200"
  namespace: "ldap-monitoring"

  # Authentification
  auth:
    method: "approle"
    role_id_file: "/opt/ldap-monitor/secrets/vault-role-id"
    secret_id_file: "/opt/ldap-monitor/secrets/vault-secret-id"

  # Chemins des secrets
  secrets:
    ldap_credentials: "secret/data/ldap/production"
    api_tokens: "secret/data/tokens"
    certificates: "pki/cert"

  # Configuration avancée
  max_retries: 3
  timeout: 10
  tls:
    verify: true
    ca_cert: "/etc/ssl/certs/vault-ca.crt"
```

#### Initialisation et Utilisation

```bash
#!/bin/bash
# vault-setup.sh

# Variables
VAULT_ADDR="https://vault.example.com:8200"
VAULT_NAMESPACE="ldap-monitoring"

# Activer le moteur KV
vault secrets enable -path=secret kv-v2

# Créer une politique pour l'application
vault policy write ldap-monitor - <<EOF
# Lecture des credentials LDAP
path "secret/data/ldap/*" {
  capabilities = ["read"]
}

# Lecture des tokens
path "secret/data/tokens/*" {
  capabilities = ["read"]
}

# Renouvellement de token
path "auth/token/renew-self" {
  capabilities = ["update"]
}
EOF

# Créer un AppRole
vault auth enable approle
vault write auth/approle/role/ldap-monitor \
    token_policies="ldap-monitor" \
    token_ttl=1h \
    token_max_ttl=4h

# Récupérer les identifiants AppRole
ROLE_ID=$(vault read -field=role_id auth/approle/role/ldap-monitor/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/ldap-monitor/secret-id)

# Sauvegarder les identifiants
echo "$ROLE_ID" > /opt/ldap-monitor/secrets/vault-role-id
echo "$SECRET_ID" > /opt/ldap-monitor/secrets/vault-secret-id
chmod 600 /opt/ldap-monitor/secrets/vault-*

# Stocker les secrets
vault kv put secret/ldap/production \
    bind_dn="cn=admin,dc=example,dc=com" \
    bind_password="SuperSecret123!"
```

#### Script d'Intégration

```python
#!/usr/bin/env python3
# vault-integration.py

import hvac
import os
import sys

class VaultSecretManager:
    def __init__(self):
        self.client = hvac.Client(
            url=os.getenv('VAULT_ADDR'),
            namespace=os.getenv('VAULT_NAMESPACE')
        )
        self._authenticate()

    def _authenticate(self):
        """Authentification via AppRole"""
        role_id = open('/opt/ldap-monitor/secrets/vault-role-id').read().strip()
        secret_id = open('/opt/ldap-monitor/secrets/vault-secret-id').read().strip()

        response = self.client.auth.approle.login(
            role_id=role_id,
            secret_id=secret_id
        )

        if not self.client.is_authenticated():
            raise Exception("Authentication failed")

    def get_secret(self, path):
        """Récupérer un secret"""
        try:
            response = self.client.secrets.kv.v2.read_secret_version(
                path=path
            )
            return response['data']['data']
        except Exception as e:
            print(f"Error getting secret: {e}")
            return None

    def put_secret(self, path, data):
        """Stocker un secret"""
        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                secret=data
            )
            return True
        except Exception as e:
            print(f"Error putting secret: {e}")
            return False

# Utilisation
if __name__ == '__main__':
    vault = VaultSecretManager()

    # Récupérer les credentials LDAP
    ldap_creds = vault.get_secret('ldap/production')
    print(f"LDAP Bind DN: {ldap_creds['bind_dn']}")
```

### AWS Secrets Manager

```yaml
# config/aws-secrets.yml
aws_secrets_manager:
  enabled: true

  # Configuration AWS
  region: "eu-west-1"

  # Authentification
  auth:
    method: "iam_role"  # ou "access_key"
    # Si access_key:
    # access_key_id_env: "AWS_ACCESS_KEY_ID"
    # secret_access_key_env: "AWS_SECRET_ACCESS_KEY"

  # Mapping des secrets
  secrets:
    ldap_credentials:
      secret_name: "prod/ldap/credentials"
      version_stage: "AWSCURRENT"

    api_tokens:
      secret_name: "prod/api/tokens"
      version_stage: "AWSCURRENT"
```

#### Script d'Intégration AWS

```python
#!/usr/bin/env python3
# aws-secrets-integration.py

import boto3
import json
from botocore.exceptions import ClientError

class AWSSecretManager:
    def __init__(self, region='eu-west-1'):
        self.client = boto3.client(
            service_name='secretsmanager',
            region_name=region
        )

    def get_secret(self, secret_name):
        """Récupérer un secret depuis AWS Secrets Manager"""
        try:
            response = self.client.get_secret_value(
                SecretId=secret_name
            )

            # Parse le JSON
            if 'SecretString' in response:
                return json.loads(response['SecretString'])
            else:
                return response['SecretBinary']

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                print(f"Secret {secret_name} not found")
            elif e.response['Error']['Code'] == 'InvalidRequestException':
                print(f"Invalid request: {e}")
            elif e.response['Error']['Code'] == 'InvalidParameterException':
                print(f"Invalid parameter: {e}")
            return None

    def create_secret(self, secret_name, secret_value):
        """Créer un nouveau secret"""
        try:
            response = self.client.create_secret(
                Name=secret_name,
                SecretString=json.dumps(secret_value)
            )
            return response['ARN']
        except ClientError as e:
            print(f"Error creating secret: {e}")
            return None

    def rotate_secret(self, secret_name):
        """Déclencher la rotation d'un secret"""
        try:
            response = self.client.rotate_secret(
                SecretId=secret_name,
                RotationLambdaARN='arn:aws:lambda:region:account:function:rotation-function'
            )
            return response['VersionId']
        except ClientError as e:
            print(f"Error rotating secret: {e}")
            return None

# Utilisation
if __name__ == '__main__':
    manager = AWSSecretManager()

    # Récupérer les credentials
    ldap_creds = manager.get_secret('prod/ldap/credentials')
    print(f"Bind DN: {ldap_creds['bind_dn']}")

    # Créer un nouveau secret
    manager.create_secret(
        'prod/ldap/readonly',
        {
            'bind_dn': 'cn=readonly,dc=example,dc=com',
            'bind_password': 'ReadOnlyPassword123!'
        }
    )
```

### Azure Key Vault

```yaml
# config/azure-keyvault.yml
azure_key_vault:
  enabled: true

  # Configuration Azure
  vault_url: "https://ldap-monitor-kv.vault.azure.net/"
  tenant_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"

  # Authentification
  auth:
    method: "managed_identity"  # ou "service_principal"
    # Si service_principal:
    # client_id: "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
    # client_secret_env: "AZURE_CLIENT_SECRET"

  # Mapping des secrets
  secrets:
    ldap_bind_password: "ldap-bind-password"
    api_token: "monitoring-api-token"
```

### Google Cloud Secret Manager

```yaml
# config/gcp-secrets.yml
gcp_secret_manager:
  enabled: true

  # Configuration GCP
  project_id: "ldap-monitor-prod"

  # Authentification
  auth:
    method: "service_account"
    credentials_file: "/opt/ldap-monitor/secrets/gcp-service-account.json"

  # Mapping des secrets
  secrets:
    ldap_credentials: "projects/123456789/secrets/ldap-credentials/versions/latest"
```

## Rotation des Credentials

### Politique de Rotation

```yaml
# config/rotation-policy.yml
rotation:
  # Activation globale
  enabled: true

  # Politiques par type
  policies:
    # Mots de passe LDAP
    - name: "ldap_passwords"
      secrets:
        - "ldap:bind_password"
        - "ldap:admin_password"
      frequency: "90d"
      warning_days: [30, 14, 7, 1]
      auto_rotate: true

    # Tokens API
    - name: "api_tokens"
      secrets:
        - "api:monitoring_token"
        - "api:webhook_token"
      frequency: "30d"
      warning_days: [7, 3, 1]
      auto_rotate: true

    # Clés de chiffrement
    - name: "encryption_keys"
      secrets:
        - "encryption:data_key"
        - "encryption:backup_key"
      frequency: "180d"
      warning_days: [60, 30, 14]
      auto_rotate: false  # Manuel

    # Certificats
    - name: "certificates"
      secrets:
        - "cert:tls_certificate"
        - "cert:client_certificate"
      frequency: "365d"
      warning_days: [90, 60, 30, 14]
      auto_rotate: false

  # Notifications
  notifications:
    enabled: true
    channels:
      - email
      - slack
    recipients:
      - "security@example.com"
      - "ops@example.com"
```

### Script de Rotation Automatique

```bash
#!/bin/bash
# rotate-credentials.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/ldap-monitor/credential-rotation.log"

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

rotate_ldap_password() {
    local bind_dn="$1"
    local current_password="$2"

    log "Rotation du mot de passe LDAP pour $bind_dn"

    # Générer un nouveau mot de passe fort
    new_password=$(openssl rand -base64 32)

    # Changer le mot de passe dans LDAP
    ldappasswd -H ldaps://ldap.example.com \
        -D "$bind_dn" \
        -w "$current_password" \
        -s "$new_password" \
        "$bind_dn"

    # Mettre à jour dans Vault
    vault kv put secret/ldap/production \
        bind_dn="$bind_dn" \
        bind_password="$new_password"

    log "Mot de passe rotationné avec succès"
}

rotate_api_token() {
    local token_name="$1"

    log "Rotation du token API: $token_name"

    # Générer un nouveau token
    new_token=$(openssl rand -hex 32)

    # Mettre à jour dans Vault
    vault kv put secret/tokens/$token_name \
        token="$new_token" \
        created_at="$(date -Iseconds)"

    log "Token API rotationné avec succès"
}

rotate_encryption_key() {
    local key_name="$1"

    log "Rotation de la clé de chiffrement: $key_name"

    # Générer une nouvelle clé
    new_key=$(openssl rand -base64 32)

    # Rechiffrer les données avec la nouvelle clé
    # (Implémentation spécifique selon vos besoins)

    # Sauvegarder l'ancienne clé pour déchiffrement legacy
    old_key=$(vault kv get -field=key secret/encryption/$key_name)
    vault kv put secret/encryption/${key_name}-old \
        key="$old_key" \
        deprecated_at="$(date -Iseconds)"

    # Mettre à jour la nouvelle clé
    vault kv put secret/encryption/$key_name \
        key="$new_key" \
        rotated_at="$(date -Iseconds)"

    log "Clé de chiffrement rotationnée avec succès"
}

# Fonction principale
main() {
    case "$1" in
        ldap)
            rotate_ldap_password "$2" "$3"
            ;;
        api)
            rotate_api_token "$2"
            ;;
        encryption)
            rotate_encryption_key "$2"
            ;;
        all)
            log "Rotation de tous les credentials..."
            # Implémenter la rotation complète
            ;;
        *)
            echo "Usage: $0 {ldap|api|encryption|all} [args...]"
            exit 1
            ;;
    esac
}

main "$@"
```

### Automatisation avec Cron

```bash
# /etc/cron.d/ldap-monitor-rotation

# Rotation mensuelle des tokens API (1er du mois à 2h)
0 2 1 * * ldapmon /opt/ldap-monitor/scripts/rotate-credentials.sh api monitoring_token

# Rotation trimestrielle des mots de passe LDAP (1er janvier, avril, juillet, octobre à 3h)
0 3 1 1,4,7,10 * ldapmon /opt/ldap-monitor/scripts/rotate-credentials.sh ldap

# Vérification quotidienne des expirations (tous les jours à 8h)
0 8 * * * ldapmon /opt/ldap-monitor/scripts/check-expiration.sh
```

## Variables d'Environnement

### Gestion Sécurisée

```bash
#!/bin/bash
# secure-env.sh

# Fichier d'environnement sécurisé
ENV_FILE="/opt/ldap-monitor/secrets/.env"

# Créer le fichier avec permissions strictes
touch "$ENV_FILE"
chmod 600 "$ENV_FILE"
chown ldapmon:ldapmon "$ENV_FILE"

# Définir les variables
cat > "$ENV_FILE" <<EOF
# LDAP Configuration
LDAP_URI=ldaps://ldap.example.com:636
LDAP_BIND_DN=cn=monitoring,dc=example,dc=com

# Secrets (références vers Vault)
LDAP_BIND_PASSWORD=vault:secret/ldap/monitoring#password

# Monitoring
MONITORING_API_TOKEN=vault:secret/tokens/monitoring#token

# Encryption
ENCRYPTION_KEY_ID=current
EOF

# Fonction de chargement sécurisé
load_secure_env() {
    if [ -f "$ENV_FILE" ]; then
        # Vérifier les permissions
        perms=$(stat -c "%a" "$ENV_FILE")
        if [ "$perms" != "600" ]; then
            echo "ERREUR: Permissions incorrectes sur $ENV_FILE"
            exit 1
        fi

        # Charger les variables
        set -a
        source "$ENV_FILE"
        set +a

        # Résoudre les références Vault
        resolve_vault_secrets
    fi
}

resolve_vault_secrets() {
    for var in $(env | grep "=vault:" | cut -d'=' -f1); do
        vault_path=$(eval echo \$$var | sed 's/vault://')
        secret_value=$(vault kv get -field=${vault_path##*#} ${vault_path%#*})
        eval export $var="$secret_value"
    done
}
```

### Configuration systemd avec Secrets

```ini
# /etc/systemd/system/ldap-monitor.service
[Unit]
Description=LDAP Health Monitor
After=network.target vault.service

[Service]
Type=simple
User=ldapmon
Group=ldapmon

# Charger les variables d'environnement
EnvironmentFile=/opt/ldap-monitor/secrets/.env

# Sécurité renforcée
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/log/ldap-monitor

# Commande
ExecStart=/opt/ldap-monitor/bin/ldap-health-monitor daemon start

# Restart automatique
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Certificats et Clés

### Gestion des Certificats TLS

```yaml
# config/certificates.yml
certificates:
  # Certificat client pour LDAPS
  client:
    cert_file: "/opt/ldap-monitor/secrets/certs/client.crt"
    key_file: "/opt/ldap-monitor/secrets/certs/client.key"
    ca_file: "/opt/ldap-monitor/secrets/certs/ca.crt"

  # Permissions strictes
  permissions:
    cert: "644"
    key: "600"
    ca: "644"

  # Vérifications
  verification:
    verify_cert: true
    verify_hostname: true
    check_crl: true
    ocsp_stapling: true

  # Renouvellement automatique
  renewal:
    enabled: true
    days_before_expiry: 30
    method: "acme"  # ou "manual"
```

### Script de Gestion des Certificats

```bash
#!/bin/bash
# cert-management.sh

CERT_DIR="/opt/ldap-monitor/secrets/certs"
CA_CERT="$CERT_DIR/ca.crt"
CLIENT_CERT="$CERT_DIR/client.crt"
CLIENT_KEY="$CERT_DIR/client.key"

# Vérifier l'expiration
check_cert_expiry() {
    local cert_file="$1"
    local days_threshold="${2:-30}"

    expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
    expiry_epoch=$(date -d "$expiry_date" +%s)
    current_epoch=$(date +%s)
    days_until_expiry=$(( ($expiry_epoch - $current_epoch) / 86400 ))

    if [ $days_until_expiry -lt $days_threshold ]; then
        echo "ALERTE: Le certificat expire dans $days_until_expiry jours!"
        return 1
    fi

    echo "Certificat valide pour $days_until_expiry jours"
    return 0
}

# Générer une nouvelle clé privée
generate_private_key() {
    openssl genrsa -out "$CLIENT_KEY" 4096
    chmod 600 "$CLIENT_KEY"
}

# Générer une CSR
generate_csr() {
    openssl req -new \
        -key "$CLIENT_KEY" \
        -out "$CERT_DIR/client.csr" \
        -subj "/C=FR/ST=IDF/L=Paris/O=Example/CN=ldap-monitor"
}

# Renouveler le certificat
renew_certificate() {
    echo "Renouvellement du certificat..."

    # Sauvegarder l'ancien certificat
    cp "$CLIENT_CERT" "$CLIENT_CERT.old"

    # Générer nouvelle clé et CSR
    generate_private_key
    generate_csr

    # Signer avec la CA (à adapter selon votre PKI)
    openssl x509 -req \
        -in "$CERT_DIR/client.csr" \
        -CA "$CA_CERT" \
        -CAkey "$CERT_DIR/ca.key" \
        -CAcreateserial \
        -out "$CLIENT_CERT" \
        -days 365 \
        -sha256

    chmod 644 "$CLIENT_CERT"

    echo "Certificat renouvelé avec succès"
}

# Vérifier la validité
verify_certificate() {
    openssl verify -CAfile "$CA_CERT" "$CLIENT_CERT"
}

# Vérification quotidienne
if ! check_cert_expiry "$CLIENT_CERT" 30; then
    renew_certificate
fi
```

## Bonnes Pratiques

### Checklist de Sécurité des Secrets

```markdown
## Stockage

- [ ] Aucun secret en clair dans le code
- [ ] Aucun secret dans les fichiers de configuration
- [ ] Aucun secret committé dans Git
- [ ] Tous les secrets chiffrés au repos
- [ ] Permissions fichiers strictes (600 pour secrets)
- [ ] Utilisation d'un gestionnaire de secrets

## Accès

- [ ] Principe du moindre privilège appliqué
- [ ] Accès aux secrets audités
- [ ] MFA pour accès aux secrets critiques
- [ ] Séparation des droits (dev/staging/prod)
- [ ] Révocation immédiate possible

## Rotation

- [ ] Politique de rotation définie
- [ ] Rotation automatique configurée
- [ ] Notifications d'expiration actives
- [ ] Historique des rotations conservé
- [ ] Procédure de rotation d'urgence documentée

## Monitoring

- [ ] Logs d'accès aux secrets
- [ ] Alertes sur accès anormaux
- [ ] Monitoring des expirations
- [ ] Audit régulier des accès
- [ ] Détection d'anomalies active
```

### Politiques de Mots de Passe

```yaml
password_policy:
  # Complexité
  complexity:
    min_length: 16
    require_uppercase: true
    require_lowercase: true
    require_digits: true
    require_special_chars: true
    special_chars: "!@#$%^&*()_+-=[]{}|;:,.<>?"

  # Historique
  history:
    enabled: true
    remember_last: 12

  # Expiration
  expiration:
    enabled: true
    max_age_days: 90
    warning_days: [30, 14, 7, 1]

  # Restrictions
  restrictions:
    no_username_in_password: true
    no_common_passwords: true
    no_repeated_characters: true
    no_sequential_characters: true
```

## Audit et Conformité

### Logging des Accès aux Secrets

```yaml
audit_logging:
  secrets_access:
    enabled: true
    log_level: "info"

    # Événements à logger
    events:
      - secret_read
      - secret_write
      - secret_delete
      - secret_list
      - authentication_to_vault
      - failed_access_attempt

    # Format
    format:
      type: "json"
      fields:
        - timestamp
        - user
        - action
        - secret_path
        - result
        - source_ip
        - session_id

    # Destination
    destinations:
      - type: "file"
        path: "/var/log/ldap-monitor/secrets-audit.log"
        rotation: "daily"
        retention: 365

      - type: "syslog"
        facility: "auth"
        severity: "info"

      - type: "siem"
        endpoint: "https://siem.example.com/api/events"
```

## Récupération d'Urgence

### Procédure de Récupération

```bash
#!/bin/bash
# emergency-recovery.sh

BACKUP_DIR="/secure/backups/secrets"
RECOVERY_DIR="/opt/ldap-monitor/secrets-recovery"

# Fonction: Récupération d'urgence
emergency_recovery() {
    echo "URGENCE: Début de la récupération des secrets..."

    # Créer le répertoire de récupération
    mkdir -p "$RECOVERY_DIR"
    chmod 700 "$RECOVERY_DIR"

    # Récupérer la dernière sauvegarde
    latest_backup=$(ls -t "$BACKUP_DIR"/secrets-*.tar.gz.age | head -1)

    if [ -z "$latest_backup" ]; then
        echo "ERREUR: Aucune sauvegarde trouvée!"
        exit 1
    fi

    echo "Récupération depuis: $latest_backup"

    # Déchiffrer et extraire
    age -d -i /secure/recovery-key.txt "$latest_backup" | \
        tar -xzf - -C "$RECOVERY_DIR"

    # Vérifier l'intégrité
    if [ -f "$RECOVERY_DIR/checksums.txt" ]; then
        cd "$RECOVERY_DIR"
        sha256sum -c checksums.txt
    fi

    echo "Récupération terminée. Secrets dans: $RECOVERY_DIR"
}

# Exécuter
emergency_recovery
```

---

**Note Critique**: La gestion des secrets est cruciale pour la sécurité. Ne prenez jamais de raccourcis et suivez toujours les meilleures pratiques.
