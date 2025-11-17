# Guide d'Automatisation Cron et Systemd

Guide complet pour automatiser LDAP Health Monitor avec cron, systemd timers, et autres planificateurs.

## 🎯 Vue d'Ensemble

Ce guide couvre :

- Automatisation avec cron
- Utilisation de systemd timers
- Planification d'audits et rapports
- Scripts d'automatisation
- Gestion des logs et notifications
- Bonnes pratiques d'automatisation

## ⏰ Automatisation avec Cron

### Configuration Basique

```bash
# Éditer crontab
crontab -e

# Audit quotidien à 2h du matin
0 2 * * * /usr/local/bin/ldap-monitor audit all --format html --output /var/reports/ldap-audit-$(date +\%Y\%m\%d).html

# Health check toutes les heures
0 * * * * /usr/local/bin/ldap-monitor audit health --quiet

# Rapport hebdomadaire le lundi à 8h
0 8 * * 1 /usr/local/bin/ldap-monitor audit all --email admin@example.com

# Sauvegarde mensuelle le 1er à minuit
0 0 1 * * /usr/local/bin/ldap-monitor backup create --compress
```

### Exemples Avancés

```bash
# Fichier: /etc/cron.d/ldap-monitor
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=admin@example.com
LDAP_CONFIG=/etc/ldap-monitor/config.yaml

# Health checks fréquents (toutes les 15 minutes)
*/15 * * * * ldapmon /usr/local/bin/ldap-monitor audit health --config $LDAP_CONFIG --quiet || echo "LDAP Health Check Failed" | mail -s "LDAP Alert" $MAILTO

# Audit utilisateurs inactifs quotidien
0 3 * * * ldapmon /usr/local/bin/ldap-monitor audit users --inactive --days 90 --output /var/reports/inactive-users-$(date +\%Y\%m\%d).csv

# Audit de sécurité hebdomadaire
0 4 * * 0 ldapmon /usr/local/bin/ldap-monitor audit security --comprehensive --format pdf --output /var/reports/security/weekly-$(date +\%Y-W\%U).pdf

# Nettoyage des anciens rapports (>30 jours)
0 5 * * * ldapmon find /var/reports -name "*.html" -mtime +30 -delete

# Export mensuel pour archivage
0 1 1 * * ldapmon /usr/local/bin/ldap-monitor export all --format json --output /var/archives/ldap-export-$(date +\%Y-\%m).json.gz --compress

# Vérification quotidienne des groupes privilégiés
0 6 * * * ldapmon /usr/local/bin/ldap-monitor audit groups --privileged --alert-on-changes

# Synchronisation avec système externe
*/30 * * * * ldapmon /usr/local/bin/ldap-monitor export users --format csv --output /tmp/ldap-users.csv && rsync /tmp/ldap-users.csv backup-server:/data/
```

### Script Wrapper pour Cron

```bash
#!/bin/bash
# /usr/local/bin/ldap-monitor-cron-wrapper.sh

# Configuration
SCRIPT_NAME="ldap-monitor-cron"
LOG_DIR="/var/log/ldap-monitor"
LOG_FILE="$LOG_DIR/cron-$(date +%Y%m%d).log"
LOCK_FILE="/var/lock/ldap-monitor-cron.lock"
MAILTO="admin@example.com"
RETENTION_DAYS=30

# Créer répertoire logs
mkdir -p "$LOG_DIR"

# Fonction de logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Fonction d'erreur
error() {
    log "ERROR: $1"
    echo "$1" | mail -s "LDAP Monitor Cron Error" "$MAILTO"
    exit 1
}

# Vérifier lock (éviter exécutions simultanées)
if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE")
    if ps -p "$PID" > /dev/null 2>&1; then
        log "Already running (PID: $PID), exiting"
        exit 0
    else
        log "Stale lock file found, removing"
        rm -f "$LOCK_FILE"
    fi
fi

# Créer lock
echo $$ > "$LOCK_FILE"

# Trap pour cleanup
trap "rm -f $LOCK_FILE" EXIT INT TERM

# Début
log "Starting LDAP Monitor cron job"

# Vérifier configuration
if ! ldap-monitor config validate; then
    error "Configuration validation failed"
fi

# Exécuter commande
COMMAND="$@"
log "Executing: $COMMAND"

if $COMMAND >> "$LOG_FILE" 2>&1; then
    log "Command completed successfully"
    EXIT_CODE=0
else
    EXIT_CODE=$?
    error "Command failed with exit code: $EXIT_CODE"
fi

# Nettoyage logs anciens
find "$LOG_DIR" -name "cron-*.log" -mtime +$RETENTION_DAYS -delete

# Fin
log "Completed"
exit $EXIT_CODE
```

