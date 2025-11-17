# Guide de Monitoring en Production

Guide complet pour déployer LDAP Health Monitor en production avec monitoring, alerting et haute disponibilité.

## 🎯 Vue d'Ensemble

Ce guide couvre :

- Déploiement en production
- Architecture haute disponibilité
- Monitoring et métriques
- Système d'alerting
- Intégrations (Prometheus, Grafana, etc.)
- Sécurité et bonnes pratiques
- Gestion des incidents

## 🏗️ Architecture de Production

### Architecture Basique

```
┌─────────────────────────────────────────────┐
│           Load Balancer (HAProxy)           │
└─────────────────┬───────────────────────────┘
                  │
         ┌────────┴────────┐
         │                 │
    ┌────▼────┐       ┌────▼────┐
    │ LDAP 1  │       │ LDAP 2  │
    │ Master  │◄─────►│ Replica │
    └────┬────┘       └────┬────┘
         │                 │
    ┌────▼─────────────────▼────┐
    │   LDAP Health Monitor     │
    │   - Monitoring Daemon     │
    │   - Metrics Collection    │
    │   - Alert Manager         │
    └────┬──────────────────────┘
         │
    ┌────▼────┐
    │ Storage │
    │ - Logs  │
    │ - Data  │
    └─────────┘
```

### Architecture Haute Disponibilité

```
                     ┌─────────────┐
                     │   Consul    │
                     │   Cluster   │
                     └──────┬──────┘
                            │
┌───────────────────────────┴───────────────────────────┐
│                                                       │
│  ┌─────────────────┐              ┌─────────────────┐│
│  │ Monitor Node 1  │              │ Monitor Node 2  ││
│  │ - Active        │◄────────────►│ - Standby       ││
│  │ - Daemon        │   Heartbeat  │ - Daemon        ││
│  └────────┬────────┘              └────────┬────────┘│
│           │                                │         │
└───────────┼────────────────────────────────┼─────────┘
            │                                │
       ┌────▼────────────────────────────────▼────┐
       │         LDAP Cluster (3+ nodes)          │
       │  - Master/Master ou Master/Replica       │
       └────┬─────────────────────────────────────┘
            │
       ┌────▼────┐
       │ Metrics │
       │ Backend │
       │ (Prom)  │
       └─────────┘
```

## 🚀 Déploiement en Production

### Pré-requis Système

```bash
# Système d'exploitation
# - Ubuntu 20.04+ / Debian 11+
# - RHEL 8+ / CentOS 8+
# - Rocky Linux 8+

# Ressources minimales
# - CPU: 2 cores
# - RAM: 4 GB
# - Disk: 50 GB
# - Network: 1 Gbps

# Packages requis
apt-get update
apt-get install -y \
    python3.9 \
    python3-pip \
    python3-venv \
    libldap2-dev \
    libsasl2-dev \
    build-essential \
    supervisor \
    nginx \
    redis-server \
    postgresql-13

# OU pour RHEL/CentOS
yum install -y \
    python39 \
    python3-devel \
    openldap-devel \
    cyrus-sasl-devel \
    gcc \
    supervisor \
    nginx \
    redis \
    postgresql13-server
```

### Installation Production

```bash
#!/bin/bash
# scripts/production-install.sh

set -euo pipefail

# Variables
INSTALL_DIR="/opt/ldap-monitor"
VENV_DIR="$INSTALL_DIR/venv"
CONFIG_DIR="/etc/ldap-monitor"
DATA_DIR="/var/lib/ldap-monitor"
LOG_DIR="/var/log/ldap-monitor"
USER="ldapmon"
GROUP="ldapmon"

# Créer utilisateur système
useradd -r -s /bin/false -d "$DATA_DIR" "$USER"

# Créer répertoires
mkdir -p "$INSTALL_DIR" "$CONFIG_DIR" "$DATA_DIR" "$LOG_DIR"

# Installer application
cd "$INSTALL_DIR"
git clone https://github.com/your-org/ldap-health-monitor.git .

# Environnement virtuel Python
python3.9 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"

# Dépendances
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
pip install -e .

# Configuration
cp config/production.yaml.example "$CONFIG_DIR/config.yaml"

# Permissions
chown -R "$USER:$GROUP" "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
chmod 750 "$CONFIG_DIR"
chmod 640 "$CONFIG_DIR/config.yaml"

echo "✓ Installation terminée"
```

### Configuration Production

