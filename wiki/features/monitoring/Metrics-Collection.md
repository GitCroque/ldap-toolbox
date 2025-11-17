# Collecte de Métriques LDAP

## Introduction

La collecte de métriques est le cœur du système de surveillance de LDAP Health Monitor. Ce guide détaille les métriques disponibles, leur signification, les intervalles de collecte recommandés, et les stratégies de stockage.

## Table des Matières

- [Introduction](#introduction)
- [Architecture de Collecte](#architecture-de-collecte)
- [Métriques Disponibles](#métriques-disponibles)
- [Configuration de la Collecte](#configuration-de-la-collecte)
- [Intervalles de Collecte](#intervalles-de-collecte)
- [Stockage des Métriques](#stockage-des-métriques)
- [Export et Formats](#export-et-formats)
- [Optimisation des Performances](#optimisation-des-performances)
- [Exemples Pratiques](#exemples-pratiques)
- [API de Collecte](#api-de-collecte)
- [Métriques Personnalisées](#métriques-personnalisées)
- [Troubleshooting](#troubleshooting)
- [Bonnes Pratiques](#bonnes-pratiques)

---

## Architecture de Collecte

### Composants du Système de Collecte

```
┌─────────────────────────────────────────────────────────────────┐
│                Architecture de Collecte                          │
└─────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────┐
    │             MetricsCollector                        │
    ├────────────────────────────────────────────────────┤
    │                                                     │
    │  ┌──────────────┐      ┌──────────────────────┐  │
    │  │   Scheduler  │────► │  Collection Engine    │  │
    │  └──────────────┘      └──────────┬───────────┘  │
    │                                    │               │
    │  ┌─────────────────────────────────▼───────────┐ │
    │  │         LDAP Query Executor                  │ │
    │  ├─────────────────────────────────────────────┤ │
    │  │  • User Count Collector                     │ │
    │  │  • Group Count Collector                    │ │
    │  │  • Response Time Collector                  │ │
    │  │  • Auth Failures Collector                  │ │
    │  │  • Connection Pool Collector                │ │
    │  └─────────────────────────────────────────────┘ │
    │                                                     │
    │  ┌─────────────────────────────────────────────┐ │
    │  │         Prometheus Registry                  │ │
    │  ├─────────────────────────────────────────────┤ │
    │  │  • Gauges                                    │ │
    │  │  • Counters                                  │ │
    │  │  • Histograms                                │ │
    │  │  • Summaries                                 │ │
    │  └─────────────────────────────────────────────┘ │
    │                                                     │
    └─────────────────────┬───────────────────────────────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
    ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
    │  Prometheus │ │  InfluxDB│ │   SQLite   │
    │  (TSDB)     │ │  (TSDB)  │ │  (Local)   │
    └─────────────┘ └──────────┘ └────────────┘
```

### Flux de Collecte

```
┌───────────────────────────────────────────────────────────────┐
│                    Flux de Collecte                            │
└───────────────────────────────────────────────────────────────┘

  1. Déclenchement     2. Connexion      3. Requête       4. Traitement
  ┌──────────┐         ┌──────────┐      ┌─────────┐     ┌──────────┐
  │ Schedule │────────►│   LDAP   │─────►│ Query   │────►│ Process  │
  │  Timer   │         │  Connect │      │ Execute │     │  Result  │
  └──────────┘         └──────────┘      └─────────┘     └─────┬────┘
                                                                │
  5. Validation       6. Enrichment     7. Storage      8. Export
  ┌──────────┐       ┌──────────┐      ┌─────────┐    ┌──────────┐
  │ Validate │◄──────┤ Enrich   │◄─────┤  Store  │◄───┤  Export  │
  │  Data    │       │ Metadata │      │  TSDB   │    │ Prometheus│
  └──────────┘       └──────────┘      └─────────┘    └──────────┘
```

---

## Métriques Disponibles

### 1. Métriques de Disponibilité

#### ldap_server_up

**Description** : Indique si le serveur LDAP est accessible (1) ou non (0).

**Type** : Gauge
**Unité** : booléen (0 ou 1)
**Labels** : `server`, `port`
**Intervalle recommandé** : 60s

```python
# Prometheus
ldap_server_up{server="ldap.example.com",port="636"} 1
```

**Seuils recommandés** :
- **CRITICAL** : 0 (serveur down)
- **WARNING** : N/A

**Requête LDAP** :
```python
# Simple bind test
try:
    success, response_time, message = connector.test_connection()
    return 1 if success else 0
except:
    return 0
```

#### ldap_response_time_seconds

**Description** : Temps de réponse d'une requête LDAP simple (bind + unbind).

**Type** : Histogram
**Unité** : secondes
**Labels** : `operation`
**Intervalle recommandé** : 60s

```python
# Prometheus
ldap_response_time_seconds_bucket{operation="bind",le="0.1"} 145
ldap_response_time_seconds_bucket{operation="bind",le="0.5"} 289
ldap_response_time_seconds_bucket{operation="bind",le="1.0"} 298
ldap_response_time_seconds_sum 127.3
ldap_response_time_seconds_count 300
```

**Seuils recommandés** :
- **CRITICAL** : > 2000ms
- **WARNING** : > 500ms

**Requête LDAP** :
```python
start = time.time()
success, _, _ = connector.test_connection()
response_time = (time.time() - start) * 1000  # ms
```

#### ldap_connections_active

**Description** : Nombre de connexions LDAP actuellement actives.

**Type** : Gauge
**Unité** : nombre
**Labels** : aucun
**Intervalle recommandé** : 30s

```python
# Prometheus
ldap_connections_active 8
```

**Seuils recommandés** :
- **CRITICAL** : > 100 (ajuster selon capacité)
- **WARNING** : > 80

### 2. Métriques de Contenu

#### ldap_users_total

**Description** : Nombre total d'utilisateurs dans l'annuaire LDAP.

**Type** : Gauge
**Unité** : nombre
**Labels** : `status` (total, active, inactive, disabled)
**Intervalle recommandé** : 300s

```python
# Prometheus
ldap_users_total{status="total"} 1247
ldap_users_total{status="active"} 1189
ldap_users_total{status="inactive"} 58
ldap_users_total{status="disabled"} 0
```

**Requête LDAP** :
```python
# Total users
user_filter = f"(objectClass={config.ldap.user_objectclass})"
users = connector.search(
    search_base=config.ldap.users_ou,
    search_filter=user_filter,
    attributes=["dn"]
)
total_count = len(users)

# Active users (logged in last 90 days)
active_filter = f"(&(objectClass={config.ldap.user_objectclass})" \
                f"(lastLogon>={ninety_days_ago}))"
active_users = connector.search(
    search_base=config.ldap.users_ou,
    search_filter=active_filter,
    attributes=["dn"]
)
active_count = len(active_users)
```

**CLI** :
```bash
# Collecter manuellement
ldap-monitor metrics collect users_count

# Sortie
✅ User count collected
────────────────────────────────
Total users:    1247
Active users:   1189 (95.3%)
Inactive users: 58 (4.7%)
Disabled users: 0 (0.0%)
```

#### ldap_groups_total

**Description** : Nombre total de groupes dans l'annuaire LDAP.

**Type** : Gauge
**Unité** : nombre
**Labels** : `empty` (true/false)
**Intervalle recommandé** : 300s

```python
# Prometheus
ldap_groups_total 89
ldap_groups_total{empty="true"} 5
ldap_groups_total{empty="false"} 84
```

**Requête LDAP** :
```python
# Total groups
group_filter = f"(objectClass={config.ldap.group_objectclass})"
groups = connector.search(
    search_base=config.ldap.groups_ou,
    search_filter=group_filter,
    attributes=["dn", "member"]
)
total_count = len(groups)

# Empty groups (no members)
empty_count = sum(1 for g in groups if not g.get("member"))
```

#### ldap_group_members_total

**Description** : Nombre total de membres dans tous les groupes.

**Type** : Gauge
**Unité** : nombre
**Labels** : `group_dn`
**Intervalle recommandé** : 300s

```python
# Prometheus (avec labels)
ldap_group_members_total{group_dn="cn=admins,ou=groups,dc=example,dc=com"} 12
ldap_group_members_total{group_dn="cn=users,ou=groups,dc=example,dc=com"} 1247
```

### 3. Métriques de Performance

#### ldap_query_duration_seconds

**Description** : Durée d'exécution des requêtes LDAP par type.

**Type** : Histogram
**Unité** : secondes
**Labels** : `query_type` (search, bind, modify, add, delete)
**Intervalle recommandé** : En continu

```python
# Prometheus
ldap_query_duration_seconds_bucket{query_type="search",le="0.1"} 456
ldap_query_duration_seconds_bucket{query_type="search",le="0.5"} 789
ldap_query_duration_seconds_bucket{query_type="search",le="1.0"} 795
```

**Seuils recommandés** :
- **CRITICAL** : > 5s
- **WARNING** : > 1s

#### ldap_operations_total

**Description** : Nombre total d'opérations LDAP par type.

**Type** : Counter
**Unité** : nombre
**Labels** : `operation` (search, bind, modify, add, delete)
**Intervalle recommandé** : En continu

```python
# Prometheus
ldap_operations_total{operation="search"} 125684
ldap_operations_total{operation="bind"} 89562
ldap_operations_total{operation="modify"} 3421
```

#### ldap_search_entries_total

**Description** : Nombre d'entrées retournées par les recherches LDAP.

**Type** : Counter
**Unité** : nombre
**Labels** : aucun
**Intervalle recommandé** : En continu

```python
# Prometheus
ldap_search_entries_total 1245678
```

### 4. Métriques de Sécurité

#### ldap_auth_failures_total

**Description** : Nombre d'échecs d'authentification LDAP.

**Type** : Counter
**Unité** : nombre
**Labels** : `reason` (invalid_credentials, account_disabled, account_locked)
**Intervalle recommandé** : 60s

```python
# Prometheus
ldap_auth_failures_total{reason="invalid_credentials"} 145
ldap_auth_failures_total{reason="account_disabled"} 12
ldap_auth_failures_total{reason="account_locked"} 3
```

**Seuils recommandés** :
- **CRITICAL** : > 100 échecs/heure
- **WARNING** : > 10 échecs/heure

**Alerte de sécurité** :
```yaml
# Configuration d'alerte
monitoring:
  alerts:
    auth_failure_threshold: 10  # Par intervalle de collecte
```

#### ldap_password_expiring_users

**Description** : Nombre d'utilisateurs dont le mot de passe expire bientôt.

**Type** : Gauge
**Unité** : nombre
**Labels** : `days_until_expiry` (7, 14, 30)
**Intervalle recommandé** : 3600s (1 heure)

```python
# Prometheus
ldap_password_expiring_users{days_until_expiry="7"} 3
ldap_password_expiring_users{days_until_expiry="14"} 8
ldap_password_expiring_users{days_until_expiry="30"} 23
```

#### ldap_ssl_cert_expiry_days

**Description** : Nombre de jours avant l'expiration du certificat SSL.

**Type** : Gauge
**Unité** : jours
**Labels** : `server`
**Intervalle recommandé** : 86400s (24 heures)

```python
# Prometheus
ldap_ssl_cert_expiry_days{server="ldap.example.com"} 287
```

**Seuils recommandés** :
- **CRITICAL** : < 7 jours
- **WARNING** : < 30 jours

### 5. Métriques de Santé

#### ldap_replication_lag_seconds

**Description** : Retard de réplication entre serveurs LDAP (si applicable).

**Type** : Gauge
**Unité** : secondes
**Labels** : `master`, `replica`
**Intervalle recommandé** : 300s

```python
# Prometheus
ldap_replication_lag_seconds{master="ldap1.example.com",replica="ldap2.example.com"} 1.2
```

**Seuils recommandés** :
- **CRITICAL** : > 300s (5 minutes)
- **WARNING** : > 60s (1 minute)

#### ldap_database_size_bytes

**Description** : Taille de la base de données LDAP.

**Type** : Gauge
**Unité** : bytes
**Labels** : aucun
**Intervalle recommandé** : 3600s (1 heure)

```python
# Prometheus
ldap_database_size_bytes 2147483648  # 2 GB
```

#### ldap_disk_usage_percent

**Description** : Pourcentage d'utilisation du disque.

**Type** : Gauge
**Unité** : pourcentage (0-100)
**Labels** : `mount_point`
**Intervalle recommandé** : 300s

```python
# Prometheus
ldap_disk_usage_percent{mount_point="/var/lib/ldap"} 68.5
```

**Seuils recommandés** :
- **CRITICAL** : > 90%
- **WARNING** : > 80%

#### ldap_memory_usage_percent

**Description** : Pourcentage d'utilisation de la mémoire du processus LDAP.

**Type** : Gauge
**Unité** : pourcentage (0-100)
**Labels** : aucun
**Intervalle recommandé** : 60s

```python
# Prometheus
ldap_memory_usage_percent 45.2
```

**Seuils recommandés** :
- **CRITICAL** : > 95%
- **WARNING** : > 85%

---

## Configuration de la Collecte

### Configuration Minimale

```yaml
# config.yaml - Configuration minimale

monitoring:
  enabled: true
  interval: 300  # 5 minutes

  # Métriques à collecter
  metrics:
    - users_count
    - groups_count
    - response_time
```

### Configuration Complète

```yaml
# config.yaml - Configuration complète

monitoring:
  enabled: true
  interval: 300  # 5 minutes (300 secondes)
  retention_days: 90

  # Métriques à collecter
  metrics:
    # Disponibilité
    - server_up
    - response_time
    - connections

    # Contenu
    - users_count
    - groups_count
    - group_members

    # Performance
    - query_duration
    - operations_rate
    - search_entries

    # Sécurité
    - auth_failures
    - password_expiring
    - ssl_cert_expiry

    # Santé
    - replication_lag
    - database_size
    - disk_usage
    - memory_usage

  # Configuration avancée par métrique
  metrics_config:
    users_count:
      enabled: true
      interval: 300  # Override global interval
      cache_ttl: 300  # Cache result for 5 minutes
      filters:
        - active_only: false
        - include_disabled: true

    response_time:
      enabled: true
      interval: 60  # Check every minute
      timeout: 10
      retry_max: 3

    auth_failures:
      enabled: true
      interval: 60
      window: 3600  # Count failures in last hour

  # Optimisations
  cache:
    enabled: true
    ttl: 300  # 5 minutes default

  parallel_collection:
    enabled: true
    max_workers: 5

  # Stratégie en cas d'erreur
  error_handling:
    retry_failed_metrics: true
    retry_max: 3
    retry_delay: 5
    continue_on_error: true  # Continue collecting other metrics
```

### Configuration par Environnement

#### Production

```yaml
# config.production.yaml

monitoring:
  enabled: true
  interval: 300  # 5 minutes
  retention_days: 90

  metrics:
    - users_count
    - groups_count
    - response_time
    - connections
    - auth_failures
    - ssl_cert_expiry
    - disk_usage

  cache:
    enabled: true
    ttl: 300

  parallel_collection:
    enabled: true
    max_workers: 5
```

#### Développement

```yaml
# config.development.yaml

monitoring:
  enabled: true
  interval: 60  # 1 minute (plus fréquent pour dev)
  retention_days: 7

  metrics:
    - users_count
    - response_time

  cache:
    enabled: false  # Pas de cache en dev

  parallel_collection:
    enabled: false  # Séquentiel pour debugging
```

#### Staging

```yaml
# config.staging.yaml

monitoring:
  enabled: true
  interval: 120  # 2 minutes
  retention_days: 30

  metrics:
    - users_count
    - groups_count
    - response_time
    - auth_failures

  cache:
    enabled: true
    ttl: 120
```

---

## Intervalles de Collecte

### Recommandations par Type de Métrique

| Type de Métrique | Intervalle Recommandé | Justification |
|------------------|----------------------|---------------|
| **Disponibilité** | 60s | Détection rapide des pannes |
| **Performance** | 60-300s | Balance entre charge et visibilité |
| **Contenu** | 300-3600s | Change rarement, peut être moins fréquent |
| **Sécurité** | 60-300s | Important pour détection d'intrusion |
| **Santé** | 300-3600s | Tendances à long terme |

### Configuration des Intervalles

```yaml
monitoring:
  # Intervalle global par défaut
  interval: 300

  # Intervalles spécifiques par métrique
  metrics_config:
    # Métriques critiques - vérification fréquente
    server_up:
      interval: 60
    response_time:
      interval: 60
    auth_failures:
      interval: 60

    # Métriques standard
    users_count:
      interval: 300
    groups_count:
      interval: 300
    connections:
      interval: 120

    # Métriques lourdes - moins fréquentes
    database_size:
      interval: 3600  # 1 heure
    replication_lag:
      interval: 600   # 10 minutes
    ssl_cert_expiry:
      interval: 86400 # 1 jour
```

### Stratégies d'Intervalle

#### Stratégie Adaptative

Ajustement automatique des intervalles selon la charge :

```yaml
monitoring:
  adaptive_intervals:
    enabled: true

    # Augmenter l'intervalle si charge élevée
    high_load_threshold: 80  # % CPU
    high_load_multiplier: 2  # Doubler l'intervalle

    # Réduire l'intervalle si anomalie détectée
    anomaly_multiplier: 0.5  # Diviser par 2
```

#### Stratégie par Horaire

Intervalles différents selon l'heure de la journée :

```yaml
monitoring:
  scheduled_intervals:
    enabled: true

    # Heures de bureau (9h-18h) - surveillance intensive
    business_hours:
      start: "09:00"
      end: "18:00"
      interval: 60

    # Heures creuses - surveillance normale
    off_hours:
      interval: 300

    # Week-end - surveillance réduite
    weekend:
      interval: 600
```

---

## Stockage des Métriques

### Options de Stockage

#### 1. Prometheus (Recommandé)

**Avantages** :
- Time-series database optimisé
- Intégration native avec Grafana
- Requêtes PromQL puissantes
- Alerting intégré

**Configuration** :
```yaml
integrations:
  prometheus:
    enabled: true
    port: 9090
    host: 0.0.0.0
    path: /metrics
    retention: 90d
```

**Démarrage** :
```bash
# Lancer le serveur Prometheus exporter
ldap-monitor prometheus serve --port 9090

# Vérifier les métriques
curl http://localhost:9090/metrics
```

#### 2. InfluxDB

**Avantages** :
- Très performant pour time-series
- Bon pour de très gros volumes
- SQL-like query language

**Configuration** :
```yaml
integrations:
  influxdb:
    enabled: true
    url: http://localhost:8086
    database: ldap_metrics
    username: ${INFLUXDB_USER}
    password: ${INFLUXDB_PASSWORD}
    retention_policy: 90d
```

#### 3. SQLite (Local)

**Avantages** :
- Pas de dépendances externes
- Simple pour petits déploiements
- Bon pour dev/test

**Configuration** :
```yaml
storage:
  backend: sqlite
  path: /var/lib/ldap-monitor/metrics.db
  retention_days: 30
```

#### 4. PostgreSQL

**Avantages** :
- Robuste et scalable
- Support de TimescaleDB pour time-series
- Requêtes SQL complexes possibles

**Configuration** :
```yaml
storage:
  backend: postgresql
  host: localhost
  port: 5432
  database: ldap_metrics
  username: ${POSTGRES_USER}
  password: ${POSTGRES_PASSWORD}

  # TimescaleDB extension
  timescaledb:
    enabled: true
    chunk_time_interval: 1d
    retention_policy: 90d
```

### Schéma de Stockage

#### Schema SQLite/PostgreSQL

```sql
-- Table des métriques
CREATE TABLE metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value FLOAT NOT NULL,
    labels JSON,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_timestamp (timestamp),
    INDEX idx_metric_name (metric_name)
);

-- Table d'agrégation (pour optimiser les requêtes)
CREATE TABLE metrics_hourly (
    timestamp DATETIME NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    min_value FLOAT,
    max_value FLOAT,
    avg_value FLOAT,
    count INTEGER,
    PRIMARY KEY (timestamp, metric_name)
);

-- Table d'agrégation journalière
CREATE TABLE metrics_daily (
    date DATE NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    min_value FLOAT,
    max_value FLOAT,
    avg_value FLOAT,
    count INTEGER,
    PRIMARY KEY (date, metric_name)
);
```

### Rétention et Nettoyage

#### Configuration de Rétention

```yaml
monitoring:
  retention_days: 90

  # Rétention différenciée par type
  retention_policies:
    # Métriques brutes
    raw_metrics:
      retention_days: 7

    # Métriques agrégées (horaires)
    hourly_aggregates:
      retention_days: 90

    # Métriques agrégées (journalières)
    daily_aggregates:
      retention_days: 365
```

#### Nettoyage Automatique

```yaml
monitoring:
  cleanup:
    enabled: true
    schedule: "0 2 * * *"  # Tous les jours à 2h du matin

    # Stratégie de nettoyage
    strategy:
      # Supprimer les métriques brutes > 7 jours
      - type: raw
        older_than: 7d

      # Agréger puis supprimer les métriques > 30 jours
      - type: aggregate_and_delete
        older_than: 30d
        aggregate_to: hourly

      # Supprimer tout ce qui est > 1 an
      - type: delete
        older_than: 365d
```

#### Nettoyage Manuel

```bash
# Nettoyer les métriques anciennes
ldap-monitor metrics cleanup --older-than 90d

# Nettoyer une métrique spécifique
ldap-monitor metrics cleanup --metric users_count --older-than 30d

# Dry-run (voir ce qui serait supprimé)
ldap-monitor metrics cleanup --older-than 90d --dry-run

# Sortie
📊 Cleanup Summary (Dry Run)
────────────────────────────────────────
Metrics to delete: 125,847
Space to free: 1.2 GB
Oldest metric: 2024-08-17 14:30:00
Newest metric: 2025-11-17 14:30:00

Breakdown by metric:
  - users_count: 43,200 entries (340 MB)
  - groups_count: 43,200 entries (340 MB)
  - response_time: 86,400 entries (520 MB)

Continue? [y/N]:
```

---

## Export et Formats

### Export Prometheus

```bash
# Démarrer le serveur d'export
ldap-monitor prometheus serve --port 9090

# Tester l'endpoint
curl http://localhost:9090/metrics

# Sortie
# HELP ldap_users_total Total number of LDAP users
# TYPE ldap_users_total gauge
ldap_users_total{status="total"} 1247
ldap_users_total{status="active"} 1189

# HELP ldap_response_time_seconds LDAP query response time
# TYPE ldap_response_time_seconds histogram
ldap_response_time_seconds_bucket{le="0.1"} 145
ldap_response_time_seconds_bucket{le="0.5"} 289
ldap_response_time_seconds_sum 127.3
ldap_response_time_seconds_count 300
```

### Export JSON

```bash
# Export au format JSON
ldap-monitor metrics export --format json --output metrics.json

# Avec filtres
ldap-monitor metrics export \
  --format json \
  --metric users_count \
  --start-time "2025-11-01" \
  --end-time "2025-11-17" \
  --output metrics.json

# Sortie (metrics.json)
{
  "timestamp": "2025-11-17T14:30:00Z",
  "metrics": [
    {
      "name": "users_count",
      "value": 1247,
      "timestamp": "2025-11-17T14:30:00Z",
      "labels": {
        "status": "total"
      }
    },
    {
      "name": "groups_count",
      "value": 89,
      "timestamp": "2025-11-17T14:30:00Z",
      "labels": {}
    }
  ]
}
```

### Export CSV

```bash
# Export au format CSV
ldap-monitor metrics export --format csv --output metrics.csv

# Sortie (metrics.csv)
timestamp,metric_name,value,labels
2025-11-17T14:30:00Z,users_count,1247,status=total
2025-11-17T14:30:00Z,users_count,1189,status=active
2025-11-17T14:30:00Z,groups_count,89,
2025-11-17T14:30:00Z,response_time,45.2,
```

### Export InfluxDB Line Protocol

```bash
# Export au format InfluxDB
ldap-monitor metrics export --format influxdb --output metrics.txt

# Sortie (metrics.txt)
ldap_users,status=total value=1247 1700230200000000000
ldap_users,status=active value=1189 1700230200000000000
ldap_groups value=89 1700230200000000000
ldap_response_time value=45.2 1700230200000000000
```

---

## Optimisation des Performances

### Stratégies de Caching

```yaml
monitoring:
  cache:
    enabled: true
    backend: redis  # redis, memcached, memory

    # Redis configuration
    redis:
      host: localhost
      port: 6379
      db: 0
      password: ${REDIS_PASSWORD}

    # TTL par métrique
    ttl:
      users_count: 300      # 5 minutes
      groups_count: 300     # 5 minutes
      response_time: 60     # 1 minute (temps réel)
      database_size: 3600   # 1 heure (change rarement)
```

### Collecte Parallèle

```yaml
monitoring:
  parallel_collection:
    enabled: true
    max_workers: 10  # Nombre de threads

    # Groupes de métriques à collecter en parallèle
    groups:
      - name: availability
        metrics:
          - server_up
          - response_time
          - connections

      - name: content
        metrics:
          - users_count
          - groups_count

      - name: security
        metrics:
          - auth_failures
          - password_expiring
```

### Optimisation des Requêtes LDAP

```yaml
ldap:
  # Pagination pour grandes bases
  page_size: 1000

  # Timeout approprié
  timeout: 10

  # Attributs minimaux
  minimal_attributes: true  # Récupérer seulement les attributs nécessaires

  # Scope optimisé
  search_scope: ONELEVEL  # Au lieu de SUBTREE si possible

monitoring:
  # Optimisations spécifiques
  metrics_config:
    users_count:
      # Ne récupérer que les DNs (pas tous les attributs)
      attributes: ["dn"]

      # Utiliser un filtre optimisé
      optimized_filter: true
```

### Exemple de Collecte Optimisée

```python
# Code optimisé pour collecter le nombre d'utilisateurs

def collect_user_count_optimized(connector, config):
    """Collecte optimisée du nombre d'utilisateurs."""

    # Utiliser seulement les attributs nécessaires
    user_filter = f"(objectClass={config.ldap.user_objectclass})"

    # Recherche avec pagination
    users = connector.search(
        search_base=config.ldap.users_ou,
        search_filter=user_filter,
        attributes=["dn"],  # Seulement DN, pas tous les attributs
        page_size=1000,
        size_limit=0  # Pas de limite
    )

    return len(users)
```

### Monitoring des Performances de Collecte

```bash
# Activer le profiling
ldap-monitor metrics collect --profile

# Sortie avec timing détaillé
📊 Metrics Collection Profile
────────────────────────────────────────
Total time: 2.34s

Breakdown:
  Connection:     0.12s (5.1%)
  users_count:    0.89s (38.0%)
  groups_count:   0.67s (28.6%)
  response_time:  0.05s (2.1%)
  auth_failures:  0.45s (19.2%)
  Cleanup:        0.16s (6.8%)

Recommendations:
  ⚠️  users_count is slow (>500ms)
  💡  Consider caching or increasing interval
```

---

## Exemples Pratiques

### Exemple 1 : Collecte Manuelle Simple

```bash
# Collecter toutes les métriques configurées
ldap-monitor metrics collect

# Sortie
✅ Collected 8 metrics in 1.23s
────────────────────────────────────────
users_total:       1247
groups_total:      89
response_time_ms:  45
connections:       8
auth_failures:     2
ssl_cert_expiry:   287 days
disk_usage:        68.5%
memory_usage:      45.2%
```

### Exemple 2 : Collecte d'une Métrique Spécifique

```bash
# Collecter seulement le nombre d'utilisateurs
ldap-monitor metrics collect --metric users_count

# Avec détails
ldap-monitor metrics collect --metric users_count --verbose

# Sortie détaillée
📊 Collecting metric: users_count
────────────────────────────────────────
Connecting to: ldaps://ldap.example.com:636
Search base: ou=users,dc=example,dc=com
Filter: (objectClass=inetOrgPerson)
Attributes: [dn]

Searching... ━━━━━━━━━━━━━━━━━━━━━ 100% 1247/1247

✅ Collection completed in 0.89s
────────────────────────────────────────
Total users:    1247
Active users:   1189 (95.3%)
Inactive users: 58 (4.7%)
Disabled users: 0 (0.0%)

Metric stored:
  Name: ldap_users_total
  Value: 1247
  Labels: {status: "total"}
  Timestamp: 2025-11-17T14:30:00Z
```

### Exemple 3 : Surveillance Continue

```bash
# Mode watch - rafraîchissement automatique
ldap-monitor metrics watch --interval 5

# Sortie (mise à jour toutes les 5s)
╔═══════════════════════════════════════════════════════╗
║      LDAP Health Monitor - Live Metrics               ║
║      Server: ldap.example.com:636                     ║
║      Updated: 2025-11-17 14:30:45 (auto-refresh)      ║
╠═══════════════════════════════════════════════════════╣
║ users_total        : 1247      ▲ +2 (1h)             ║
║ groups_total       : 89        ─ (no change)         ║
║ response_time      : 45ms      ▼ -3ms (5m)           ║
║ connections        : 8         ▲ +1 (5m)             ║
║ auth_failures      : 2/h       ▼ -1 (1h)             ║
╚═══════════════════════════════════════════════════════╝

Press Ctrl+C to stop
```

### Exemple 4 : Export pour Analyse

```bash
# Export des métriques des 7 derniers jours
ldap-monitor metrics export \
  --format csv \
  --start-time "2025-11-10" \
  --end-time "2025-11-17" \
  --output metrics-week.csv

# Analyse avec des outils standards
# Moyenne du temps de réponse
awk -F',' '$2=="response_time" {sum+=$3; count++} END {print sum/count}' metrics-week.csv

# Pic d'utilisateurs
awk -F',' '$2=="users_count" {if($3>max) max=$3} END {print max}' metrics-week.csv
```

### Exemple 5 : Dashboard Temps Réel avec Prometheus

```bash
# 1. Démarrer l'exporter Prometheus
ldap-monitor prometheus serve --port 9090 &

# 2. Configurer Prometheus pour scraper
cat > prometheus.yml <<EOF
global:
  scrape_interval: 60s

scrape_configs:
  - job_name: 'ldap-monitor'
    static_configs:
      - targets: ['localhost:9090']
EOF

# 3. Démarrer Prometheus
prometheus --config.file=prometheus.yml &

# 4. Requêtes PromQL pour analyser
# Temps de réponse moyen sur 5 minutes
rate(ldap_response_time_seconds_sum[5m]) / rate(ldap_response_time_seconds_count[5m])

# Taux de croissance des utilisateurs
rate(ldap_users_total[1h])

# Échecs d'authentification par heure
rate(ldap_auth_failures_total[1h]) * 3600
```

---

## API de Collecte

### API Python

```python
from src.monitor.metrics import MetricsCollector
from src.core.connector import LDAPConnector
from src.core.config import load_config

# Initialisation
config = load_config("config.yaml")
connector = LDAPConnector(config.ldap)
collector = MetricsCollector(connector, config)

# Collecter toutes les métriques
metrics = collector.collect_all_metrics()
for metric in metrics:
    print(f"{metric.name}: {metric.value}")

# Collecter une métrique spécifique
user_count = collector._collect_user_count()
print(f"Users: {user_count}")

# Obtenir un résumé
summary = collector.get_metrics_summary()
print(summary)
# {'users_total': 1247, 'groups_total': 89, 'response_time_ms': 45}
```

### API REST (si disponible)

```bash
# Collecter les métriques
curl -X POST http://localhost:8080/api/v1/metrics/collect

# Obtenir les métriques actuelles
curl http://localhost:8080/api/v1/metrics

# Obtenir une métrique spécifique
curl http://localhost:8080/api/v1/metrics/users_count

# Obtenir l'historique
curl "http://localhost:8080/api/v1/metrics/users_count/history?start=2025-11-10&end=2025-11-17"

# Réponse JSON
{
  "metric": "users_count",
  "current_value": 1247,
  "timestamp": "2025-11-17T14:30:00Z",
  "history": [
    {"timestamp": "2025-11-10T00:00:00Z", "value": 1230},
    {"timestamp": "2025-11-11T00:00:00Z", "value": 1235},
    ...
  ]
}
```

---

## Métriques Personnalisées

### Définir une Métrique Personnalisée

```python
# custom_metrics.py

from src.monitor.metrics import MetricsCollector
from prometheus_client import Gauge

class CustomMetricsCollector(MetricsCollector):
    """Collecteur de métriques personnalisées."""

    def _init_prometheus_metrics(self):
        """Initialiser les métriques standard + personnalisées."""
        super()._init_prometheus_metrics()

        # Métrique personnalisée : nombre d'utilisateurs par département
        self.users_by_dept = Gauge(
            "ldap_users_by_department",
            "Number of users by department",
            ["department"],
            registry=self.registry
        )

    def collect_users_by_department(self):
        """Collecter le nombre d'utilisateurs par département."""
        dept_filter = "(objectClass=inetOrgPerson)"
        users = self.connector.search(
            search_base=self.config.ldap.users_ou,
            search_filter=dept_filter,
            attributes=["departmentNumber"]
        )

        # Compter par département
        dept_counts = {}
        for user in users:
            dept = user.get("departmentNumber", ["Unknown"])[0]
            dept_counts[dept] = dept_counts.get(dept, 0) + 1

        # Mettre à jour la métrique Prometheus
        for dept, count in dept_counts.items():
            self.users_by_dept.labels(department=dept).set(count)

        return dept_counts
```

### Configuration de Métriques Personnalisées

```yaml
# config.yaml

monitoring:
  metrics:
    # Métriques standard
    - users_count
    - groups_count

    # Métriques personnalisées
    - users_by_department
    - users_by_location
    - inactive_accounts_detail

  # Configuration des métriques personnalisées
  custom_metrics:
    users_by_department:
      enabled: true
      interval: 600  # 10 minutes
      attribute: departmentNumber

    users_by_location:
      enabled: true
      interval: 600
      attribute: l  # location

    inactive_accounts_detail:
      enabled: true
      interval: 3600
      inactive_days: 90
      attributes:
        - cn
        - mail
        - lastLogon
```

### Utilisation de Métriques Personnalisées

```bash
# Collecter les métriques personnalisées
ldap-monitor metrics collect --custom users_by_department

# Sortie
✅ Custom metric collected: users_by_department
────────────────────────────────────────
Engineering:    450
Sales:          234
Marketing:      178
HR:             45
IT:             89
Finance:        67
Unknown:        184

# Export Prometheus
curl http://localhost:9090/metrics | grep users_by_department

# Sortie
ldap_users_by_department{department="Engineering"} 450
ldap_users_by_department{department="Sales"} 234
ldap_users_by_department{department="Marketing"} 178
```

---

## Troubleshooting

### Problème 1 : Métriques Non Collectées

**Symptôme** :
```bash
$ ldap-monitor metrics collect
❌ Error: No metrics collected
```

**Diagnostic** :
```bash
# Vérifier la configuration
ldap-monitor config validate

# Tester la connexion LDAP
ldap-monitor health

# Mode verbose pour voir les erreurs
ldap-monitor metrics collect --verbose --debug
```

**Solutions** :
1. Vérifier que `monitoring.enabled = true`
2. Vérifier les permissions LDAP (bind DN doit pouvoir lire)
3. Vérifier la connectivité réseau
4. Vérifier les filtres de recherche

### Problème 2 : Collecte Très Lente

**Symptôme** :
```bash
$ time ldap-monitor metrics collect
real    5m23.456s
```

**Diagnostic** :
```bash
# Profiler la collecte
ldap-monitor metrics collect --profile

# Vérifier les métriques activées
ldap-monitor config show | grep metrics -A 10
```

**Solutions** :
1. Réduire le nombre de métriques collectées
2. Augmenter `page_size` dans la config LDAP
3. Activer le caching
4. Utiliser la collecte parallèle
5. Augmenter l'intervalle de collecte

### Problème 3 : Valeurs Incohérentes

**Symptôme** :
Les métriques affichent des valeurs qui ne correspondent pas à la réalité.

**Diagnostic** :
```bash
# Vérifier directement via LDAP
ldapsearch -x -H ldaps://ldap.example.com \
  -D "cn=admin,dc=example,dc=com" \
  -w password \
  -b "ou=users,dc=example,dc=com" \
  "(objectClass=inetOrgPerson)" dn | grep "^dn:" | wc -l

# Comparer avec la métrique collectée
ldap-monitor metrics collect --metric users_count
```

**Solutions** :
1. Vérifier le `search_base` configuré
2. Vérifier le filtre `objectClass`
3. Vérifier que le compte de monitoring a accès à toutes les OUs
4. Désactiver le cache temporairement pour tester

### Problème 4 : Erreurs Prometheus

**Symptôme** :
```bash
$ curl http://localhost:9090/metrics
curl: (7) Failed to connect to localhost port 9090: Connection refused
```

**Diagnostic** :
```bash
# Vérifier que le serveur est lancé
ldap-monitor prometheus status

# Vérifier les ports en écoute
netstat -tuln | grep 9090

# Vérifier les logs
tail -f /var/log/ldap-monitor/prometheus.log
```

**Solutions** :
1. Démarrer le serveur Prometheus : `ldap-monitor prometheus serve`
2. Vérifier que le port n'est pas déjà utilisé
3. Vérifier les permissions firewall
4. Vérifier la configuration dans `config.yaml`

---

## Bonnes Pratiques

### 1. Configuration

#### ✅ À FAIRE

```yaml
# Activer seulement les métriques nécessaires
monitoring:
  metrics:
    - users_count        # Essentiel
    - response_time      # Performance
    - auth_failures      # Sécurité

# Intervalles adaptés au besoin
monitoring:
  interval: 300  # 5 minutes pour production

# Utiliser le caching
monitoring:
  cache:
    enabled: true
    ttl: 300
```

#### ❌ À ÉVITER

```yaml
# Toutes les métriques activées
monitoring:
  metrics:
    - '*'  # ❌ Peut surcharger le serveur

# Intervalle trop court
monitoring:
  interval: 10  # ❌ Trop fréquent

# Pas de cache
monitoring:
  cache:
    enabled: false  # ❌ Performance dégradée
```

### 2. Performance

#### ✅ Recommandé

- Utiliser la pagination LDAP (`page_size: 1000`)
- Activer le caching pour les métriques lourdes
- Collecter en parallèle quand possible
- Monitorer uniquement les attributs nécessaires
- Utiliser des filtres LDAP optimisés

#### ❌ À Éviter

- Collecter tous les attributs systématiquement
- Désactiver la pagination
- Intervalle de collecte < 30s en production
- Pas de stratégie de rétention

### 3. Stockage

#### ✅ Stratégie Efficace

```yaml
# Rétention différenciée
monitoring:
  retention_days: 90

  retention_policies:
    raw_metrics: 7d
    hourly_aggregates: 90d
    daily_aggregates: 365d

# Nettoyage automatique
monitoring:
  cleanup:
    enabled: true
    schedule: "0 2 * * *"
```

#### ❌ À Éviter

- Pas de limite de rétention
- Pas de nettoyage automatique
- Stocker toutes les métriques brutes indéfiniment

### 4. Monitoring

#### ✅ Meta-Monitoring

Surveiller le système de monitoring lui-même :

```yaml
# Métriques sur le collecteur
monitoring:
  self_monitoring:
    enabled: true
    metrics:
      - collection_duration
      - collection_errors
      - storage_size
      - cache_hit_rate
```

```bash
# Alerter si la collecte échoue
ldap-monitor alerts create \
  --trigger "collection_errors > 3" \
  --level critical \
  --message "Metric collection failing"
```

---

## Conclusion

La collecte de métriques est un processus critique qui nécessite :

1. **Configuration adaptée** au contexte (prod/dev/staging)
2. **Intervalles appropriés** selon l'importance des métriques
3. **Stratégie de stockage** efficace avec rétention adaptée
4. **Optimisations** pour minimiser l'impact sur le serveur LDAP
5. **Monitoring** du système de monitoring lui-même

### Prochaines Étapes

- **[Alerts System](./Alerts-System.md)** - Configuration des alertes sur les métriques
- **[Daemon Mode](./Daemon-Mode.md)** - Déploiement en mode service
- **[Prometheus Metrics](./Prometheus-Metrics.md)** - Intégration Prometheus/Grafana
- **[History & Trends](./History-Trends.md)** - Analyse de l'historique

---

**Dernière mise à jour** : 2025-11-17
**Version** : 1.0.0