```bash
# Utilisation dans crontab
0 2 * * * /usr/local/bin/ldap-monitor-cron-wrapper.sh ldap-monitor audit all --format html --output /var/reports/daily-audit.html
```

## ⚙️ Automatisation avec Systemd Timers

### Service Systemd

```ini
# /etc/systemd/system/ldap-monitor-audit.service
[Unit]
Description=LDAP Health Monitor Audit
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=ldapmon
Group=ldapmon
WorkingDirectory=/var/lib/ldap-monitor

# Variables d'environnement
Environment="LDAP_CONFIG=/etc/ldap-monitor/config.yaml"
EnvironmentFile=-/etc/ldap-monitor/env

# Commande
ExecStart=/usr/local/bin/ldap-monitor audit all \
    --format html \
    --output /var/reports/ldap-audit-%Y%m%d.html

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ldap-monitor-audit

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/reports /var/lib/ldap-monitor

# Limites ressources
MemoryLimit=512M
CPUQuota=50%
TimeoutStartSec=300

[Install]
WantedBy=multi-user.target
```

### Timer Systemd

```ini
# /etc/systemd/system/ldap-monitor-audit.timer
[Unit]
Description=LDAP Health Monitor Audit Timer
Requires=ldap-monitor-audit.service

[Timer]
# Exécuter quotidiennement à 2h du matin
OnCalendar=daily
# Décalage aléatoire de 0-30 minutes
RandomizedDelaySec=30min
# Heure précise
OnCalendar=*-*-* 02:00:00
# Persister à travers reboots
Persistent=true
# Unité à activer
Unit=ldap-monitor-audit.service

[Install]
WantedBy=timers.target
```

### Services Multiples

```ini
# /etc/systemd/system/ldap-monitor-health.service
[Unit]
Description=LDAP Health Check
After=network-online.target

[Service]
Type=oneshot
User=ldapmon
ExecStart=/usr/local/bin/ldap-monitor audit health
StandardOutput=journal
```

```ini
# /etc/systemd/system/ldap-monitor-health.timer
[Unit]
Description=LDAP Health Check Timer (every 15 minutes)

[Timer]
OnBootSec=5min
OnUnitActiveSec=15min
Unit=ldap-monitor-health.service

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/ldap-monitor-security.service
[Unit]
Description=LDAP Security Audit
After=network-online.target

[Service]
Type=oneshot
User=ldapmon
ExecStart=/usr/local/bin/ldap-monitor audit security --comprehensive
StandardOutput=journal
```

```ini
# /etc/systemd/system/ldap-monitor-security.timer
[Unit]
Description=LDAP Security Audit Timer (weekly)

[Timer]
OnCalendar=Sun 04:00
Persistent=true
Unit=ldap-monitor-security.service

[Install]
WantedBy=timers.target
```

### Activation et Gestion

```bash
# Recharger systemd
systemctl daemon-reload

# Activer et démarrer timers
systemctl enable ldap-monitor-audit.timer
systemctl start ldap-monitor-audit.timer

systemctl enable ldap-monitor-health.timer
systemctl start ldap-monitor-health.timer

systemctl enable ldap-monitor-security.timer
systemctl start ldap-monitor-security.timer

# Vérifier statut
systemctl list-timers ldap-monitor-*

# Voir les logs
journalctl -u ldap-monitor-audit.service -f

# Exécution manuelle
systemctl start ldap-monitor-audit.service

# Désactiver
systemctl stop ldap-monitor-audit.timer
systemctl disable ldap-monitor-audit.timer
```

### Calendrier OnCalendar Avancé

```ini
# Exemples de syntaxe OnCalendar

# Toutes les 15 minutes
OnCalendar=*:0/15

# Toutes les heures
OnCalendar=hourly

# Quotidien à 2h
OnCalendar=daily
OnCalendar=*-*-* 02:00:00

# Hebdomadaire (dimanche à 3h)
OnCalendar=Sun *-*-* 03:00:00

# Mensuel (1er du mois à minuit)
OnCalendar=*-*-01 00:00:00

# Jours ouvrables à 8h
OnCalendar=Mon-Fri *-*-* 08:00:00

# Multiple times
OnCalendar=Mon,Wed,Fri 09:00
OnCalendar=Tue,Thu 14:00

# Trimestre (tous les 3 mois)
OnCalendar=*-01,04,07,10-01 00:00:00
```