```yaml
# /etc/ldap-monitor/config.yaml

# LDAP Configuration
ldap:
  # Serveurs primaire et secondaire
  servers:
    - uri: ldaps://ldap01.prod.example.com:636
      priority: 1
    - uri: ldaps://ldap02.prod.example.com:636
      priority: 2

  bind_dn: cn=monitor,dc=prod,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=prod,dc=example,dc=com

  # Connexion
  use_ssl: true
  verify_ssl: true
  ca_cert: /etc/ssl/certs/ca-bundle.crt
  timeout: 10
  retry_max: 3
  retry_delay: 2

  # Pool de connexions
  pool_size: 10
  pool_timeout: 30

# Monitoring Production
monitoring:
  enabled: true
  daemon: true

  # Intervalles
  health_check_interval: 60
  metrics_interval: 300
  audit_interval: 3600

  # Métriques
  metrics:
    enabled: true
    backend: prometheus
    push_gateway: http://prometheus-pushgateway:9091
    job_name: ldap-monitor

  # Health checks
  checks:
    - name: ldap_connection
      type: connection
      interval: 60
      timeout: 5
      critical: true

    - name: ldap_response_time
      type: response_time
      interval: 60
      warning_threshold: 1000
      critical_threshold: 3000

    - name: ldap_replication_lag
      type: replication
      interval: 300
      warning_threshold: 300
      critical_threshold: 900

    - name: ldap_disk_usage
      type: disk
      interval: 600
      warning_threshold: 80
      critical_threshold: 90

# Alerting
alerts:
  enabled: true

  # Email
  email:
    enabled: true
    smtp_server: smtp.prod.example.com
    smtp_port: 587
    use_tls: true
    username: ${SMTP_USER}
    password: ${SMTP_PASSWORD}
    from: ldap-monitor@example.com
    to:
      - ops-team@example.com
      - oncall@example.com

  # Slack
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    username: "LDAP Monitor"
    mention_on_critical: true
    mentions:
      critical: ["@channel", "@ops-lead"]
      warning: ["@ops-team"]

  # PagerDuty
  pagerduty:
    enabled: true
    integration_key: ${PAGERDUTY_KEY}
    severity_mapping:
      critical: "critical"
      warning: "warning"
      info: "info"

  # Webhooks personnalisés
  webhooks:
    - name: incident_management
      url: https://incidents.example.com/api/webhook
      events: ["critical"]
      headers:
        Authorization: "Bearer ${WEBHOOK_TOKEN}"

# Sécurité
security:
  # Authentification API
  api:
    enabled: true
    bind_address: "127.0.0.1"
    port: 8080
    auth_required: true
    api_key: ${API_KEY}
    tls:
      enabled: true
      cert: /etc/ssl/certs/ldap-monitor.crt
      key: /etc/ssl/private/ldap-monitor.key

  # Audit logging
  audit_log:
    enabled: true
    file: /var/log/ldap-monitor/audit.log
    rotate: true
    max_size: 100M
    max_files: 10

# Storage
storage:
  # Base de données pour métriques historiques
  database:
    type: postgresql
    host: localhost
    port: 5432
    name: ldap_monitor
    user: ${DB_USER}
    password: ${DB_PASSWORD}
    pool_size: 20

  # Cache Redis
  cache:
    enabled: true
    backend: redis
    host: localhost
    port: 6379
    db: 0
    password: ${REDIS_PASSWORD}
    ttl: 300

# Performance
performance:
  # Worker threads
  workers: 4

  # Queue pour tâches async
  queue:
    enabled: true
    backend: redis
    max_jobs: 1000

  # Rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 100

# Logging
logging:
  level: INFO
  format: json
  output:
    - type: file
      path: /var/log/ldap-monitor/app.log
      rotate: true
    - type: syslog
      facility: local0
```

### Service Systemd Production

```ini
# /etc/systemd/system/ldap-monitor.service
[Unit]
Description=LDAP Health Monitor Daemon
Documentation=https://github.com/your-org/ldap-health-monitor
After=network-online.target postgresql.service redis.service
Wants=network-online.target
Requires=postgresql.service redis.service

[Service]
Type=notify
User=ldapmon
Group=ldapmon
WorkingDirectory=/opt/ldap-monitor

# Environment
Environment="PATH=/opt/ldap-monitor/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONUNBUFFERED=1"
EnvironmentFile=/etc/ldap-monitor/env

# Commande principale
ExecStartPre=/opt/ldap-monitor/venv/bin/ldap-monitor config validate
ExecStart=/opt/ldap-monitor/venv/bin/ldap-monitor monitor start --daemon --production
ExecReload=/bin/kill -HUP $MAINPID
ExecStop=/bin/kill -TERM $MAINPID

# Restart policy
Restart=always
RestartSec=10s
StartLimitInterval=200s
StartLimitBurst=5

# Logging
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ldap-monitor

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/var/lib/ldap-monitor /var/log/ldap-monitor
ProtectKernelTunables=true
ProtectControlGroups=true
RestrictRealtime=true

# Limites
LimitNOFILE=65536
MemoryLimit=2G
CPUQuota=200%
TasksMax=256

# Watchdog
WatchdogSec=60s

[Install]
WantedBy=multi-user.target
```

