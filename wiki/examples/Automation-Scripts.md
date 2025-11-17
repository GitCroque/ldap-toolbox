# Scripts d'Automatisation - LDAP Health Monitor

Guide complet des scripts d'automatisation, workflows, tâches cron et intégrations pour LDAP Health Monitor.

## 📋 Table des Matières

- [Scripts Cron Essentiels](#scripts-cron-essentiels)
- [Workflows CI/CD](#workflows-cicd)
- [Scripts de Maintenance](#scripts-de-maintenance)
- [Automatisation des Alertes](#automatisation-des-alertes)
- [Intégration n8n](#intégration-n8n)
- [Scripts Kubernetes](#scripts-kubernetes)
- [Orchestration Ansible](#orchestration-ansible)

---

## Scripts Cron Essentiels

### Configuration Crontab Complète

```bash
# /etc/cron.d/ldap-monitor

# Variables d'environnement
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=ops@company.com

# Monitoring continu (toutes les 5 minutes)
*/5 * * * * ldap-svc /opt/ldap-monitor/scripts/quick-health-check.sh

# Audit complet quotidien (6h du matin)
0 6 * * * ldap-svc /opt/ldap-monitor/scripts/daily-audit.sh

# Backup quotidien (2h du matin)
0 2 * * * ldap-svc /opt/ldap-monitor/scripts/daily-backup.sh

# Nettoyage hebdomadaire (dimanche 3h)
0 3 * * 0 ldap-svc /opt/ldap-monitor/scripts/weekly-cleanup.sh

# Rapport hebdomadaire (lundi 9h)
0 9 * * 1 ldap-svc /opt/ldap-monitor/scripts/weekly-report.sh

# Rapport mensuel (1er du mois à 10h)
0 10 1 * * ldap-svc /opt/ldap-monitor/scripts/monthly-report.sh

# Vérification des certificats (quotidien 7h)
0 7 * * * ldap-svc /opt/ldap-monitor/scripts/check-certificates.sh

# Rotation des logs (quotidien 1h)
0 1 * * * ldap-svc /opt/ldap-monitor/scripts/rotate-logs.sh

# Test de restauration (mensuel, le 15 à 4h)
0 4 15 * * ldap-svc /opt/ldap-monitor/scripts/test-backup-restore.sh

# Audit de conformité (trimestriel, 1er jour à 8h)
0 8 1 */3 * ldap-svc /opt/ldap-monitor/scripts/compliance-audit.sh
```

### Quick Health Check (Toutes les 5 minutes)

```bash
#!/bin/bash
# /opt/ldap-monitor/scripts/quick-health-check.sh

set -euo pipefail

LOG_FILE="/var/log/ldap-monitor/health-checks.log"
METRICS_FILE="/var/lib/ldap-monitor/metrics/current.json"
ALERT_THRESHOLD=3000  # ms

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$LOG_FILE"
}

log "Démarrage du health check rapide"

# Charger les credentials
source /etc/ldap-monitor/credentials.env

# Test de connexion avec métriques
START_TIME=$(date +%s%3N)

HEALTH_OUTPUT=$(ldap-monitor -c /etc/ldap-monitor/config.yaml \
    test connection \
    --format json 2>&1)

END_TIME=$(date +%s%3N)
RESPONSE_TIME=$((END_TIME - START_TIME))

# Parser la réponse
SUCCESS=$(echo "$HEALTH_OUTPUT" | jq -r '.success // false')
ERROR_MSG=$(echo "$HEALTH_OUTPUT" | jq -r '.error // "none"')

# Enregistrer les métriques
cat > "$METRICS_FILE" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "response_time_ms": $RESPONSE_TIME,
  "success": $SUCCESS,
  "error": "$ERROR_MSG"
}
EOF

# Vérifier les seuils
if [ "$SUCCESS" = "false" ]; then
    log "❌ CRITICAL: Connexion LDAP échouée - $ERROR_MSG"

    # Incrémenter le compteur d'échecs
    FAILURE_COUNT=$(cat /var/lib/ldap-monitor/failure_count 2>/dev/null || echo 0)
    FAILURE_COUNT=$((FAILURE_COUNT + 1))
    echo "$FAILURE_COUNT" > /var/lib/ldap-monitor/failure_count

    # Alerter après 3 échecs consécutifs
    if [ "$FAILURE_COUNT" -ge 3 ]; then
        /opt/ldap-monitor/scripts/send-critical-alert.sh \
            "LDAP Service Down" \
            "Connexion LDAP échouée $FAILURE_COUNT fois. Erreur: $ERROR_MSG"
    fi

    exit 1
fi

# Réinitialiser le compteur d'échecs
echo "0" > /var/lib/ldap-monitor/failure_count

# Vérifier le temps de réponse
if [ "$RESPONSE_TIME" -gt "$ALERT_THRESHOLD" ]; then
    log "⚠️  WARNING: Temps de réponse élevé: ${RESPONSE_TIME}ms"

    /opt/ldap-monitor/scripts/send-warning-alert.sh \
        "LDAP Slow Response" \
        "Temps de réponse: ${RESPONSE_TIME}ms (seuil: ${ALERT_THRESHOLD}ms)"
fi

log "✅ Health check OK - ${RESPONSE_TIME}ms"

# Envoyer les métriques à Prometheus Pushgateway
if command -v curl &> /dev/null; then
    cat << METRICS | curl --data-binary @- http://localhost:9091/metrics/job/ldap_health_check
# TYPE ldap_connection_success gauge
ldap_connection_success $([[ "$SUCCESS" = "true" ]] && echo 1 || echo 0)
# TYPE ldap_response_time_ms gauge
ldap_response_time_ms $RESPONSE_TIME
METRICS
fi

exit 0
```

### Daily Audit (Quotidien à 6h)

```bash
#!/bin/bash
# /opt/ldap-monitor/scripts/daily-audit.sh

set -euo pipefail

REPORT_DATE=$(date +%Y-%m-%d)
REPORT_DIR="/var/reports/ldap-monitor/daily/${REPORT_DATE}"
TEMP_DIR="/tmp/ldap-audit-$$"

mkdir -p "$REPORT_DIR" "$TEMP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "/var/log/ldap-monitor/daily-audit.log"
}

cleanup() {
    rm -rf "$TEMP_DIR"
}
trap cleanup EXIT

log "🔍 Démarrage de l'audit quotidien - $REPORT_DATE"

# Charger les credentials
source /etc/ldap-monitor/credentials.env

# 1. Audit de santé
log "1/7 Audit de santé..."
ldap-monitor -c /etc/ldap-monitor/config.yaml audit health \
    --format json \
    --output "$TEMP_DIR/health.json"

HEALTH_STATUS=$(jq -r '.status' "$TEMP_DIR/health.json")
log "  Status: $HEALTH_STATUS"

# 2. Audit des utilisateurs
log "2/7 Audit des utilisateurs..."
ldap-monitor -c /etc/ldap-monitor/config.yaml audit users \
    --inactive --missing-attributes \
    --format json \
    --output "$TEMP_DIR/users.json"

USER_ISSUES=$(jq '. | length' "$TEMP_DIR/users.json")
log "  Problèmes utilisateurs: $USER_ISSUES"

# 3. Audit des groupes
log "3/7 Audit des groupes..."
ldap-monitor -c /etc/ldap-monitor/config.yaml audit groups \
    --empty --large \
    --format json \
    --output "$TEMP_DIR/groups.json"

GROUP_ISSUES=$(jq '. | length' "$TEMP_DIR/groups.json")
log "  Problèmes groupes: $GROUP_ISSUES"

# 4. Audit de sécurité
log "4/7 Audit de sécurité..."
ldap-monitor -c /etc/ldap-monitor/config.yaml audit security \
    --format json \
    --output "$TEMP_DIR/security.json"

SECURITY_ISSUES=$(jq '. | length' "$TEMP_DIR/security.json")
log "  Problèmes sécurité: $SECURITY_ISSUES"

# 5. Audit de structure
log "5/7 Audit de structure..."
ldap-monitor -c /etc/ldap-monitor/config.yaml audit structure \
    --format json \
    --output "$TEMP_DIR/structure.json"

# 6. Audit de cohérence
log "6/7 Audit de cohérence..."
ldap-monitor -c /etc/ldap-monitor/config.yaml audit consistency \
    --format json \
    --output "$TEMP_DIR/consistency.json"

# 7. Générer le rapport consolidé
log "7/7 Génération du rapport..."
ldap-monitor -c /etc/ldap-monitor/config.yaml audit all \
    --format html \
    --output "$REPORT_DIR/audit-report.html"

ldap-monitor -c /etc/ldap-monitor/config.yaml audit all \
    --format json \
    --output "$REPORT_DIR/audit-report.json"

# Copier les rapports détaillés
cp "$TEMP_DIR"/*.json "$REPORT_DIR/"

# Générer un résumé texte
cat > "$REPORT_DIR/summary.txt" << EOF
LDAP Health Monitor - Rapport Quotidien
Date: $REPORT_DATE
Généré: $(date '+%Y-%m-%d %H:%M:%S')

=== RÉSUMÉ ===
Status Santé: $HEALTH_STATUS
Problèmes Utilisateurs: $USER_ISSUES
Problèmes Groupes: $GROUP_ISSUES
Problèmes Sécurité: $SECURITY_ISSUES

=== MÉTRIQUES ===
$(jq -r '.metrics | to_entries[] | "\(.key): \(.value)"' "$TEMP_DIR/health.json")

=== TOP ISSUES ===
$(jq -r '.issues[:5] | .[] | "- [\(.severity)] \(.title)"' "$REPORT_DIR/audit-report.json")

Rapport complet: $REPORT_DIR/audit-report.html
EOF

# Envoyer le rapport par email si des problèmes sont détectés
TOTAL_ISSUES=$((USER_ISSUES + GROUP_ISSUES + SECURITY_ISSUES))

if [ "$TOTAL_ISSUES" -gt 0 ]; then
    log "📧 Envoi du rapport par email ($TOTAL_ISSUES problèmes détectés)"

    mail -s "LDAP Daily Audit - $TOTAL_ISSUES issues - $REPORT_DATE" \
        -A "$REPORT_DIR/audit-report.html" \
        -A "$REPORT_DIR/summary.txt" \
        ops@company.com < "$REPORT_DIR/summary.txt"
fi

# Envoyer à Slack
if [ -n "${SLACK_WEBHOOK:-}" ]; then
    SLACK_COLOR=$([[ "$TOTAL_ISSUES" -eq 0 ]] && echo "good" || echo "warning")

    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d @- << SLACK
{
    "attachments": [{
        "color": "$SLACK_COLOR",
        "title": "LDAP Daily Audit - $REPORT_DATE",
        "fields": [
            {"title": "Status", "value": "$HEALTH_STATUS", "short": true},
            {"title": "Total Issues", "value": "$TOTAL_ISSUES", "short": true},
            {"title": "User Issues", "value": "$USER_ISSUES", "short": true},
            {"title": "Security Issues", "value": "$SECURITY_ISSUES", "short": true}
        ],
        "footer": "LDAP Health Monitor"
    }]
}
SLACK
fi

# Archiver les anciens rapports (garder 90 jours)
log "🗑️  Nettoyage des anciens rapports..."
find /var/reports/ldap-monitor/daily -type d -mtime +90 -exec rm -rf {} + 2>/dev/null || true

log "✅ Audit quotidien terminé"
```

### Daily Backup (Quotidien à 2h)

```bash
#!/bin/bash
# /opt/ldap-monitor/scripts/daily-backup.sh

set -euo pipefail

BACKUP_DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/backups/ldap/${BACKUP_DATE}"
RETENTION_DAYS=30
S3_BUCKET="s3://company-ldap-backups"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "/var/log/ldap-monitor/backup.log"
}

log "💾 Démarrage du backup quotidien - $BACKUP_DATE"

mkdir -p "$BACKUP_DIR"

# Charger les credentials
source /etc/ldap-monitor/credentials.env

# 1. Backup LDIF complet
log "1/4 Backup LDIF..."
ldap-monitor -c /etc/ldap-monitor/config.yaml backup full \
    --output "$BACKUP_DIR/full-backup.ldif" \
    --format ldif

# Compresser
gzip -9 "$BACKUP_DIR/full-backup.ldif"
LDIF_SIZE=$(du -h "$BACKUP_DIR/full-backup.ldif.gz" | cut -f1)
log "  LDIF backup: $LDIF_SIZE"

# 2. Backup JSON (pour parsing facile)
log "2/4 Backup JSON..."
ldap-monitor -c /etc/ldap-monitor/config.yaml backup full \
    --output "$BACKUP_DIR/full-backup.json" \
    --format json

gzip -9 "$BACKUP_DIR/full-backup.json"
JSON_SIZE=$(du -h "$BACKUP_DIR/full-backup.json.gz" | cut -f1)
log "  JSON backup: $JSON_SIZE"

# 3. Export des utilisateurs en CSV (pour analyse)
log "3/4 Export utilisateurs CSV..."
ldap-monitor -c /etc/ldap-monitor/config.yaml export users \
    --output "$BACKUP_DIR/users.csv" \
    --format csv

gzip -9 "$BACKUP_DIR/users.csv"

# 4. Backup de la configuration
log "4/4 Backup configuration..."
cp /etc/ldap-monitor/config.yaml "$BACKUP_DIR/config.yaml"

# Créer un manifeste
cat > "$BACKUP_DIR/MANIFEST.txt" << EOF
LDAP Backup Manifest
Date: $BACKUP_DATE
Created: $(date -Iseconds)
Hostname: $(hostname)

Files:
$(ls -lh "$BACKUP_DIR")

Checksums (SHA256):
$(cd "$BACKUP_DIR" && sha256sum *.gz config.yaml)

Statistics:
- Total Users: $(zcat "$BACKUP_DIR/users.csv.gz" | wc -l)
- LDIF Size: $LDIF_SIZE
- JSON Size: $JSON_SIZE
EOF

# Créer une archive tar complète
log "📦 Création de l'archive..."
tar -czf "$BACKUP_DIR.tar.gz" -C /backups/ldap "$BACKUP_DATE"

ARCHIVE_SIZE=$(du -h "$BACKUP_DIR.tar.gz" | cut -f1)
log "  Archive: $ARCHIVE_SIZE"

# Upload vers S3
if command -v aws &> /dev/null; then
    log "☁️  Upload vers S3..."

    aws s3 cp "$BACKUP_DIR.tar.gz" \
        "$S3_BUCKET/daily/$BACKUP_DATE.tar.gz" \
        --storage-class STANDARD_IA

    # Vérifier l'upload
    if aws s3 ls "$S3_BUCKET/daily/$BACKUP_DATE.tar.gz" &> /dev/null; then
        log "  ✅ Upload S3 réussi"

        # Supprimer la copie locale après upload réussi
        rm -rf "$BACKUP_DIR"
        log "  🗑️  Copie locale supprimée"
    else
        log "  ❌ Échec upload S3"
        exit 1
    fi
fi

# Rotation des anciens backups locaux
log "🗑️  Rotation des backups locaux..."
find /backups/ldap -name "*.tar.gz" -type f -mtime +$RETENTION_DAYS -delete

# Rotation des backups S3 (garder 90 jours pour conformité)
if command -v aws &> /dev/null; then
    CUTOFF_DATE=$(date -d "$RETENTION_DAYS days ago" +%Y-%m-%d)

    aws s3 ls "$S3_BUCKET/daily/" | while read -r line; do
        BACKUP_FILE=$(echo "$line" | awk '{print $4}')
        BACKUP_DATE=$(echo "$BACKUP_FILE" | grep -oP '\d{4}-\d{2}-\d{2}')

        if [[ "$BACKUP_DATE" < "$CUTOFF_DATE" ]]; then
            log "  Suppression ancien backup S3: $BACKUP_FILE"
            aws s3 rm "$S3_BUCKET/daily/$BACKUP_FILE"
        fi
    done
fi

# Test de restauration (1 fois par semaine)
if [ "$(date +%u)" -eq 7 ]; then  # Dimanche
    log "🧪 Test de restauration..."
    /opt/ldap-monitor/scripts/test-backup-restore.sh "$BACKUP_DIR.tar.gz"
fi

log "✅ Backup quotidien terminé - Archive: $ARCHIVE_SIZE"

# Notification Slack
if [ -n "${SLACK_WEBHOOK:-}" ]; then
    curl -X POST "$SLACK_WEBHOOK" \
        -H 'Content-Type: application/json' \
        -d @- << SLACK
{
    "text": "💾 LDAP Backup Completed",
    "attachments": [{
        "color": "good",
        "fields": [
            {"title": "Date", "value": "$BACKUP_DATE", "short": true},
            {"title": "Size", "value": "$ARCHIVE_SIZE", "short": true},
            {"title": "Location", "value": "S3 + Local", "short": true}
        ]
    }]
}
SLACK
fi
```

---

## Workflows CI/CD

### GitHub Actions - Audit LDAP sur Pull Request

```yaml
# .github/workflows/ldap-audit.yml
name: LDAP Configuration Audit

on:
  pull_request:
    paths:
      - 'infrastructure/ldap/**'
      - 'config/ldap-*.yaml'
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM

jobs:
  audit-ldap:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install LDAP Health Monitor
        run: |
          pip install ldap-health-monitor

      - name: Configure credentials
        env:
          LDAP_PASSWORD: ${{ secrets.LDAP_PASSWORD }}
          SLACK_WEBHOOK: ${{ secrets.SLACK_WEBHOOK }}
        run: |
          echo "LDAP_PASSWORD=$LDAP_PASSWORD" >> $GITHUB_ENV
          echo "SLACK_WEBHOOK=$SLACK_WEBHOOK" >> $GITHUB_ENV

      - name: Validate LDAP configuration
        run: |
          ldap-monitor -c config/ldap-staging.yaml config validate

      - name: Run health check
        id: health_check
        run: |
          ldap-monitor -c config/ldap-staging.yaml audit health \
            --format json \
            --output health-report.json

      - name: Run full audit
        id: audit
        run: |
          ldap-monitor -c config/ldap-staging.yaml audit all \
            --format json \
            --output audit-report.json

      - name: Generate HTML report
        run: |
          ldap-monitor -c config/ldap-staging.yaml audit all \
            --format html \
            --output audit-report.html

      - name: Upload reports
        uses: actions/upload-artifact@v3
        with:
          name: ldap-audit-reports
          path: |
            health-report.json
            audit-report.json
            audit-report.html

      - name: Check for critical issues
        run: |
          CRITICAL_COUNT=$(jq '[.issues[] | select(.severity == "critical")] | length' audit-report.json)

          if [ "$CRITICAL_COUNT" -gt 0 ]; then
            echo "❌ $CRITICAL_COUNT critical issues found!"
            exit 1
          fi

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = JSON.parse(fs.readFileSync('audit-report.json', 'utf8'));

            const summary = `## LDAP Audit Report

            **Status:** ${report.health.status}
            **Total Issues:** ${report.issues.length}
            **Critical:** ${report.issues.filter(i => i.severity === 'critical').length}
            **Warning:** ${report.issues.filter(i => i.severity === 'warning').length}

            ### Top Issues
            ${report.issues.slice(0, 5).map(i => `- [${i.severity}] ${i.title}`).join('\n')}

            [View Full Report](https://github.com/${context.repo.owner}/${context.repo.repo}/actions/runs/${context.runId})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });

      - name: Notify Slack
        if: failure()
        run: |
          curl -X POST $SLACK_WEBHOOK \
            -H 'Content-Type: application/json' \
            -d '{
              "text": "❌ LDAP Audit Failed in CI",
              "attachments": [{
                "color": "danger",
                "fields": [
                  {"title": "Repository", "value": "${{ github.repository }}", "short": true},
                  {"title": "Branch", "value": "${{ github.ref }}", "short": true},
                  {"title": "Run", "value": "${{ github.server_url }}/${{ github.repository }}/actions/runs/${{ github.run_id }}", "short": false}
                ]
              }]
            }'
```

### GitLab CI - Pipeline LDAP

```yaml
# .gitlab-ci.yml
stages:
  - validate
  - audit
  - backup
  - deploy

variables:
  LDAP_CONFIG: "config/ldap-production.yaml"

.ldap_base:
  image: python:3.11-slim
  before_script:
    - pip install ldap-health-monitor
    - export LDAP_PASSWORD="$LDAP_PASSWORD_SECRET"

validate_config:
  extends: .ldap_base
  stage: validate
  script:
    - ldap-monitor -c $LDAP_CONFIG config validate
  only:
    changes:
      - config/*.yaml
      - infrastructure/ldap/**

health_check:
  extends: .ldap_base
  stage: audit
  script:
    - ldap-monitor -c $LDAP_CONFIG test connection
    - ldap-monitor -c $LDAP_CONFIG audit health --format json --output health.json
  artifacts:
    paths:
      - health.json
    expire_in: 30 days

full_audit:
  extends: .ldap_base
  stage: audit
  script:
    - ldap-monitor -c $LDAP_CONFIG audit all --format html --output audit-report.html
    - ldap-monitor -c $LDAP_CONFIG audit all --format json --output audit-report.json
  artifacts:
    paths:
      - audit-report.html
      - audit-report.json
    expire_in: 90 days
  only:
    - schedules
    - main

backup_production:
  extends: .ldap_base
  stage: backup
  script:
    - ldap-monitor -c $LDAP_CONFIG backup full --output backup-$(date +%Y%m%d).ldif
    - gzip backup-*.ldif
  artifacts:
    paths:
      - backup-*.ldif.gz
    expire_in: 90 days
  only:
    - schedules
  when: manual

security_audit:
  extends: .ldap_base
  stage: audit
  script:
    - ldap-monitor -c $LDAP_CONFIG audit security --format json --output security.json
    - |
      CRITICAL=$(jq '[.issues[] | select(.severity == "critical")] | length' security.json)
      if [ "$CRITICAL" -gt 0 ]; then
        echo "Critical security issues found!"
        exit 1
      fi
  only:
    - main
    - merge_requests
```

---

## Intégration n8n

### Workflow n8n - Automatisation Onboarding

```json
{
  "name": "LDAP User Onboarding",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "onboard-user",
        "responseMode": "responseNode"
      },
      "name": "Webhook - New User",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "authentication": "headerAuth",
        "url": "https://hr-system.company.com/api/validate-employee",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "employee_id",
              "value": "={{ $json.employee_id }}"
            }
          ]
        }
      },
      "name": "Validate in HR System",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "command": "ldap-monitor user create --email {{ $json.email }} --name \"{{ $json.full_name }}\" --department {{ $json.department }}"
      },
      "name": "Create LDAP User",
      "type": "n8n-nodes-base.executeCommand",
      "position": [650, 300]
    },
    {
      "parameters": {
        "command": "ldap-monitor group add-member --group {{ $json.default_group }} --user {{ $json.email }}"
      },
      "name": "Add to Default Groups",
      "type": "n8n-nodes-base.executeCommand",
      "position": [850, 300]
    },
    {
      "parameters": {
        "functionCode": "// Generate temp password\nconst crypto = require('crypto');\nconst tempPassword = crypto.randomBytes(16).toString('hex');\n\nreturn [{\n  json: {\n    ...items[0].json,\n    temp_password: tempPassword\n  }\n}];"
      },
      "name": "Generate Temp Password",
      "type": "n8n-nodes-base.function",
      "position": [1050, 300]
    },
    {
      "parameters": {
        "operation": "send",
        "fromEmail": "noreply@company.com",
        "toEmail": "={{ $json.email }}",
        "subject": "Welcome to Company - LDAP Account Created",
        "emailFormat": "html",
        "text": "=<h1>Welcome {{ $json.full_name }}!</h1>\n<p>Your LDAP account has been created.</p>\n<p><strong>Username:</strong> {{ $json.email }}</p>\n<p><strong>Temporary Password:</strong> {{ $json.temp_password }}</p>\n<p>Please change your password on first login.</p>"
      },
      "name": "Send Welcome Email",
      "type": "n8n-nodes-base.emailSend",
      "position": [1250, 300]
    },
    {
      "parameters": {
        "channel": "#it-onboarding",
        "text": "=✅ New user onboarded: {{ $json.full_name }} ({{ $json.email }})\nDepartment: {{ $json.department }}",
        "otherOptions": {}
      },
      "name": "Notify Slack",
      "type": "n8n-nodes-base.slack",
      "position": [1450, 300]
    },
    {
      "parameters": {
        "command": "ldap-monitor audit users --user {{ $json.email }} --format json"
      },
      "name": "Verify User Created",
      "type": "n8n-nodes-base.executeCommand",
      "position": [1050, 450]
    },
    {
      "parameters": {
        "conditions": {
          "string": [
            {
              "value1": "={{ $json.success }}",
              "value2": "true"
            }
          ]
        }
      },
      "name": "Check Creation Success",
      "type": "n8n-nodes-base.if",
      "position": [1250, 450]
    }
  ],
  "connections": {
    "Webhook - New User": {
      "main": [[{"node": "Validate in HR System", "type": "main", "index": 0}]]
    },
    "Validate in HR System": {
      "main": [[{"node": "Create LDAP User", "type": "main", "index": 0}]]
    },
    "Create LDAP User": {
      "main": [[{"node": "Add to Default Groups", "type": "main", "index": 0}]]
    },
    "Add to Default Groups": {
      "main": [[{"node": "Generate Temp Password", "type": "main", "index": 0}]]
    },
    "Generate Temp Password": {
      "main": [
        [
          {"node": "Send Welcome Email", "type": "main", "index": 0},
          {"node": "Verify User Created", "type": "main", "index": 0}
        ]
      ]
    },
    "Send Welcome Email": {
      "main": [[{"node": "Notify Slack", "type": "main", "index": 0}]]
    },
    "Verify User Created": {
      "main": [[{"node": "Check Creation Success", "type": "main", "index": 0}]]
    }
  }
}
```

---

## Scripts Kubernetes

### CronJob Kubernetes - Daily Audit

```yaml
# k8s/cronjob-ldap-audit.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: ldap-daily-audit
  namespace: infrastructure
spec:
  schedule: "0 6 * * *"  # Daily at 6 AM
  concurrencyPolicy: Forbid
  successfulJobsHistoryLimit: 7
  failedJobsHistoryLimit: 3

  jobTemplate:
    spec:
      template:
        metadata:
          labels:
            app: ldap-monitor
            job: daily-audit
        spec:
          restartPolicy: OnFailure

          serviceAccountName: ldap-monitor

          volumes:
            - name: config
              configMap:
                name: ldap-monitor-config
            - name: credentials
              secret:
                secretName: ldap-credentials
            - name: reports
              persistentVolumeClaim:
                claimName: ldap-reports-pvc

          containers:
            - name: ldap-audit
              image: company/ldap-health-monitor:latest
              imagePullPolicy: Always

              env:
                - name: LDAP_PASSWORD
                  valueFrom:
                    secretKeyRef:
                      name: ldap-credentials
                      key: password
                - name: SLACK_WEBHOOK
                  valueFrom:
                    secretKeyRef:
                      name: slack-credentials
                      key: webhook-url

              volumeMounts:
                - name: config
                  mountPath: /etc/ldap-monitor
                  readOnly: true
                - name: credentials
                  mountPath: /secrets
                  readOnly: true
                - name: reports
                  mountPath: /reports

              command:
                - /bin/bash
                - -c
                - |
                  set -e

                  REPORT_DATE=$(date +%Y-%m-%d)
                  REPORT_DIR="/reports/${REPORT_DATE}"

                  mkdir -p "$REPORT_DIR"

                  echo "Running LDAP audit..."

                  # Full audit
                  ldap-monitor -c /etc/ldap-monitor/config.yaml audit all \
                    --format json \
                    --output "$REPORT_DIR/audit.json"

                  ldap-monitor -c /etc/ldap-monitor/config.yaml audit all \
                    --format html \
                    --output "$REPORT_DIR/audit.html"

                  # Check for critical issues
                  CRITICAL=$(jq '[.issues[] | select(.severity == "critical")] | length' "$REPORT_DIR/audit.json")

                  if [ "$CRITICAL" -gt 0 ]; then
                    echo "Found $CRITICAL critical issues!"

                    # Send Slack alert
                    curl -X POST "$SLACK_WEBHOOK" \
                      -H 'Content-Type: application/json' \
                      -d "{\"text\": \"⚠️ LDAP Audit: $CRITICAL critical issues found!\"}"

                    exit 1
                  fi

                  echo "Audit completed successfully"

              resources:
                requests:
                  memory: "256Mi"
                  cpu: "100m"
                limits:
                  memory: "512Mi"
                  cpu: "500m"

---
apiVersion: v1
kind: ConfigMap
metadata:
  name: ldap-monitor-config
  namespace: infrastructure
data:
  config.yaml: |
    ldap:
      server: ldaps://ad.company.local
      port: 636
      bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=company,DC=local
      bind_password: ${LDAP_PASSWORD}
      base_dn: DC=company,DC=local

    audit:
      users:
        required_attributes:
          - mail
          - givenName
          - sn
        inactive_days: 90

    alerts:
      slack:
        enabled: true
        webhook_url: ${SLACK_WEBHOOK}

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: ldap-reports-pvc
  namespace: infrastructure
spec:
  accessModes:
    - ReadWriteMany
  resources:
    requests:
      storage: 10Gi
  storageClassName: nfs-client
```

---

## Orchestration Ansible

### Playbook Ansible - Déploiement Multi-Serveurs

```yaml
# ansible/ldap-monitor-deploy.yml
---
- name: Deploy LDAP Health Monitor
  hosts: ldap_monitors
  become: yes

  vars:
    ldap_monitor_version: "1.0.0"
    install_dir: "/opt/ldap-monitor"
    config_dir: "/etc/ldap-monitor"
    log_dir: "/var/log/ldap-monitor"
    backup_dir: "/backups/ldap"

  tasks:
    - name: Install system dependencies
      apt:
        name:
          - python3
          - python3-pip
          - python3-venv
          - ldap-utils
        state: present
        update_cache: yes

    - name: Create ldap-monitor user
      user:
        name: ldap-monitor
        system: yes
        shell: /bin/bash
        home: "{{ install_dir }}"

    - name: Create directories
      file:
        path: "{{ item }}"
        state: directory
        owner: ldap-monitor
        group: ldap-monitor
        mode: '0755'
      loop:
        - "{{ install_dir }}"
        - "{{ config_dir }}"
        - "{{ log_dir }}"
        - "{{ backup_dir }}"

    - name: Install LDAP Health Monitor
      pip:
        name: ldap-health-monitor
        version: "{{ ldap_monitor_version }}"
        virtualenv: "{{ install_dir }}/venv"
        virtualenv_command: python3 -m venv

    - name: Deploy configuration
      template:
        src: templates/config.yaml.j2
        dest: "{{ config_dir }}/config.yaml"
        owner: ldap-monitor
        group: ldap-monitor
        mode: '0600'
      notify: validate config

    - name: Deploy credentials
      template:
        src: templates/credentials.env.j2
        dest: "{{ config_dir }}/credentials.env"
        owner: ldap-monitor
        group: ldap-monitor
        mode: '0600'
      no_log: yes

    - name: Deploy automation scripts
      copy:
        src: "scripts/{{ item }}"
        dest: "{{ install_dir }}/scripts/{{ item }}"
        owner: ldap-monitor
        group: ldap-monitor
        mode: '0755'
      loop:
        - quick-health-check.sh
        - daily-audit.sh
        - daily-backup.sh
        - weekly-cleanup.sh

    - name: Configure cron jobs
      cron:
        name: "{{ item.name }}"
        minute: "{{ item.minute }}"
        hour: "{{ item.hour }}"
        day: "{{ item.day | default('*') }}"
        weekday: "{{ item.weekday | default('*') }}"
        job: "{{ item.job }}"
        user: ldap-monitor
      loop:
        - name: "Health check"
          minute: "*/5"
          hour: "*"
          job: "{{ install_dir }}/scripts/quick-health-check.sh"

        - name: "Daily backup"
          minute: "0"
          hour: "2"
          job: "{{ install_dir }}/scripts/daily-backup.sh"

        - name: "Daily audit"
          minute: "0"
          hour: "6"
          job: "{{ install_dir }}/scripts/daily-audit.sh"

        - name: "Weekly cleanup"
          minute: "0"
          hour: "3"
          weekday: "0"
          job: "{{ install_dir }}/scripts/weekly-cleanup.sh"

    - name: Configure logrotate
      copy:
        dest: /etc/logrotate.d/ldap-monitor
        content: |
          {{ log_dir }}/*.log {
            daily
            rotate 30
            compress
            delaycompress
            missingok
            notifempty
            create 0644 ldap-monitor ldap-monitor
          }

    - name: Deploy systemd service for monitoring daemon
      template:
        src: templates/ldap-monitor.service.j2
        dest: /etc/systemd/system/ldap-monitor.service
      notify: reload systemd

    - name: Enable and start monitoring service
      systemd:
        name: ldap-monitor
        enabled: yes
        state: started

  handlers:
    - name: validate config
      command: "{{ install_dir }}/venv/bin/ldap-monitor -c {{ config_dir }}/config.yaml config validate"
      become_user: ldap-monitor

    - name: reload systemd
      systemd:
        daemon_reload: yes
```

### Playbook Ansible - Vérification Conformité

```yaml
# ansible/ldap-compliance-check.yml
---
- name: LDAP Compliance Check
  hosts: ldap_monitors
  become: yes
  become_user: ldap-monitor

  vars:
    config_file: "/etc/ldap-monitor/config.yaml"
    report_dir: "/var/reports/compliance"

  tasks:
    - name: Create report directory
      file:
        path: "{{ report_dir }}/{{ ansible_date_time.date }}"
        state: directory

    - name: Run SOC2 compliance audit
      command: >
        /opt/ldap-monitor/venv/bin/ldap-monitor
        -c {{ config_file }}
        audit all
        --compliance soc2
        --format json
        --output {{ report_dir }}/{{ ansible_date_time.date }}/soc2.json
      register: soc2_audit

    - name: Run security audit
      command: >
        /opt/ldap-monitor/venv/bin/ldap-monitor
        -c {{ config_file }}
        audit security
        --format json
        --output {{ report_dir }}/{{ ansible_date_time.date }}/security.json
      register: security_audit

    - name: Parse audit results
      set_fact:
        critical_issues: "{{ lookup('file', report_dir + '/' + ansible_date_time.date + '/security.json') | from_json | json_query('[?severity==`critical`]') | length }}"

    - name: Send alert if critical issues found
      uri:
        url: "{{ slack_webhook }}"
        method: POST
        body_format: json
        body:
          text: "⚠️ LDAP Compliance Check: {{ critical_issues }} critical issues found on {{ inventory_hostname }}"
      when: critical_issues | int > 0
      delegate_to: localhost
```

---

## Conclusion

Ces scripts d'automatisation couvrent les principaux scénarios d'utilisation de LDAP Health Monitor :

- **Monitoring continu** avec cron et health checks
- **Audits automatisés** quotidiens, hebdomadaires, mensuels
- **Backups planifiés** avec rotation et tests de restauration
- **Intégration CI/CD** pour validation continue
- **Orchestration** avec Kubernetes et Ansible
- **Workflows n8n** pour automatisation avancée

Pour des exemples de configurations avancées, consultez [Advanced-Configs.md](./Advanced-Configs.md).