## 📊 Scripts d'Automatisation Avancés

### Script de Rapport Quotidien

```bash
#!/bin/bash
# /usr/local/bin/ldap-daily-report.sh

set -euo pipefail

# Configuration
DATE=$(date +%Y%m%d)
REPORT_DIR="/var/reports/daily"
ARCHIVE_DIR="/var/archives/reports"
CONFIG="/etc/ldap-monitor/config.yaml"
EMAIL_TO="admin@example.com,team@example.com"
RETENTION_DAYS=90

# Créer répertoires
mkdir -p "$REPORT_DIR" "$ARCHIVE_DIR"

# Fichiers de sortie
HTML_REPORT="$REPORT_DIR/ldap-report-$DATE.html"
CSV_USERS="$REPORT_DIR/users-$DATE.csv"
CSV_GROUPS="$REPORT_DIR/groups-$DATE.csv"
SUMMARY="$REPORT_DIR/summary-$DATE.txt"

echo "=== LDAP Daily Report - $DATE ===" | tee "$SUMMARY"
echo "" | tee -a "$SUMMARY"

# 1. Health Check
echo "Running health check..." | tee -a "$SUMMARY"
if ldap-monitor audit health --config "$CONFIG" --quiet; then
    echo "✓ Health check PASSED" | tee -a "$SUMMARY"
else
    echo "✗ Health check FAILED" | tee -a "$SUMMARY"
    echo "CRITICAL: LDAP health check failed" | mail -s "LDAP Health Alert" "$EMAIL_TO"
fi

# 2. Audit complet
echo "Running full audit..." | tee -a "$SUMMARY"
ldap-monitor audit all \
    --config "$CONFIG" \
    --format html \
    --output "$HTML_REPORT"

# 3. Export utilisateurs
echo "Exporting users..." | tee -a "$SUMMARY"
USER_COUNT=$(ldap-monitor export users \
    --config "$CONFIG" \
    --format csv \
    --output "$CSV_USERS" \
    --count)
echo "Total users: $USER_COUNT" | tee -a "$SUMMARY"

# 4. Export groupes
echo "Exporting groups..." | tee -a "$SUMMARY"
GROUP_COUNT=$(ldap-monitor export groups \
    --config "$CONFIG" \
    --format csv \
    --output "$CSV_GROUPS" \
    --count)
echo "Total groups: $GROUP_COUNT" | tee -a "$SUMMARY"

# 5. Utilisateurs inactifs
echo "Checking inactive users..." | tee -a "$SUMMARY"
INACTIVE_COUNT=$(ldap-monitor audit users \
    --config "$CONFIG" \
    --inactive \
    --days 90 \
    --count)
echo "Inactive users (>90 days): $INACTIVE_COUNT" | tee -a "$SUMMARY"

if [ "$INACTIVE_COUNT" -gt 0 ]; then
    ldap-monitor audit users \
        --inactive \
        --days 90 \
        --format csv \
        --output "$REPORT_DIR/inactive-users-$DATE.csv"
fi

# 6. Audit de sécurité
echo "Running security audit..." | tee -a "$SUMMARY"
ldap-monitor audit security \
    --config "$CONFIG" \
    --brief | tee -a "$SUMMARY"

# 7. Créer archive
echo "Creating archive..." | tee -a "$SUMMARY"
tar -czf "$ARCHIVE_DIR/ldap-reports-$DATE.tar.gz" \
    -C "$REPORT_DIR" \
    .

# 8. Envoyer email avec rapport
{
    echo "LDAP Daily Report - $DATE"
    echo ""
    cat "$SUMMARY"
    echo ""
    echo "HTML Report: $HTML_REPORT"
    echo "Archive: $ARCHIVE_DIR/ldap-reports-$DATE.tar.gz"
} | mail -s "LDAP Daily Report - $DATE" \
    -a "$HTML_REPORT" \
    "$EMAIL_TO"

# 9. Nettoyage anciens rapports
find "$REPORT_DIR" -type f -mtime +$RETENTION_DAYS -delete
find "$ARCHIVE_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete

echo "Report completed successfully" | tee -a "$SUMMARY"
```

