# Intégration Prometheus et Métriques

## Introduction

Prometheus est un système de surveillance et d'alerting open-source conçu pour la fiabilité et la scalabilité. LDAP Health Monitor fournit une intégration native avec Prometheus, exposant toutes les métriques LDAP au format Prometheus pour une surveillance complète et des dashboards Grafana.

## Table des Matières

- [Introduction](#introduction)
- [Architecture Prometheus](#architecture-prometheus)
- [Configuration de Base](#configuration-de-base)
- [Métriques Exposées](#métriques-exposées)
- [Labels et Dimensions](#labels-et-dimensions)
- [Requêtes PromQL](#requêtes-promql)
- [Règles d'Alerting](#règles-dalerting)
- [Dashboards Grafana](#dashboards-grafana)
- [Fédération et Haute Disponibilité](#fédération-et-haute-disponibilité)
- [Optimisation et Performance](#optimisation-et-performance)
- [Exemples Pratiques](#exemples-pratiques)
- [Troubleshooting](#troubleshooting)
- [Bonnes Pratiques](#bonnes-pratiques)

---

## Architecture Prometheus

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│             Architecture Prometheus + LDAP Monitor              │
└─────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────┐
    │        LDAP Health Monitor                         │
    ├────────────────────────────────────────────────────┤
    │                                                     │
    │  ┌──────────────────────────────────────────┐     │
    │  │     Metrics Collector                    │     │
    │  │  - Collecte depuis LDAP                  │     │
    │  │  - Traitement des données                │     │
    │  └──────────────┬───────────────────────────┘     │
    │                 │                                  │
    │  ┌──────────────▼───────────────────────────┐     │
    │  │     Prometheus Registry                  │     │
    │  │  - Gauges, Counters, Histograms         │     │
    │  │  - Labels et métadonnées                │     │
    │  └──────────────┬───────────────────────────┘     │
    │                 │                                  │
    │  ┌──────────────▼───────────────────────────┐     │
    │  │     HTTP Server (:9090)                  │     │
    │  │  GET /metrics                            │     │
    │  └──────────────┬───────────────────────────┘     │
    │                 │                                  │
    └─────────────────┼──────────────────────────────────┘
                      │
                      │ HTTP Scrape (pull)
                      │ Toutes les 60s
                      │
    ┌─────────────────▼──────────────────────────────────┐
    │            Prometheus Server                        │
    ├────────────────────────────────────────────────────┤
    │  • TSDB (Time Series Database)                     │
    │  • PromQL Query Engine                             │
    │  • Alertmanager integration                        │
    │  • Federation support                              │
    └─────────────────┬──────────────────────────────────┘
                      │
           ┌──────────┼──────────┐
           │          │          │
    ┌──────▼──┐  ┌───▼──────┐  ┌▼──────────┐
    │ Grafana │  │Alertmgr  │  │  API      │
    │Dashboard│  │          │  │ Clients   │
    └─────────┘  └──────────┘  └───────────┘
```

### Flux de Données

```
┌─────────────────────────────────────────────────────────────┐
│                  Flux de Scraping Prometheus                │
└─────────────────────────────────────────────────────────────┘

  LDAP Server         Monitor           Prometheus        Grafana
      │                  │                   │               │
  1.  │  Query           │                   │               │
      │◄─────────────────┤                   │               │
      │                  │                   │               │
  2.  │  Response        │                   │               │
      ├─────────────────►│                   │               │
      │                  │                   │               │
  3.  │              Process                 │               │
      │              & Store                 │               │
      │              in Registry             │               │
      │                  │                   │               │
  4.  │                  │   HTTP GET        │               │
      │                  │   /metrics        │               │
      │                  │◄──────────────────┤               │
      │                  │                   │               │
  5.  │                  │   Metrics (text)  │               │
      │                  ├──────────────────►│               │
      │                  │                   │               │
  6.  │                  │               Store in            │
      │                  │               TSDB               │
      │                  │                   │               │
  7.  │                  │                   │   Query       │
      │                  │                   │◄──────────────┤
      │                  │                   │               │
  8.  │                  │                   │   Results     │
      │                  │                   ├──────────────►│
      │                  │                   │               │
      │                  │                   │           Visualize
```

---

## Configuration de Base

### Configuration LDAP Monitor

```yaml
# config.yaml

integrations:
  prometheus:
    enabled: true

    # Port d'écoute
    port: 9090
    host: 0.0.0.0  # 0.0.0.0 = toutes les interfaces, 127.0.0.1 = localhost uniquement

    # Path de l'endpoint
    path: /metrics

    # Options
    include_timestamp: true
    include_process_metrics: true  # Métriques CPU/mémoire du processus
    include_platform_metrics: false  # Métriques système (disk, network)

    # Sécurité (optionnel)
    basic_auth:
      enabled: false
      username: prometheus
      password: ${PROMETHEUS_PASSWORD}

    # TLS (optionnel)
    tls:
      enabled: false
      cert_file: /path/to/cert.pem
      key_file: /path/to/key.pem
```

### Démarrage du Serveur Prometheus

```bash
# Démarrer le serveur de métriques
ldap-monitor prometheus serve --port 9090

# Sortie
✅ Prometheus metrics server started
────────────────────────────────────
Listening on: http://0.0.0.0:9090
Metrics endpoint: http://0.0.0.0:9090/metrics
Process metrics: Enabled
Platform metrics: Disabled

Press Ctrl+C to stop
```

```bash
# En mode daemon (avec le monitoring)
ldap-monitor monitor start --daemon

# Le serveur Prometheus démarre automatiquement si configuré
```

### Configuration Prometheus Server

```yaml
# prometheus.yml

global:
  scrape_interval: 60s      # Scrape toutes les 60 secondes
  evaluation_interval: 60s  # Évaluer les règles toutes les 60 secondes
  scrape_timeout: 10s

  # Labels externes (ajoutés à toutes les métriques)
  external_labels:
    environment: production
    cluster: ldap-prod

# Configuration des scrape
scrape_configs:
  - job_name: 'ldap-monitor'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          instance: ldap-monitor-01
          datacenter: dc1

    # Scrape interval spécifique pour ce job
    scrape_interval: 60s
    scrape_timeout: 10s

    # Relabeling (optionnel)
    relabel_configs:
      - source_labels: [__address__]
        target_label: __param_target
      - source_labels: [__param_target]
        target_label: instance
      - target_label: __address__
        replacement: localhost:9090

# Alerting (optionnel)
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']

# Règles d'alerting
rule_files:
  - "alerts/ldap-monitor.yml"
```

### Vérification de l'Endpoint

```bash
# Tester l'endpoint manuellement
curl http://localhost:9090/metrics

# Sortie (format Prometheus)
# HELP ldap_users_total Total number of LDAP users
# TYPE ldap_users_total gauge
ldap_users_total{status="total"} 1247
ldap_users_total{status="active"} 1189
ldap_users_total{status="inactive"} 58

# HELP ldap_groups_total Total number of LDAP groups
# TYPE ldap_groups_total gauge
ldap_groups_total 89
ldap_groups_total{empty="true"} 5
ldap_groups_total{empty="false"} 84

# HELP ldap_response_time_seconds LDAP query response time
# TYPE ldap_response_time_seconds histogram
ldap_response_time_seconds_bucket{le="0.1"} 145
ldap_response_time_seconds_bucket{le="0.5"} 289
ldap_response_time_seconds_bucket{le="1.0"} 298
ldap_response_time_seconds_bucket{le="2.0"} 300
ldap_response_time_seconds_bucket{le="+Inf"} 300
ldap_response_time_seconds_sum 127.3
ldap_response_time_seconds_count 300

# HELP ldap_auth_failures_total Total authentication failures
# TYPE ldap_auth_failures_total counter
ldap_auth_failures_total 145

# HELP process_cpu_seconds_total Total user and system CPU time
# TYPE process_cpu_seconds_total counter
process_cpu_seconds_total 23.45
```

---

## Métriques Exposées

### Métriques de Disponibilité

#### ldap_server_up

**Description** : Indique si le serveur LDAP est accessible.

**Type** : Gauge
**Valeurs** : 0 (down) ou 1 (up)

```prometheus
# HELP ldap_server_up LDAP server availability
# TYPE ldap_server_up gauge
ldap_server_up{server="ldap.example.com",port="636"} 1
```

**PromQL** :
```promql
# Vérifier disponibilité
ldap_server_up == 0

# Uptime en pourcentage (dernières 24h)
avg_over_time(ldap_server_up[24h]) * 100
```

#### ldap_connections_active

**Description** : Nombre de connexions LDAP actives.

**Type** : Gauge

```prometheus
# HELP ldap_connections_active Active LDAP connections
# TYPE ldap_connections_active gauge
ldap_connections_active 8
```

**PromQL** :
```promql
# Connexions actuelles
ldap_connections_active

# Pic de connexions (dernière heure)
max_over_time(ldap_connections_active[1h])

# Moyenne de connexions (dernier jour)
avg_over_time(ldap_connections_active[24h])
```

### Métriques de Performance

#### ldap_response_time_seconds

**Description** : Temps de réponse des requêtes LDAP.

**Type** : Histogram

```prometheus
# HELP ldap_response_time_seconds LDAP query response time
# TYPE ldap_response_time_seconds histogram
ldap_response_time_seconds_bucket{operation="bind",le="0.1"} 145
ldap_response_time_seconds_bucket{operation="bind",le="0.5"} 289
ldap_response_time_seconds_bucket{operation="bind",le="1.0"} 298
ldap_response_time_seconds_bucket{operation="bind",le="2.0"} 300
ldap_response_time_seconds_bucket{operation="bind",le="+Inf"} 300
ldap_response_time_seconds_sum{operation="bind"} 127.3
ldap_response_time_seconds_count{operation="bind"} 300
```

**PromQL** :
```promql
# Temps de réponse moyen
rate(ldap_response_time_seconds_sum[5m]) / rate(ldap_response_time_seconds_count[5m])

# 95e percentile
histogram_quantile(0.95, rate(ldap_response_time_seconds_bucket[5m]))

# 99e percentile
histogram_quantile(0.99, rate(ldap_response_time_seconds_bucket[5m]))
```

#### ldap_operations_total

**Description** : Nombre total d'opérations LDAP par type.

**Type** : Counter
**Labels** : operation (search, bind, modify, add, delete)

```prometheus
# HELP ldap_operations_total Total LDAP operations by type
# TYPE ldap_operations_total counter
ldap_operations_total{operation="search"} 125684
ldap_operations_total{operation="bind"} 89562
ldap_operations_total{operation="modify"} 3421
ldap_operations_total{operation="add"} 234
ldap_operations_total{operation="delete"} 12
```

**PromQL** :
```promql
# Taux d'opérations par seconde
rate(ldap_operations_total[5m])

# Opérations par type
sum by (operation) (rate(ldap_operations_total[5m]))

# Total sur la dernière heure
increase(ldap_operations_total[1h])
```

### Métriques de Contenu

#### ldap_users_total

**Description** : Nombre d'utilisateurs LDAP.

**Type** : Gauge
**Labels** : status (total, active, inactive, disabled)

```prometheus
# HELP ldap_users_total Total number of LDAP users
# TYPE ldap_users_total gauge
ldap_users_total{status="total"} 1247
ldap_users_total{status="active"} 1189
ldap_users_total{status="inactive"} 58
ldap_users_total{status="disabled"} 0
```

**PromQL** :
```promql
# Nombre total d'utilisateurs
ldap_users_total{status="total"}

# Pourcentage d'utilisateurs actifs
ldap_users_total{status="active"} / ldap_users_total{status="total"} * 100

# Croissance du nombre d'utilisateurs (dernière semaine)
ldap_users_total{status="total"} - ldap_users_total{status="total"} offset 7d

# Taux de croissance par jour
rate(ldap_users_total{status="total"}[1d]) * 86400
```

#### ldap_groups_total

**Description** : Nombre de groupes LDAP.

**Type** : Gauge
**Labels** : empty (true/false)

```prometheus
# HELP ldap_groups_total Total number of LDAP groups
# TYPE ldap_groups_total gauge
ldap_groups_total 89
ldap_groups_total{empty="true"} 5
ldap_groups_total{empty="false"} 84
```

**PromQL** :
```promql
# Nombre total de groupes
ldap_groups_total

# Pourcentage de groupes vides
ldap_groups_total{empty="true"} / ldap_groups_total * 100

# Groupes non vides
ldap_groups_total{empty="false"}
```

### Métriques de Sécurité

#### ldap_auth_failures_total

**Description** : Nombre d'échecs d'authentification.

**Type** : Counter
**Labels** : reason (invalid_credentials, account_disabled, account_locked)

```prometheus
# HELP ldap_auth_failures_total Total authentication failures
# TYPE ldap_auth_failures_total counter
ldap_auth_failures_total{reason="invalid_credentials"} 145
ldap_auth_failures_total{reason="account_disabled"} 12
ldap_auth_failures_total{reason="account_locked"} 3
```

**PromQL** :
```promql
# Taux d'échecs par minute
rate(ldap_auth_failures_total[5m]) * 60

# Total sur la dernière heure
increase(ldap_auth_failures_total[1h])

# Par raison
sum by (reason) (rate(ldap_auth_failures_total[5m]))
```

#### ldap_ssl_cert_expiry_days

**Description** : Nombre de jours avant l'expiration du certificat SSL.

**Type** : Gauge
**Labels** : server

```prometheus
# HELP ldap_ssl_cert_expiry_days Days until SSL certificate expiry
# TYPE ldap_ssl_cert_expiry_days gauge
ldap_ssl_cert_expiry_days{server="ldap.example.com"} 287
```

**PromQL** :
```promql
# Jours avant expiration
ldap_ssl_cert_expiry_days

# Alerter si < 30 jours
ldap_ssl_cert_expiry_days < 30

# Alerter si < 7 jours (critique)
ldap_ssl_cert_expiry_days < 7
```

### Métriques de Santé

#### ldap_disk_usage_percent

**Description** : Utilisation du disque en pourcentage.

**Type** : Gauge
**Labels** : mount_point

```prometheus
# HELP ldap_disk_usage_percent Disk usage percentage
# TYPE ldap_disk_usage_percent gauge
ldap_disk_usage_percent{mount_point="/var/lib/ldap"} 68.5
```

#### ldap_memory_usage_percent

**Description** : Utilisation de la mémoire du processus LDAP.

**Type** : Gauge

```prometheus
# HELP ldap_memory_usage_percent Memory usage percentage
# TYPE ldap_memory_usage_percent gauge
ldap_memory_usage_percent 45.2
```

### Métriques de Processus (Standard Prometheus)

```prometheus
# CPU
process_cpu_seconds_total 23.45

# Mémoire
process_resident_memory_bytes 145629184

# Descripteurs de fichiers
process_open_fds 12
process_max_fds 1024

# Goroutines (si applicable)
process_num_threads 8
```

---

## Labels et Dimensions

### Labels Standard

| Label | Description | Exemple |
|-------|-------------|---------|
| `server` | Serveur LDAP | ldap.example.com |
| `port` | Port LDAP | 636 |
| `status` | Statut (users) | active, inactive, disabled |
| `operation` | Type d'opération | search, bind, modify |
| `reason` | Raison (échecs auth) | invalid_credentials |
| `empty` | Groupe vide | true, false |

### Labels Personnalisés

```yaml
# config.yaml

integrations:
  prometheus:
    enabled: true

    # Labels personnalisés (ajoutés à toutes les métriques)
    extra_labels:
      environment: production
      datacenter: dc1
      cluster: ldap-cluster-1
      team: ops
```

**Résultat** :
```prometheus
ldap_users_total{status="total",environment="production",datacenter="dc1",cluster="ldap-cluster-1",team="ops"} 1247
```

### Relabeling

```yaml
# prometheus.yml

scrape_configs:
  - job_name: 'ldap-monitor'
    static_configs:
      - targets: ['ldap-monitor-01:9090']

    # Ajouter/modifier des labels
    relabel_configs:
      # Ajouter le hostname
      - source_labels: [__address__]
        target_label: hostname
        regex: '([^:]+)(:\d+)?'
        replacement: '$1'

      # Ajouter une région
      - target_label: region
        replacement: eu-west-1

    # Relabeling après scrape
    metric_relabel_configs:
      # Supprimer les métriques de debug
      - source_labels: [__name__]
        regex: 'debug_.*'
        action: drop

      # Renommer un label
      - source_labels: [old_label]
        target_label: new_label
```

---

## Requêtes PromQL

### Requêtes de Base

```promql
# Valeur actuelle d'une métrique
ldap_users_total{status="total"}

# Dernière valeur connue
ldap_users_total{status="total"} offset 0s

# Valeur il y a 1 heure
ldap_users_total{status="total"} offset 1h

# Différence avec il y a 1 heure
ldap_users_total{status="total"} - ldap_users_total{status="total"} offset 1h
```

### Requêtes avec Agrégation

```promql
# Somme par statut
sum by (status) (ldap_users_total)

# Moyenne sur tous les serveurs
avg(ldap_response_time_seconds_sum) / avg(ldap_response_time_seconds_count)

# Maximum
max(ldap_connections_active)

# Minimum
min(ldap_disk_usage_percent)

# Comptage
count(ldap_server_up == 1)
```

### Requêtes sur Intervalles de Temps

```promql
# Moyenne sur 5 minutes
avg_over_time(ldap_response_time_seconds_sum[5m]) / avg_over_time(ldap_response_time_seconds_count[5m])

# Maximum sur 1 heure
max_over_time(ldap_connections_active[1h])

# Minimum sur 24 heures
min_over_time(ldap_disk_usage_percent[24h])

# Changement absolu sur 1 heure
delta(ldap_users_total{status="total"}[1h])

# Taux de changement par seconde
rate(ldap_operations_total[5m])

# Augmentation totale
increase(ldap_auth_failures_total[1h])
```

### Requêtes Avancées

#### Disponibilité en Pourcentage

```promql
# SLA sur les dernières 24h
avg_over_time(ldap_server_up[24h]) * 100

# SLA sur le dernier mois
avg_over_time(ldap_server_up[30d]) * 100
```

#### Temps de Réponse - Percentiles

```promql
# Médiane (50e percentile)
histogram_quantile(0.50, rate(ldap_response_time_seconds_bucket[5m]))

# 95e percentile
histogram_quantile(0.95, rate(ldap_response_time_seconds_bucket[5m]))

# 99e percentile
histogram_quantile(0.99, rate(ldap_response_time_seconds_bucket[5m]))

# 99.9e percentile
histogram_quantile(0.999, rate(ldap_response_time_seconds_bucket[5m]))
```

#### Taux d'Erreur

```promql
# Pourcentage d'échecs d'authentification
rate(ldap_auth_failures_total[5m]) / rate(ldap_operations_total{operation="bind"}[5m]) * 100

# Taux de succès (disponibilité)
sum(rate(ldap_operations_total[5m])) - sum(rate(ldap_errors_total[5m]))
```

#### Prédictions

```promql
# Prédiction linéaire du nombre d'utilisateurs dans 7 jours
predict_linear(ldap_users_total{status="total"}[7d], 7*24*3600)

# Prédiction de l'utilisation disque dans 30 jours
predict_linear(ldap_disk_usage_percent[30d], 30*24*3600)

# Estimer quand le disque sera plein
(100 - ldap_disk_usage_percent) / deriv(ldap_disk_usage_percent[7d])
```

#### Corrélations

```promql
# Corrélation entre utilisateurs et temps de réponse
ldap_users_total{status="total"} * on() group_left ldap_response_time_seconds_sum / ldap_response_time_seconds_count

# Ratio utilisateurs actifs / inactifs
ldap_users_total{status="active"} / ldap_users_total{status="inactive"}
```

---

## Règles d'Alerting

### Fichier de Règles Prometheus

```yaml
# /etc/prometheus/rules/ldap-monitor.yml

groups:
  - name: ldap_availability
    interval: 60s
    rules:
      # Serveur LDAP down
      - alert: LDAPServerDown
        expr: ldap_server_up == 0
        for: 1m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "LDAP server is down"
          description: "LDAP server {{ $labels.server }}:{{ $labels.port }} has been down for more than 1 minute"
          runbook_url: "https://wiki.company.com/runbooks/ldap-server-down"

      # Temps de réponse élevé
      - alert: LDAPHighResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(ldap_response_time_seconds_bucket[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "LDAP response time is high"
          description: "95th percentile response time is {{ $value }}s (threshold: 2.0s)"

      # Temps de réponse critique
      - alert: LDAPCriticalResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(ldap_response_time_seconds_bucket[5m])
          ) > 5.0
        for: 2m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "LDAP response time is critically high"
          description: "95th percentile response time is {{ $value }}s"

  - name: ldap_security
    interval: 60s
    rules:
      # Échecs d'authentification élevés
      - alert: LDAPHighAuthFailures
        expr: rate(ldap_auth_failures_total[5m]) * 300 > 10
        for: 5m
        labels:
          severity: warning
          team: security
        annotations:
          summary: "High authentication failure rate"
          description: "{{ $value }} auth failures per 5 minutes"

      # Échecs d'authentification critiques (attaque possible)
      - alert: LDAPAuthAttack
        expr: rate(ldap_auth_failures_total[5m]) * 300 > 50
        for: 1m
        labels:
          severity: critical
          team: security
        annotations:
          summary: "Possible brute force attack"
          description: "{{ $value }} auth failures per 5 minutes - possible attack"

      # Certificat SSL expire bientôt
      - alert: LDAPSSLCertExpiringSoon
        expr: ldap_ssl_cert_expiry_days < 30
        for: 1h
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "SSL certificate expiring soon"
          description: "SSL certificate for {{ $labels.server }} expires in {{ $value }} days"

      # Certificat SSL expire dans moins de 7 jours
      - alert: LDAPSSLCertExpiringCritical
        expr: ldap_ssl_cert_expiry_days < 7
        for: 1h
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "SSL certificate expiring very soon"
          description: "SSL certificate for {{ $labels.server }} expires in {{ $value }} days - URGENT"

  - name: ldap_content
    interval: 300s
    rules:
      # Pic soudain d'utilisateurs
      - alert: LDAPUserSpike
        expr: |
          (
            ldap_users_total{status="total"} -
            ldap_users_total{status="total"} offset 1h
          ) > 100
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "Unusual increase in user count"
          description: "User count increased by {{ $value }} in the last hour"

      # Chute soudaine d'utilisateurs
      - alert: LDAPUserDrop
        expr: |
          (
            ldap_users_total{status="total"} -
            ldap_users_total{status="total"} offset 1h
          ) < -50
        for: 5m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "Large decrease in user count"
          description: "User count decreased by {{ $value }} in the last hour - possible data loss"

      # Trop de groupes vides
      - alert: LDAPManyEmptyGroups
        expr: ldap_groups_total{empty="true"} > 10
        for: 1h
        labels:
          severity: info
          team: ops
        annotations:
          summary: "Many empty groups detected"
          description: "{{ $value }} empty groups found - cleanup recommended"

  - name: ldap_performance
    interval: 60s
    rules:
      # Utilisation disque élevée
      - alert: LDAPHighDiskUsage
        expr: ldap_disk_usage_percent > 80
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "LDAP disk usage is high"
          description: "Disk usage is {{ $value }}% (threshold: 80%)"

      # Utilisation disque critique
      - alert: LDAPCriticalDiskUsage
        expr: ldap_disk_usage_percent > 90
        for: 5m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "LDAP disk usage is critical"
          description: "Disk usage is {{ $value }}% (threshold: 90%) - immediate action required"

      # Utilisation mémoire élevée
      - alert: LDAPHighMemoryUsage
        expr: ldap_memory_usage_percent > 85
        for: 10m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "LDAP memory usage is high"
          description: "Memory usage is {{ $value }}%"

  - name: ldap_monitoring
    interval: 60s
    rules:
      # Monitor collector lui-même
      - alert: LDAPMonitorDown
        expr: up{job="ldap-monitor"} == 0
        for: 2m
        labels:
          severity: critical
          team: ops
        annotations:
          summary: "LDAP Monitor is down"
          description: "Cannot scrape metrics from LDAP Monitor"

      # Pas de mise à jour des métriques
      - alert: LDAPMetricsStale
        expr: (time() - ldap_users_total{status="total"}) > 600
        for: 5m
        labels:
          severity: warning
          team: ops
        annotations:
          summary: "LDAP metrics are stale"
          description: "Metrics haven't been updated for more than 10 minutes"
```

---

## Dashboards Grafana

### Dashboard JSON (Exemple Complet)

```json
{
  "dashboard": {
    "title": "LDAP Health Monitor",
    "tags": ["ldap", "monitoring", "infrastructure"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "LDAP Server Status",
        "type": "stat",
        "targets": [
          {
            "expr": "ldap_server_up",
            "legendFormat": "{{ server }}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 1, "color": "green"}
              ]
            },
            "mappings": [
              {"value": 0, "text": "DOWN"},
              {"value": 1, "text": "UP"}
            ]
          }
        }
      },
      {
        "id": 2,
        "title": "Response Time (95th percentile)",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(ldap_response_time_seconds_bucket[5m]))",
            "legendFormat": "p95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(ldap_response_time_seconds_bucket[5m]))",
            "legendFormat": "p99"
          }
        ],
        "yaxes": [
          {"format": "s", "label": "Response Time"}
        ]
      },
      {
        "id": 3,
        "title": "User Count",
        "type": "graph",
        "targets": [
          {
            "expr": "ldap_users_total{status=\"total\"}",
            "legendFormat": "Total Users"
          },
          {
            "expr": "ldap_users_total{status=\"active\"}",
            "legendFormat": "Active Users"
          },
          {
            "expr": "ldap_users_total{status=\"inactive\"}",
            "legendFormat": "Inactive Users"
          }
        ]
      },
      {
        "id": 4,
        "title": "Authentication Failures",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ldap_auth_failures_total[5m]) * 300",
            "legendFormat": "{{ reason }}"
          }
        ],
        "alert": {
          "conditions": [
            {
              "evaluator": {"type": "gt", "params": [10]},
              "query": {"params": ["A", "5m", "now"]}
            }
          ]
        }
      }
    ]
  }
}
```

### Panneaux Recommandés

#### 1. Vue d'Ensemble (Overview)

```promql
# Statut global (Stat panel)
ldap_server_up

# Utilisateurs totaux (Stat panel)
ldap_users_total{status="total"}

# Groupes totaux (Stat panel)
ldap_groups_total

# Temps de réponse moyen (Gauge panel)
rate(ldap_response_time_seconds_sum[5m]) / rate(ldap_response_time_seconds_count[5m])
```

#### 2. Performance

```promql
# Temps de réponse (Graph panel)
histogram_quantile(0.50, rate(ldap_response_time_seconds_bucket[5m])) # Médiane
histogram_quantile(0.95, rate(ldap_response_time_seconds_bucket[5m])) # p95
histogram_quantile(0.99, rate(ldap_response_time_seconds_bucket[5m])) # p99

# Opérations par seconde (Graph panel)
sum(rate(ldap_operations_total[5m])) by (operation)

# Connexions actives (Graph panel)
ldap_connections_active
```

#### 3. Contenu

```promql
# Évolution utilisateurs (Graph panel)
ldap_users_total{status="total"}
ldap_users_total{status="active"}
ldap_users_total{status="inactive"}

# Ratio actifs/inactifs (Pie chart)
ldap_users_total

# Groupes vides (Stat panel)
ldap_groups_total{empty="true"}
```

#### 4. Sécurité

```promql
# Échecs d'authentification (Graph panel)
rate(ldap_auth_failures_total[5m]) * 300

# Jours avant expiration SSL (Stat panel)
ldap_ssl_cert_expiry_days

# Taux d'échec auth (Gauge panel)
rate(ldap_auth_failures_total[5m]) / rate(ldap_operations_total{operation="bind"}[5m]) * 100
```

#### 5. Ressources

```promql
# Utilisation disque (Gauge panel)
ldap_disk_usage_percent

# Utilisation mémoire (Gauge panel)
ldap_memory_usage_percent

# CPU du processus (Graph panel)
rate(process_cpu_seconds_total{job="ldap-monitor"}[5m]) * 100
```

### Import de Dashboard Prêt à l'Emploi

```bash
# Créer un dashboard JSON
cat > ldap-monitor-dashboard.json <<'EOF'
{
  "dashboard": {
    "title": "LDAP Health Monitor",
    "uid": "ldap-monitor",
    ...
  }
}
EOF

# Importer via API Grafana
curl -X POST \
  -H "Authorization: Bearer ${GRAFANA_API_KEY}" \
  -H "Content-Type: application/json" \
  -d @ldap-monitor-dashboard.json \
  http://grafana.example.com/api/dashboards/db

# Ou via UI:
# Grafana → Dashboards → Import → Upload JSON file
```

---

## Fédération et Haute Disponibilité

### Prometheus Federation

```yaml
# prometheus-global.yml (serveur de fédération)

scrape_configs:
  # Fédération depuis instances Prometheus locales
  - job_name: 'federate'
    scrape_interval: 60s
    honor_labels: true
    metrics_path: '/federate'

    params:
      'match[]':
        - '{job="ldap-monitor"}'
        - '{__name__=~"ldap_.*"}'

    static_configs:
      - targets:
          - 'prometheus-dc1:9090'
          - 'prometheus-dc2:9090'
          - 'prometheus-dc3:9090'
```

### Multiple LDAP Monitors

```yaml
# prometheus.yml

scrape_configs:
  - job_name: 'ldap-monitor-cluster'
    static_configs:
      - targets:
          - 'ldap-monitor-01:9090'
          - 'ldap-monitor-02:9090'
          - 'ldap-monitor-03:9090'
        labels:
          cluster: ldap-prod

  - job_name: 'ldap-monitor-dr'
    static_configs:
      - targets:
          - 'ldap-monitor-dr-01:9090'
        labels:
          cluster: ldap-dr
```

---

## Optimisation et Performance

### Limiter les Métriques Exposées

```yaml
# config.yaml

integrations:
  prometheus:
    enabled: true

    # Désactiver les métriques inutiles
    include_process_metrics: false
    include_platform_metrics: false

    # Filtrer les métriques
    metrics_filter:
      include:
        - ldap_users_total
        - ldap_groups_total
        - ldap_response_time_seconds
      exclude:
        - ldap_debug_*
```

### Agrégation et Recording Rules

```yaml
# prometheus-rules.yml

groups:
  - name: ldap_recording_rules
    interval: 60s
    rules:
      # Pré-calculer les percentiles (plus rapide pour les dashboards)
      - record: ldap:response_time:p95
        expr: histogram_quantile(0.95, rate(ldap_response_time_seconds_bucket[5m]))

      - record: ldap:response_time:p99
        expr: histogram_quantile(0.99, rate(ldap_response_time_seconds_bucket[5m]))

      # Agrégations utiles
      - record: ldap:users:active_ratio
        expr: ldap_users_total{status="active"} / ldap_users_total{status="total"}

      - record: ldap:auth_failures:rate5m
        expr: rate(ldap_auth_failures_total[5m]) * 300
```

---

## Exemples Pratiques

### Exemple 1 : Setup Complet Local

```bash
# 1. Démarrer LDAP Monitor avec Prometheus
ldap-monitor monitor start --daemon

# 2. Installer Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# 3. Configurer Prometheus
cat > prometheus.yml <<EOF
global:
  scrape_interval: 60s

scrape_configs:
  - job_name: 'ldap-monitor'
    static_configs:
      - targets: ['localhost:9090']
EOF

# 4. Démarrer Prometheus
./prometheus --config.file=prometheus.yml &

# 5. Vérifier
# Prometheus UI: http://localhost:9090
# Métriques LDAP: http://localhost:9090/metrics

# 6. Installer Grafana
docker run -d -p 3000:3000 grafana/grafana

# 7. Configurer datasource dans Grafana
# URL: http://localhost:9090
# Type: Prometheus
```

### Exemple 2 : Query Performance Trends

```bash
# Dans Prometheus UI (http://localhost:9090)

# Temps de réponse moyen sur 7 jours
avg_over_time(ldap:response_time:p95[7d])

# Croissance des utilisateurs
(ldap_users_total{status="total"} - ldap_users_total{status="total"} offset 7d) / 7

# Prédiction du nombre d'utilisateurs dans 30 jours
predict_linear(ldap_users_total{status="total"}[30d], 30*24*3600)
```

---

## Troubleshooting

### Problème 1 : Prometheus Ne Scrape Pas

**Diagnostic** :
```bash
# Vérifier que l'endpoint répond
curl http://localhost:9090/metrics

# Vérifier les targets dans Prometheus UI
# http://prometheus:9090/targets

# Logs Prometheus
tail -f /var/log/prometheus/prometheus.log
```

**Solutions** :
1. Vérifier la configuration dans prometheus.yml
2. Vérifier le firewall
3. Vérifier que le serveur LDAP Monitor tourne

### Problème 2 : Métriques Manquantes

**Diagnostic** :
```bash
# Lister toutes les métriques disponibles
curl http://localhost:9090/metrics | grep "^ldap_"

# Vérifier dans Prometheus
# Query: {__name__=~"ldap_.*"}
```

**Solutions** :
1. Vérifier la configuration des métriques dans config.yaml
2. Vérifier que la collecte fonctionne: `ldap-monitor metrics collect`
3. Redémarrer le serveur Prometheus

---

## Bonnes Pratiques

### 1. Naming des Métriques

```
✅ Bon:
ldap_users_total
ldap_response_time_seconds
ldap_auth_failures_total

❌ Mauvais:
usersCount
responseTime_ms
authFail
```

### 2. Labels

```promql
# ✅ Utiliser des labels pour les dimensions
ldap_users_total{status="active"}
ldap_operations_total{operation="search"}

# ❌ Créer des métriques séparées
ldap_users_active
ldap_users_inactive
ldap_operations_search
ldap_operations_bind
```

### 3. Recording Rules

```yaml
# ✅ Pré-calculer les requêtes complexes
- record: ldap:response_time:p95
  expr: histogram_quantile(0.95, rate(ldap_response_time_seconds_bucket[5m]))

# Puis utiliser dans les dashboards
ldap:response_time:p95

# Au lieu de recalculer à chaque fois
histogram_quantile(0.95, rate(ldap_response_time_seconds_bucket[5m]))
```

### 4. Alertes

```yaml
# ✅ Utiliser for pour éviter les faux positifs
- alert: LDAPHighResponseTime
  expr: ldap:response_time:p95 > 2.0
  for: 5m  # Attendre 5 minutes

# ❌ Alerter immédiatement
- alert: LDAPHighResponseTime
  expr: ldap:response_time:p95 > 2.0
  # Risque d'alertes intempestives
```

---

## Conclusion

L'intégration Prometheus fournit une solution complète et scalable pour la surveillance LDAP :

1. **Métriques standardisées** au format Prometheus
2. **Requêtes puissantes** avec PromQL
3. **Alerting flexible** avec règles personnalisables
4. **Visualisation** via Grafana
5. **Scalabilité** via fédération

### Ressources

- **Prometheus Documentation** : https://prometheus.io/docs/
- **PromQL Tutorial** : https://prometheus.io/docs/prometheus/latest/querying/basics/
- **Grafana Dashboards** : https://grafana.com/grafana/dashboards/

---

**Dernière mise à jour** : 2025-11-17
**Version** : 1.0.0
