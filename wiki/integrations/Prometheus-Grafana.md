# Intégration Prometheus & Grafana

Guide complet pour intégrer LDAP Health Monitor avec Prometheus et Grafana pour une visualisation avancée des métriques et un monitoring en temps réel.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Prérequis](#prérequis)
- [Installation de Prometheus](#installation-de-prometheus)
- [Installation de Grafana](#installation-de-grafana)
- [Configuration LDAP Monitor](#configuration-ldap-monitor)
- [Configuration Prometheus](#configuration-prometheus)
- [Configuration Grafana](#configuration-grafana)
- [Métriques Disponibles](#métriques-disponibles)
- [Dashboards Grafana](#dashboards-grafana)
- [Alertes](#alertes)
- [Optimisation](#optimisation)
- [Troubleshooting](#troubleshooting)

## 📊 Vue d'ensemble

### Architecture

```
┌─────────────────────┐
│  LDAP Health Monitor│
│   Metrics Exporter  │ :9090
└──────────┬──────────┘
           │ HTTP /metrics
           ↓
┌─────────────────────┐
│    Prometheus       │ :9091
│  Time Series DB     │
└──────────┬──────────┘
           │ PromQL
           ↓
┌─────────────────────┐
│     Grafana         │ :3000
│   Dashboards UI     │
└─────────────────────┘
```

### Avantages

- ✅ **Visualisation temps réel** - Graphiques et métriques en direct
- ✅ **Historique complet** - Conservation des données sur plusieurs mois
- ✅ **Alertes configurables** - Notifications basées sur des seuils
- ✅ **Dashboards personnalisables** - Créez vos propres vues
- ✅ **Standards de l'industrie** - Outils éprouvés et largement utilisés

## 🔧 Prérequis

### Versions recommandées

- **LDAP Health Monitor** : v1.0.0+
- **Prometheus** : v2.40.0+
- **Grafana** : v9.0.0+
- **Docker** (optionnel) : v20.10+

### Ressources système

**Minimum :**
- CPU : 2 cores
- RAM : 4 GB
- Disque : 20 GB (pour rétention de 30 jours)

**Recommandé :**
- CPU : 4 cores
- RAM : 8 GB
- Disque : 100 GB (pour rétention de 90 jours)

## 📥 Installation de Prometheus

### Méthode 1 : Installation native (macOS)

```bash
# Installation via Homebrew
brew install prometheus

# Démarrer Prometheus
brew services start prometheus

# Vérifier l'installation
prometheus --version
```

### Méthode 2 : Installation native (Linux)

```bash
# Télécharger la dernière version
PROM_VERSION="2.45.0"
wget https://github.com/prometheus/prometheus/releases/download/v${PROM_VERSION}/prometheus-${PROM_VERSION}.linux-amd64.tar.gz

# Extraire
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Déplacer les binaires
sudo mv prometheus /usr/local/bin/
sudo mv promtool /usr/local/bin/

# Créer les répertoires
sudo mkdir -p /etc/prometheus
sudo mkdir -p /var/lib/prometheus

# Copier les fichiers de configuration
sudo mv prometheus.yml /etc/prometheus/
sudo mv consoles /etc/prometheus/
sudo mv console_libraries /etc/prometheus/
```

**Créer le service systemd :**

```bash
sudo tee /etc/systemd/system/prometheus.service << EOF
[Unit]
Description=Prometheus
Wants=network-online.target
After=network-online.target

[Service]
User=prometheus
Group=prometheus
Type=simple
ExecStart=/usr/local/bin/prometheus \
    --config.file /etc/prometheus/prometheus.yml \
    --storage.tsdb.path /var/lib/prometheus/ \
    --web.console.templates=/etc/prometheus/consoles \
    --web.console.libraries=/etc/prometheus/console_libraries

[Install]
WantedBy=multi-user.target
EOF

# Créer l'utilisateur
sudo useradd --no-create-home --shell /bin/false prometheus
sudo chown -R prometheus:prometheus /etc/prometheus /var/lib/prometheus

# Démarrer le service
sudo systemctl daemon-reload
sudo systemctl start prometheus
sudo systemctl enable prometheus
sudo systemctl status prometheus
```

### Méthode 3 : Docker (Recommandé)

```bash
# Créer le réseau Docker
docker network create monitoring

# Lancer Prometheus
docker run -d \
  --name prometheus \
  --network monitoring \
  -p 9091:9090 \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v prometheus-data:/prometheus \
  prom/prometheus:latest \
  --config.file=/etc/prometheus/prometheus.yml \
  --storage.tsdb.path=/prometheus \
  --web.enable-lifecycle

# Vérifier
docker logs prometheus
```

**Accès interface web :** `http://localhost:9091`

## 📥 Installation de Grafana

### Méthode 1 : Installation native (macOS)

```bash
# Installation via Homebrew
brew install grafana

# Démarrer Grafana
brew services start grafana

# Vérifier
curl http://localhost:3000
```

### Méthode 2 : Installation native (Linux)

**Ubuntu/Debian :**

```bash
# Ajouter le dépôt Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"

# Ajouter la clé GPG
wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -

# Installer
sudo apt-get update
sudo apt-get install grafana

# Démarrer
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
sudo systemctl status grafana-server
```

**RHEL/CentOS :**

```bash
# Créer le fichier repo
sudo tee /etc/yum.repos.d/grafana.repo << EOF
[grafana]
name=grafana
baseurl=https://packages.grafana.com/oss/rpm
repo_gpgcheck=1
enabled=1
gpgcheck=1
gpgkey=https://packages.grafana.com/gpg.key
sslverify=1
sslcacert=/etc/pki/tls/certs/ca-bundle.crt
EOF

# Installer
sudo dnf install grafana

# Démarrer
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

### Méthode 3 : Docker (Recommandé)

```bash
# Lancer Grafana
docker run -d \
  --name grafana \
  --network monitoring \
  -p 3000:3000 \
  -v grafana-data:/var/lib/grafana \
  -e "GF_SECURITY_ADMIN_PASSWORD=admin" \
  -e "GF_INSTALL_PLUGINS=grafana-piechart-panel" \
  grafana/grafana:latest

# Vérifier
docker logs grafana
```

**Accès interface web :** `http://localhost:3000`
**Login par défaut :** admin / admin (changez-le au premier login)

## ⚙️ Configuration LDAP Monitor

### 1. Activer l'exportateur de métriques

Éditez `config.yaml` :

```yaml
monitoring:
  enabled: true

  # Métriques Prometheus
  prometheus:
    enabled: true
    port: 9090
    path: "/metrics"

  # Intervalles de collecte
  intervals:
    metrics_collection: 60  # Collecter les métriques toutes les 60s
    health_check: 300       # Check de santé toutes les 5 min
    user_audit: 3600        # Audit utilisateurs toutes les heures
    group_audit: 3600       # Audit groupes toutes les heures

  # Métriques à exporter
  metrics:
    # Métriques serveur
    - ldap_server_up
    - ldap_server_response_time
    - ldap_server_connections
    - ldap_server_operations_total

    # Métriques utilisateurs
    - ldap_users_total
    - ldap_users_active
    - ldap_users_inactive
    - ldap_users_locked
    - ldap_users_password_expired

    # Métriques groupes
    - ldap_groups_total
    - ldap_groups_empty
    - ldap_groups_members_total

    # Métriques de performance
    - ldap_query_duration_seconds
    - ldap_audit_duration_seconds
```

### 2. Démarrer l'exportateur de métriques

```bash
# Mode daemon avec Prometheus
ldap-monitor monitor prometheus --port 9090

# Ou en mode daemon complet
ldap-monitor monitor start --prometheus

# En arrière-plan avec nohup
nohup ldap-monitor monitor prometheus --port 9090 > /tmp/ldap-monitor.log 2>&1 &

# Avec systemd (voir section ci-dessous)
```

### 3. Créer un service systemd (Linux)

```bash
sudo tee /etc/systemd/system/ldap-monitor.service << EOF
[Unit]
Description=LDAP Health Monitor Prometheus Exporter
After=network.target

[Service]
Type=simple
User=ldap-monitor
Group=ldap-monitor
WorkingDirectory=/opt/ldap-monitor
Environment="LDAP_PASSWORD=your-password"
ExecStart=/usr/local/bin/ldap-monitor monitor prometheus --port 9090 --config /etc/ldap-monitor/config.yaml
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Créer l'utilisateur
sudo useradd --system --no-create-home ldap-monitor

# Démarrer le service
sudo systemctl daemon-reload
sudo systemctl start ldap-monitor
sudo systemctl enable ldap-monitor
sudo systemctl status ldap-monitor
```

### 4. Vérifier les métriques

```bash
# Tester l'endpoint
curl http://localhost:9090/metrics

# Vous devriez voir :
# HELP ldap_server_up LDAP server availability (1=up, 0=down)
# TYPE ldap_server_up gauge
# ldap_server_up{server="ldap.example.com"} 1
#
# HELP ldap_users_total Total number of users
# TYPE ldap_users_total gauge
# ldap_users_total 1523
```

## 🔧 Configuration Prometheus

### 1. Fichier de configuration

Créez ou éditez `prometheus.yml` :

```yaml
# Configuration globale
global:
  scrape_interval: 60s        # Scrape toutes les 60 secondes
  evaluation_interval: 60s    # Évaluer les règles toutes les 60s
  scrape_timeout: 30s         # Timeout après 30s

  # Labels externes (pour fédération)
  external_labels:
    cluster: 'production'
    environment: 'prod'

# Configuration des alertes (Alertmanager)
alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - 'localhost:9093'

# Règles d'alerte
rule_files:
  - "alerts/ldap_alerts.yml"

# Scrape configs
scrape_configs:
  # LDAP Health Monitor
  - job_name: 'ldap-monitor'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'ldap'
          team: 'infrastructure'

    # Métriques additionnelles
    metric_relabel_configs:
      - source_labels: [__name__]
        regex: 'ldap_.*'
        action: keep

  # Prometheus lui-même
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9091']

  # Plusieurs serveurs LDAP
  - job_name: 'ldap-monitor-dc1'
    static_configs:
      - targets: ['ldap-monitor-dc1:9090']
        labels:
          datacenter: 'dc1'

  - job_name: 'ldap-monitor-dc2'
    static_configs:
      - targets: ['ldap-monitor-dc2:9090']
        labels:
          datacenter: 'dc2'
```

### 2. Règles d'alerte

Créez `alerts/ldap_alerts.yml` :

```yaml
groups:
  - name: ldap_alerts
    interval: 60s
    rules:
      # Serveur LDAP down
      - alert: LDAPServerDown
        expr: ldap_server_up == 0
        for: 5m
        labels:
          severity: critical
          component: ldap
        annotations:
          summary: "Serveur LDAP indisponible"
          description: "Le serveur LDAP {{ $labels.server }} est down depuis 5 minutes."

      # Temps de réponse élevé
      - alert: LDAPHighResponseTime
        expr: ldap_server_response_time > 5000
        for: 10m
        labels:
          severity: warning
          component: ldap
        annotations:
          summary: "Temps de réponse LDAP élevé"
          description: "Le serveur {{ $labels.server }} répond en {{ $value }}ms (>5s)."

      # Trop d'utilisateurs inactifs
      - alert: LDAPHighInactiveUsers
        expr: (ldap_users_inactive / ldap_users_total) > 0.3
        for: 1h
        labels:
          severity: warning
          component: ldap
        annotations:
          summary: "Taux élevé d'utilisateurs inactifs"
          description: "{{ $value | humanizePercentage }} d'utilisateurs inactifs."

      # Utilisateurs avec mot de passe expiré
      - alert: LDAPPasswordsExpired
        expr: ldap_users_password_expired > 10
        for: 30m
        labels:
          severity: info
          component: ldap
        annotations:
          summary: "Mots de passe expirés"
          description: "{{ $value }} utilisateurs ont leur mot de passe expiré."

      # Groupes vides
      - alert: LDAPEmptyGroups
        expr: ldap_groups_empty > 5
        for: 24h
        labels:
          severity: info
          component: ldap
        annotations:
          summary: "Groupes vides détectés"
          description: "{{ $value }} groupes sont vides et peuvent être nettoyés."
```

### 3. Recharger la configuration

```bash
# Vérifier la syntaxe
promtool check config prometheus.yml

# Recharger sans redémarrer (si --web.enable-lifecycle activé)
curl -X POST http://localhost:9091/-/reload

# Ou redémarrer
sudo systemctl restart prometheus

# Avec Docker
docker restart prometheus
```

## 📊 Configuration Grafana

### 1. Connexion initiale

1. Accédez à `http://localhost:3000`
2. Login : `admin` / `admin`
3. Changez le mot de passe

### 2. Ajouter la source de données Prometheus

**Via l'interface :**

1. Menu → Configuration → Data Sources
2. Cliquez sur "Add data source"
3. Sélectionnez "Prometheus"
4. Configurez :
   - **Name**: Prometheus
   - **URL**: `http://localhost:9091` (ou `http://prometheus:9090` si Docker)
   - **Access**: Server (default)
5. Cliquez "Save & Test"

**Via l'API :**

```bash
curl -X POST \
  http://admin:admin@localhost:3000/api/datasources \
  -H 'Content-Type: application/json' \
  -d '{
    "name": "Prometheus",
    "type": "prometheus",
    "url": "http://localhost:9091",
    "access": "proxy",
    "isDefault": true
  }'
```

**Via provisioning (recommandé) :**

Créez `/etc/grafana/provisioning/datasources/prometheus.yml` :

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9091
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "60s"
      queryTimeout: "60s"
      httpMethod: "POST"
```

### 3. Importer le dashboard LDAP

**Dashboard JSON disponible :**

Créez `dashboards/ldap-health-monitor.json` :

```json
{
  "dashboard": {
    "title": "LDAP Health Monitor",
    "tags": ["ldap", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Server Status",
        "type": "stat",
        "targets": [
          {
            "expr": "ldap_server_up",
            "legendFormat": "{{ server }}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"value": 1, "text": "UP", "color": "green"},
              {"value": 0, "text": "DOWN", "color": "red"}
            ]
          }
        }
      }
    ]
  }
}
```

**Importer via l'interface :**

1. Menu → Dashboards → Import
2. Upload le fichier JSON ou collez le contenu
3. Sélectionnez la datasource Prometheus
4. Cliquez "Import"

## 📈 Métriques Disponibles

### Métriques Serveur

| Métrique | Type | Description |
|----------|------|-------------|
| `ldap_server_up` | Gauge | Statut du serveur (1=up, 0=down) |
| `ldap_server_response_time` | Gauge | Temps de réponse en ms |
| `ldap_server_connections` | Gauge | Nombre de connexions actives |
| `ldap_server_operations_total` | Counter | Total des opérations LDAP |
| `ldap_server_search_operations` | Counter | Nombre de recherches |
| `ldap_server_bind_operations` | Counter | Nombre de binds |

### Métriques Utilisateurs

| Métrique | Type | Description |
|----------|------|-------------|
| `ldap_users_total` | Gauge | Nombre total d'utilisateurs |
| `ldap_users_active` | Gauge | Utilisateurs actifs |
| `ldap_users_inactive` | Gauge | Utilisateurs inactifs |
| `ldap_users_locked` | Gauge | Comptes verrouillés |
| `ldap_users_password_expired` | Gauge | Mots de passe expirés |
| `ldap_users_password_expiring_soon` | Gauge | Expire dans <30 jours |
| `ldap_users_missing_attributes` | Gauge | Attributs manquants |

### Métriques Groupes

| Métrique | Type | Description |
|----------|------|-------------|
| `ldap_groups_total` | Gauge | Nombre total de groupes |
| `ldap_groups_empty` | Gauge | Groupes sans membres |
| `ldap_groups_members_total` | Gauge | Total des membres |
| `ldap_groups_large` | Gauge | Groupes >100 membres |

### Métriques de Performance

| Métrique | Type | Description |
|----------|------|-------------|
| `ldap_query_duration_seconds` | Histogram | Durée des requêtes |
| `ldap_audit_duration_seconds` | Histogram | Durée des audits |

## 📊 Dashboards Grafana Prédéfinis

### Dashboard 1 : Vue d'ensemble

**Panels recommandés :**

1. **Server Status** (Stat)
   - Query: `ldap_server_up`
   - Affichage : UP/DOWN avec couleur

2. **Response Time** (Graph)
   - Query: `ldap_server_response_time`
   - Unité : milliseconds (ms)

3. **Total Users** (Stat)
   - Query: `ldap_users_total`

4. **Active vs Inactive** (Pie Chart)
   - Query 1: `ldap_users_active`
   - Query 2: `ldap_users_inactive`

5. **Password Status** (Bar Gauge)
   - Query 1: `ldap_users_password_expired`
   - Query 2: `ldap_users_password_expiring_soon`

### Dashboard 2 : Performance

**Panels :**

1. **Query Duration** (Heatmap)
   ```promql
   rate(ldap_query_duration_seconds_bucket[5m])
   ```

2. **Operations Rate** (Graph)
   ```promql
   rate(ldap_server_operations_total[5m])
   ```

3. **Connection Pool** (Graph)
   ```promql
   ldap_server_connections
   ```

### Queries PromQL Utiles

```promql
# Taux d'utilisateurs inactifs
(ldap_users_inactive / ldap_users_total) * 100

# Moyenne du temps de réponse sur 5 min
avg_over_time(ldap_server_response_time[5m])

# Taux de croissance des utilisateurs
rate(ldap_users_total[1d])

# Groupes par taille moyenne
ldap_groups_members_total / ldap_groups_total

# P95 du temps de requête
histogram_quantile(0.95, rate(ldap_query_duration_seconds_bucket[5m]))
```

## 🚨 Configuration des Alertes

### Alertmanager

**Installation :**

```bash
# Docker
docker run -d \
  --name alertmanager \
  --network monitoring \
  -p 9093:9093 \
  -v $(pwd)/alertmanager.yml:/etc/alertmanager/alertmanager.yml \
  prom/alertmanager:latest
```

**Configuration `alertmanager.yml` :**

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'cluster']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'slack-ldap'

  routes:
    - match:
        severity: critical
      receiver: 'slack-critical'

    - match:
        severity: warning
      receiver: 'slack-warnings'

receivers:
  - name: 'slack-ldap'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#ldap-monitoring'

  - name: 'slack-critical'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#alerts-critical'
        text: '@channel LDAP Critical Alert'

  - name: 'slack-warnings'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
        channel: '#ldap-monitoring'
```

## ⚡ Optimisation

### Rétention des données

**Prometheus :**

```bash
# Dans prometheus.yml ou en ligne de commande
--storage.tsdb.retention.time=90d
--storage.tsdb.retention.size=50GB
```

### Performance queries

**Utilisez le recording rules pour les queries complexes :**

```yaml
groups:
  - name: ldap_recording_rules
    interval: 60s
    rules:
      - record: ldap:users:inactive_ratio
        expr: ldap_users_inactive / ldap_users_total

      - record: ldap:server:avg_response_time_5m
        expr: avg_over_time(ldap_server_response_time[5m])
```

## 🐛 Troubleshooting

### Prometheus ne récupère pas les métriques

```bash
# Vérifier le target dans Prometheus UI
# http://localhost:9091/targets

# Vérifier les logs
docker logs prometheus

# Tester manuellement
curl http://localhost:9090/metrics
```

### Grafana ne se connecte pas à Prometheus

```bash
# Vérifier la connectivité
curl http://localhost:9091/api/v1/query?query=up

# Vérifier les logs Grafana
docker logs grafana

# Tester depuis le container Grafana
docker exec -it grafana curl http://prometheus:9090/api/v1/query?query=up
```

## 📚 Ressources

- [Documentation Prometheus](https://prometheus.io/docs/)
- [Documentation Grafana](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [Grafana Dashboards](https://grafana.com/grafana/dashboards/)

## 🔗 Liens Connexes

- [Configuration du Monitoring](../configuration/Monitoring-Configuration.md)
- [Système d'Alertes](../features/monitoring/Alerts-System.md)
- [Slack Integration](Slack.md)