### Script de Monitoring Continu

```bash
#!/bin/bash
# /usr/local/bin/ldap-continuous-monitor.sh

# Configuration
INTERVAL=300  # 5 minutes
LOG_FILE="/var/log/ldap-monitor/continuous.log"
METRICS_FILE="/var/lib/ldap-monitor/metrics.json"
ALERT_THRESHOLD=3  # Nombre d'échecs avant alerte

# Compteur d'échecs
FAIL_COUNT=0

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_ldap_health() {
    if ldap-monitor audit health --quiet; then
        return 0
    else
        return 1
    fi
}

collect_metrics() {
    ldap-monitor monitor metrics \
        --format json \
        --output "$METRICS_FILE"
}

send_alert() {
    local message="$1"
    log "ALERT: $message"

    # Email
    echo "$message" | mail -s "LDAP Monitor Alert" admin@example.com

    # Slack (si configuré)
    if [ -n "${SLACK_WEBHOOK:-}" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\":\"$message\"}"
    fi
}

# Boucle principale
log "Starting continuous monitoring (interval: ${INTERVAL}s)"

while true; do
    if check_ldap_health; then
        log "Health check OK"
        FAIL_COUNT=0

        # Collecter métriques
        collect_metrics

    else
        FAIL_COUNT=$((FAIL_COUNT + 1))
        log "Health check FAILED (failures: $FAIL_COUNT)"

        if [ $FAIL_COUNT -ge $ALERT_THRESHOLD ]; then
            send_alert "LDAP health check has failed $FAIL_COUNT consecutive times"
        fi
    fi

    sleep $INTERVAL
done
```

### Script de Rapport Hebdomadaire

```bash
#!/bin/bash
# /usr/local/bin/ldap-weekly-report.sh

set -euo pipefail

WEEK=$(date +%Y-W%U)
REPORT_DIR="/var/reports/weekly"
mkdir -p "$REPORT_DIR"

REPORT_FILE="$REPORT_DIR/weekly-report-$WEEK.html"

# Générer rapport HTML complet
cat > "$REPORT_FILE" << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>LDAP Weekly Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #333; }
        .section { margin: 20px 0; padding: 15px; border: 1px solid #ddd; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: #f5f5f5; }
        .alert { color: red; font-weight: bold; }
        .ok { color: green; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #4CAF50; color: white; }
    </style>
</head>
<body>
EOF

echo "<h1>LDAP Weekly Report - Week $WEEK</h1>" >> "$REPORT_FILE"
echo "<p>Generated: $(date)</p>" >> "$REPORT_FILE"

# Section: Statistiques globales
echo "<div class='section'>" >> "$REPORT_FILE"
echo "<h2>Global Statistics</h2>" >> "$REPORT_FILE"

TOTAL_USERS=$(ldap-monitor audit users --count)
TOTAL_GROUPS=$(ldap-monitor audit groups --count)
INACTIVE_USERS=$(ldap-monitor audit users --inactive --days 90 --count)

cat >> "$REPORT_FILE" << EOF
<div class="metric">Total Users: <strong>$TOTAL_USERS</strong></div>
<div class="metric">Total Groups: <strong>$TOTAL_GROUPS</strong></div>
<div class="metric">Inactive Users (>90d): <strong>$INACTIVE_USERS</strong></div>
EOF

echo "</div>" >> "$REPORT_FILE"

# Section: Top 10 plus gros groupes
echo "<div class='section'>" >> "$REPORT_FILE"
echo "<h2>Top 10 Largest Groups</h2>" >> "$REPORT_FILE"
echo "<table>" >> "$REPORT_FILE"
echo "<tr><th>Group Name</th><th>Member Count</th></tr>" >> "$REPORT_FILE"

ldap-monitor audit groups --size --top 10 --format csv | tail -n +2 | while IFS=, read -r group count; do
    echo "<tr><td>$group</td><td>$count</td></tr>" >> "$REPORT_FILE"
done

echo "</table>" >> "$REPORT_FILE"
echo "</div>" >> "$REPORT_FILE"

# Fermer HTML
cat >> "$REPORT_FILE" << 'EOF'
</body>
</html>
EOF

# Envoyer par email
mail -s "LDAP Weekly Report - Week $WEEK" \
    -a "$REPORT_FILE" \
    -r "ldap-monitor@example.com" \
    admin@example.com team@example.com < "$REPORT_FILE"

echo "Weekly report generated: $REPORT_FILE"
```

