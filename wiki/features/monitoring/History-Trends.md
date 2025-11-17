# Historique et Analyse de Tendances

## Introduction

L'analyse historique et la détection de tendances permettent de comprendre l'évolution de votre infrastructure LDAP au fil du temps, d'anticiper les problèmes futurs, et d'optimiser les performances. Ce guide couvre le stockage des données historiques, l'analyse de tendances, et la visualisation avancée.

## Table des Matières

- [Introduction](#introduction)
- [Architecture de Stockage](#architecture-de-stockage)
- [Configuration du Stockage Historique](#configuration-du-stockage-historique)
- [Rétention et Agrégation](#rétention-et-agrégation)
- [Analyse de Tendances](#analyse-de-tendances)
- [Détection d'Anomalies](#détection-danomalies)
- [Visualisation des Données](#visualisation-des-données)
- [Rapports Périodiques](#rapports-périodiques)
- [Capacity Planning](#capacity-planning)
- [Comparaisons Temporelles](#comparaisons-temporelles)
- [Export et Archivage](#export-et-archivage)
- [Exemples Pratiques](#exemples-pratiques)
- [Troubleshooting](#troubleshooting)
- [Bonnes Pratiques](#bonnes-pratiques)

---

## Architecture de Stockage

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│            Architecture de Stockage Historique                  │
└─────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────┐
    │         Metrics Collector                          │
    │      (Collecte temps réel)                         │
    └──────────────────┬─────────────────────────────────┘
                       │
                       │ Métriques brutes
                       │
    ┌──────────────────▼─────────────────────────────────┐
    │         Stockage Court Terme                       │
    │      (Métriques brutes - 7 jours)                  │
    ├────────────────────────────────────────────────────┤
    │  • Résolution: 1 minute                            │
    │  • Backend: SQLite / PostgreSQL                    │
    │  • Size: ~100 MB                                   │
    └──────────────────┬─────────────────────────────────┘
                       │
                       │ Agrégation horaire
                       │
    ┌──────────────────▼─────────────────────────────────┐
    │         Stockage Moyen Terme                       │
    │      (Agrégations horaires - 90 jours)             │
    ├────────────────────────────────────────────────────┤
    │  • Résolution: 1 heure                             │
    │  • Métriques: min, max, avg, count                 │
    │  • Size: ~500 MB                                   │
    └──────────────────┬─────────────────────────────────┘
                       │
                       │ Agrégation journalière
                       │
    ┌──────────────────▼─────────────────────────────────┐
    │         Stockage Long Terme                        │
    │      (Agrégations journalières - 365 jours)        │
    ├────────────────────────────────────────────────────┤
    │  • Résolution: 1 jour                              │
    │  • Métriques: min, max, avg, count                 │
    │  • Size: ~100 MB                                   │
    └────────────────────────────────────────────────────┘
```

### Niveaux de Rétention

| Niveau | Résolution | Rétention | Cas d'Usage |
|--------|------------|-----------|-------------|
| **Raw** | 1 minute | 7 jours | Troubleshooting récent, alerting temps réel |
| **Hourly** | 1 heure | 90 jours | Analyse tendances courtes, dashboards |
| **Daily** | 1 jour | 365 jours | Capacity planning, rapports mensuels |
| **Monthly** | 1 mois | 5 ans | Analyse long terme, conformité |

---

## Configuration du Stockage Historique

### Configuration Complète

```yaml
# config.yaml

monitoring:
  # Stockage des métriques
  storage:
    backend: postgresql  # sqlite, postgresql, timescaledb, influxdb

    # Configuration PostgreSQL
    postgresql:
      host: localhost
      port: 5432
      database: ldap_metrics
      username: ${POSTGRES_USER}
      password: ${POSTGRES_PASSWORD}
      pool_size: 10
      max_overflow: 20

    # TimescaleDB (extension PostgreSQL pour time-series)
    timescaledb:
      enabled: true
      chunk_time_interval: 1d  # Partitionnement par jour
      compression:
        enabled: true
        after: 7d  # Compresser après 7 jours
      continuous_aggregates:
        enabled: true

  # Politiques de rétention
  retention:
    # Métriques brutes (haute résolution)
    raw:
      enabled: true
      retention_days: 7
      resolution: 1m

    # Agrégations horaires
    hourly:
      enabled: true
      retention_days: 90
      resolution: 1h
      aggregations:
        - min
        - max
        - avg
        - count
        - sum

    # Agrégations journalières
    daily:
      enabled: true
      retention_days: 365
      resolution: 1d
      aggregations:
        - min
        - max
        - avg
        - count

    # Agrégations mensuelles
    monthly:
      enabled: true
      retention_days: 1825  # 5 ans
      resolution: 30d
      aggregations:
        - min
        - max
        - avg

  # Nettoyage automatique
  cleanup:
    enabled: true
    schedule: "0 2 * * *"  # Tous les jours à 2h du matin
    compression:
      enabled: true
      older_than: 7d

  # Archivage
  archiving:
    enabled: true
    backend: s3  # s3, gcs, azure, local
    schedule: "0 3 1 * *"  # Premier jour du mois à 3h
    retention_months: 24
    compression: gzip

    s3:
      bucket: ldap-metrics-archive
      region: eu-west-1
      prefix: archives/
      access_key: ${AWS_ACCESS_KEY}
      secret_key: ${AWS_SECRET_KEY}
```

### Schéma de Base de Données

#### Tables Principales

```sql
-- Table des métriques brutes (résolution 1 minute)
CREATE TABLE metrics_raw (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    metric_value DOUBLE PRECISION NOT NULL,
    labels JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),

    -- Index pour performances
    INDEX idx_metrics_raw_timestamp (timestamp DESC),
    INDEX idx_metrics_raw_name (metric_name),
    INDEX idx_metrics_raw_name_timestamp (metric_name, timestamp DESC)
);

-- Partitionnement par jour (PostgreSQL)
-- Améliore les performances et facilite le nettoyage
ALTER TABLE metrics_raw PARTITION BY RANGE (timestamp);

-- Table d'agrégation horaire
CREATE TABLE metrics_hourly (
    timestamp TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    avg_value DOUBLE PRECISION,
    sum_value DOUBLE PRECISION,
    count INTEGER,
    labels JSONB,

    PRIMARY KEY (timestamp, metric_name, labels),
    INDEX idx_metrics_hourly_timestamp (timestamp DESC),
    INDEX idx_metrics_hourly_name (metric_name)
);

-- Table d'agrégation journalière
CREATE TABLE metrics_daily (
    date DATE NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    avg_value DOUBLE PRECISION,
    sum_value DOUBLE PRECISION,
    count INTEGER,
    labels JSONB,

    PRIMARY KEY (date, metric_name, labels),
    INDEX idx_metrics_daily_date (date DESC)
);

-- Table d'agrégation mensuelle
CREATE TABLE metrics_monthly (
    month DATE NOT NULL,
    metric_name VARCHAR(255) NOT NULL,
    min_value DOUBLE PRECISION,
    max_value DOUBLE PRECISION,
    avg_value DOUBLE PRECISION,
    count INTEGER,
    labels JSONB,

    PRIMARY KEY (month, metric_name, labels)
);

-- Table des événements (pour traçabilité)
CREATE TABLE events (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    event_type VARCHAR(100) NOT NULL,  -- alert, maintenance, change
    severity VARCHAR(20),
    title VARCHAR(255),
    description TEXT,
    metadata JSONB,

    INDEX idx_events_timestamp (timestamp DESC),
    INDEX idx_events_type (event_type)
);
```

#### TimescaleDB (Optimisé pour Time-Series)

```sql
-- Convertir en hypertable (TimescaleDB)
SELECT create_hypertable('metrics_raw', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Continuous aggregate (vue matérialisée automatiquement mise à jour)
CREATE MATERIALIZED VIEW metrics_hourly_view
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 hour', timestamp) AS timestamp,
    metric_name,
    labels,
    MIN(metric_value) as min_value,
    MAX(metric_value) as max_value,
    AVG(metric_value) as avg_value,
    SUM(metric_value) as sum_value,
    COUNT(*) as count
FROM metrics_raw
GROUP BY time_bucket('1 hour', timestamp), metric_name, labels;

-- Politique de refresh automatique
SELECT add_continuous_aggregate_policy('metrics_hourly_view',
    start_offset => INTERVAL '3 hours',
    end_offset => INTERVAL '1 hour',
    schedule_interval => INTERVAL '1 hour');

-- Politique de compression
ALTER TABLE metrics_raw SET (
    timescaledb.compress,
    timescaledb.compress_segmentby = 'metric_name'
);

SELECT add_compression_policy('metrics_raw', INTERVAL '7 days');

-- Politique de rétention automatique
SELECT add_retention_policy('metrics_raw', INTERVAL '90 days');
```

---

## Rétention et Agrégation

### Job d'Agrégation Automatique

```python
# jobs/aggregate_metrics.py

from datetime import datetime, timedelta
from src.core.database import Database

class MetricsAggregator:
    """Agrège les métriques historiques."""

    def __init__(self, db: Database):
        self.db = db

    def aggregate_hourly(self):
        """Agrège les métriques brutes en données horaires."""
        # Dernier timestamp agrégé
        last_aggregated = self.db.query(
            "SELECT MAX(timestamp) FROM metrics_hourly"
        ).scalar() or datetime.now() - timedelta(days=7)

        # Agréger par heure
        query = """
        INSERT INTO metrics_hourly (timestamp, metric_name, labels, min_value, max_value, avg_value, sum_value, count)
        SELECT
            date_trunc('hour', timestamp) as timestamp,
            metric_name,
            labels,
            MIN(metric_value) as min_value,
            MAX(metric_value) as max_value,
            AVG(metric_value) as avg_value,
            SUM(metric_value) as sum_value,
            COUNT(*) as count
        FROM metrics_raw
        WHERE timestamp > %s
        GROUP BY date_trunc('hour', timestamp), metric_name, labels
        ON CONFLICT (timestamp, metric_name, labels) DO UPDATE
        SET
            min_value = EXCLUDED.min_value,
            max_value = EXCLUDED.max_value,
            avg_value = EXCLUDED.avg_value,
            sum_value = EXCLUDED.sum_value,
            count = EXCLUDED.count
        """

        self.db.execute(query, (last_aggregated,))

    def aggregate_daily(self):
        """Agrège les données horaires en données journalières."""
        last_aggregated = self.db.query(
            "SELECT MAX(date) FROM metrics_daily"
        ).scalar() or datetime.now() - timedelta(days=90)

        query = """
        INSERT INTO metrics_daily (date, metric_name, labels, min_value, max_value, avg_value, sum_value, count)
        SELECT
            date_trunc('day', timestamp)::date as date,
            metric_name,
            labels,
            MIN(min_value) as min_value,
            MAX(max_value) as max_value,
            AVG(avg_value) as avg_value,
            SUM(sum_value) as sum_value,
            SUM(count) as count
        FROM metrics_hourly
        WHERE timestamp > %s
        GROUP BY date_trunc('day', timestamp)::date, metric_name, labels
        ON CONFLICT (date, metric_name, labels) DO UPDATE
        SET
            min_value = EXCLUDED.min_value,
            max_value = EXCLUDED.max_value,
            avg_value = EXCLUDED.avg_value,
            sum_value = EXCLUDED.sum_value,
            count = EXCLUDED.count
        """

        self.db.execute(query, (last_aggregated,))
```

### Nettoyage Automatique

```bash
# Script de nettoyage
#!/bin/bash
# cleanup-old-metrics.sh

# Supprimer les métriques brutes > 7 jours
ldap-monitor metrics cleanup --type raw --older-than 7d

# Supprimer les agrégations horaires > 90 jours
ldap-monitor metrics cleanup --type hourly --older-than 90d

# Supprimer les agrégations journalières > 365 jours
ldap-monitor metrics cleanup --type daily --older-than 365d

# Vacuum de la base (PostgreSQL)
psql -U ldap_metrics -c "VACUUM ANALYZE metrics_raw;"
psql -U ldap_metrics -c "VACUUM ANALYZE metrics_hourly;"
psql -U ldap_metrics -c "VACUUM ANALYZE metrics_daily;"
```

```bash
# Cron job (tous les jours à 2h)
# crontab -e
0 2 * * * /opt/ldap-monitor/scripts/cleanup-old-metrics.sh >> /var/log/ldap-monitor/cleanup.log 2>&1
```

---

## Analyse de Tendances

### Calculs de Tendances

#### Croissance Simple

```sql
-- Croissance du nombre d'utilisateurs (derniers 30 jours)
SELECT
    date,
    metric_value as users,
    metric_value - LAG(metric_value) OVER (ORDER BY date) as daily_growth,
    ROUND(
        (metric_value - LAG(metric_value) OVER (ORDER BY date)) * 100.0 /
        NULLIF(LAG(metric_value) OVER (ORDER BY date), 0),
        2
    ) as growth_percent
FROM metrics_daily
WHERE metric_name = 'ldap_users_total'
    AND labels->>'status' = 'total'
    AND date >= CURRENT_DATE - INTERVAL '30 days'
ORDER BY date DESC;

-- Résultat
   date    | users | daily_growth | growth_percent
-----------+-------+--------------+----------------
2025-11-17 | 1247  |            2 |           0.16
2025-11-16 | 1245  |            3 |           0.24
2025-11-15 | 1242  |            1 |           0.08
```

#### Moyennes Mobiles

```sql
-- Moyenne mobile sur 7 jours du temps de réponse
SELECT
    date,
    avg_value as daily_avg_response_time,
    AVG(avg_value) OVER (
        ORDER BY date
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) as moving_avg_7d
FROM metrics_daily
WHERE metric_name = 'ldap_response_time_seconds'
    AND date >= CURRENT_DATE - INTERVAL '90 days'
ORDER BY date DESC;
```

#### Détection de Tendance (Régression Linéaire)

```sql
-- Tendance du nombre d'utilisateurs (régression linéaire)
WITH data AS (
    SELECT
        date,
        metric_value,
        EXTRACT(EPOCH FROM date - (SELECT MIN(date) FROM metrics_daily WHERE metric_name = 'ldap_users_total')) / 86400 as x
    FROM metrics_daily
    WHERE metric_name = 'ldap_users_total'
        AND labels->>'status' = 'total'
        AND date >= CURRENT_DATE - INTERVAL '90 days'
),
stats AS (
    SELECT
        COUNT(*) as n,
        AVG(x) as x_avg,
        AVG(metric_value) as y_avg,
        SUM((x - AVG(x) OVER ()) * (metric_value - AVG(metric_value) OVER ())) as numerator,
        SUM(POWER(x - AVG(x) OVER (), 2)) as denominator
    FROM data
)
SELECT
    y_avg - (numerator / denominator) * x_avg as intercept,
    numerator / denominator as slope,
    CASE
        WHEN numerator / denominator > 0 THEN 'Increasing'
        WHEN numerator / denominator < 0 THEN 'Decreasing'
        ELSE 'Stable'
    END as trend
FROM stats;

-- Résultat
 intercept | slope | trend
-----------+-------+-----------
    1180.5 |  0.74 | Increasing

-- Interprétation: +0.74 utilisateurs par jour en moyenne
```

### CLI pour Analyse de Tendances

```bash
# Afficher les tendances des 30 derniers jours
ldap-monitor history trends --metric users_count --days 30

# Sortie
📊 Trend Analysis: users_count (Last 30 days)
────────────────────────────────────────────────────────

Current value:     1247 users
Start value:       1225 users (30 days ago)
Change:            +22 users (+1.8%)
Daily average:     +0.73 users/day

Trend:             📈 Increasing
Confidence:        High (R² = 0.89)

Forecast (30 days):
  Conservative:    1269 users
  Expected:        1278 users
  Optimistic:      1287 users

Anomalies detected:
  2025-11-10: Spike (+15 users)
  2025-11-03: Drop (-8 users)

Recommendation:
  Current growth rate is sustainable.
  No action required.
```

```bash
# Comparer plusieurs périodes
ldap-monitor history compare \
  --metric users_count \
  --period1 "2025-10-01,2025-10-31" \
  --period2 "2025-11-01,2025-11-30"

# Sortie
📊 Comparison: users_count
────────────────────────────────────────────────────────

October 2025:
  Start:    1198 users
  End:      1225 users
  Change:   +27 users (+2.3%)
  Avg/day:  +0.87 users

November 2025:
  Start:    1225 users
  End:      1247 users
  Change:   +22 users (+1.8%)
  Avg/day:  +0.73 users

Comparison:
  Growth rate: -16% slower in November
  Trend:       Both months show growth

Analysis:
  November shows continued but slightly slower growth.
  This is normal seasonal variation.
```

---

## Détection d'Anomalies

### Algorithmes de Détection

#### Méthode 1 : Écart-Type (Standard Deviation)

```sql
-- Détecter les anomalies basées sur l'écart-type
WITH stats AS (
    SELECT
        AVG(avg_value) as mean,
        STDDEV(avg_value) as stddev
    FROM metrics_daily
    WHERE metric_name = 'ldap_response_time_seconds'
        AND date >= CURRENT_DATE - INTERVAL '90 days'
)
SELECT
    d.date,
    d.avg_value,
    s.mean,
    s.stddev,
    (d.avg_value - s.mean) / s.stddev as z_score,
    CASE
        WHEN ABS((d.avg_value - s.mean) / s.stddev) > 3 THEN 'High Anomaly'
        WHEN ABS((d.avg_value - s.mean) / s.stddev) > 2 THEN 'Medium Anomaly'
        ELSE 'Normal'
    END as anomaly_level
FROM metrics_daily d, stats s
WHERE d.metric_name = 'ldap_response_time_seconds'
    AND d.date >= CURRENT_DATE - INTERVAL '30 days'
    AND ABS((d.avg_value - s.mean) / s.stddev) > 2
ORDER BY d.date DESC;
```

#### Méthode 2 : Interquartile Range (IQR)

```sql
-- Détecter les outliers avec IQR
WITH quartiles AS (
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY avg_value) as q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY avg_value) as q3
    FROM metrics_daily
    WHERE metric_name = 'ldap_users_total'
        AND date >= CURRENT_DATE - INTERVAL '90 days'
),
iqr AS (
    SELECT
        q1,
        q3,
        q3 - q1 as iqr,
        q1 - 1.5 * (q3 - q1) as lower_fence,
        q3 + 1.5 * (q3 - q1) as upper_fence
    FROM quartiles
)
SELECT
    d.date,
    d.avg_value as users,
    i.lower_fence,
    i.upper_fence,
    CASE
        WHEN d.avg_value < i.lower_fence THEN 'Low Outlier'
        WHEN d.avg_value > i.upper_fence THEN 'High Outlier'
        ELSE 'Normal'
    END as status
FROM metrics_daily d, iqr i
WHERE d.metric_name = 'ldap_users_total'
    AND d.date >= CURRENT_DATE - INTERVAL '30 days'
    AND (d.avg_value < i.lower_fence OR d.avg_value > i.upper_fence)
ORDER BY d.date DESC;
```

#### Méthode 3 : Isolation Forest (Machine Learning)

```python
# anomaly_detection.py

from sklearn.ensemble import IsolationForest
import pandas as pd

class AnomalyDetector:
    """Détecte les anomalies dans les métriques LDAP."""

    def __init__(self):
        self.model = IsolationForest(
            contamination=0.1,  # 10% de données sont des anomalies
            random_state=42
        )

    def detect(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Détecte les anomalies dans un DataFrame.

        Args:
            df: DataFrame avec colonnes 'timestamp' et 'value'

        Returns:
            DataFrame avec colonne 'anomaly' (-1 = anomalie, 1 = normal)
        """
        # Features engineering
        df['hour'] = df['timestamp'].dt.hour
        df['day_of_week'] = df['timestamp'].dt.dayofweek
        df['value_lag1'] = df['value'].shift(1)
        df['value_lag7'] = df['value'].shift(7)

        # Features pour le modèle
        features = ['value', 'hour', 'day_of_week', 'value_lag1', 'value_lag7']
        X = df[features].dropna()

        # Prédiction
        df.loc[X.index, 'anomaly'] = self.model.fit_predict(X)
        df.loc[X.index, 'anomaly_score'] = self.model.score_samples(X)

        return df
```

### CLI pour Détection d'Anomalies

```bash
# Détecter les anomalies dans les 30 derniers jours
ldap-monitor history anomalies --metric users_count --days 30

# Sortie
🔍 Anomaly Detection: users_count (Last 30 days)
────────────────────────────────────────────────────────

Method: Isolation Forest
Contamination: 10%

Anomalies detected: 3

┌────────────┬───────┬──────────┬─────────────┬─────────────┐
│ Date       │ Value │ Expected │ Anomaly     │ Severity    │
├────────────┼───────┼──────────┼─────────────┼─────────────┤
│ 2025-11-10 │ 1260  │ 1242     │ +18 (1.4%)  │ Medium      │
│ 2025-11-05 │ 1215  │ 1238     │ -23 (-1.9%) │ High        │
│ 2025-10-28 │ 1195  │ 1220     │ -25 (-2.0%) │ High        │
└────────────┴───────┴──────────┴─────────────┴─────────────┘

Analysis:
  • 2025-11-10: Sudden spike - Possible bulk user import
  • 2025-11-05: Unexpected drop - Check for deletions
  • 2025-10-28: Drop - Weekend maintenance?

Recommendation:
  Investigate the causes of these anomalies.
  Set up alerts for future similar events.
```

---

## Visualisation des Données

### Graphiques de Tendance (Grafana)

```json
{
  "panels": [
    {
      "title": "User Growth Trend (90 days)",
      "type": "graph",
      "targets": [
        {
          "expr": "ldap_users_total{status=\"total\"}",
          "legendFormat": "Actual",
          "refId": "A"
        },
        {
          "expr": "avg_over_time(ldap_users_total{status=\"total\"}[7d])",
          "legendFormat": "7-day moving average",
          "refId": "B"
        },
        {
          "expr": "predict_linear(ldap_users_total{status=\"total\"}[30d], 30*24*3600)",
          "legendFormat": "30-day forecast",
          "refId": "C"
        }
      ],
      "yaxes": [
        {"label": "Users", "format": "short"}
      ]
    }
  ]
}
```

### Heatmap de Performance

```promql
# Heatmap du temps de réponse par heure de la journée
sum by (hour) (
    avg_over_time(
        ldap_response_time_seconds[1h]
    ) * on() group_left(hour)
    hour(timestamp())
)
```

### Graphiques de Comparaison

```bash
# Générer un graphique de comparaison
ldap-monitor history chart \
  --metric users_count \
  --type comparison \
  --periods "last_month,this_month" \
  --output users_comparison.png

# Sortie: users_comparison.png
```

---

## Rapports Périodiques

### Rapport Mensuel Automatique

```yaml
# config.yaml

reports:
  monthly:
    enabled: true
    schedule: "0 9 1 * *"  # Le 1er de chaque mois à 9h

    recipients:
      - management@company.com
      - ops-team@company.com

    sections:
      - summary
      - growth_trends
      - performance_metrics
      - anomalies
      - capacity_forecast
      - recommendations

    format: html  # html, pdf, markdown

    charts:
      - user_growth
      - response_time_trend
      - auth_failures
      - disk_usage_forecast
```

### Template de Rapport

```html
<!-- templates/monthly_report.html -->

<!DOCTYPE html>
<html>
<head>
    <title>LDAP Health Monitor - Monthly Report</title>
    <style>
        .summary { background: #e3f2fd; padding: 20px; }
        .metric { display: inline-block; margin: 10px; }
        .chart { width: 800px; margin: 20px auto; }
        .positive { color: green; }
        .negative { color: red; }
    </style>
</head>
<body>
    <h1>LDAP Health Monitor - Rapport Mensuel</h1>
    <p>Période: {{ start_date }} - {{ end_date }}</p>

    <div class="summary">
        <h2>Résumé Exécutif</h2>
        <div class="metric">
            <h3>Utilisateurs</h3>
            <p>{{ users_end }} utilisateurs</p>
            <p class="{{ 'positive' if users_growth > 0 else 'negative' }}">
                {{ users_growth_sign }}{{ users_growth }} ({{ users_growth_percent }}%)
            </p>
        </div>
        <div class="metric">
            <h3>Disponibilité</h3>
            <p>{{ availability_percent }}%</p>
            <p>SLA: {{ 'Respecté' if availability_percent >= sla_target else 'Non respecté' }}</p>
        </div>
        <div class="metric">
            <h3>Performance</h3>
            <p>Temps de réponse moyen: {{ avg_response_time }}ms</p>
            <p class="{{ 'positive' if response_time_trend < 0 else 'negative' }}">
                {{ response_time_trend_sign }}{{ response_time_trend }}% vs. mois précédent
            </p>
        </div>
    </div>

    <h2>Tendances de Croissance</h2>
    <div class="chart">
        <img src="data:image/png;base64,{{ user_growth_chart }}" />
    </div>

    <h2>Anomalies Détectées</h2>
    <table>
        <tr>
            <th>Date</th>
            <th>Type</th>
            <th>Sévérité</th>
            <th>Description</th>
        </tr>
        {% for anomaly in anomalies %}
        <tr>
            <td>{{ anomaly.date }}</td>
            <td>{{ anomaly.type }}</td>
            <td>{{ anomaly.severity }}</td>
            <td>{{ anomaly.description }}</td>
        </tr>
        {% endfor %}
    </table>

    <h2>Prévisions Capacité</h2>
    <p>Basé sur les tendances actuelles:</p>
    <ul>
        <li>Dans 3 mois: {{ forecast_3m }} utilisateurs</li>
        <li>Dans 6 mois: {{ forecast_6m }} utilisateurs</li>
        <li>Dans 12 mois: {{ forecast_12m }} utilisateurs</li>
    </ul>

    <h2>Recommandations</h2>
    <ul>
        {% for recommendation in recommendations %}
        <li>{{ recommendation }}</li>
        {% endfor %}
    </ul>
</body>
</html>
```

### Génération du Rapport

```bash
# Générer le rapport mensuel
ldap-monitor reports generate monthly \
  --month 2025-11 \
  --output report_2025-11.html

# Générer et envoyer par email
ldap-monitor reports generate monthly \
  --month 2025-11 \
  --send-email

# Sortie
✅ Monthly report generated
────────────────────────────────────
Period: 2025-11-01 to 2025-11-30
Output: report_2025-11.html (2.3 MB)
Email sent to: management@company.com, ops-team@company.com
```

---

## Capacity Planning

### Prévisions de Croissance

```sql
-- Prévision de croissance des utilisateurs (régression linéaire)
WITH historical_data AS (
    SELECT
        date,
        avg_value as users,
        EXTRACT(EPOCH FROM date - (SELECT MIN(date) FROM metrics_daily WHERE metric_name = 'ldap_users_total')) / 86400 as x
    FROM metrics_daily
    WHERE metric_name = 'ldap_users_total'
        AND labels->>'status' = 'total'
        AND date >= CURRENT_DATE - INTERVAL '90 days'
),
regression AS (
    SELECT
        AVG(x) as x_avg,
        AVG(users) as y_avg,
        SUM((x - AVG(x) OVER ()) * (users - AVG(users) OVER ())) / SUM(POWER(x - AVG(x) OVER (), 2)) as slope,
        AVG(users) - (SUM((x - AVG(x) OVER ()) * (users - AVG(users) OVER ())) / SUM(POWER(x - AVG(x) OVER (), 2))) * AVG(x) as intercept
    FROM historical_data
)
SELECT
    'Current' as period,
    ROUND((SELECT MAX(users) FROM historical_data)) as users
UNION ALL
SELECT
    '30 days' as period,
    ROUND(intercept + slope * ((SELECT MAX(x) FROM historical_data) + 30)) as users
FROM regression
UNION ALL
SELECT
    '90 days' as period,
    ROUND(intercept + slope * ((SELECT MAX(x) FROM historical_data) + 90)) as users
FROM regression
UNION ALL
SELECT
    '180 days' as period,
    ROUND(intercept + slope * ((SELECT MAX(x) FROM historical_data) + 180)) as users
FROM regression
UNION ALL
SELECT
    '365 days' as period,
    ROUND(intercept + slope * ((SELECT MAX(x) FROM historical_data) + 365)) as users
FROM regression;

-- Résultat
  period  | users
----------+-------
Current   |  1247
30 days   |  1269
90 days   |  1313
180 days  |  1380
365 days  |  1517
```

### CLI Capacity Planning

```bash
# Prévoir la croissance
ldap-monitor capacity forecast \
  --metric users_count \
  --period 12m

# Sortie
📊 Capacity Forecast: users_count
────────────────────────────────────────────────────────

Current Metrics:
  Current users:     1247
  Monthly growth:    +18 users/month
  Growth rate:       +1.5%/month

Forecasts:
┌──────────┬───────────┬─────────────┬─────────────┐
│ Period   │ Forecast  │ Confidence  │ Range       │
├──────────┼───────────┼─────────────┼─────────────┤
│ 3 months │ 1,301     │ High (95%)  │ 1,285-1,317 │
│ 6 months │ 1,355     │ Medium(85%) │ 1,322-1,388 │
│ 12 months│ 1,463     │ Low (70%)   │ 1,398-1,528 │
└──────────┴───────────┴─────────────┴─────────────┘

Infrastructure Impact:
  • Database size:     +2.1 GB (estimated)
  • Backup size:       +650 MB (estimated)
  • Query load:        +15% (estimated)

Recommendations:
  ✓ Current capacity sufficient for 12 months
  ⚠️  Plan storage expansion in Q3 2026
  ℹ️  Monitor performance as user count approaches 1,500
```

---

## Comparaisons Temporelles

### Comparaison Hebdomadaire

```bash
# Comparer cette semaine vs semaine dernière
ldap-monitor history compare-weekly

# Sortie
📊 Weekly Comparison
────────────────────────────────────────────────────────

This Week (2025-11-11 to 2025-11-17):
  Users:            1247 (avg: 1245)
  Response time:    45ms (avg)
  Auth failures:    23 total
  Uptime:           99.8%

Last Week (2025-11-04 to 2025-11-10):
  Users:            1235 (avg: 1233)
  Response time:    48ms (avg)
  Auth failures:    19 total
  Uptime:           99.9%

Changes:
  Users:            +12 (+1.0%) 📈
  Response time:    -3ms (-6.3%) ✅
  Auth failures:    +4 (+21.1%) ⚠️
  Uptime:           -0.1% ⚠️

Notable Events:
  • 2025-11-15: Spike in auth failures (12 failures)
  • 2025-11-13: Brief downtime (2 minutes)
```

---

## Export et Archivage

### Export de Données Historiques

```bash
# Export CSV des 90 derniers jours
ldap-monitor history export \
  --format csv \
  --period 90d \
  --output metrics_90d.csv

# Export JSON avec agrégation
ldap-monitor history export \
  --format json \
  --period 1y \
  --aggregation daily \
  --output metrics_1y.json

# Export vers S3
ldap-monitor history export \
  --format parquet \
  --period 2y \
  --destination s3://bucket/archives/ldap-metrics-2023-2025.parquet
```

### Archivage Automatique

```yaml
# config.yaml

archiving:
  enabled: true

  schedules:
    - name: monthly_archive
      frequency: monthly
      format: parquet
      compression: gzip
      destination: s3://ldap-metrics-archive/monthly/
      retention: 5y

    - name: quarterly_archive
      frequency: quarterly
      format: parquet
      compression: snappy
      destination: s3://ldap-metrics-archive/quarterly/
      retention: 10y
```

---

## Exemples Pratiques

### Exemple 1 : Analyse Complète Mensuelle

```bash
#!/bin/bash
# monthly-analysis.sh

MONTH="2025-11"

echo "Analysing LDAP metrics for $MONTH..."

# Générer le rapport mensuel
ldap-monitor reports generate monthly --month $MONTH

# Détecter les anomalies
ldap-monitor history anomalies --month $MONTH

# Analyser les tendances
ldap-monitor history trends --month $MONTH

# Prévoir la capacité
ldap-monitor capacity forecast --period 6m

# Archiver les données
ldap-monitor history archive --month $MONTH --destination s3://archives/

echo "Analysis complete!"
```

### Exemple 2 : Dashboard Temps Réel avec Historique

```python
# dashboard.py

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go

# Charger les données historiques
def load_metrics(days=90):
    # Récupérer depuis la base
    query = """
    SELECT date, avg_value
    FROM metrics_daily
    WHERE metric_name = 'ldap_users_total'
        AND date >= CURRENT_DATE - INTERVAL '%s days'
    ORDER BY date
    """ % days

    return pd.read_sql(query, connection)

# Afficher le dashboard
st.title("LDAP Health Monitor - Historical Dashboard")

# Sélection de la période
period = st.selectbox("Period", ["7 days", "30 days", "90 days", "1 year"])
days = {"7 days": 7, "30 days": 30, "90 days": 90, "1 year": 365}[period]

# Charger les données
df = load_metrics(days)

# Graphique principal
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['date'], y=df['avg_value'], name='Users'))

# Moyenne mobile
df['ma_7d'] = df['avg_value'].rolling(window=7).mean()
fig.add_trace(go.Scatter(x=df['date'], y=df['ma_7d'], name='7-day MA'))

st.plotly_chart(fig)

# Statistiques
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Current", df['avg_value'].iloc[-1])
with col2:
    change = df['avg_value'].iloc[-1] - df['avg_value'].iloc[0]
    st.metric("Change", change, f"{change/df['avg_value'].iloc[0]*100:.1f}%")
with col3:
    st.metric("Avg Growth/day", f"{change/days:.2f}")
```

---

## Troubleshooting

### Problème 1 : Base de Données Qui Grossit Trop

**Diagnostic** :
```sql
-- Taille de la base
SELECT pg_size_pretty(pg_database_size('ldap_metrics'));

-- Taille par table
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

**Solutions** :
1. Activer la compression (TimescaleDB)
2. Réduire la rétention
3. Augmenter l'agrégation
4. Archiver vers S3

### Problème 2 : Requêtes Lentes

**Diagnostic** :
```sql
-- Requêtes lentes
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Index manquants
SELECT * FROM pg_stat_user_tables
WHERE idx_scan = 0 AND seq_scan > 0;
```

**Solutions** :
1. Ajouter des index
2. Utiliser le partitionnement
3. Optimiser les requêtes
4. Utiliser les continuous aggregates (TimescaleDB)

---

## Bonnes Pratiques

### 1. Rétention

```yaml
# ✅ Rétention différenciée
retention:
  raw: 7d
  hourly: 90d
  daily: 365d
  monthly: 5y

# ❌ Tout garder indéfiniment
retention:
  raw: unlimited  # Trop lourd
```

### 2. Agrégation

```yaml
# ✅ Agrégations automatiques
aggregations:
  hourly:
    enabled: true
  daily:
    enabled: true

# ❌ Seulement des données brutes
# Requêtes très lentes sur l'historique
```

### 3. Archivage

```yaml
# ✅ Archivage vers stockage froid
archiving:
  enabled: true
  destination: s3://archives/
  compression: gzip

# ❌ Pas d'archivage
# Base de données énorme
```

---

## Conclusion

L'analyse historique et des tendances permet :

1. **Comprendre** l'évolution de votre infrastructure
2. **Anticiper** les problèmes futurs
3. **Optimiser** les ressources
4. **Planifier** les capacités
5. **Détecter** les anomalies

### Prochaines Étapes

- **[Overview](./Overview.md)** - Vue d'ensemble du monitoring
- **[Metrics Collection](./Metrics-Collection.md)** - Collecte des métriques
- **[Prometheus Metrics](./Prometheus-Metrics.md)** - Intégration Prometheus

---

**Dernière mise à jour** : 2025-11-17
**Version** : 1.0.0
