# Vue d'Ensemble de la Surveillance LDAP

## Introduction

Le système de surveillance de LDAP Health Monitor fournit une surveillance continue, en temps réel et automatisée de votre infrastructure LDAP. Il permet de détecter proactivement les problèmes de performance, de disponibilité et de santé de votre annuaire avant qu'ils n'impactent vos utilisateurs et applications.

## Table des Matières

- [Introduction](#introduction)
- [Architecture du Système](#architecture-du-système)
- [Composants Principaux](#composants-principaux)
- [Qu'est-ce qui est Surveillé ?](#quest-ce-qui-est-surveillé)
- [Comment Fonctionne la Surveillance ?](#comment-fonctionne-la-surveillance)
- [Flux de Données](#flux-de-données)
- [Modes de Fonctionnement](#modes-de-fonctionnement)
- [Intégrations](#intégrations)
- [Cas d'Usage](#cas-dusage)
- [Démarrage Rapide](#démarrage-rapide)
- [Configuration de Base](#configuration-de-base)
- [Exemples d'Utilisation](#exemples-dutilisation)
- [Troubleshooting](#troubleshooting)
- [Bonnes Pratiques](#bonnes-pratiques)

---

## Architecture du Système

### Vue Architecturale Globale

```
┌─────────────────────────────────────────────────────────────────────┐
│                    LDAP Health Monitor - Architecture                │
└─────────────────────────────────────────────────────────────────────┘

                          ┌──────────────────┐
                          │  Serveur LDAP    │
                          │   (Production)   │
                          └────────┬─────────┘
                                   │
                          Connexions LDAP
                                   │
                          ┌────────▼─────────┐
                          │  LDAPConnector   │◄────┐
                          │   (Core Layer)   │     │
                          └────────┬─────────┘     │
                                   │               │
                    ┌──────────────┼───────────────┘
                    │              │
         ┌──────────▼─────┐  ┌────▼─────────────┐
         │ MetricsCollector│  │  AlertManager    │
         │  (Prometheus)   │  │   (Multi-canal)  │
         └──────────┬──────┘  └────┬─────────────┘
                    │              │
                    │    ┌─────────▼──────────┐
                    │    │ MonitoringDaemon   │
                    │    │  (Scheduler)       │
                    │    └─────────┬──────────┘
                    │              │
         ┌──────────▼──────────────▼────────────┐
         │        Storage & Reporting            │
         ├───────────────┬───────────────────────┤
         │ Time Series   │  Alert Channels       │
         │   Database    │  - Slack              │
         │ (Prometheus)  │  - Email              │
         │               │  - Webhooks           │
         └───────────────┴───────────────────────┘
```

### Architecture Détaillée des Composants

```
┌─────────────────────────────────────────────────────────────┐
│                    Couche de Collecte                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │          MetricsCollector                          │    │
│  ├────────────────────────────────────────────────────┤    │
│  │  • Collecte des métriques                          │    │
│  │  • Intervalle configurable                         │    │
│  │  • Export Prometheus                               │    │
│  │  • Agrégation de données                           │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                 Couche de Traitement                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────┐      ┌──────────────────────────┐  │
│  │  ThresholdChecker  │      │   HealthAnalyzer         │  │
│  ├────────────────────┤      ├──────────────────────────┤  │
│  │  • Seuils alertes  │      │  • Analyse tendances     │  │
│  │  • Comparaisons    │      │  • Détection anomalies   │  │
│  │  • Évaluation état │      │  • Score de santé        │  │
│  └────────────────────┘      └──────────────────────────┘  │
│                                                              │
└──────────────────────┬───────────────────────────────────────┘
                       │
┌──────────────────────▼───────────────────────────────────────┐
│                  Couche d'Alerting                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │           AlertManager                             │    │
│  ├────────────────────────────────────────────────────┤    │
│  │                                                     │    │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────┐ │    │
│  │  │ SlackChannel │  │ EmailChannel │  │ Webhook │ │    │
│  │  └──────────────┘  └──────────────┘  └─────────┘ │    │
│  │                                                     │    │
│  │  • Filtrage par niveau                             │    │
│  │  • Rate limiting                                   │    │
│  │  • Déduplication                                   │    │
│  │  • Escalade automatique                            │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## Composants Principaux

### 1. **MetricsCollector** (Collecteur de Métriques)

Le collecteur de métriques est responsable de l'extraction et de l'agrégation des données depuis le serveur LDAP.

**Fonctionnalités :**
- Collecte périodique automatique
- Support de multiples types de métriques
- Export au format Prometheus
- Cache intelligent pour optimiser les performances
- Gestion des erreurs et reconnexions automatiques

**Métriques collectées :**
```python
MetricsCollector
├── Compteurs (Gauges)
│   ├── ldap_users_total           # Nombre total d'utilisateurs
│   ├── ldap_groups_total          # Nombre total de groupes
│   └── ldap_connections_active    # Connexions actives
├── Histogrammes
│   └── ldap_response_time_seconds # Temps de réponse
└── Compteurs (Counters)
    └── ldap_auth_failures_total   # Échecs d'authentification
```

### 2. **AlertManager** (Gestionnaire d'Alertes)

Le gestionnaire d'alertes traite les événements détectés et distribue les notifications.

**Fonctionnalités :**
- Support multi-canal (Slack, Email, Webhooks)
- Filtrage par niveau de sévérité
- Templating personnalisable
- Rate limiting pour éviter le spam
- Agrégation d'alertes similaires
- Escalade automatique

**Niveaux d'alerte :**
- **INFO** : Événements informatifs
- **WARNING** : Situations nécessitant une attention
- **CRITICAL** : Problèmes urgents nécessitant une intervention immédiate

### 3. **MonitoringDaemon** (Service de Surveillance)

Le daemon orchestre la surveillance continue en arrière-plan.

**Fonctionnalités :**
- Exécution en mode service (systemd, launchd)
- Scheduling intelligent avec `schedule`
- Gestion gracieuse des arrêts
- Auto-recovery en cas d'erreur
- Journalisation complète
- Monitoring de l'état du daemon lui-même

---

## Qu'est-ce qui est Surveillé ?

### Métriques de Disponibilité

| Métrique | Description | Intervalle | Unité |
|----------|-------------|------------|-------|
| `ldap_server_up` | Disponibilité du serveur | 60s | booléen |
| `ldap_response_time` | Temps de réponse | 60s | millisecondes |
| `ldap_connections_active` | Connexions actives | 30s | nombre |
| `ldap_connection_errors` | Erreurs de connexion | 60s | nombre/min |

### Métriques de Contenu

| Métrique | Description | Intervalle | Unité |
|----------|-------------|------------|-------|
| `ldap_users_total` | Nombre total d'utilisateurs | 300s | nombre |
| `ldap_users_active` | Utilisateurs actifs | 300s | nombre |
| `ldap_users_inactive` | Utilisateurs inactifs | 300s | nombre |
| `ldap_groups_total` | Nombre total de groupes | 300s | nombre |
| `ldap_groups_empty` | Groupes vides | 300s | nombre |

### Métriques de Performance

| Métrique | Description | Intervalle | Seuil Warning | Seuil Critical |
|----------|-------------|------------|---------------|----------------|
| `ldap_query_duration` | Durée des requêtes | 60s | 500ms | 2000ms |
| `ldap_bind_duration` | Durée de bind | 60s | 100ms | 500ms |
| `ldap_search_entries` | Entrées retournées | 60s | - | - |
| `ldap_operations_rate` | Opérations/seconde | 60s | - | - |

### Métriques de Sécurité

| Métrique | Description | Intervalle | Action |
|----------|-------------|------------|--------|
| `ldap_auth_failures` | Échecs d'authentification | 60s | Alerte si > 10/min |
| `ldap_password_expiring` | Mots de passe expirant | 3600s | Alerte si < 30 jours |
| `ldap_ssl_cert_expiry` | Expiration certificat SSL | 86400s | Alerte si < 30 jours |
| `ldap_privileged_access` | Accès comptes privilégiés | 300s | Alerte immédiate |

### Métriques de Santé

| Métrique | Description | Intervalle | Type |
|----------|-------------|------------|------|
| `ldap_replication_lag` | Retard de réplication | 300s | Gauge |
| `ldap_db_size` | Taille de la base | 3600s | Gauge |
| `ldap_disk_usage` | Utilisation disque | 300s | Percentage |
| `ldap_memory_usage` | Utilisation mémoire | 60s | Percentage |

---

## Comment Fonctionne la Surveillance ?

### Cycle de Surveillance Standard

```
┌─────────────────────────────────────────────────────────────┐
│                    Cycle de Surveillance                     │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────────────┐
    │  1. Initialisation   │
    │  - Chargement config │
    │  - Test connexion    │
    └──────────┬───────────┘
               │
    ┌──────────▼───────────┐
    │  2. Collecte         │◄────────────────┐
    │  - Query LDAP        │                 │
    │  - Mesure metrics    │                 │
    │  - Timestamp         │                 │
    └──────────┬───────────┘                 │
               │                             │
    ┌──────────▼───────────┐                 │
    │  3. Stockage         │                 │
    │  - Prometheus        │                 │
    │  - Time Series DB    │                 │
    └──────────┬───────────┘                 │
               │                             │
    ┌──────────▼───────────┐                 │
    │  4. Analyse          │                 │
    │  - Seuils            │                 │
    │  - Tendances         │                 │
    │  - Anomalies         │                 │
    └──────────┬───────────┘                 │
               │                             │
           ┌───▼───┐                         │
           │Alerte?│                         │
           └───┬───┘                         │
           Oui │ Non                         │
    ┌──────────▼───────────┐                 │
    │  5. Notification     │                 │
    │  - Slack / Email     │                 │
    │  - Webhook           │                 │
    └──────────┬───────────┘                 │
               │                             │
    ┌──────────▼───────────┐                 │
    │  6. Attente          │                 │
    │  - Sleep(interval)   │─────────────────┘
    └──────────────────────┘
```

### Processus de Collecte des Métriques

1. **Connexion LDAP**
   ```python
   # Établissement de la connexion sécurisée
   connector = LDAPConnector(config)
   connector.connect()
   ```

2. **Extraction des Données**
   ```python
   # Collecte du nombre d'utilisateurs
   users = connector.search(
       search_base=config.ldap.users_ou,
       search_filter="(objectClass=inetOrgPerson)",
       attributes=["dn"]
   )
   user_count = len(users)
   ```

3. **Enregistrement de la Métrique**
   ```python
   # Enregistrement dans Prometheus
   self.users_total.labels(status="total").set(user_count)

   # Création d'un objet Metric
   metric = Metric(
       name="users_total",
       value=user_count,
       timestamp=datetime.now()
   )
   ```

4. **Vérification des Seuils**
   ```python
   # Comparaison avec les seuils configurés
   if metric.value > threshold:
       alert_manager.create_alert(
           level=AlertLevel.WARNING,
           title="Seuil dépassé",
           message=f"La métrique {metric.name} a dépassé le seuil"
       )
   ```

### Processus d'Alerting

```
┌────────────────────────────────────────────────────────────┐
│                  Processus d'Alerting                       │
└────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │ Événement Détecté│
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │  Évaluation      │
    │  - Niveau        │
    │  - Priorité      │
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │  Déduplication   │
    │  (éviter spam)   │
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │  Formatage       │
    │  - Template      │
    │  - Enrichissement│
    └────────┬─────────┘
             │
    ┌────────▼─────────┐
    │  Distribution    │
    ├──────────────────┤
    │  ┌─────────────┐ │
    │  │   Slack     │ │
    │  └─────────────┘ │
    │  ┌─────────────┐ │
    │  │   Email     │ │
    │  └─────────────┘ │
    │  ┌─────────────┐ │
    │  │  Webhook    │ │
    │  └─────────────┘ │
    └──────────────────┘
```

---

## Flux de Données

### Flux Complet de Bout en Bout

```
  LDAP Server                    Monitor                  Storage                 Alerting
      │                             │                        │                       │
      │                             │                        │                       │
  ┌───┴───┐                    ┌────┴────┐            ┌──────┴──────┐        ┌──────┴──────┐
  │ Users │                    │ Collect │            │ Prometheus  │        │   Slack     │
  │Groups │◄───────Query───────┤ Metrics │───Store───►│  Time DB    │        │   Email     │
  │Structs│                    │         │            │             │        │   Webhook   │
  └───┬───┘                    └────┬────┘            └──────┬──────┘        └──────▲──────┘
      │                             │                        │                       │
      │                             │                        │                       │
      │         Response            │                        │                       │
      ├─────────with data──────────►│                        │                       │
      │                             │                        │                       │
      │                        ┌────▼────┐                   │                       │
      │                        │ Process │                   │                       │
      │                        │Analyze  │───Query history───┤                       │
      │                        │ Check   │◄──────────────────┘                       │
      │                        └────┬────┘                                           │
      │                             │                                                │
      │                             │                                                │
      │                        ┌────▼────┐                                           │
      │                        │Threshold│                                           │
      │                        │ Check   │────────────If exceeded────────────────────┘
      │                        └─────────┘
      │
```

---

## Modes de Fonctionnement

### 1. Mode One-Shot (Exécution Unique)

Exécution ponctuelle pour vérification immédiate :

```bash
# Collecte et affichage des métriques actuelles
ldap-monitor metrics collect

# Sortie
✅ Métriques collectées avec succès
────────────────────────────────────────
users_total: 1247
groups_total: 89
response_time_ms: 45
active_connections: 3
```

**Cas d'usage :**
- Vérification manuelle
- Tests de configuration
- Debugging
- Scripts ponctuels

### 2. Mode Daemon (Service Continu)

Surveillance continue en arrière-plan :

```bash
# Démarrage du daemon
ldap-monitor monitor start --daemon

# Sortie
Starting LDAP monitoring (interval: 300s)
✅ Daemon started (PID: 12345)
📊 Collecting metrics every 5 minutes
🔔 Alerts enabled: Slack, Email
```

**Cas d'usage :**
- Surveillance production 24/7
- Détection proactive
- Alerting automatique
- SLA monitoring

### 3. Mode Cron (Planification)

Exécution planifiée via cron :

```bash
# Configuration cron (toutes les 5 minutes)
*/5 * * * * /usr/local/bin/ldap-monitor metrics collect --quiet >> /var/log/ldap-monitor.log
```

**Cas d'usage :**
- Collecte périodique légère
- Environnements sans systemd
- Intégration CI/CD
- Rapports programmés

### 4. Mode Interactif

Interface interactive pour exploration :

```bash
# Lancement du mode interactif
ldap-monitor monitor interactive

# Interface
╔═══════════════════════════════════════════════════════╗
║          LDAP Health Monitor - Interactive            ║
╠═══════════════════════════════════════════════════════╣
║ [1] Collect metrics now                              ║
║ [2] View current metrics                             ║
║ [3] Check alert status                               ║
║ [4] Test alert channels                              ║
║ [5] View daemon status                               ║
║ [0] Exit                                             ║
╚═══════════════════════════════════════════════════════╝
Enter choice:
```

---

## Intégrations

### Prometheus

Export natif des métriques au format Prometheus :

```yaml
# Configuration
integrations:
  prometheus:
    enabled: true
    port: 9090
    path: /metrics
```

```bash
# Démarrage du serveur de métriques
ldap-monitor prometheus serve --port 9090
```

**Accès aux métriques :**
```bash
curl http://localhost:9090/metrics

# Sortie (format Prometheus)
# HELP ldap_users_total Total number of LDAP users
# TYPE ldap_users_total gauge
ldap_users_total{status="total"} 1247
ldap_users_total{status="active"} 1189
ldap_users_total{status="inactive"} 58

# HELP ldap_response_time_seconds LDAP query response time
# TYPE ldap_response_time_seconds histogram
ldap_response_time_seconds_bucket{le="0.1"} 145
ldap_response_time_seconds_bucket{le="0.5"} 289
ldap_response_time_seconds_bucket{le="1.0"} 298
```

### Grafana

Dashboards préconfigurés disponibles :

```bash
# Import du dashboard
ldap-monitor grafana export-dashboard > ldap-dashboard.json

# Configuration de la datasource dans Grafana
# Datasource: Prometheus
# URL: http://localhost:9090
# Import: ldap-dashboard.json
```

### Slack

Notifications en temps réel :

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    mention_on_critical: "@here"
```

### Email

Alerting par email avec support SMTP :

```yaml
alerts:
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_use_tls: true
    from: ldap-monitor@example.com
    to:
      - admin@example.com
```

---

## Cas d'Usage

### Cas 1 : Surveillance de Production

**Objectif :** Maintenir un SLA de 99.9% sur l'infrastructure LDAP.

**Configuration :**
```yaml
monitoring:
  enabled: true
  interval: 60  # Check toutes les minutes

  alerts:
    response_time_threshold: 500  # 500ms warning
    connection_error_threshold: 3
```

**Métriques critiques :**
- Disponibilité serveur
- Temps de réponse
- Erreurs de connexion

### Cas 2 : Détection d'Anomalies

**Objectif :** Détecter les comportements anormaux (pics d'authentification, modifications massives).

**Configuration :**
```yaml
monitoring:
  metrics:
    - auth_failures
    - modifications
    - user_changes

  alerts:
    auth_failure_threshold: 10
```

**Alertes configurées :**
- Échecs d'authentification répétés
- Suppressions massives
- Créations suspectes

### Cas 3 : Capacity Planning

**Objectif :** Anticiper les besoins de scaling basés sur les tendances.

**Configuration :**
```yaml
monitoring:
  retention_days: 365  # 1 an d'historique
  metrics:
    - users_count
    - groups_count
    - db_size
```

**Analyses réalisées :**
- Croissance du nombre d'utilisateurs
- Évolution de la taille de la base
- Patterns d'utilisation

---

## Démarrage Rapide

### Installation

```bash
# Installation du package
pip install ldap-health-monitor

# Vérification
ldap-monitor --version
```

### Configuration Minimale

```bash
# Création du fichier de configuration
cat > config.yaml <<EOF
ldap:
  server: ldap.example.com
  port: 636
  use_ssl: true
  bind_dn: cn=monitor,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com

monitoring:
  enabled: true
  interval: 300
  metrics:
    - users_count
    - groups_count
    - response_time
EOF
```

### Premier Test

```bash
# Test de connexion
ldap-monitor health

# Collecte manuelle de métriques
ldap-monitor metrics collect

# Affichage des métriques
ldap-monitor metrics show
```

### Démarrage du Monitoring

```bash
# Mode foreground (pour test)
ldap-monitor monitor start

# Mode daemon (pour production)
ldap-monitor monitor start --daemon

# Vérification du status
ldap-monitor monitor status
```

---

## Configuration de Base

### Fichier de Configuration Complet

```yaml
# /etc/ldap-monitor/config.yaml

# ============================================================================
# Configuration LDAP
# ============================================================================
ldap:
  server: ldap.example.com
  port: 636
  use_ssl: true
  use_tls: true
  bind_dn: cn=monitor,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com
  timeout: 10
  retry_max: 3
  retry_delay: 2
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com

# ============================================================================
# Configuration Monitoring
# ============================================================================
monitoring:
  enabled: true
  interval: 300  # 5 minutes
  retention_days: 90

  # Métriques à collecter
  metrics:
    - users_count
    - groups_count
    - response_time
    - auth_failures
    - connections
    - modifications

  # Configuration des alertes
  alerts:
    enabled: true
    channels:
      - slack
      - email

    # Seuils
    response_time_threshold: 2000        # ms
    auth_failure_threshold: 10           # par intervalle
    connection_error_threshold: 3        # erreurs consécutives
    disk_usage_threshold: 80             # pourcentage
    memory_usage_threshold: 90           # pourcentage

# ============================================================================
# Canaux d'Alerte
# ============================================================================
alerts:
  # Slack
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    username: "LDAP Monitor"
    icon_emoji: ":warning:"
    mention_on_critical: "@channel"

  # Email
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    from: ldap-monitor@example.com
    to:
      - admin@example.com
      - ops-team@example.com
    subject_prefix: "[LDAP Monitor]"

  # Webhook générique
  webhook:
    enabled: false
    url: ${WEBHOOK_URL}
    method: POST
    headers:
      Content-Type: application/json

  # Niveaux d'alerte à envoyer
  levels:
    info: true
    warning: true
    critical: true

# ============================================================================
# Intégration Prometheus
# ============================================================================
integrations:
  prometheus:
    enabled: true
    port: 9090
    host: 0.0.0.0
    path: /metrics

# ============================================================================
# Logging
# ============================================================================
logging:
  level: INFO
  file: /var/log/ldap-monitor/monitor.log
  max_bytes: 10485760  # 10MB
  backup_count: 5
  console: true
```

---

## Exemples d'Utilisation

### Exemple 1 : Surveillance Basique

```bash
# Configuration minimale
cat > config-basic.yaml <<EOF
ldap:
  server: ldap.corp.com
  port: 389
  bind_dn: cn=admin,dc=corp,dc=com
  bind_password: secret
  base_dn: dc=corp,dc=com

monitoring:
  enabled: true
  interval: 300
  metrics:
    - users_count
    - response_time
EOF

# Lancement
ldap-monitor -c config-basic.yaml monitor start
```

### Exemple 2 : Alerting Avancé

```bash
# Test d'un canal d'alerte
ldap-monitor alerts test slack --message "Test de connectivité"

# Envoi d'une alerte manuelle
ldap-monitor alerts send \
  --level warning \
  --title "Maintenance planifiée" \
  --message "Migration LDAP ce soir à 22h"

# Liste des alertes récentes
ldap-monitor alerts history --last 24h
```

### Exemple 3 : Intégration avec Systemd

```bash
# Création du service systemd
sudo cat > /etc/systemd/system/ldap-monitor.service <<EOF
[Unit]
Description=LDAP Health Monitor
After=network.target

[Service]
Type=simple
User=ldap-monitor
Group=ldap-monitor
WorkingDirectory=/opt/ldap-monitor
ExecStart=/usr/local/bin/ldap-monitor monitor start --daemon
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Activation et démarrage
sudo systemctl daemon-reload
sudo systemctl enable ldap-monitor
sudo systemctl start ldap-monitor

# Vérification
sudo systemctl status ldap-monitor
```

### Exemple 4 : Dashboard Temps Réel

```bash
# Affichage continu des métriques
ldap-monitor metrics watch --interval 5

# Sortie (rafraîchie toutes les 5s)
╔═══════════════════════════════════════════════════════════════╗
║         LDAP Health Monitor - Live Metrics                    ║
║         Server: ldap.example.com:636                          ║
║         Updated: 2025-11-17 14:30:45                          ║
╠═══════════════════════════════════════════════════════════════╣
║ Availability                                                  ║
║   Server Status        : ✅ UP                                ║
║   Response Time        : 42ms                                 ║
║   Active Connections   : 8                                    ║
╠═══════════════════════════════════════════════════════════════╣
║ Content                                                       ║
║   Total Users          : 1,247                                ║
║   Active Users         : 1,189 (95.3%)                        ║
║   Total Groups         : 89                                   ║
╠═══════════════════════════════════════════════════════════════╣
║ Performance                                                   ║
║   Queries/min          : 145                                  ║
║   Avg Query Time       : 38ms                                 ║
║   Auth Failures        : 2 (last hour)                        ║
╠═══════════════════════════════════════════════════════════════╣
║ Health Score: 98/100                                          ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## Troubleshooting

### Problème 1 : Le Daemon Ne Démarre Pas

**Symptôme :**
```bash
$ ldap-monitor monitor start --daemon
❌ Error: Failed to start daemon
Connection refused
```

**Diagnostic :**
```bash
# Vérifier la configuration
ldap-monitor config validate

# Tester la connexion LDAP
ldap-monitor health

# Vérifier les logs
tail -f /var/log/ldap-monitor/monitor.log
```

**Solutions :**
1. Vérifier les credentials LDAP
2. Vérifier la connectivité réseau
3. Vérifier les permissions du fichier de config
4. Vérifier que le port n'est pas déjà utilisé

### Problème 2 : Métriques Non Collectées

**Symptôme :**
```bash
$ ldap-monitor metrics show
⚠️  No metrics available
```

**Diagnostic :**
```bash
# Collecte manuelle pour voir les erreurs
ldap-monitor metrics collect --verbose

# Vérifier la configuration
ldap-monitor config show | grep monitoring
```

**Solutions :**
1. Vérifier que `monitoring.enabled = true`
2. Vérifier les permissions sur l'OU
3. Augmenter le timeout si le serveur est lent
4. Vérifier les filtres de recherche

### Problème 3 : Alertes Non Reçues

**Symptôme :**
Aucune alerte n'arrive sur Slack/Email malgré des problèmes détectés.

**Diagnostic :**
```bash
# Test du canal Slack
ldap-monitor alerts test slack

# Test du canal Email
ldap-monitor alerts test email

# Vérifier la configuration des alertes
ldap-monitor config show | grep -A 20 alerts
```

**Solutions :**
1. Vérifier le webhook URL Slack
2. Vérifier les credentials SMTP
3. Vérifier que les niveaux d'alerte sont activés
4. Vérifier les seuils configurés
5. Tester la connectivité réseau vers les services externes

### Problème 4 : Performance Dégradée

**Symptôme :**
La collecte de métriques ralentit le serveur LDAP.

**Diagnostic :**
```bash
# Mesurer le temps de collecte
time ldap-monitor metrics collect

# Vérifier les logs du serveur LDAP
# (dépend de votre serveur LDAP)
```

**Solutions :**
1. Augmenter l'intervalle de collecte
2. Réduire le nombre de métriques collectées
3. Utiliser des filtres plus restrictifs
4. Implémenter du caching
5. Utiliser une connexion dédiée au monitoring

---

## Bonnes Pratiques

### 1. Configuration

#### ✅ À FAIRE

```yaml
# Utiliser des variables d'environnement pour les secrets
ldap:
  bind_password: ${LDAP_PASSWORD}

alerts:
  slack:
    webhook_url: ${SLACK_WEBHOOK}
  email:
    smtp_password: ${SMTP_PASSWORD}
```

```yaml
# Configurer des intervalles adaptés
monitoring:
  interval: 300  # 5 min pour production
  retention_days: 90  # 3 mois d'historique
```

```yaml
# Activer seulement les métriques nécessaires
monitoring:
  metrics:
    - users_count      # Essentiel
    - groups_count     # Essentiel
    - response_time    # Performance
    # Désactiver les métriques lourdes si pas nécessaire
```

#### ❌ À ÉVITER

```yaml
# NE PAS mettre de mots de passe en clair
ldap:
  bind_password: SuperSecret123  # ❌ MAUVAIS

# NE PAS utiliser un intervalle trop court
monitoring:
  interval: 10  # ❌ Trop fréquent, surcharge le serveur

# NE PAS activer toutes les métriques sans réfléchir
monitoring:
  metrics:
    - '*'  # ❌ Peut causer des problèmes de performance
```

### 2. Déploiement

#### ✅ Recommandé

```bash
# Utiliser systemd pour gérer le daemon
sudo systemctl enable ldap-monitor
sudo systemctl start ldap-monitor

# Configurer la rotation des logs
sudo cat > /etc/logrotate.d/ldap-monitor <<EOF
/var/log/ldap-monitor/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
EOF

# Mettre en place un monitoring du monitoring
# (healthcheck du daemon lui-même)
```

#### ❌ À Éviter

```bash
# NE PAS lancer en tant que root
sudo ldap-monitor monitor start  # ❌

# NE PAS oublier de configurer le firewall
# Si Prometheus exposé, limiter l'accès

# NE PAS négliger les logs
# Toujours configurer la rotation
```

### 3. Alerting

#### ✅ Stratégie Efficace

```yaml
# Configurer des niveaux appropriés
alerts:
  levels:
    info: false       # Pas d'alerte pour INFO
    warning: true     # Email uniquement
    critical: true    # Tous les canaux + @mention

# Configurer des seuils réalistes
monitoring:
  alerts:
    response_time_threshold: 2000  # Basé sur votre SLA
    auth_failure_threshold: 10     # Adapté à votre trafic
```

#### ❌ Alerting Toxique

```yaml
# Trop d'alertes = alert fatigue
alerts:
  levels:
    info: true    # ❌ Trop de bruit
    warning: true
    critical: true

monitoring:
  interval: 30  # ❌ Trop fréquent
  alerts:
    response_time_threshold: 100  # ❌ Seuil trop bas
```

### 4. Sécurité

#### ✅ Sécurisation

```bash
# Permissions strictes sur le fichier de config
chmod 600 /etc/ldap-monitor/config.yaml
chown ldap-monitor:ldap-monitor /etc/ldap-monitor/config.yaml

# Utiliser un compte dédié avec permissions minimales
# Le compte de monitoring ne devrait avoir que des droits de lecture

# Chiffrer les communications
ldap:
  use_ssl: true
  use_tls: true
```

```yaml
# Limiter l'exposition Prometheus
integrations:
  prometheus:
    host: 127.0.0.1  # Uniquement localhost
    port: 9090
```

#### ❌ Failles de Sécurité

```bash
# Fichier de config lisible par tous
chmod 644 config.yaml  # ❌ DANGEREUX

# Utiliser le compte admin pour le monitoring
bind_dn: cn=admin,dc=example,dc=com  # ❌ Trop de permissions
```

### 5. Performance

#### ✅ Optimisations

```yaml
# Utiliser le paging pour les grandes bases
ldap:
  page_size: 1000
  timeout: 10

# Cacher les résultats
advanced:
  cache_enabled: true
  cache_ttl: 300

# Limiter le scope des recherches
ldap:
  search_scope: ONELEVEL  # Au lieu de SUBTREE si possible
```

#### ❌ Anti-patterns

```yaml
# Pas de limite de page
ldap:
  page_size: 999999  # ❌ Peut causer des timeouts

# Timeout trop long
ldap:
  timeout: 300  # ❌ 5 minutes c'est trop

# Recherches trop larges
ldap:
  base_dn: ""  # ❌ Recherche depuis la racine
```

### 6. Maintenance

#### ✅ Procédures Recommandées

```bash
# Vérification régulière de la santé
# Ajouter dans crontab
0 */6 * * * /usr/local/bin/ldap-monitor health --quiet || \
  /usr/local/bin/ldap-monitor alerts send --level critical \
  --title "Health check failed"

# Nettoyage régulier des anciennes métriques
0 2 * * 0 /usr/local/bin/ldap-monitor metrics cleanup --older-than 90d

# Sauvegarde de la configuration
0 3 * * * cp /etc/ldap-monitor/config.yaml \
  /backups/ldap-monitor/config-$(date +%Y%m%d).yaml
```

---

## Conclusion

Le système de surveillance de LDAP Health Monitor fournit une solution complète pour :

- **Surveiller** la disponibilité et les performances de votre infrastructure LDAP
- **Détecter** proactivement les problèmes avant qu'ils n'impactent les utilisateurs
- **Alerter** les équipes via multiples canaux (Slack, Email, Webhooks)
- **Analyser** les tendances et anticiper les besoins de scaling
- **Intégrer** avec votre stack de monitoring existant (Prometheus, Grafana)

### Prochaines Étapes

1. **[Metrics Collection](./Metrics-Collection.md)** - Comprendre la collecte de métriques en détail
2. **[Alerts System](./Alerts-System.md)** - Configurer et personnaliser les alertes
3. **[Daemon Mode](./Daemon-Mode.md)** - Déployer comme service système
4. **[Prometheus Metrics](./Prometheus-Metrics.md)** - Intégration avec Prometheus/Grafana
5. **[History & Trends](./History-Trends.md)** - Analyser l'historique et les tendances

---

## Ressources Additionnelles

- **Documentation API** : `/docs/api/monitoring`
- **Exemples de Configuration** : `/examples/monitoring/`
- **Scripts d'Automatisation** : `/examples/scripts/`
- **FAQ Monitoring** : `/wiki/troubleshooting/Monitoring-FAQ.md`
- **Communauté** : https://github.com/ldap-health-monitor/discussions

---

**Dernière mise à jour** : 2025-11-17
**Version** : 1.0.0
