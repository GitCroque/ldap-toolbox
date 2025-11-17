# Journaux d'Audit et Monitoring de Sécurité

## Table des Matières

- [Introduction](#introduction)
- [Architecture de Logging](#architecture-de-logging)
- [Types de Logs](#types-de-logs)
- [Configuration des Logs](#configuration-des-logs)
- [Niveaux de Logging](#niveaux-de-logging)
- [Formats de Logs](#formats-de-logs)
- [Rotation et Rétention](#rotation-et-rétention)
- [Centralisation des Logs](#centralisation-des-logs)
- [Analyse et Corrélation](#analyse-et-corrélation)
- [Alertes de Sécurité](#alertes-de-sécurité)
- [Intégration SIEM](#intégration-siem)
- [Conformité et Audit](#conformité-et-audit)
- [Forensique et Investigation](#forensique-et-investigation)

## Introduction

Les journaux d'audit sont essentiels pour la sécurité, la conformité et le dépannage. Ce guide couvre la configuration complète du système de logging pour LDAP Health Monitor, de la collecte à l'analyse.

### Objectifs du Logging

```
┌─────────────────────────────────────────────────────────┐
│              OBJECTIFS DU LOGGING                        │
├─────────────────────────────────────────────────────────┤
│  1. Sécurité        →  Détection des menaces            │
│  2. Conformité      →  Preuves d'audit                  │
│  3. Dépannage       →  Résolution des incidents         │
│  4. Analyse         →  Insights opérationnels           │
│  5. Forensique      →  Investigation post-incident      │
└─────────────────────────────────────────────────────────┘
```

### Flux de Logging

```
┌──────────────┐
│ Application  │
└──────┬───────┘
       │
       ├──────────────┬──────────────┬──────────────┐
       │              │              │              │
       ▼              ▼              ▼              ▼
┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐
│  Security  │ │   Audit    │ │   Access   │ │Application │
│    Logs    │ │    Logs    │ │    Logs    │ │    Logs    │
└──────┬─────┘ └──────┬─────┘ └──────┬─────┘ └──────┬─────┘
       │              │              │              │
       └──────────────┴──────────────┴──────────────┘
                      │
                      ▼
              ┌──────────────┐
              │ Log Collector│
              │   (rsyslog,  │
              │  fluentd)    │
              └──────┬───────┘
                     │
       ┌─────────────┼─────────────┐
       │             │             │
       ▼             ▼             ▼
┌────────────┐ ┌────────────┐ ┌────────────┐
│  Local     │ │   SIEM     │ │   Cloud    │
│  Storage   │ │ (Splunk,   │ │  Storage   │
│            │ │  Elastic)  │ │  (S3)      │
└────────────┘ └────────────┘ └────────────┘
```

## Architecture de Logging

### Configuration Globale

```yaml
# config/logging.yml
logging:
  # Niveau global
  level: "info"

  # Configuration générale
  global:
    enabled: true
    async: true  # Logging asynchrone
    buffer_size: 10000
    flush_interval: 5  # secondes

  # Enrichissement des logs
  enrichment:
    enabled: true
    fields:
      - hostname
      - pid
      - thread_id
      - version
      - environment

  # Filtres
  filters:
    # Exclure les logs de santé répétitifs
    - pattern: "Health check OK"
      action: "drop"
      frequency: "1/60s"  # Garder 1 toutes les 60s

    # Masquer les données sensibles
    - pattern: 'password["\s:=]+([^\s"]+)'
      action: "redact"
      replacement: "***REDACTED***"

  # Destinations multiples
  handlers:
    - console
    - file
    - syslog
    - elasticsearch
```

### Hiérarchie des Loggers

```yaml
loggers:
  # Logger racine
  root:
    level: "info"
    handlers:
      - console
      - file

  # Logger sécurité
  security:
    level: "debug"
    handlers:
      - security_file
      - siem
    propagate: false

  # Logger audit
  audit:
    level: "info"
    handlers:
      - audit_file
      - elasticsearch
    propagate: false

  # Logger accès
  access:
    level: "info"
    handlers:
      - access_file
      - siem

  # Logger applicatif
  app:
    level: "info"
    handlers:
      - app_file
```

## Types de Logs

### Logs de Sécurité

```yaml
security_logs:
  enabled: true
  level: "debug"

  # Événements à logger
  events:
    authentication:
      - login_success
      - login_failure
      - logout
      - session_expired
      - mfa_success
      - mfa_failure

    authorization:
      - permission_granted
      - permission_denied
      - role_assigned
      - role_revoked
      - privilege_escalation

    security_events:
      - password_change
      - password_reset
      - account_locked
      - account_unlocked
      - suspicious_activity
      - intrusion_detected

  # Format
  format:
    type: "json"
    schema:
      timestamp: "iso8601"
      level: "string"
      event_type: "string"
      username: "string"
      source_ip: "string"
      result: "string"
      details: "object"

  # Stockage
  storage:
    path: "/var/log/ldap-monitor/security.log"
    rotation: "daily"
    retention: 365
    compress: true
```

### Logs d'Audit

```yaml
audit_logs:
  enabled: true
  level: "info"

  # Événements d'audit
  events:
    operations:
      - create
      - read
      - update
      - delete
      - execute

    resources:
      - users
      - groups
      - configuration
      - credentials
      - reports

    changes:
      - before_state
      - after_state
      - changed_by
      - change_reason

  # Format détaillé
  format:
    type: "json"
    include:
      - timestamp
      - event_id
      - event_type
      - actor
      - action
      - resource
      - resource_id
      - result
      - before_state
      - after_state
      - metadata

  # Stockage
  storage:
    path: "/var/log/ldap-monitor/audit.log"
    rotation: "daily"
    retention: 2555  # 7 ans (conformité)
    compress: true
    immutable: true  # Logs immuables
```

### Logs d'Accès

```yaml
access_logs:
  enabled: true

  # Format Apache Combined + extensions
  format: 'combined_extended'

  # Champs personnalisés
  fields:
    - timestamp
    - client_ip
    - username
    - method
    - url
    - status_code
    - response_time
    - bytes_sent
    - user_agent
    - referer
    - session_id
    - request_id

  # Stockage
  storage:
    path: "/var/log/ldap-monitor/access.log"
    rotation: "daily"
    retention: 90
    compress: true
```

### Logs Applicatifs

```yaml
application_logs:
  enabled: true
  level: "info"

  # Catégories
  categories:
    - general
    - ldap_operations
    - monitoring
    - performance
    - errors

  # Format structuré
  format:
    type: "json"
    fields:
      - timestamp
      - level
      - logger_name
      - message
      - thread_id
      - exception
      - stack_trace

  # Stockage
  storage:
    path: "/var/log/ldap-monitor/application.log"
    rotation: "100MB"
    retention: 30
    compress: true
```

## Configuration des Logs

### Configuration Complète

```yaml
# config/logging-complete.yml
logging:
  version: 1

  # Formatters
  formatters:
    # JSON structuré
    json:
      class: "logging.JSONFormatter"
      fields:
        timestamp: "%(asctime)s"
        level: "%(levelname)s"
        logger: "%(name)s"
        message: "%(message)s"
        module: "%(module)s"
        function: "%(funcName)s"
        line: "%(lineno)d"

    # Format détaillé pour debug
    detailed:
      format: "[%(asctime)s] [%(levelname)8s] [%(name)s] [%(process)d:%(thread)d] %(message)s"
      datefmt: "%Y-%m-%d %H:%M:%S"

    # Format simple pour console
    simple:
      format: "%(levelname)s: %(message)s"

    # Format syslog
    syslog:
      format: "ldap-monitor[%(process)d]: %(levelname)s %(message)s"

  # Handlers
  handlers:
    # Console
    console:
      class: "logging.StreamHandler"
      level: "INFO"
      formatter: "simple"
      stream: "ext://sys.stdout"

    # Fichier principal
    main_file:
      class: "logging.handlers.RotatingFileHandler"
      level: "INFO"
      formatter: "json"
      filename: "/var/log/ldap-monitor/main.log"
      maxBytes: 104857600  # 100MB
      backupCount: 10
      encoding: "utf8"

    # Fichier sécurité
    security_file:
      class: "logging.handlers.TimedRotatingFileHandler"
      level: "DEBUG"
      formatter: "json"
      filename: "/var/log/ldap-monitor/security.log"
      when: "midnight"
      interval: 1
      backupCount: 365
      encoding: "utf8"

    # Fichier audit
    audit_file:
      class: "logging.handlers.TimedRotatingFileHandler"
      level: "INFO"
      formatter: "json"
      filename: "/var/log/ldap-monitor/audit.log"
      when: "midnight"
      interval: 1
      backupCount: 2555  # 7 ans
      encoding: "utf8"

    # Syslog
    syslog:
      class: "logging.handlers.SysLogHandler"
      level: "WARNING"
      formatter: "syslog"
      address: "/dev/log"
      facility: "local0"

    # Elasticsearch
    elasticsearch:
      class: "custom.ElasticsearchHandler"
      level: "INFO"
      hosts: ["https://logs.example.com:9200"]
      index_pattern: "ldap-monitor-%{+YYYY.MM.dd}"
      ssl_verify: true

  # Loggers
  loggers:
    # Sécurité
    security:
      level: "DEBUG"
      handlers: ["security_file", "syslog"]
      propagate: false

    # Audit
    audit:
      level: "INFO"
      handlers: ["audit_file", "elasticsearch"]
      propagate: false

    # Application
    app:
      level: "INFO"
      handlers: ["main_file", "console"]
      propagate: true

  # Logger root
  root:
    level: "INFO"
    handlers: ["console", "main_file"]
```

## Niveaux de Logging

### Définition des Niveaux

```python
#!/usr/bin/env python3
# logging_levels.py

import logging

# Niveaux standard
LEVELS = {
    'DEBUG': logging.DEBUG,       # 10 - Informations détaillées
    'INFO': logging.INFO,         # 20 - Informations générales
    'WARNING': logging.WARNING,   # 30 - Avertissements
    'ERROR': logging.ERROR,       # 40 - Erreurs
    'CRITICAL': logging.CRITICAL  # 50 - Erreurs critiques
}

# Niveaux personnalisés
SECURITY = 25  # Entre INFO et WARNING
AUDIT = 22     # Entre INFO et SECURITY

logging.addLevelName(SECURITY, "SECURITY")
logging.addLevelName(AUDIT, "AUDIT")

def security(self, message, *args, **kwargs):
    if self.isEnabledFor(SECURITY):
        self._log(SECURITY, message, args, **kwargs)

def audit(self, message, *args, **kwargs):
    if self.isEnabledFor(AUDIT):
        self._log(AUDIT, message, args, **kwargs)

logging.Logger.security = security
logging.Logger.audit = audit

# Utilisation
logger = logging.getLogger(__name__)

logger.debug("Détails techniques pour debug")
logger.info("Information générale")
logger.audit("Événement d'audit")
logger.security("Événement de sécurité")
logger.warning("Avertissement")
logger.error("Erreur")
logger.critical("Erreur critique")
```

### Politiques par Niveau

```yaml
level_policies:
  DEBUG:
    description: "Informations détaillées pour le développement"
    use_in_production: false
    retention_days: 7

  INFO:
    description: "Événements normaux du système"
    use_in_production: true
    retention_days: 30

  AUDIT:
    description: "Événements nécessitant traçabilité"
    use_in_production: true
    retention_days: 2555  # 7 ans

  SECURITY:
    description: "Événements de sécurité"
    use_in_production: true
    retention_days: 365
    alert_threshold: 1

  WARNING:
    description: "Situations anormales non critiques"
    use_in_production: true
    retention_days: 90
    alert_threshold: 10

  ERROR:
    description: "Erreurs nécessitant attention"
    use_in_production: true
    retention_days: 180
    alert_threshold: 5

  CRITICAL:
    description: "Erreurs critiques du système"
    use_in_production: true
    retention_days: 365
    alert_threshold: 1
    immediate_notification: true
```

## Formats de Logs

### Format JSON Structuré

```json
{
  "timestamp": "2024-11-17T10:30:45.123Z",
  "level": "SECURITY",
  "event_type": "authentication_failure",
  "event_id": "evt_auth_fail_20241117_103045",
  "severity": "high",
  "actor": {
    "username": "john.doe",
    "ip_address": "192.168.1.100",
    "user_agent": "ldap-health-monitor/1.0.0",
    "session_id": "sess_abc123"
  },
  "action": "login",
  "resource": {
    "type": "authentication_service",
    "id": "auth_ldap_prod"
  },
  "result": "failure",
  "reason": "invalid_password",
  "metadata": {
    "attempts": 3,
    "lockout_pending": false,
    "mfa_required": true
  },
  "context": {
    "hostname": "ldap-monitor-01",
    "pid": 12345,
    "environment": "production",
    "version": "1.0.0"
  }
}
```

### Format CEF (Common Event Format)

```
CEF:0|LDAPHealthMonitor|LDAP Monitor|1.0.0|AUTH_FAIL|Authentication Failure|8|
src=192.168.1.100 suser=john.doe outcome=Failure reason=invalid_password
cs1Label=SessionID cs1=sess_abc123 cn1Label=AttemptCount cn1=3
```

### Format Syslog

```
Nov 17 10:30:45 ldap-monitor-01 ldap-monitor[12345]: SECURITY event_type=authentication_failure username=john.doe source_ip=192.168.1.100 result=failure reason=invalid_password
```

## Rotation et Rétention

### Configuration de Rotation

```yaml
# config/log-rotation.yml
log_rotation:
  # Rotation par taille
  size_based:
    enabled: true
    max_size: "100MB"
    max_files: 10

  # Rotation temporelle
  time_based:
    enabled: true
    when: "midnight"  # ou "hourly", "weekly"
    interval: 1
    backup_count: 30

  # Compression
  compression:
    enabled: true
    format: "gzip"  # ou "bzip2", "xz"
    compress_after: 1  # Compresser après 1 jour

  # Archivage
  archiving:
    enabled: true
    destination: "s3://logs-archive/ldap-monitor/"
    archive_after: 90  # Archiver après 90 jours
```

### Script de Rotation

```bash
#!/bin/bash
# /etc/logrotate.d/ldap-monitor

/var/log/ldap-monitor/*.log {
    # Rotation quotidienne
    daily

    # Garder 30 jours de logs
    rotate 30

    # Compresser les anciens logs
    compress
    delaycompress

    # Ne pas générer d'erreur si le fichier est absent
    missingok

    # Ne pas rotationner si le fichier est vide
    notifempty

    # Créer nouveau fichier avec permissions
    create 0640 ldapmon ldapmon

    # Script post-rotation
    postrotate
        # Recharger la configuration de logging
        systemctl reload ldap-monitor.service > /dev/null 2>&1 || true

        # Archiver les logs anciens vers S3
        /opt/ldap-monitor/scripts/archive-logs.sh
    endscript
}

# Logs de sécurité - rétention longue
/var/log/ldap-monitor/security.log {
    daily
    rotate 365
    compress
    delaycompress
    missingok
    notifempty
    create 0600 ldapmon ldapmon

    # Copier vers stockage immuable
    postrotate
        /opt/ldap-monitor/scripts/backup-security-logs.sh
    endscript
}

# Logs d'audit - rétention très longue (7 ans)
/var/log/ldap-monitor/audit.log {
    daily
    rotate 2555
    compress
    delaycompress
    missingok
    notifempty
    create 0600 ldapmon ldapmon

    # Signature cryptographique
    postrotate
        /opt/ldap-monitor/scripts/sign-audit-logs.sh
    endscript
}
```

### Script d'Archivage

```bash
#!/bin/bash
# archive-logs.sh

set -e

LOG_DIR="/var/log/ldap-monitor"
ARCHIVE_DIR="/var/archive/ldap-monitor"
S3_BUCKET="s3://logs-archive/ldap-monitor"
AGE_KEY="/opt/ldap-monitor/secrets/archive.key"

# Créer le répertoire d'archive
mkdir -p "$ARCHIVE_DIR"

# Trouver les logs de plus de 90 jours
find "$LOG_DIR" -name "*.log.*.gz" -mtime +90 | while read log_file; do
    filename=$(basename "$log_file")
    archive_path="$ARCHIVE_DIR/$filename"

    echo "Archivage de $log_file..."

    # Chiffrer avec Age
    age -r "$(cat ${AGE_KEY}.pub)" -o "${archive_path}.age" "$log_file"

    # Upload vers S3
    aws s3 cp "${archive_path}.age" "$S3_BUCKET/" \
        --storage-class GLACIER \
        --metadata "retention=7years"

    # Vérifier l'upload
    if aws s3 ls "$S3_BUCKET/$(basename ${archive_path}.age)" > /dev/null 2>&1; then
        # Supprimer le fichier local
        rm -f "$log_file"
        rm -f "${archive_path}.age"
        echo "Archivé avec succès: $filename"
    else
        echo "ERREUR: Échec de l'archivage de $filename"
    fi
done
```

## Centralisation des Logs

### Configuration rsyslog

```bash
# /etc/rsyslog.d/ldap-monitor.conf

# Recevoir les logs de l'application
module(load="imuxsock")
module(load="imfile")

# Charger les logs JSON
input(type="imfile"
      File="/var/log/ldap-monitor/security.log"
      Tag="ldap-monitor-security"
      Severity="info"
      Facility="local0")

input(type="imfile"
      File="/var/log/ldap-monitor/audit.log"
      Tag="ldap-monitor-audit"
      Severity="info"
      Facility="local1")

# Template JSON
template(name="json-template"
         type="list") {
    constant(value="{")
    property(name="timestamp" dateFormat="rfc3339")
    constant(value=",\"host\":\"")
    property(name="hostname")
    constant(value="\",\"severity\":\"")
    property(name="syslogseverity-text")
    constant(value="\",\"facility\":\"")
    property(name="syslogfacility-text")
    constant(value="\",\"tag\":\"")
    property(name="syslogtag")
    constant(value="\",\"message\":\"")
    property(name="msg")
    constant(value="\"}")
}

# Envoyer vers SIEM
if $syslogtag == 'ldap-monitor-security' then {
    action(type="omfwd"
           target="siem.example.com"
           port="514"
           protocol="tcp"
           template="json-template")
}

# Envoyer vers Elasticsearch
if $syslogtag == 'ldap-monitor-audit' then {
    action(type="omelasticsearch"
           server="logs.example.com"
           serverport="9200"
           template="json-template"
           searchIndex="ldap-monitor-audit"
           bulkmode="on")
}
```

### Configuration Fluentd

```ruby
# /etc/fluent/fluent.conf

# Source - Logs fichiers
<source>
  @type tail
  path /var/log/ldap-monitor/*.log
  pos_file /var/log/td-agent/ldap-monitor.pos
  tag ldap-monitor.*
  format json
  time_key timestamp
  time_format %Y-%m-%dT%H:%M:%S.%L%Z
</source>

# Filtres - Enrichissement
<filter ldap-monitor.**>
  @type record_transformer
  <record>
    hostname "#{Socket.gethostname}"
    environment "production"
    service "ldap-health-monitor"
  </record>
</filter>

# Filtre - Anonymisation
<filter ldap-monitor.security>
  @type record_modifier
  <record>
    # Masquer les IPs privées dans les messages
    message ${record["message"].gsub(/\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b/, "***.***.***")}
  </record>
</filter>

# Sortie - Elasticsearch
<match ldap-monitor.security>
  @type elasticsearch
  host logs.example.com
  port 9200
  scheme https
  ssl_verify true
  user elastic
  password "#{ENV['ELASTIC_PASSWORD']}"
  index_name ldap-monitor-security-%Y%m%d
  type_name _doc

  <buffer>
    @type file
    path /var/log/td-agent/buffer/elasticsearch
    flush_interval 10s
    retry_max_interval 30
    retry_forever false
  </buffer>
</match>

# Sortie - S3 Archive
<match ldap-monitor.audit>
  @type s3
  aws_key_id "#{ENV['AWS_ACCESS_KEY_ID']}"
  aws_sec_key "#{ENV['AWS_SECRET_ACCESS_KEY']}"
  s3_bucket ldap-monitor-audit-logs
  s3_region eu-west-1
  path logs/audit/%Y/%m/%d/

  <buffer time>
    @type file
    path /var/log/td-agent/buffer/s3
    timekey 3600  # 1 heure
    timekey_wait 10m
  </buffer>

  <format>
    @type json
  </format>
</match>

# Sortie - SIEM
<match ldap-monitor.**>
  @type forward
  <server>
    host siem.example.com
    port 24224
  </server>

  <buffer>
    flush_interval 5s
  </buffer>
</match>
```

## Analyse et Corrélation

### Requêtes d'Analyse

```bash
#!/bin/bash
# log-analysis.sh

# Analyse des tentatives de connexion échouées
analyze_failed_logins() {
    echo "=== Tentatives de connexion échouées (24h) ==="
    jq -r 'select(.event_type == "authentication_failure") |
           "\(.timestamp) \(.actor.ip_address) \(.actor.username) \(.reason)"' \
        /var/log/ldap-monitor/security.log | \
        tail -n 1000
}

# Top 10 des IPs avec échecs
top_failed_ips() {
    echo "=== Top 10 IPs avec échecs de connexion ==="
    jq -r 'select(.event_type == "authentication_failure") |
           .actor.ip_address' \
        /var/log/ldap-monitor/security.log | \
        sort | uniq -c | sort -rn | head -10
}

# Détection de brute force
detect_brute_force() {
    echo "=== Détection brute force (>5 échecs en 5 min) ==="
    jq -r 'select(.event_type == "authentication_failure") |
           "\(.timestamp) \(.actor.ip_address)"' \
        /var/log/ldap-monitor/security.log | \
        awk '{print $2}' | sort | uniq -c | \
        awk '$1 > 5 {print "ALERTE: "$2" - "$1" tentatives"}'
}

# Accès en dehors des heures ouvrables
after_hours_access() {
    echo "=== Accès en dehors des heures ouvrables ==="
    jq -r 'select(.timestamp | fromdateiso8601 |
           strftime("%H") | tonumber < 8 or tonumber > 18) |
           "\(.timestamp) \(.actor.username) \(.action)"' \
        /var/log/ldap-monitor/audit.log
}

# Opérations privilégiées
privileged_operations() {
    echo "=== Opérations privilégiées ==="
    jq -r 'select(.action == "delete" or .action == "config_write") |
           "\(.timestamp) \(.actor.username) \(.action) \(.resource.type)"' \
        /var/log/ldap-monitor/audit.log | tail -n 100
}

# Rapport complet
generate_report() {
    {
        echo "===================="
        echo "Rapport d'Analyse de Sécurité"
        echo "Date: $(date)"
        echo "===================="
        echo
        analyze_failed_logins
        echo
        top_failed_ips
        echo
        detect_brute_force
        echo
        after_hours_access
        echo
        privileged_operations
    } | tee "/var/log/ldap-monitor/security-report-$(date +%Y%m%d).txt"
}

# Exécution
generate_report
```

### Corrélation d'Événements

```python
#!/usr/bin/env python3
# event-correlation.py

import json
from datetime import datetime, timedelta
from collections import defaultdict

class EventCorrelator:
    def __init__(self):
        self.events = []
        self.patterns = []

    def load_logs(self, log_file):
        """Charger les logs"""
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    self.events.append(event)
                except:
                    continue

    def detect_brute_force(self, threshold=5, window_minutes=5):
        """Détecter les tentatives de brute force"""
        failures = defaultdict(list)

        for event in self.events:
            if event.get('event_type') == 'authentication_failure':
                ip = event.get('actor', {}).get('ip_address')
                timestamp = datetime.fromisoformat(event['timestamp'].replace('Z', '+00:00'))
                failures[ip].append(timestamp)

        alerts = []
        for ip, timestamps in failures.items():
            timestamps.sort()
            for i, ts in enumerate(timestamps):
                window_end = ts + timedelta(minutes=window_minutes)
                count = sum(1 for t in timestamps[i:] if t <= window_end)

                if count >= threshold:
                    alerts.append({
                        'type': 'brute_force',
                        'ip': ip,
                        'count': count,
                        'first_attempt': ts.isoformat(),
                        'severity': 'high'
                    })
                    break

        return alerts

    def detect_privilege_escalation(self):
        """Détecter les escalades de privilèges"""
        user_actions = defaultdict(list)

        for event in self.events:
            if event.get('event_type') == 'role_assigned':
                username = event.get('actor', {}).get('username')
                role = event.get('resource', {}).get('role')
                timestamp = event['timestamp']

                user_actions[username].append({
                    'role': role,
                    'timestamp': timestamp
                })

        alerts = []
        for username, actions in user_actions.items():
            # Détecter attribution de rôle admin
            for action in actions:
                if action['role'] in ['admin', 'super_admin']:
                    alerts.append({
                        'type': 'privilege_escalation',
                        'username': username,
                        'role': action['role'],
                        'timestamp': action['timestamp'],
                        'severity': 'critical'
                    })

        return alerts

    def detect_data_exfiltration(self, threshold_mb=100):
        """Détecter les exfiltrations de données"""
        user_exports = defaultdict(int)

        for event in self.events:
            if event.get('action') == 'export':
                username = event.get('actor', {}).get('username')
                size_mb = event.get('metadata', {}).get('size_mb', 0)
                user_exports[username] += size_mb

        alerts = []
        for username, total_mb in user_exports.items():
            if total_mb > threshold_mb:
                alerts.append({
                    'type': 'data_exfiltration',
                    'username': username,
                    'total_mb': total_mb,
                    'severity': 'high'
                })

        return alerts

    def generate_report(self):
        """Générer un rapport de corrélation"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_events': len(self.events),
            'alerts': []
        }

        # Détecter les patterns
        report['alerts'].extend(self.detect_brute_force())
        report['alerts'].extend(self.detect_privilege_escalation())
        report['alerts'].extend(self.detect_data_exfiltration())

        return report


# Utilisation
if __name__ == '__main__':
    correlator = EventCorrelator()
    correlator.load_logs('/var/log/ldap-monitor/security.log')

    report = correlator.generate_report()

    print(json.dumps(report, indent=2))

    # Alerter si des problèmes détectés
    if report['alerts']:
        print(f"\n⚠️  {len(report['alerts'])} alertes de sécurité détectées!")
```

## Alertes de Sécurité

### Configuration des Alertes

```yaml
# config/security-alerts.yml
security_alerts:
  enabled: true

  # Règles d'alerte
  rules:
    # Brute force
    - name: "brute_force_detection"
      condition: "authentication_failure count > 5 in 5m"
      severity: "high"
      actions:
        - type: "email"
          recipients: ["security@example.com"]
        - type: "slack"
          channel: "#security-alerts"
        - type: "block_ip"
          duration: 3600

    # Escalade de privilèges
    - name: "privilege_escalation"
      condition: "role_assigned AND role IN ['admin', 'super_admin']"
      severity: "critical"
      actions:
        - type: "email"
          recipients: ["security@example.com", "ciso@example.com"]
        - type: "slack"
          channel: "#security-critical"
        - type: "create_incident"
          priority: "P1"

    # Accès hors heures
    - name: "after_hours_access"
      condition: "time < 08:00 OR time > 18:00"
      severity: "medium"
      actions:
        - type: "log"
          level: "warning"
        - type: "email"
          recipients: ["ops@example.com"]

    # Export massif de données
    - name: "mass_data_export"
      condition: "export size > 100MB"
      severity: "high"
      actions:
        - type: "email"
          recipients: ["security@example.com", "dpo@example.com"]
        - type: "suspend_session"
        - type: "require_approval"

  # Throttling des alertes
  throttling:
    enabled: true
    max_alerts_per_rule: 10
    time_window: 3600
```

## Intégration SIEM

### Configuration Splunk

```ini
# /opt/splunk/etc/apps/ldap_monitor/inputs.conf
[monitor:///var/log/ldap-monitor/*.log]
disabled = false
sourcetype = ldap_monitor_json
index = security

# /opt/splunk/etc/apps/ldap_monitor/props.conf
[ldap_monitor_json]
SHOULD_LINEMERGE = false
KV_MODE = json
TIME_PREFIX = "timestamp":"
TIME_FORMAT = %Y-%m-%dT%H:%M:%S.%3N%Z
MAX_TIMESTAMP_LOOKAHEAD = 32
```

### Configuration Elastic Stack

```yaml
# filebeat.yml
filebeat.inputs:
  - type: log
    enabled: true
    paths:
      - /var/log/ldap-monitor/security.log
      - /var/log/ldap-monitor/audit.log
    json.keys_under_root: true
    json.add_error_key: true
    fields:
      service: ldap-health-monitor
      environment: production

output.elasticsearch:
  hosts: ["https://logs.example.com:9200"]
  username: "elastic"
  password: "${ELASTIC_PASSWORD}"
  index: "ldap-monitor-%{+yyyy.MM.dd}"
  ssl.verification_mode: "full"

processors:
  - add_host_metadata: ~
  - add_cloud_metadata: ~
  - drop_fields:
      fields: ["agent", "ecs", "host"]
```

## Conformité et Audit

### Checklist de Conformité

```markdown
## Logging

- [ ] Tous les accès sont loggés
- [ ] Tous les changements sont loggés
- [ ] Logs incluent qui, quoi, quand, où
- [ ] Horodatage précis (NTP synchronisé)
- [ ] Logs immuables et signés

## Rétention

- [ ] Politique de rétention documentée
- [ ] Rétention conforme aux réglementations
- [ ] Archivage sécurisé (chiffré)
- [ ] Procédure de récupération testée
- [ ] Destruction sécurisée après rétention

## Sécurité

- [ ] Logs chiffrés en transit et au repos
- [ ] Accès aux logs contrôlé (RBAC)
- [ ] Logs centralisés et isolés
- [ ] Détection de tampering
- [ ] Alertes sur anomalies

## Audit

- [ ] Revue régulière des logs
- [ ] Rapports d'audit générés
- [ ] Preuves d'audit conservées
- [ ] Conformité vérifiable
- [ ] Documentation complète
```

## Forensique et Investigation

### Outils d'Investigation

```bash
#!/bin/bash
# forensic-tools.sh

# Extraire les événements d'un utilisateur
investigate_user() {
    local username="$1"
    local output="/tmp/investigation-$username-$(date +%Y%m%d).json"

    jq "select(.actor.username == \"$username\")" \
        /var/log/ldap-monitor/*.log > "$output"

    echo "Rapport sauvegardé: $output"
}

# Timeline des événements
create_timeline() {
    local start_date="$1"
    local end_date="$2"

    jq -r "select(.timestamp >= \"$start_date\" and .timestamp <= \"$end_date\") |
           \"\(.timestamp) \(.event_type) \(.actor.username) \(.action)\"" \
        /var/log/ldap-monitor/*.log | sort
}

# Préserver les preuves
preserve_evidence() {
    local incident_id="$1"
    local evidence_dir="/secure/evidence/$incident_id"

    mkdir -p "$evidence_dir"
    chmod 700 "$evidence_dir"

    # Copier les logs
    cp -r /var/log/ldap-monitor/ "$evidence_dir/logs/"

    # Calculer les checksums
    find "$evidence_dir" -type f -exec sha256sum {} \; > "$evidence_dir/checksums.txt"

    # Signer avec GPG
    gpg --sign "$evidence_dir/checksums.txt"

    # Chiffrer l'archive
    tar -czf - "$evidence_dir" | \
        age -r "$(cat /secure/forensic-key.pub)" > \
        "$evidence_dir.tar.gz.age"

    echo "Preuves préservées: $evidence_dir.tar.gz.age"
}
```

---

**Note Critique**: Les journaux d'audit sont des preuves légales. Assurez-vous de leur intégrité, confidentialité et disponibilité.
