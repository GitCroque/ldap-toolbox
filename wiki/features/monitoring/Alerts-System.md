# Système d'Alertes LDAP

## Introduction

Le système d'alertes de LDAP Health Monitor permet de recevoir des notifications automatiques lorsque des problèmes sont détectés sur votre infrastructure LDAP. Ce guide couvre la configuration, les canaux de notification disponibles, et les meilleures pratiques pour un alerting efficace.

## Table des Matières

- [Introduction](#introduction)
- [Architecture du Système d'Alertes](#architecture-du-système-dalertes)
- [Niveaux d'Alerte](#niveaux-dalerte)
- [Canaux de Notification](#canaux-de-notification)
- [Configuration des Alertes](#configuration-des-alertes)
- [Règles d'Alerting](#règles-dalerting)
- [Templates et Personnalisation](#templates-et-personnalisation)
- [Escalade et Routing](#escalade-et-routing)
- [Testing et Validation](#testing-et-validation)
- [Exemples Pratiques](#exemples-pratiques)
- [Intégrations Avancées](#intégrations-avancées)
- [Troubleshooting](#troubleshooting)
- [Bonnes Pratiques](#bonnes-pratiques)

---

## Architecture du Système d'Alertes

### Vue d'Ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                  Architecture d'Alerting                         │
└─────────────────────────────────────────────────────────────────┘

    ┌────────────────────────────────────────────────────┐
    │           Metrics Collector                         │
    │        (Collecte des métriques)                     │
    └──────────────────┬─────────────────────────────────┘
                       │
                       │ Métriques
                       │
    ┌──────────────────▼─────────────────────────────────┐
    │          Threshold Checker                          │
    │    (Vérification des seuils)                        │
    ├────────────────────────────────────────────────────┤
    │  • Comparaison avec seuils configurés              │
    │  • Détection d'anomalies                           │
    │  • Évaluation de tendances                         │
    └──────────────────┬─────────────────────────────────┘
                       │
                       │ Événements
                       │
    ┌──────────────────▼─────────────────────────────────┐
    │           Alert Manager                             │
    │      (Gestionnaire d'alertes)                       │
    ├────────────────────────────────────────────────────┤
    │  • Déduplication                                    │
    │  • Rate Limiting                                    │
    │  • Enrichissement                                   │
    │  • Routage                                          │
    └──────────┬──────────────┬──────────────┬───────────┘
               │              │              │
        ┌──────▼──────┐ ┌────▼─────┐ ┌─────▼──────┐
        │    Slack    │ │  Email   │ │  Webhook   │
        │   Channel   │ │ Channel  │ │  Channel   │
        └─────────────┘ └──────────┘ └────────────┘
```

### Flux de Traitement d'une Alerte

```
┌─────────────────────────────────────────────────────────────────┐
│                  Flux de Traitement                              │
└─────────────────────────────────────────────────────────────────┘

  1. Détection          2. Création         3. Évaluation
  ┌──────────┐         ┌──────────┐        ┌──────────┐
  │ Métrique │────────►│  Alerte  │───────►│ Filtrage │
  │ > Seuil  │         │  Créée   │        │  Niveau  │
  └──────────┘         └──────────┘        └─────┬────┘
                                                  │
  4. Déduplication     5. Enrichissement   6. Routage
  ┌──────────┐         ┌──────────┐        ┌──────────┐
  │ Vérifier │◄────────┤  Ajouter │◄───────┤ Choisir  │
  │ Duplicat │         │  Contexte│        │  Canal   │
  └─────┬────┘         └──────────┘        └──────────┘
        │
        │ Unique
        │
  7. Rate Limit        8. Formatage        9. Envoi
  ┌──────────┐         ┌──────────┐        ┌──────────┐
  │ Vérifier │────────►│ Template │───────►│ Notifier │
  │  Quota   │         │  Message │        │  Canaux  │
  └──────────┘         └──────────┘        └──────────┘
```

---

## Niveaux d'Alerte

### Types de Niveaux

LDAP Health Monitor utilise trois niveaux d'alerte standards :

#### 1. INFO (Informationnel)

**Usage** : Événements informatifs, changements normaux, confirmations.

**Exemples** :
- Collecte de métriques réussie
- Backup complété avec succès
- Service démarré/arrêté normalement
- Nouveau utilisateur créé

**Couleur** : Vert 🟢
**Notification** : Optionnelle (souvent désactivée en production)

```yaml
alerts:
  levels:
    info: false  # Désactivé en production
```

#### 2. WARNING (Avertissement)

**Usage** : Situations nécessitant attention mais non urgentes, dégradation de performance, seuils préventifs atteints.

**Exemples** :
- Temps de réponse élevé (> 500ms mais < 2000ms)
- Échecs d'authentification modérés (> 10 mais < 50)
- Espace disque > 80% mais < 90%
- Certificat SSL expire dans 30 jours
- Utilisateurs inactifs > seuil configuré

**Couleur** : Orange 🟠
**Notification** : Oui (email généralement)

```yaml
alerts:
  levels:
    warning: true
```

#### 3. CRITICAL (Critique)

**Usage** : Problèmes urgents nécessitant intervention immédiate, service dégradé ou indisponible, violations de sécurité.

**Exemples** :
- Serveur LDAP inaccessible
- Temps de réponse > 2000ms
- Échecs d'authentification massifs (> 50)
- Espace disque > 90%
- Certificat SSL expiré ou expire dans < 7 jours
- Erreurs de réplication

**Couleur** : Rouge 🔴
**Notification** : Oui (tous les canaux + mentions)

```yaml
alerts:
  levels:
    critical: true
```

### Configuration des Niveaux

```yaml
# config.yaml

alerts:
  # Activer/désactiver par niveau
  levels:
    info: false      # Désactivé en prod
    warning: true    # Activé
    critical: true   # Toujours activé

  # Canaux par niveau
  routing:
    info:
      channels: []

    warning:
      channels:
        - email

    critical:
      channels:
        - slack
        - email
        - webhook
      mentions:
        slack: "@channel"
        email: "ops-team@example.com"

  # Rate limiting par niveau
  rate_limits:
    warning:
      max_per_hour: 10
      max_per_day: 50

    critical:
      max_per_hour: 50  # Moins restrictif pour critiques
      max_per_day: 200
```

---

## Canaux de Notification

### 1. Slack

#### Configuration

```yaml
# config.yaml

alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    username: "LDAP Monitor"
    icon_emoji: ":warning:"
    mention_on_critical: "@channel"
    mention_on_warning: ""

    # Options avancées
    thread_replies: true  # Regrouper les alertes similaires en threads
    color_by_level: true  # Couleur selon niveau d'alerte
    include_graphs: false  # Inclure des graphiques (si disponible)
```

#### Variables d'Environnement

```bash
# .env

# Webhook Slack (obtenir sur https://api.slack.com/apps)
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN
```

#### Format du Message Slack

```json
{
  "username": "LDAP Monitor",
  "icon_emoji": ":warning:",
  "channel": "#ldap-alerts",
  "text": "@channel",
  "attachments": [
    {
      "color": "#ff0000",
      "title": "🔴 CRITICAL: High LDAP Response Time",
      "text": "LDAP response time is 2340ms (threshold: 2000ms)",
      "footer": "LDAP Health Monitor",
      "ts": 1700230200,
      "fields": [
        {
          "title": "Level",
          "value": "CRITICAL",
          "short": true
        },
        {
          "title": "Time",
          "value": "2025-11-17 14:30:00",
          "short": true
        },
        {
          "title": "Server",
          "value": "ldap.example.com:636",
          "short": true
        },
        {
          "title": "Response Time",
          "value": "2340ms",
          "short": true
        }
      ]
    }
  ]
}
```

#### Test Slack

```bash
# Tester la connexion Slack
ldap-monitor alerts test slack

# Sortie
✅ Slack connection successful
────────────────────────────────────
Webhook URL: https://hooks.slack.com/services/T.../B.../XX...
Channel: #ldap-alerts
Test message sent successfully

# Envoyer un message de test personnalisé
ldap-monitor alerts test slack --message "Test depuis LDAP Monitor"
```

### 2. Email

#### Configuration

```yaml
# config.yaml

alerts:
  email:
    enabled: true

    # Configuration SMTP
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}

    # Expéditeur et destinataires
    from: ldap-monitor@example.com
    to:
      - admin@example.com
      - ops-team@example.com

    # Options
    subject_prefix: "[LDAP Monitor]"
    html_enabled: true  # Emails en HTML
    include_logo: true

    # CC/BCC pour certains niveaux
    critical_cc:
      - cto@example.com
      - oncall@example.com
```

#### Variables d'Environnement

```bash
# .env

# SMTP Gmail (exemple)
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Ou SMTP Office 365
SMTP_HOST=smtp.office365.com
SMTP_PORT=587
SMTP_USER=your-email@company.com
SMTP_PASSWORD=your-password

# Ou SMTP SendGrid
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASSWORD=your-sendgrid-api-key
```

#### Format de l'Email

**Sujet** :
```
[LDAP Monitor] CRITICAL: High LDAP Response Time
```

**Corps (version texte)** :
```
LDAP Health Monitor Alert

Level: CRITICAL
Time: 2025-11-17 14:30:00
Server: ldap.example.com:636

High LDAP Response Time

LDAP response time is 2340ms (threshold: 2000ms)

Details:
{
  "response_time": 2340,
  "threshold": 2000,
  "server": "ldap.example.com:636"
}

---
LDAP Health Monitor v1.0.0
```

**Corps (version HTML)** :
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    .alert { padding: 20px; border-radius: 5px; }
    .critical { background-color: #ffebee; border-left: 5px solid #f44336; }
    .warning { background-color: #fff3e0; border-left: 5px solid #ff9800; }
  </style>
</head>
<body>
  <div class="alert critical">
    <h2>🔴 CRITICAL: High LDAP Response Time</h2>
    <p>LDAP response time is <strong>2340ms</strong> (threshold: 2000ms)</p>

    <table>
      <tr><td>Server:</td><td>ldap.example.com:636</td></tr>
      <tr><td>Time:</td><td>2025-11-17 14:30:00</td></tr>
      <tr><td>Response Time:</td><td>2340ms</td></tr>
      <tr><td>Threshold:</td><td>2000ms</td></tr>
    </table>
  </div>
</body>
</html>
```

#### Test Email

```bash
# Tester la connexion SMTP
ldap-monitor alerts test email

# Sortie
✅ Email connection successful
────────────────────────────────────
SMTP Host: smtp.gmail.com:587
From: ldap-monitor@example.com
To: admin@example.com, ops-team@example.com
Test email sent successfully

# Envoyer un email de test
ldap-monitor alerts test email \
  --to admin@example.com \
  --subject "Test LDAP Monitor" \
  --message "Ceci est un test"
```

### 3. Webhook (Générique)

#### Configuration

```yaml
# config.yaml

alerts:
  webhook:
    enabled: true
    url: ${WEBHOOK_URL}
    method: POST  # POST ou GET

    # Headers personnalisés
    headers:
      Content-Type: application/json
      Authorization: Bearer ${WEBHOOK_TOKEN}
      X-Custom-Header: ldap-monitor

    # Options
    timeout: 10  # secondes
    retry_max: 3
    retry_delay: 5  # secondes
    verify_ssl: true
```

#### Format de la Payload

```json
{
  "level": "critical",
  "title": "High LDAP Response Time",
  "message": "LDAP response time is 2340ms (threshold: 2000ms)",
  "timestamp": "2025-11-17T14:30:00Z",
  "details": {
    "response_time": 2340,
    "threshold": 2000,
    "server": "ldap.example.com:636",
    "metric": "ldap_response_time_seconds"
  },
  "source": {
    "system": "LDAP Health Monitor",
    "version": "1.0.0",
    "hostname": "monitor-server"
  }
}
```

#### Exemples d'Intégration

##### n8n Workflow

```yaml
# Webhook pour n8n
alerts:
  webhook:
    enabled: true
    url: https://n8n.example.com/webhook/ldap-alerts
    method: POST
    headers:
      Content-Type: application/json
```

**Workflow n8n** :
1. Webhook trigger reçoit l'alerte
2. Router par niveau (WARNING/CRITICAL)
3. Si CRITICAL → Envoyer SMS via Twilio
4. Créer ticket dans Jira
5. Logger dans base de données

##### Zapier

```yaml
# Webhook pour Zapier
alerts:
  webhook:
    enabled: true
    url: https://hooks.zapier.com/hooks/catch/123456/abcdef/
    method: POST
```

**Zap actions** :
1. Recevoir webhook
2. Créer ticket ServiceNow
3. Envoyer notification PagerDuty
4. Logger dans Google Sheets

##### Custom API

```yaml
# Votre API interne
alerts:
  webhook:
    enabled: true
    url: https://api.internal.com/alerts
    method: POST
    headers:
      Authorization: Bearer ${API_TOKEN}
```

#### Test Webhook

```bash
# Tester le webhook
ldap-monitor alerts test webhook

# Sortie
✅ Webhook connection successful
────────────────────────────────────
URL: https://n8n.example.com/webhook/ldap-alerts
Method: POST
Status Code: 200 OK
Response Time: 145ms
```

### 4. PagerDuty (via Webhook)

```yaml
# config.yaml

alerts:
  pagerduty:
    enabled: true
    integration_key: ${PAGERDUTY_KEY}
    severity_mapping:
      critical: critical
      warning: warning
      info: info
```

**Payload PagerDuty** :
```json
{
  "routing_key": "your-integration-key",
  "event_action": "trigger",
  "payload": {
    "summary": "High LDAP Response Time",
    "severity": "critical",
    "source": "ldap.example.com",
    "timestamp": "2025-11-17T14:30:00Z",
    "custom_details": {
      "response_time": 2340,
      "threshold": 2000
    }
  }
}
```

### 5. Microsoft Teams

```yaml
# config.yaml

alerts:
  teams:
    enabled: true
    webhook_url: ${TEAMS_WEBHOOK}
    theme_color: "FF0000"  # Rouge pour alertes
```

**Payload Teams** :
```json
{
  "@type": "MessageCard",
  "@context": "http://schema.org/extensions",
  "themeColor": "FF0000",
  "summary": "LDAP Alert",
  "sections": [{
    "activityTitle": "🔴 CRITICAL: High LDAP Response Time",
    "activitySubtitle": "2025-11-17 14:30:00",
    "facts": [
      {"name": "Server", "value": "ldap.example.com:636"},
      {"name": "Response Time", "value": "2340ms"},
      {"name": "Threshold", "value": "2000ms"}
    ],
    "markdown": true
  }]
}
```

---

## Configuration des Alertes

### Configuration Complète

```yaml
# config.yaml

# ============================================================================
# Configuration Alertes
# ============================================================================

alerts:
  # ─────────────────────────────────────────────────────────────────────────
  # Canaux de notification
  # ─────────────────────────────────────────────────────────────────────────

  # Slack
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    username: "LDAP Monitor"
    icon_emoji: ":warning:"
    mention_on_critical: "@channel"
    thread_replies: true

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
    html_enabled: true

  # Webhook
  webhook:
    enabled: false
    url: ${WEBHOOK_URL}
    method: POST
    headers:
      Content-Type: application/json

  # ─────────────────────────────────────────────────────────────────────────
  # Configuration des niveaux
  # ─────────────────────────────────────────────────────────────────────────

  levels:
    info: false
    warning: true
    critical: true

  # Routage par niveau
  routing:
    warning:
      channels: [email]
    critical:
      channels: [slack, email]

  # ─────────────────────────────────────────────────────────────────────────
  # Rate Limiting (éviter le spam)
  # ─────────────────────────────────────────────────────────────────────────

  rate_limits:
    enabled: true

    # Limites globales
    global:
      max_per_minute: 10
      max_per_hour: 100
      max_per_day: 500

    # Limites par niveau
    warning:
      max_per_hour: 10
      max_per_day: 50

    critical:
      max_per_hour: 50
      max_per_day: 200

  # ─────────────────────────────────────────────────────────────────────────
  # Déduplication
  # ─────────────────────────────────────────────────────────────────────────

  deduplication:
    enabled: true
    window: 3600  # 1 heure (secondes)
    fields: [level, title, metric]  # Champs pour identifier duplicates

  # ─────────────────────────────────────────────────────────────────────────
  # Escalade automatique
  # ─────────────────────────────────────────────────────────────────────────

  escalation:
    enabled: true

    rules:
      - name: "Escalade après 3 warnings"
        condition: "3 warnings in 1 hour"
        action: "upgrade to critical"

      - name: "Escalade si non résolu"
        condition: "critical not resolved in 30 minutes"
        action: "send to pagerduty"

  # ─────────────────────────────────────────────────────────────────────────
  # Maintenance Windows (silence pendant maintenance)
  # ─────────────────────────────────────────────────────────────────────────

  maintenance:
    enabled: true
    windows: []  # Défini via CLI ou API

# ============================================================================
# Configuration Monitoring (seuils d'alerte)
# ============================================================================

monitoring:
  alerts:
    enabled: true
    channels: [slack, email]

    # Seuils par métrique
    thresholds:
      response_time:
        warning: 500    # ms
        critical: 2000  # ms

      auth_failures:
        warning: 10     # par intervalle
        critical: 50

      disk_usage:
        warning: 80     # %
        critical: 90    # %

      memory_usage:
        warning: 85     # %
        critical: 95    # %

      ssl_cert_expiry:
        warning: 30     # jours
        critical: 7     # jours

      connection_errors:
        warning: 3      # erreurs consécutives
        critical: 5
```

---

## Règles d'Alerting

### Règles Basées sur Seuils

```yaml
# config.yaml

monitoring:
  alert_rules:
    # Règle simple : seuil fixe
    - name: high_response_time
      metric: ldap_response_time_seconds
      condition: value > 2.0
      level: critical
      message: "LDAP response time is {{ value }}s (threshold: 2.0s)"

    # Règle avec plusieurs seuils
    - name: disk_usage
      metric: ldap_disk_usage_percent
      conditions:
        - condition: value > 90
          level: critical
          message: "Disk usage critical: {{ value }}%"
        - condition: value > 80
          level: warning
          message: "Disk usage high: {{ value }}%"

    # Règle avec fenêtre temporelle
    - name: sustained_high_response
      metric: ldap_response_time_seconds
      condition: avg(5m) > 1.0
      level: warning
      message: "Average response time > 1s for 5 minutes"

    # Règle de taux de changement
    - name: sudden_user_drop
      metric: ldap_users_total
      condition: change_rate(1h) < -10%
      level: critical
      message: "User count dropped by {{ change }}% in last hour"
```

### Règles Avancées

```yaml
monitoring:
  alert_rules:
    # Règle composite (ET logique)
    - name: ldap_degraded
      conditions:
        - ldap_response_time_seconds > 1.0
        - ldap_auth_failures_total > 10
      level: critical
      message: "LDAP service degraded: slow + auth failures"

    # Règle avec agrégation
    - name: many_empty_groups
      metric: ldap_groups_total
      condition: count(empty=true) > 10
      level: warning
      message: "{{ count }} empty groups found"

    # Règle basée sur ratio
    - name: high_inactive_ratio
      metrics:
        - ldap_users_total{status="inactive"}
        - ldap_users_total{status="total"}
      condition: (inactive / total) > 0.20
      level: warning
      message: "{{ ratio }}% of users are inactive"

    # Règle avec prédiction
    - name: disk_will_fill
      metric: ldap_disk_usage_percent
      condition: predict_linear(7d) > 90
      level: warning
      message: "Disk will reach 90% in {{ days }} days"
```

### Règles PromQL (si Prometheus)

```yaml
monitoring:
  prometheus_rules:
    # Fichier de règles Prometheus
    rules_file: /etc/ldap-monitor/prometheus-rules.yml
```

**prometheus-rules.yml** :
```yaml
groups:
  - name: ldap_alerts
    interval: 60s
    rules:
      # Serveur down
      - alert: LDAPServerDown
        expr: ldap_server_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "LDAP server is down"
          description: "LDAP server {{ $labels.server }} has been down for 1 minute"

      # Temps de réponse élevé
      - alert: LDAPHighResponseTime
        expr: |
          histogram_quantile(0.95,
            rate(ldap_response_time_seconds_bucket[5m])
          ) > 2.0
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LDAP response time high"
          description: "95th percentile response time is {{ $value }}s"

      # Échecs d'authentification
      - alert: LDAPAuthFailures
        expr: rate(ldap_auth_failures_total[5m]) * 300 > 10
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate"
          description: "{{ $value }} auth failures per 5 minutes"

      # Croissance anormale du nombre d'utilisateurs
      - alert: LDAPUserSpike
        expr: |
          (
            ldap_users_total - ldap_users_total offset 1h
          ) > 100
        labels:
          severity: warning
        annotations:
          summary: "Unusual user count increase"
          description: "User count increased by {{ $value }} in last hour"
```

---

## Templates et Personnalisation

### Templates de Message

```yaml
# config.yaml

alerts:
  templates:
    # Template pour Slack
    slack:
      critical: |
        🔴 *CRITICAL: {{ title }}*
        {{ message }}

        *Server:* {{ details.server }}
        *Time:* {{ timestamp }}
        *Metric:* {{ details.metric }}
        *Value:* {{ details.value }}

      warning: |
        🟠 *WARNING: {{ title }}*
        {{ message }}

        Details: {{ details }}

    # Template pour Email (sujet)
    email_subject: |
      [{{ level|upper }}] {{ title }}

    # Template pour Email (corps)
    email_body: |
      LDAP Health Monitor Alert

      Level: {{ level|upper }}
      Time: {{ timestamp }}

      {{ title }}

      {{ message }}

      {% if details %}
      Details:
      {% for key, value in details.items() %}
      - {{ key }}: {{ value }}
      {% endfor %}
      {% endif %}

      ---
      LDAP Health Monitor
```

### Variables Disponibles dans les Templates

| Variable | Description | Exemple |
|----------|-------------|---------|
| `{{ level }}` | Niveau d'alerte | critical |
| `{{ title }}` | Titre de l'alerte | High Response Time |
| `{{ message }}` | Message détaillé | Response time is 2340ms |
| `{{ timestamp }}` | Horodatage | 2025-11-17T14:30:00Z |
| `{{ details }}` | Dict de détails | {server: "ldap.example.com"} |
| `{{ details.server }}` | Détail spécifique | ldap.example.com |
| `{{ metric }}` | Nom de la métrique | ldap_response_time_seconds |
| `{{ value }}` | Valeur de la métrique | 2.34 |

### Filtres Template

```jinja2
{# Formatage #}
{{ timestamp|format_date("%Y-%m-%d %H:%M") }}
{{ value|round(2) }}
{{ level|upper }}
{{ level|lower }}

{# Conditionnels #}
{% if level == "critical" %}
  🔴 URGENT: {{ title }}
{% elif level == "warning" %}
  🟠 Attention: {{ title }}
{% endif %}

{# Boucles #}
{% for key, value in details.items() %}
- {{ key }}: {{ value }}
{% endfor %}

{# Calculs #}
{{ (value / threshold * 100)|round(1) }}%
```

---

## Escalade et Routing

### Routage Conditionnel

```yaml
# config.yaml

alerts:
  routing:
    rules:
      # Alertes de sécurité → Security team
      - match:
          category: security
        channels: [email]
        recipients:
          email: [security@example.com]

      # Alertes critiques → Tous
      - match:
          level: critical
        channels: [slack, email, pagerduty]

      # Alertes de performance → Ops team
      - match:
          category: performance
        channels: [slack]
        slack_channel: "#ops-perf"

      # Heures de bureau vs. heures creuses
      - match:
          time: business_hours
        channels: [slack, email]
      - match:
          time: off_hours
        channels: [pagerduty]  # Réveil de l'astreinte
```

### Escalade Automatique

```yaml
# config.yaml

alerts:
  escalation:
    enabled: true

    policies:
      # Politique par défaut
      - name: default
        steps:
          - delay: 0
            notify: [email]

          - delay: 15m  # Si pas résolu après 15 min
            notify: [slack]
            mention: "@ops-team"

          - delay: 30m  # Si pas résolu après 30 min
            notify: [pagerduty]
            severity: high

          - delay: 1h  # Si pas résolu après 1h
            notify: [email]
            recipients: [cto@example.com]

      # Politique pour alertes critiques
      - name: critical_fast
        match:
          level: critical
        steps:
          - delay: 0
            notify: [slack, email, pagerduty]

          - delay: 5m
            notify: [pagerduty]
            severity: critical
            recipients: [oncall_manager]
```

---

## Testing et Validation

### Test des Canaux

```bash
# Tester tous les canaux configurés
ldap-monitor alerts test all

# Sortie
Testing alert channels...
────────────────────────────────────

✅ Slack: OK (200ms)
✅ Email: OK (1.2s)
❌ Webhook: Failed (Connection timeout)

Summary: 2/3 channels working
```

### Test d'une Alerte Complète

```bash
# Envoyer une alerte de test
ldap-monitor alerts send \
  --level warning \
  --title "Test Alert" \
  --message "This is a test alert from LDAP Monitor" \
  --details '{"server": "ldap.example.com", "test": true}'

# Sortie
✅ Alert sent successfully
────────────────────────────────────
Level: WARNING
Title: Test Alert
Channels:
  - Slack: ✅ Sent
  - Email: ✅ Sent
  - Webhook: ⏭️  Skipped (disabled)
```

### Simulation d'Alertes

```bash
# Simuler une alerte de temps de réponse élevé
ldap-monitor alerts simulate high_response_time

# Simuler une alerte de serveur down
ldap-monitor alerts simulate server_down

# Simuler plusieurs alertes (charge)
ldap-monitor alerts simulate --count 10 --interval 1s
```

---

## Exemples Pratiques

### Exemple 1 : Configuration Production Minimale

```yaml
# config.yaml - Production minimale

alerts:
  # Slack pour toutes les alertes
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-prod-alerts"
    mention_on_critical: "@channel"

  # Email pour les critiques uniquement
  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    from: ldap-monitor@company.com
    to: [ops-team@company.com]

  # Niveaux
  levels:
    info: false
    warning: true
    critical: true

  # Routage
  routing:
    warning:
      channels: [slack]
    critical:
      channels: [slack, email]

monitoring:
  alerts:
    enabled: true
    response_time_threshold: 2000
    auth_failure_threshold: 10
```

### Exemple 2 : Multi-Environnement

```yaml
# config.production.yaml
alerts:
  slack:
    channel: "#ldap-prod-alerts"
    mention_on_critical: "@channel"

  routing:
    critical:
      channels: [slack, email, pagerduty]

# config.staging.yaml
alerts:
  slack:
    channel: "#ldap-staging-alerts"
    mention_on_critical: ""  # Pas de mention en staging

  routing:
    critical:
      channels: [slack]  # Email seulement en prod

# config.development.yaml
alerts:
  slack:
    channel: "#ldap-dev-alerts"

  levels:
    info: true  # Plus verbeux en dev
    warning: true
    critical: true
```

### Exemple 3 : Alerting avec n8n

**Configuration** :
```yaml
# config.yaml
alerts:
  webhook:
    enabled: true
    url: https://n8n.company.com/webhook/ldap-alerts
    method: POST
    headers:
      Authorization: Bearer ${N8N_TOKEN}
```

**Workflow n8n** :
```json
{
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "ldap-alerts",
        "method": "POST"
      }
    },
    {
      "name": "Router",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "rules": [
          {
            "condition": "={{ $json.level === 'critical' }}",
            "output": 0
          },
          {
            "condition": "={{ $json.level === 'warning' }}",
            "output": 1
          }
        ]
      }
    },
    {
      "name": "Send SMS (Critical)",
      "type": "n8n-nodes-base.twilio",
      "parameters": {
        "resource": "sms",
        "operation": "send",
        "to": "+33612345678",
        "body": "CRITICAL LDAP Alert: {{ $json.title }}"
      }
    },
    {
      "name": "Create Jira Ticket",
      "type": "n8n-nodes-base.jira",
      "parameters": {
        "operation": "create",
        "summary": "{{ $json.title }}",
        "description": "{{ $json.message }}"
      }
    }
  ]
}
```

---

## Intégrations Avancées

### Intégration avec Prometheus Alertmanager

```yaml
# alertmanager.yml

route:
  receiver: 'ldap-team'
  group_by: ['alertname', 'server']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h

  routes:
    # Alertes critiques LDAP
    - match:
        severity: critical
        job: ldap-monitor
      receiver: 'ldap-critical'
      continue: true

    # Alertes warning LDAP
    - match:
        severity: warning
        job: ldap-monitor
      receiver: 'ldap-warning'

receivers:
  - name: 'ldap-critical'
    slack_configs:
      - channel: '#ldap-alerts'
        title: '{{ .GroupLabels.alertname }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
    pagerduty_configs:
      - service_key: ${PAGERDUTY_KEY}

  - name: 'ldap-warning'
    email_configs:
      - to: 'ops-team@company.com'
```

### Intégration avec Grafana

```yaml
# Grafana Alert Channel (via API)
POST /api/alert-notifications
{
  "name": "LDAP Monitor",
  "type": "webhook",
  "isDefault": false,
  "sendReminder": true,
  "frequency": "24h",
  "settings": {
    "url": "https://ldap-monitor.company.com/api/alerts/receive",
    "httpMethod": "POST"
  }
}
```

---

## Troubleshooting

### Problème 1 : Alertes Non Reçues

**Diagnostic** :
```bash
# Tester les canaux
ldap-monitor alerts test all

# Vérifier la configuration
ldap-monitor config show | grep -A 50 alerts

# Vérifier les logs
tail -f /var/log/ldap-monitor/alerts.log

# Envoyer une alerte de test
ldap-monitor alerts send --level critical --title "Test"
```

**Solutions** :
1. Vérifier les credentials (SMTP, webhooks)
2. Vérifier que les niveaux sont activés
3. Vérifier les rate limits
4. Vérifier les règles de routage

### Problème 2 : Trop d'Alertes (Alert Fatigue)

**Diagnostic** :
```bash
# Voir l'historique des alertes
ldap-monitor alerts history --last 24h --summary

# Sortie
📊 Alert Summary (Last 24h)
────────────────────────────────────
Total alerts: 247
  - Critical: 12
  - Warning: 235
  - Info: 0

Most frequent:
  1. High Response Time (145 times)
  2. Auth Failures (67 times)
  3. Disk Usage (35 times)
```

**Solutions** :
```yaml
# Augmenter les seuils
monitoring:
  alerts:
    response_time_threshold: 3000  # Au lieu de 2000

# Activer rate limiting
alerts:
  rate_limits:
    enabled: true
    warning:
      max_per_hour: 5  # Maximum 5 warnings/heure

# Activer déduplication
alerts:
  deduplication:
    enabled: true
    window: 3600  # 1 heure

# Désactiver les alertes INFO
alerts:
  levels:
    info: false
```

### Problème 3 : Latence d'Alerting

**Diagnostic** :
```bash
# Mesurer le temps d'envoi
ldap-monitor alerts benchmark

# Sortie
📊 Alert Benchmark Results
────────────────────────────────────
Slack:   245ms (✅ Good)
Email:   1.2s  (✅ Good)
Webhook: 5.8s  (⚠️  Slow)
```

**Solutions** :
1. Augmenter les timeouts
2. Vérifier la connectivité réseau
3. Optimiser les templates (moins de processing)
4. Utiliser des queues asynchrones

---

## Bonnes Pratiques

### 1. Configuration

#### ✅ À FAIRE

```yaml
# Niveaux appropriés
alerts:
  levels:
    info: false      # Pas en production
    warning: true
    critical: true

# Rate limiting pour éviter le spam
alerts:
  rate_limits:
    enabled: true
    warning:
      max_per_hour: 10

# Déduplication
alerts:
  deduplication:
    enabled: true
    window: 3600
```

#### ❌ À ÉVITER

```yaml
# Tous les niveaux activés
alerts:
  levels:
    info: true  # ❌ Trop de bruit
    warning: true
    critical: true

# Pas de rate limiting
alerts:
  rate_limits:
    enabled: false  # ❌ Risque de spam
```

### 2. Routage

#### ✅ Smart Routing

```yaml
alerts:
  routing:
    # Alertes critiques → Tous les canaux
    critical:
      channels: [slack, email, pagerduty]

    # Alertes warning → Email seulement
    warning:
      channels: [email]

    # Alertes de sécurité → Security team
    security:
      channels: [email]
      recipients: [security@company.com]
```

### 3. Messages

#### ✅ Messages Efficaces

```yaml
# Concis et actionnable
"LDAP server down - Immediate action required"

# Inclure le contexte
"Response time 2.5s (threshold: 2.0s) - Server: ldap.example.com"

# Suggérer des actions
"High auth failures detected. Check for brute force attack."
```

#### ❌ Messages Inefficaces

```yaml
# Trop vague
"Something is wrong"  # ❌

# Pas de contexte
"Metric exceeded"  # ❌

# Trop technique
"ldap_response_time_seconds{quantile=\"0.95\"} > 2.0"  # ❌
```

### 4. Testing

```bash
# Tester régulièrement les canaux
ldap-monitor alerts test all

# Simuler des alertes pendant les tests
ldap-monitor alerts simulate --dry-run

# Documenter les runbooks
# Pour chaque alerte, avoir une procédure de résolution
```

---

## Conclusion

Un système d'alerting efficace est essentiel pour :

1. **Détecter** rapidement les problèmes
2. **Notifier** les bonnes personnes au bon moment
3. **Éviter** l'alert fatigue avec un bon tuning
4. **Intégrer** avec votre infrastructure existante
5. **Automatiser** la réponse aux incidents

### Prochaines Étapes

- **[Daemon Mode](./Daemon-Mode.md)** - Exécuter le monitoring en continu
- **[Prometheus Metrics](./Prometheus-Metrics.md)** - Intégration avancée
- **[History & Trends](./History-Trends.md)** - Analyser les patterns d'alertes

---

**Dernière mise à jour** : 2025-11-17
**Version** : 1.0.0