## 📊 Intégration Prometheus

### Configuration Prometheus

```yaml
# /etc/prometheus/prometheus.yml

global:
  scrape_interval: 30s
  evaluation_interval: 30s
  external_labels:
    environment: production
    cluster: ldap-prod

scrape_configs:
  # LDAP Monitor metrics
  - job_name: 'ldap-monitor'
    static_configs:
      - targets:
          - 'ldap-monitor-01:8080'
          - 'ldap-monitor-02:8080'
        labels:
          role: monitor
          region: us-east-1

  # Pushgateway pour jobs batch
  - job_name: 'ldap-monitor-batch'
    honor_labels: true
    static_configs:
      - targets: ['prometheus-pushgateway:9091']

# Alertmanager
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

# Rules
rule_files:
  - /etc/prometheus/rules/ldap-monitor.yml
```

### Règles d'Alerting Prometheus

```yaml
# /etc/prometheus/rules/ldap-monitor.yml

groups:
  - name: ldap_health
    interval: 30s
    rules:
      # LDAP Down
      - alert: LDAPServerDown
        expr: ldap_server_up == 0
        for: 2m
        labels:
          severity: critical
          component: ldap
        annotations:
          summary: "LDAP server {{ $labels.instance }} is down"
          description: "LDAP server has been down for more than 2 minutes"

      # Response time élevé
      - alert: LDAPHighResponseTime
        expr: ldap_response_time_ms > 3000
        for: 5m
        labels:
          severity: warning
          component: ldap
        annotations:
          summary: "High LDAP response time on {{ $labels.instance }}"
          description: "Response time is {{ $value }}ms (threshold: 3000ms)"

      # Réplication en retard
      - alert: LDAPReplicationLag
        expr: ldap_replication_lag_seconds > 900
        for: 10m
        labels:
          severity: critical
          component: ldap
        annotations:
          summary: "LDAP replication lag detected"
          description: "Replication lag is {{ $value }}s on {{ $labels.instance }}"

      # Connexions échouées
      - alert: LDAPHighFailureRate
        expr: rate(ldap_bind_failures_total[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          component: ldap
        annotations:
          summary: "High LDAP bind failure rate"
          description: "Failure rate: {{ $value | humanizePercentage }}"

      # Utilisation disque
      - alert: LDAPDiskSpaceLow
        expr: ldap_disk_usage_percent > 85
        for: 10m
        labels:
          severity: warning
          component: storage
        annotations:
          summary: "Low disk space on LDAP server"
          description: "Disk usage: {{ $value }}%"

      # Nombre de connexions élevé
      - alert: LDAPHighConnectionCount
        expr: ldap_active_connections > 1000
        for: 15m
        labels:
          severity: warning
          component: ldap
        annotations:
          summary: "High number of active LDAP connections"
          description: "Active connections: {{ $value }}"

  - name: ldap_capacity
    interval: 60s
    rules:
      # Croissance utilisateurs
      - alert: LDAPUserGrowthAnomaly
        expr: |
          (ldap_users_total - ldap_users_total offset 24h) /
          ldap_users_total offset 24h > 0.1
        for: 1h
        labels:
          severity: info
          component: ldap
        annotations:
          summary: "Unusual user growth detected"
          description: "User count increased by {{ $value | humanizePercentage }}"

      # Groupes orphelins
      - alert: LDAPOrphanedGroups
        expr: ldap_orphaned_groups_total > 10
        for: 6h
        labels:
          severity: warning
          component: ldap
        annotations:
          summary: "Orphaned groups detected"
          description: "{{ $value }} groups without members"
```

### Exporter Prometheus

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/exporters/prometheus_exporter.py

from prometheus_client import (
    start_http_server,
    Gauge,
    Counter,
    Histogram,
    Info
)
import time

# Métriques
ldap_up = Gauge('ldap_server_up', 'LDAP server availability', ['instance'])
ldap_response_time = Histogram(
    'ldap_response_time_ms',
    'LDAP response time in milliseconds',
    ['instance', 'operation']
)
ldap_users_total = Gauge('ldap_users_total', 'Total number of users')
ldap_groups_total = Gauge('ldap_groups_total', 'Total number of groups')
ldap_binds_total = Counter('ldap_binds_total', 'Total LDAP binds', ['status'])
ldap_searches_total = Counter('ldap_searches_total', 'Total LDAP searches')
ldap_replication_lag = Gauge(
    'ldap_replication_lag_seconds',
    'Replication lag in seconds',
    ['master', 'replica']
)
ldap_disk_usage = Gauge(
    'ldap_disk_usage_percent',
    'Disk usage percentage',
    ['instance', 'mountpoint']
)
ldap_connections = Gauge(
    'ldap_active_connections',
    'Number of active connections',
    ['instance']
)
ldap_info = Info('ldap_monitor', 'LDAP Monitor information')

