# Codes de Sortie et Gestion des Erreurs

Guide complet des codes de sortie, codes d'erreur et gestion des erreurs dans LDAP Health Monitor.

## 📑 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Codes de Sortie Standard](#codes-de-sortie-standard)
- [Codes d'Erreur LDAP](#codes-derreur-ldap)
- [Codes d'Erreur Application](#codes-derreur-application)
- [Gestion des Erreurs](#gestion-des-erreurs)
- [Débogage et Diagnostic](#débogage-et-diagnostic)
- [Exemples de Scripts](#exemples-de-scripts)

## Vue d'Ensemble

LDAP Health Monitor utilise un système de codes de sortie conforme aux standards UNIX pour indiquer le succès ou l'échec des opérations. Les codes de sortie peuvent être capturés dans des scripts shell avec la variable `$?`.

### Principe de Base

```bash
# Exécuter une commande
ldap-monitor test connection

# Capturer le code de sortie
EXIT_CODE=$?

# Vérifier le résultat
if [ $EXIT_CODE -eq 0 ]; then
    echo "Succès"
else
    echo "Échec avec code: $EXIT_CODE"
fi
```

---

## Codes de Sortie Standard

### 0 - Succès

**Description** : L'opération s'est terminée avec succès sans erreur.

**Commandes concernées** : Toutes

**Exemples** :

```bash
# Test de connexion réussi
ldap-monitor test connection
echo $?  # 0

# Audit sans problèmes critiques
ldap-monitor audit health
echo $?  # 0

# Configuration valide
ldap-monitor config validate
echo $?  # 0

# Export réussi
ldap-monitor export users --output users.csv
echo $?  # 0
```

**Dans un script** :

```bash
#!/bin/bash

if ldap-monitor test connection; then
    echo "✅ Connexion LDAP OK"
    ldap-monitor audit all --format html --output report.html
else
    echo "❌ Impossible de se connecter au serveur LDAP"
    exit 1
fi
```

---

### 1 - Erreur Générale

**Description** : Erreur générale ou non spécifique lors de l'exécution.

**Causes courantes** :
- Configuration invalide ou manquante
- Fichier non trouvé
- Permissions insuffisantes
- Échec de connexion LDAP
- Erreur d'authentification
- Erreur d'écriture de fichier

**Exemples** :

```bash
# Configuration invalide
ldap-monitor config validate
# ❌ Configuration error: Missing required field 'ldap.server'
echo $?  # 1

# Fichier de configuration inexistant
ldap-monitor --config nonexistent.yaml audit health
# Error: Path 'nonexistent.yaml' does not exist
echo $?  # 1

# Connexion LDAP échouée
ldap-monitor test connection
# ❌ Connection failed: Unable to connect to server
echo $?  # 1

# Permissions insuffisantes
ldap-monitor export users --output /root/users.csv
# ❌ Error: Permission denied
echo $?  # 1
```

**Gestion dans un script** :

```bash
#!/bin/bash

# Test de connexion avec gestion d'erreur
if ! ldap-monitor test connection; then
    echo "❌ ERREUR: Impossible de se connecter au serveur LDAP" >&2
    echo "Vérifiez:"
    echo "  - La configuration (config.yaml)"
    echo "  - Les credentials (LDAP_BIND_DN, LDAP_BIND_PASSWORD)"
    echo "  - La connectivité réseau"
    exit 1
fi

echo "✅ Connexion établie, poursuite des opérations..."
```

---

### 2 - Usage Incorrect

**Description** : Utilisation incorrecte de la commande (arguments invalides, options manquantes).

**Causes courantes** :
- Option requise manquante
- Argument invalide
- Combinaison d'options incompatibles
- Format invalide

**Exemples** :

```bash
# Option requise manquante
ldap-monitor backup full
# Error: Missing option '--output' / '-o'
echo $?  # 2

# Format invalide
ldap-monitor audit health --format invalid
# Error: Invalid value for '--format': invalid is not one of 'console', 'json', 'html'
echo $?  # 2

# Argument manquant
ldap-monitor user show
# Error: Missing argument 'DN'
echo $?  # 2
```

**Gestion dans un script** :

```bash
#!/bin/bash

# Fonction avec validation des arguments
backup_ldap() {
    local output_file=$1

    if [ -z "$output_file" ]; then
        echo "Usage: backup_ldap <output_file>" >&2
        return 2
    fi

    ldap-monitor backup full --output "$output_file"
    return $?
}

# Utilisation
backup_ldap "/backup/ldap-$(date +%Y%m%d).ldif" || exit $?
```

---

### 130 - Interruption par SIGINT (Ctrl+C)

**Description** : Programme interrompu par l'utilisateur (Ctrl+C).

**Commandes concernées** : Principalement les commandes longues (monitor, audit all)

**Exemples** :

```bash
# Démarrer monitoring et interrompre avec Ctrl+C
ldap-monitor monitor start
# ^C
# Monitoring stopped
echo $?  # 130
```

**Gestion dans un script** :

```bash
#!/bin/bash

# Trap SIGINT pour nettoyage
cleanup() {
    echo ""
    echo "🛑 Interruption détectée, nettoyage en cours..."
    # Arrêter les processus en cours
    pkill -P $$
    exit 130
}

trap cleanup SIGINT

# Démarrer monitoring
ldap-monitor monitor start
```

---

## Codes d'Erreur LDAP

Ces codes correspondent aux codes d'erreur standard du protocole LDAP (RFC 4511).

### Codes Courants

| Code | Nom | Description | Solution |
|------|-----|-------------|----------|
| 49 | INVALID_CREDENTIALS | Identifiants incorrects | Vérifier bind_dn et bind_password |
| 32 | NO_SUCH_OBJECT | Objet introuvable | Vérifier le DN ou base_dn |
| 34 | INVALID_DN_SYNTAX | Syntaxe DN invalide | Corriger la syntaxe du DN |
| 50 | INSUFFICIENT_ACCESS | Permissions insuffisantes | Accorder les droits nécessaires |
| 51 | BUSY | Serveur occupé | Réessayer plus tard |
| 52 | UNAVAILABLE | Serveur indisponible | Vérifier que le serveur est démarré |
| 53 | UNWILLING_TO_PERFORM | Opération refusée | Vérifier la politique du serveur |
| 80 | OTHER | Erreur non spécifiée | Consulter les logs du serveur |

### Exemples d'Erreurs LDAP

#### Code 49 - Invalid Credentials

```bash
# Mauvais mot de passe
export LDAP_BIND_PASSWORD="wrong_password"
ldap-monitor test connection
# ❌ Connection failed: LDAP error 49 (INVALID_CREDENTIALS): Invalid credentials
echo $?  # 1
```

**Solution** :

```bash
# Vérifier les credentials
echo "Bind DN: $LDAP_BIND_DN"
echo "Mot de passe: <caché>"

# Tester avec ldapsearch
ldapsearch -x -H ldaps://ldap.example.com \
    -D "$LDAP_BIND_DN" \
    -W \
    -b "dc=example,dc=com" \
    "(objectClass=*)" dn
```

#### Code 32 - No Such Object

```bash
# Base DN incorrect
ldap-monitor audit health
# ❌ Error: LDAP error 32 (NO_SUCH_OBJECT): Base DN 'dc=wrong,dc=com' not found
echo $?  # 1
```

**Solution** :

```yaml
# Corriger config.yaml
ldap:
  base_dn: "dc=example,dc=com"  # ✅ DN correct
```

#### Code 50 - Insufficient Access

```bash
# Compte de lecture seule tentant de modifier
ldap-monitor cleanup empty-groups --confirm
# ❌ Error: LDAP error 50 (INSUFFICIENT_ACCESS): Insufficient access rights
echo $?  # 1
```

**Solution** :

```bash
# Utiliser un compte avec permissions d'écriture
export LDAP_BIND_DN="cn=admin,dc=example,dc=com"
export LDAP_BIND_PASSWORD="admin_password"
ldap-monitor cleanup empty-groups --confirm
```

#### Code 52 - Unavailable

```bash
# Serveur LDAP arrêté
ldap-monitor test connection
# ❌ Connection failed: LDAP error 52 (UNAVAILABLE): Server is unavailable
echo $?  # 1
```

**Solution** :

```bash
# Vérifier que le serveur est démarré
sudo systemctl status slapd

# Vérifier la connectivité réseau
nc -zv ldap.example.com 636

# Vérifier les logs du serveur
sudo tail -f /var/log/slapd.log
```

---

## Codes d'Erreur Application

Codes d'erreur spécifiques à LDAP Health Monitor.

### Erreurs de Configuration

#### CONFIG_MISSING (exit 1)

**Description** : Fichier de configuration manquant ou non spécifié.

**Exemples** :

```bash
# config.yaml n'existe pas
ldap-monitor audit health
# ❌ Error: Configuration file 'config.yaml' not found
echo $?  # 1
```

**Solution** :

```bash
# Créer la configuration
ldap-monitor config init

# Ou spécifier un fichier existant
ldap-monitor --config /etc/ldap-monitor/config.yaml audit health
```

#### CONFIG_INVALID (exit 1)

**Description** : Configuration invalide ou malformée.

**Exemples** :

```bash
# YAML invalide
ldap-monitor config validate
# ❌ Configuration error: Invalid YAML syntax at line 15
echo $?  # 1

# Champs requis manquants
ldap-monitor config validate
# ❌ Configuration error: Missing required field 'ldap.server'
echo $?  # 1
```

**Solution** :

```bash
# Valider la syntaxe YAML
yamllint config.yaml

# Utiliser l'exemple comme base
cp config.example.yaml config.yaml
vim config.yaml

# Valider après modification
ldap-monitor config validate
```

### Erreurs de Connexion

#### CONNECTION_TIMEOUT (exit 1)

**Description** : Délai de connexion dépassé.

**Exemples** :

```bash
# Serveur inaccessible
ldap-monitor test connection
# ❌ Connection failed: Connection timeout after 10s
echo $?  # 1
```

**Solution** :

```bash
# Vérifier la connectivité
ping ldap.example.com
telnet ldap.example.com 636

# Augmenter le timeout dans config.yaml
ldap:
  timeout: 30  # 30 secondes
```

#### SSL_ERROR (exit 1)

**Description** : Erreur de certificat SSL/TLS.

**Exemples** :

```bash
# Certificat expiré ou invalide
ldap-monitor test connection
# ❌ Connection failed: SSL certificate verification failed
echo $?  # 1
```

**Solution** :

```bash
# Vérifier le certificat
openssl s_client -connect ldap.example.com:636 -showcerts

# Option temporaire : désactiver la validation (non recommandé en production)
# Dans config.yaml:
ldap:
  use_ssl: true
  verify_ssl: false  # ⚠️ Uniquement pour test
```

### Erreurs d'Export

#### EXPORT_PERMISSION_DENIED (exit 1)

**Description** : Permissions insuffisantes pour écrire le fichier.

**Exemples** :

```bash
# Tentative d'écriture dans /root
ldap-monitor export users --output /root/users.csv
# ❌ Error: Permission denied: /root/users.csv
echo $?  # 1
```

**Solution** :

```bash
# Utiliser un répertoire accessible
ldap-monitor export users --output ~/exports/users.csv

# Ou créer le répertoire avec bonnes permissions
sudo mkdir -p /var/exports
sudo chown $USER:$USER /var/exports
ldap-monitor export users --output /var/exports/users.csv
```

#### EXPORT_DISK_FULL (exit 1)

**Description** : Espace disque insuffisant.

**Exemples** :

```bash
# Disque plein
ldap-monitor backup full --output /backup/ldap.ldif
# ❌ Error: No space left on device
echo $?  # 1
```

**Solution** :

```bash
# Vérifier l'espace disque
df -h /backup

# Nettoyer les anciens backups
find /backup -name "*.ldif" -mtime +30 -delete

# Utiliser un autre volume
ldap-monitor backup full --output /mnt/storage/ldap.ldif
```

---

## Gestion des Erreurs

### Capture et Traitement

```bash
#!/bin/bash
# error-handling.sh

# Fonction pour gérer les erreurs
handle_error() {
    local exit_code=$1
    local command=$2

    case $exit_code in
        0)
            echo "✅ $command: Succès"
            ;;
        1)
            echo "❌ $command: Erreur générale" >&2
            return 1
            ;;
        2)
            echo "❌ $command: Usage incorrect" >&2
            echo "Consultez: ldap-monitor $command --help" >&2
            return 2
            ;;
        130)
            echo "🛑 $command: Interrompu par l'utilisateur" >&2
            return 130
            ;;
        *)
            echo "❌ $command: Erreur inconnue (code: $exit_code)" >&2
            return $exit_code
            ;;
    esac
}

# Exécuter avec gestion d'erreur
ldap-monitor test connection
handle_error $? "test connection" || exit $?

ldap-monitor audit all --format json --output audit.json
handle_error $? "audit all" || exit $?
```

### Retry Logic

```bash
#!/bin/bash
# retry-wrapper.sh

# Fonction de retry avec backoff exponentiel
retry_with_backoff() {
    local max_attempts=5
    local timeout=1
    local attempt=1
    local exit_code=0

    while [ $attempt -le $max_attempts ]; do
        echo "Tentative $attempt/$max_attempts..."

        "$@"
        exit_code=$?

        if [ $exit_code -eq 0 ]; then
            echo "✅ Succès à la tentative $attempt"
            return 0
        fi

        if [ $attempt -lt $max_attempts ]; then
            echo "❌ Échec (code: $exit_code), nouvelle tentative dans ${timeout}s..."
            sleep $timeout
            timeout=$((timeout * 2))  # Backoff exponentiel
        fi

        attempt=$((attempt + 1))
    done

    echo "❌ Échec après $max_attempts tentatives (code: $exit_code)" >&2
    return $exit_code
}

# Utilisation
retry_with_backoff ldap-monitor test connection
```

### Logging des Erreurs

```bash
#!/bin/bash
# error-logging.sh

LOG_FILE="/var/log/ldap-monitor/errors.log"

# Fonction de logging
log_error() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local exit_code=$1
    local command=$2
    local error_msg=$3

    echo "[$timestamp] ERROR (code: $exit_code) - $command: $error_msg" >> "$LOG_FILE"
}

# Exécution avec logging
output=$(ldap-monitor test connection 2>&1)
exit_code=$?

if [ $exit_code -ne 0 ]; then
    log_error $exit_code "test connection" "$output"
    echo "❌ Erreur enregistrée dans $LOG_FILE" >&2
    exit $exit_code
fi
```

---

## Débogage et Diagnostic

### Mode Verbose

```bash
# Activer le mode verbeux pour voir les détails
ldap-monitor --verbose test connection 2>&1 | tee debug.log

# Analyser les logs
grep -i error debug.log
grep -i "response time" debug.log
```

### Codes de Sortie dans Scripts CI/CD

```yaml
# .github/workflows/ldap-audit.yml
name: LDAP Audit

on:
  schedule:
    - cron: '0 0 * * *'  # Quotidien à minuit

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v2

      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'

      - name: Install LDAP Monitor
        run: pip install ldap-health-monitor

      - name: Test Connection
        id: test
        run: |
          ldap-monitor test connection
          echo "exit_code=$?" >> $GITHUB_OUTPUT
        continue-on-error: true
        env:
          LDAP_BIND_DN: ${{ secrets.LDAP_BIND_DN }}
          LDAP_BIND_PASSWORD: ${{ secrets.LDAP_BIND_PASSWORD }}

      - name: Check Connection Status
        if: steps.test.outputs.exit_code != '0'
        run: |
          echo "❌ LDAP connection failed"
          exit 1

      - name: Run Audit
        run: |
          ldap-monitor audit all \
            --format json \
            --output audit-report.json

      - name: Upload Report
        uses: actions/upload-artifact@v2
        with:
          name: audit-report
          path: audit-report.json

      - name: Notify on Failure
        if: failure()
        uses: 8398a7/action-slack@v3
        with:
          status: ${{ job.status }}
          text: 'LDAP Audit Failed'
          webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

### Scripts de Diagnostic

```bash
#!/bin/bash
# diagnose.sh - Script de diagnostic complet

echo "🔍 LDAP Health Monitor - Diagnostic"
echo "===================================="

# 1. Vérifier la version
echo -e "\n📦 Version:"
ldap-monitor version

# 2. Test de configuration
echo -e "\n⚙️  Configuration:"
if ldap-monitor config validate; then
    echo "✅ Configuration valide"
else
    echo "❌ Configuration invalide (exit code: $?)"
fi

# 3. Test de connexion
echo -e "\n🔌 Connexion:"
if ldap-monitor --verbose test connection 2>&1 | tee test-connection.log; then
    echo "✅ Connexion réussie"
else
    exit_code=$?
    echo "❌ Connexion échouée (exit code: $exit_code)"
    echo "Logs détaillés dans: test-connection.log"
fi

# 4. Test des métriques
echo -e "\n📊 Métriques:"
if ldap-monitor monitor metrics > metrics.txt 2>&1; then
    echo "✅ Métriques collectées"
    cat metrics.txt
else
    echo "❌ Échec collecte métriques (exit code: $?)"
fi

# 5. Résumé
echo -e "\n📋 Résumé:"
echo "Les logs détaillés sont disponibles dans:"
echo "  - test-connection.log"
echo "  - metrics.txt"
```

---

## Exemples de Scripts

### Script de Backup avec Gestion d'Erreurs

```bash
#!/bin/bash
# backup-with-error-handling.sh

set -euo pipefail  # Exit on error, undefined var, pipe failure

BACKUP_DIR="/var/backups/ldap"
DATE=$(date +%Y%m%d-%H%M%S)
LOG_FILE="/var/log/ldap-monitor/backup.log"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

# Fonction de cleanup en cas d'erreur
cleanup() {
    local exit_code=$?
    if [ $exit_code -ne 0 ]; then
        log "❌ Backup échoué avec code de sortie: $exit_code"
        # Envoyer notification
        if [ -n "${SLACK_WEBHOOK:-}" ]; then
            curl -X POST "$SLACK_WEBHOOK" \
                -H 'Content-Type: application/json' \
                -d "{\"text\":\"❌ LDAP Backup failed with exit code $exit_code\"}"
        fi
    fi
}

trap cleanup EXIT

# Créer répertoire de backup
mkdir -p "$BACKUP_DIR"

# Test de connexion
log "Test de connexion LDAP..."
if ! ldap-monitor test connection; then
    log "❌ Impossible de se connecter au serveur LDAP"
    exit 1
fi
log "✅ Connexion établie"

# Backup complet
log "Démarrage du backup..."
if ldap-monitor backup full \
    --output "$BACKUP_DIR/ldap-backup-$DATE.ldif" \
    --format ldif; then
    log "✅ Backup créé: ldap-backup-$DATE.ldif"
else
    exit_code=$?
    log "❌ Échec du backup (exit code: $exit_code)"
    exit $exit_code
fi

# Compression
log "Compression du backup..."
if gzip "$BACKUP_DIR/ldap-backup-$DATE.ldif"; then
    log "✅ Backup compressé: ldap-backup-$DATE.ldif.gz"
else
    log "⚠️  Échec de la compression (exit code: $?)"
fi

# Nettoyage des anciens backups (> 30 jours)
log "Nettoyage des anciens backups..."
find "$BACKUP_DIR" -name "*.ldif.gz" -mtime +30 -delete
log "✅ Nettoyage terminé"

log "✅ Backup complet terminé avec succès"
```

### Script d'Audit avec Alertes

```bash
#!/bin/bash
# audit-with-alerts.sh

REPORT_FILE="audit-$(date +%Y%m%d).json"
THRESHOLD_SCORE=80

# Exécuter l'audit
echo "🔍 Exécution de l'audit LDAP..."
if ! ldap-monitor audit all --format json --output "$REPORT_FILE"; then
    echo "❌ Échec de l'audit (exit code: $?)"
    exit 1
fi

# Extraire le score
score=$(jq -r '.data.score' "$REPORT_FILE")

# Vérifier le score
if [ "$score" -lt "$THRESHOLD_SCORE" ]; then
    echo "⚠️  Score d'audit bas: $score/$THRESHOLD_SCORE"

    # Extraire les problèmes critiques
    critical_issues=$(jq -r '.data.issues[] | select(.level=="critical") | .title' "$REPORT_FILE")

    # Envoyer alerte
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{
                \"text\": \"⚠️ LDAP Audit Score: $score/100\",
                \"attachments\": [{
                    \"color\": \"danger\",
                    \"title\": \"Critical Issues\",
                    \"text\": \"$critical_issues\"
                }]
            }"
    fi

    exit 1
else
    echo "✅ Score d'audit: $score/100"
fi
```

### Wrapper pour Cron

```bash
#!/bin/bash
# cron-wrapper.sh

# Rediriger toutes les sorties vers syslog
exec 1> >(logger -s -t ldap-monitor) 2>&1

# Charger l'environnement
if [ -f /etc/ldap-monitor/.env ]; then
    set -a
    source /etc/ldap-monitor/.env
    set +a
fi

# Exécuter la commande
ldap-monitor "$@"
exit_code=$?

# Logger le résultat
if [ $exit_code -eq 0 ]; then
    logger -p user.info -t ldap-monitor "Commande réussie: $*"
else
    logger -p user.err -t ldap-monitor "Commande échouée (code: $exit_code): $*"
fi

exit $exit_code
```

**Utilisation dans crontab** :

```cron
# /etc/crontab
# Audit quotidien à 2h du matin
0 2 * * * ldapuser /usr/local/bin/cron-wrapper.sh audit all --format json -o /var/reports/audit-daily.json

# Backup hebdomadaire le dimanche à 3h
0 3 * * 0 ldapuser /usr/local/bin/cron-wrapper.sh backup full -o /var/backups/ldap-weekly.ldif
```

---

## Voir Aussi

- [Commandes CLI](CLI-Commands.md) - Référence complète des commandes
- [Options Globales](Global-Options.md) - Options et variables d'environnement
- [Formats d'Export](Export-Formats.md) - Spécifications des formats
- [Troubleshooting](../troubleshooting/Common-Errors.md) - Guide de dépannage
- [Scripts d'Automatisation](../guides/Cron-Automation.md) - Automatisation avec cron

---

**Note** : Pour un diagnostic complet en cas d'erreur, utilisez toujours le mode `--verbose` et consultez les logs de l'application et du serveur LDAP.