## 🔔 Gestion des Notifications

### Configuration Alertes Email

```yaml
# config/alerts.yaml
alerts:
  email:
    enabled: true
    smtp_server: smtp.example.com
    smtp_port: 587
    use_tls: true
    username: ldap-monitor@example.com
    password: ${SMTP_PASSWORD}
    from: ldap-monitor@example.com
    to:
      - admin@example.com
      - oncall@example.com

    # Templates
    templates:
      subject: "[LDAP] {severity} - {title}"
      body: |
        Alert: {title}
        Severity: {severity}
        Time: {timestamp}
        Details: {details}
```

### Script de Notification Multi-Canal

```bash
#!/bin/bash
# /usr/local/bin/ldap-notify.sh

SEVERITY="$1"  # info, warning, critical
TITLE="$2"
MESSAGE="$3"

# Email
send_email() {
    echo "$MESSAGE" | mail -s "[$SEVERITY] $TITLE" admin@example.com
}

# Slack
send_slack() {
    local color="good"
    [ "$SEVERITY" = "warning" ] && color="warning"
    [ "$SEVERITY" = "critical" ] && color="danger"

    curl -X POST "${SLACK_WEBHOOK}" \
        -H 'Content-Type: application/json' \
        -d @- << EOF
{
    "attachments": [{
        "color": "$color",
        "title": "$TITLE",
        "text": "$MESSAGE",
        "footer": "LDAP Monitor",
        "ts": $(date +%s)
    }]
}
EOF
}

# PagerDuty (pour critical)
send_pagerduty() {
    if [ "$SEVERITY" = "critical" ]; then
        curl -X POST https://events.pagerduty.com/v2/enqueue \
            -H 'Content-Type: application/json' \
            -d @- << EOF
{
    "routing_key": "${PAGERDUTY_KEY}",
    "event_action": "trigger",
    "payload": {
        "summary": "$TITLE",
        "severity": "critical",
        "source": "ldap-monitor",
        "custom_details": {
            "message": "$MESSAGE"
        }
    }
}
EOF
    fi
}

# Exécuter notifications
send_email
send_slack
send_pagerduty
```

## 📁 Organisation des Logs et Rapports

### Structure Recommandée

```bash
/var/lib/ldap-monitor/
├── config/
│   ├── config.yaml
│   ├── alerts.yaml
│   └── schedules.yaml
├── logs/
│   ├── audit/
│   │   ├── audit-20250101.log
│   │   └── audit-20250102.log
│   ├── monitoring/
│   │   └── monitor.log
│   └── cron/
│       └── cron-20250101.log
├── reports/
│   ├── daily/
│   │   ├── report-20250101.html
│   │   └── report-20250102.html
│   ├── weekly/
│   │   └── report-2025-W01.html
│   └── monthly/
│       └── report-2025-01.pdf
└── archives/
    └── reports-2024-12.tar.gz
```

### Script de Rotation des Logs

```bash
#!/bin/bash
# /etc/cron.daily/ldap-monitor-logrotate

LOG_DIR="/var/log/ldap-monitor"
RETENTION=30

# Compresser logs > 1 jour
find "$LOG_DIR" -name "*.log" -mtime +1 -exec gzip {} \;

# Supprimer logs compressés > rétention
find "$LOG_DIR" -name "*.log.gz" -mtime +$RETENTION -delete

# Archiver rapports mensuels
LAST_MONTH=$(date -d "last month" +%Y-%m)
REPORT_DIR="/var/reports"
ARCHIVE_DIR="/var/archives"

if [ -d "$REPORT_DIR/daily" ]; then
    tar -czf "$ARCHIVE_DIR/reports-$LAST_MONTH.tar.gz" \
        -C "$REPORT_DIR/daily" \
        $(find "$REPORT_DIR/daily" -name "*-${LAST_MONTH}*.html")
fi
```

## 📖 Voir Aussi

- [Production Monitoring](Production-Monitoring.md)
- [Backup Strategy](Backup-Strategy.md)
- [Monitoring Configuration](../configuration/Monitoring-Configuration.md)
- [Docker Deployment](Docker-Deployment.md)