class PrometheusExporter:

    def __init__(self, monitor):
        self.monitor = monitor
        self.port = 8080

    def start(self):
        """Démarrer serveur HTTP Prometheus"""
        start_http_server(self.port)
        print(f"Prometheus exporter listening on port {self.port}")

    def update_metrics(self):
        """Mettre à jour toutes les métriques"""
        # Server status
        for server in self.monitor.servers:
            is_up = self.monitor.check_server_health(server)
            ldap_up.labels(instance=server).set(1 if is_up else 0)

        # Response times
        for op_type in ['bind', 'search', 'modify']:
            response_time = self.monitor.measure_response_time(op_type)
            ldap_response_time.labels(
                instance=self.monitor.primary_server,
                operation=op_type
            ).observe(response_time)

        # Counts
        user_count = self.monitor.count_users()
        group_count = self.monitor.count_groups()
        ldap_users_total.set(user_count)
        ldap_groups_total.set(group_count)

        # Replication
        lag = self.monitor.check_replication_lag()
        if lag is not None:
            ldap_replication_lag.labels(
                master=self.monitor.master,
                replica=self.monitor.replica
            ).set(lag)

        # Disk usage
        disk_usage = self.monitor.get_disk_usage()
        ldap_disk_usage.labels(
            instance=self.monitor.primary_server,
            mountpoint='/var/lib/ldap'
        ).set(disk_usage)

        # Connexions actives
        active_conns = self.monitor.get_active_connections()
        ldap_connections.labels(
            instance=self.monitor.primary_server
        ).set(active_conns)

        # Info
        ldap_info.info({
            'version': self.monitor.version,
            'environment': 'production',
            'base_dn': self.monitor.base_dn
        })

    def run(self):
        """Boucle principale"""
        self.start()

        while True:
            try:
                self.update_metrics()
            except Exception as e:
                print(f"Error updating metrics: {e}")

            time.sleep(30)

if __name__ == '__main__':
    from ldap_monitor import Monitor

    monitor = Monitor('/etc/ldap-monitor/config.yaml')
    exporter = PrometheusExporter(monitor)
    exporter.run()
```

## 📈 Dashboards Grafana

### Datasource Configuration

```yaml
# /etc/grafana/provisioning/datasources/prometheus.yml

apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    jsonData:
      timeInterval: "30s"
```

### Dashboard JSON

```json
{
  "dashboard": {
    "title": "LDAP Health Monitor",
    "tags": ["ldap", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "title": "LDAP Server Status",
        "type": "stat",
        "targets": [
          {
            "expr": "ldap_server_up",
            "legendFormat": "{{instance}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 1, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "ldap_response_time_ms",
            "legendFormat": "{{operation}}"
          }
        ]
      },
      {
        "title": "User/Group Counts",
        "type": "graph",
        "targets": [
          {
            "expr": "ldap_users_total",
            "legendFormat": "Users"
          },
          {
            "expr": "ldap_groups_total",
            "legendFormat": "Groups"
          }
        ]
      }
    ]
  }
}
```

## 🔔 Gestion des Alertes

### Alertmanager Configuration

```yaml
# /etc/alertmanager/alertmanager.yml

global:
  resolve_timeout: 5m
  smtp_smarthost: 'smtp.example.com:587'
  smtp_from: 'alertmanager@example.com'
  smtp_auth_username: 'alertmanager'
  smtp_auth_password: '${SMTP_PASSWORD}'

route:
  group_by: ['alertname', 'cluster', 'service']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'team-ops'

  routes:
    # Critical alerts -> PagerDuty
    - match:
        severity: critical
      receiver: 'pagerduty'
      continue: true

    # LDAP alerts -> LDAP team
    - match:
        component: ldap
      receiver: 'team-ldap'

receivers:
  - name: 'team-ops'
    email_configs:
      - to: 'ops-team@example.com'

  - name: 'team-ldap'
    email_configs:
      - to: 'ldap-team@example.com'
    slack_configs:
      - api_url: '${SLACK_WEBHOOK}'
        channel: '#ldap-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'

  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '${PAGERDUTY_KEY}'
        description: '{{ .GroupLabels.alertname }}'
```

## 📖 Voir Aussi

- [Docker Deployment](Docker-Deployment.md)
- [Performance Tuning](Performance-Tuning.md)
- [Multi-Server Setup](Multi-Server.md)
- [Backup Strategy](Backup-Strategy.md)
