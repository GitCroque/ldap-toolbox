# Configuration des Alertes

## Table des Matières

- [Introduction](#introduction)
- [Niveaux de Sévérité](#niveaux-de-sévérité)
- [Canaux d'Alertes](#canaux-dalertes)
- [Intégration Slack](#intégration-slack)
- [Intégration Email](#intégration-email)
- [Webhooks Génériques](#webhooks-génériques)
- [Règles d'Alerte](#règles-dalerte)
- [Conditions et Déclencheurs](#conditions-et-déclencheurs)
- [Formatage des Messages](#formatage-des-messages)
- [Throttling et Rate Limiting](#throttling-et-rate-limiting)
- [Escalade des Alertes](#escalade-des-alertes)
- [Alertes Personnalisées](#alertes-personnalisées)
- [Testing et Validation](#testing-et-validation)
- [Exemples Pratiques](#exemples-pratiques)
- [Dépannage](#dépannage)

## Introduction

Le système d'alertes permet de notifier les équipes en temps réel des problèmes détectés dans votre infrastructure LDAP. Il supporte plusieurs canaux de notification et offre une configuration granulaire pour adapter les alertes à vos besoins.

### Architecture des Alertes

```
┌──────────────┐
│  Audit /     │
│  Monitoring  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│  Alert       │
│  Manager     │◄──── Configuration
└──────┬───────┘
       │
       ├────────────┬────────────┬────────────┐
       │            │            │            │
       ▼            ▼            ▼            ▼
┌──────────┐  ┌─────────┐  ┌────────┐  ┌──────────┐
│  Slack   │  │  Email  │  │ Webhook│  │  Custom  │
└──────────┘  └─────────┘  └────────┘  └──────────┘
```

### Flux d'Alerte

1. **Détection** : Un problème est détecté (audit, monitoring)
2. **Évaluation** : Vérification des seuils et conditions
3. **Création** : Génération de l'alerte avec niveau de sévérité
4. **Filtrage** : Application des règles de filtrage
5. **Routage** : Sélection des canaux appropriés
6. **Envoi** : Notification via les canaux configurés
7. **Tracking** : Enregistrement et suivi

## Niveaux de Sévérité

### Configuration des Niveaux

```yaml
alerts:
  levels:
    info: true       # Informations générales
    warning: true    # Avertissements
    critical: true   # Problèmes critiques
```

### Définition des Niveaux

**INFO (Informationnel)**

```yaml
# Caractéristiques
severity: info
color: blue
urgency: low
notify: optional

# Exemples
- Audit terminé avec succès
- Sauvegarde complétée
- Nombre d'utilisateurs : rapport quotidien
- Métriques de performance normales
```

**WARNING (Avertissement)**

```yaml
# Caractéristiques
severity: warning
color: orange
urgency: medium
notify: recommended

# Exemples
- Temps de réponse élevé (> 500ms)
- Groupes vides détectés
- Certificat SSL expire dans 30 jours
- Comptes inactifs > seuil
- Échecs d'authentification modérés
```

**CRITICAL (Critique)**

```yaml
# Caractéristiques
severity: critical
color: red
urgency: high
notify: required

# Exemples
- Serveur LDAP inaccessible
- Temps de réponse > 2000ms
- Échecs d'authentification massifs
- Modifications massives non autorisées
- Certificat SSL expiré
- Perte de connectivité
```

### Routage par Sévérité

```yaml
alerts:
  routing:
    # INFO : Email uniquement
    info:
      channels:
        - email
      recipients:
        - ldap-reports@company.com

    # WARNING : Email + Slack
    warning:
      channels:
        - email
        - slack
      recipients:
        - ldap-team@company.com
      slack_channel: "#ldap-warnings"

    # CRITICAL : Tous les canaux + escalade
    critical:
      channels:
        - email
        - slack
        - webhook
      recipients:
        - ldap-team@company.com
        - ops-team@company.com
      slack_channel: "#ldap-critical"
      slack_mention: "@oncall"
      escalate: true
      escalate_after: 15m
```

## Canaux d'Alertes

### Configuration Globale

```yaml
alerts:
  # Activation des canaux
  slack:
    enabled: true
  email:
    enabled: true
  webhook:
    enabled: true

  # Canaux par défaut
  default_channels:
    - email

  # Canaux par niveau
  channels_by_level:
    info: [email]
    warning: [email, slack]
    critical: [email, slack, webhook]
```

### Paramètres Communs

```yaml
alerts:
  # Paramètres globaux
  enabled: true

  # Timeout
  timeout: 10  # secondes

  # Retry
  retry:
    max_attempts: 3
    delay: 5  # secondes
    backoff: exponential

  # Format
  format: markdown  # markdown, html, text

  # Timezone
  timezone: Europe/Paris
```

## Intégration Slack

### Configuration de Base

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
    username: "LDAP Monitor"
    icon_emoji: ":warning:"
```

### Configuration Avancée

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}

    # Canaux par sévérité
    channels:
      info: "#ldap-info"
      warning: "#ldap-warnings"
      critical: "#ldap-critical"

    # Mentions
    mention_on_warning: "@ldap-team"
    mention_on_critical: "@oncall"

    # Apparence
    username: "LDAP Health Monitor"
    icon_emoji: ":shield:"
    icon_url: "https://example.com/ldap-icon.png"

    # Format
    format:
      use_blocks: true
      include_details: true
      max_fields: 10

    # Threading
    use_threads: true
    thread_on_same_issue: true

    # Couleurs
    colors:
      info: "#36a64f"
      warning: "#ff9900"
      critical: "#ff0000"
```

### Format des Messages Slack

**Message Simple :**

```yaml
alerts:
  slack:
    message_template: |
      *{{ level | upper }}*: {{ title }}
      {{ message }}
```

**Message avec Blocks (recommandé) :**

```yaml
alerts:
  slack:
    block_template:
      - type: header
        text:
          type: plain_text
          text: "{{ level | upper }}: {{ title }}"

      - type: section
        text:
          type: mrkdwn
          text: "{{ message }}"

      - type: section
        fields:
          - type: mrkdwn
            text: "*Niveau:*\n{{ level }}"
          - type: mrkdwn
            text: "*Heure:*\n{{ timestamp }}"
          - type: mrkdwn
            text: "*Serveur:*\n{{ instance }}"
          - type: mrkdwn
            text: "*Environnement:*\n{{ environment }}"

      - type: context
        elements:
          - type: mrkdwn
            text: "LDAP Health Monitor"

      - type: actions
        elements:
          - type: button
            text:
              type: plain_text
              text: "Voir les détails"
            url: "{{ dashboard_url }}"
```

### Exemples de Webhooks Slack

**Webhook Principal :**

```bash
export SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN"
```

**Webhooks Multiples :**

```yaml
alerts:
  slack:
    webhooks:
      production:
        url: ${SLACK_WEBHOOK_PROD}
        channel: "#prod-ldap-alerts"
        mention: "@oncall"

      staging:
        url: ${SLACK_WEBHOOK_STAGING}
        channel: "#staging-alerts"

      development:
        url: ${SLACK_WEBHOOK_DEV}
        channel: "#dev-alerts"
```

### Actions Interactives Slack

```yaml
alerts:
  slack:
    interactive:
      enabled: true
      callback_url: https://ldap-monitor.company.com/slack/actions

      actions:
        - name: acknowledge
          text: "Acquitter"
          style: primary

        - name: ignore
          text: "Ignorer"
          style: danger

        - name: view_details
          text: "Détails"
          url: "{{ dashboard_url }}"
```

## Intégration Email

### Configuration SMTP

```yaml
alerts:
  email:
    enabled: true

    # Serveur SMTP
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_use_ssl: false

    # Authentification
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}

    # Expéditeur
    from: ldap-monitor@company.com
    from_name: "LDAP Health Monitor"

    # Destinataires
    to:
      - admin@company.com
      - ldap-team@company.com

    # Copie
    cc: []
    bcc:
      - archive@company.com

    # Sujet
    subject_prefix: "[LDAP Monitor]"
```

### Templates Email

**Email HTML :**

```yaml
alerts:
  email:
    format: html
    template: |
      <!DOCTYPE html>
      <html>
      <head>
        <style>
          .alert { padding: 20px; border-radius: 5px; }
          .critical { background-color: #ffebee; border-left: 4px solid #f44336; }
          .warning { background-color: #fff3e0; border-left: 4px solid #ff9800; }
          .info { background-color: #e3f2fd; border-left: 4px solid #2196f3; }
        </style>
      </head>
      <body>
        <div class="alert {{ level }}">
          <h2>{{ title }}</h2>
          <p><strong>Niveau:</strong> {{ level | upper }}</p>
          <p><strong>Heure:</strong> {{ timestamp }}</p>
          <p>{{ message }}</p>

          {% if details %}
          <h3>Détails:</h3>
          <ul>
          {% for key, value in details.items() %}
            <li><strong>{{ key }}:</strong> {{ value }}</li>
          {% endfor %}
          </ul>
          {% endif %}

          {% if recommendations %}
          <h3>Recommandations:</h3>
          <p>{{ recommendations }}</p>
          {% endif %}
        </div>
      </body>
      </html>
```

**Email Texte :**

```yaml
alerts:
  email:
    format: text
    template: |
      LDAP Health Monitor - Alerte {{ level | upper }}

      {{ title }}

      Heure: {{ timestamp }}
      Niveau: {{ level | upper }}
      Serveur: {{ instance }}

      Message:
      {{ message }}

      {% if details %}
      Détails:
      {% for key, value in details.items() %}
      - {{ key }}: {{ value }}
      {% endfor %}
      {% endif %}

      {% if recommendations %}
      Recommandations:
      {{ recommendations }}
      {% endif %}

      --
      LDAP Health Monitor
      https://ldap-monitor.company.com
```

### Destinataires Dynamiques

```yaml
alerts:
  email:
    # Destinataires par sévérité
    recipients:
      info:
        - reports@company.com
      warning:
        - ldap-team@company.com
      critical:
        - ldap-team@company.com
        - ops-team@company.com
        - oncall@company.com

    # Destinataires par type d'alerte
    recipients_by_type:
      security:
        - security-team@company.com
        - ciso@company.com
      performance:
        - ldap-team@company.com
        - monitoring@company.com
      backup:
        - backup-team@company.com
```

### Configuration par Fournisseur

**Gmail :**

```yaml
alerts:
  email:
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: your-email@gmail.com
    smtp_password: ${GMAIL_APP_PASSWORD}  # Mot de passe d'application
```

**Office 365 :**

```yaml
alerts:
  email:
    smtp_host: smtp.office365.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: alerts@company.onmicrosoft.com
    smtp_password: ${O365_PASSWORD}
```

**SendGrid :**

```yaml
alerts:
  email:
    smtp_host: smtp.sendgrid.net
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: apikey
    smtp_password: ${SENDGRID_API_KEY}
```

**Amazon SES :**

```yaml
alerts:
  email:
    smtp_host: email-smtp.eu-west-1.amazonaws.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: ${AWS_SES_USER}
    smtp_password: ${AWS_SES_PASSWORD}
```

## Webhooks Génériques

### Configuration de Base

```yaml
alerts:
  webhook:
    enabled: true
    url: ${WEBHOOK_URL}
    method: POST
    headers:
      Content-Type: application/json
      Authorization: "Bearer ${WEBHOOK_TOKEN}"
```

### Configuration Avancée

```yaml
alerts:
  webhook:
    enabled: true

    # Endpoints multiples
    endpoints:
      - name: n8n
        url: ${N8N_WEBHOOK}
        method: POST
        enabled: true

      - name: zapier
        url: ${ZAPIER_WEBHOOK}
        method: POST
        enabled: true

      - name: custom_api
        url: https://api.company.com/webhooks/ldap
        method: POST
        headers:
          X-API-Key: ${API_KEY}
          X-Service: ldap-monitor
        enabled: true

    # Timeout et retry
    timeout: 10
    retry:
      max_attempts: 3
      delay: 5

    # Format du payload
    payload_format: json  # json, form, xml

    # Signature
    sign_payload: true
    signature_header: X-Signature
    signature_secret: ${WEBHOOK_SECRET}
```

### Format du Payload

**Payload Standard :**

```json
{
  "alert": {
    "level": "critical",
    "title": "Serveur LDAP inaccessible",
    "message": "Le serveur LDAP ne répond plus depuis 5 minutes",
    "timestamp": "2025-11-17T10:30:00Z",
    "details": {
      "server": "ldap.company.com",
      "last_successful_check": "2025-11-17T10:25:00Z",
      "error": "Connection timeout"
    }
  },
  "source": {
    "type": "ldap-health-monitor",
    "instance": "ldap-monitor-01",
    "environment": "production"
  },
  "metadata": {
    "alert_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "correlation_id": "xyz789"
  }
}
```

**Payload Personnalisé :**

```yaml
alerts:
  webhook:
    payload_template: |
      {
        "severity": "{{ level }}",
        "event": "{{ title }}",
        "description": "{{ message }}",
        "timestamp": "{{ timestamp }}",
        "source": "ldap-monitor",
        "tags": ["ldap", "{{ level }}", "{{ category }}"],
        "data": {{ details | tojson }}
      }
```

### Exemples d'Intégrations

**n8n :**

```yaml
alerts:
  webhook:
    url: https://n8n.company.com/webhook/ldap-alerts
    method: POST
    headers:
      Content-Type: application/json
```

**Zapier :**

```yaml
alerts:
  webhook:
    url: https://hooks.zapier.com/hooks/catch/123456/abcdef/
    method: POST
```

**PagerDuty :**

```yaml
alerts:
  webhook:
    url: https://events.pagerduty.com/v2/enqueue
    method: POST
    headers:
      Content-Type: application/json
    payload_template: |
      {
        "routing_key": "${PAGERDUTY_KEY}",
        "event_action": "trigger",
        "payload": {
          "summary": "{{ title }}",
          "severity": "{{ level }}",
          "source": "ldap-monitor",
          "custom_details": {{ details | tojson }}
        }
      }
```

**Opsgenie :**

```yaml
alerts:
  webhook:
    url: https://api.opsgenie.com/v2/alerts
    method: POST
    headers:
      Authorization: "GenieKey ${OPSGENIE_API_KEY}"
      Content-Type: application/json
    payload_template: |
      {
        "message": "{{ title }}",
        "description": "{{ message }}",
        "priority": "{% if level == 'critical' %}P1{% elif level == 'warning' %}P3{% else %}P5{% endif %}",
        "tags": ["ldap", "{{ level }}"]
      }
```

## Règles d'Alerte

### Configuration des Règles

```yaml
alerts:
  rules:
    # Règle 1: Serveur lent
    - name: slow_response
      condition:
        metric: response_time
        operator: ">"
        threshold: 2000
        duration: 5m
      severity: critical
      title: "Serveur LDAP lent"
      message: "Temps de réponse {{ value }}ms > 2000ms"
      channels: [slack, email]

    # Règle 2: Échecs d'authentification
    - name: auth_failures
      condition:
        metric: auth_failures_rate
        operator: ">"
        threshold: 0.5
        window: 5m
      severity: warning
      title: "Échecs d'authentification élevés"
      message: "{{ value }} échecs/sec détectés"
      channels: [slack]

    # Règle 3: Certificat expirant
    - name: cert_expiry
      condition:
        metric: ssl_cert_days_remaining
        operator: "<"
        threshold: 30
      severity: warning
      title: "Certificat SSL expirant"
      message: "Expire dans {{ value }} jours"
      channels: [email]
      repeat_interval: 7d
```

### Conditions Complexes

```yaml
alerts:
  rules:
    # Règle avec conditions multiples (AND)
    - name: critical_slow_server
      conditions:
        all:
          - metric: response_time
            operator: ">"
            threshold: 2000
          - metric: error_rate
            operator: ">"
            threshold: 0.01
      severity: critical
      message: "Serveur lent ET taux d'erreur élevé"

    # Règle avec conditions alternatives (OR)
    - name: connectivity_issue
      conditions:
        any:
          - metric: connection_errors
            operator: ">"
            threshold: 5
          - metric: timeout_errors
            operator: ">"
            threshold: 3
      severity: critical
      message: "Problème de connectivité détecté"

    # Règle avec exclusions
    - name: high_user_count
      condition:
        metric: users_count
        operator: ">"
        threshold: 10000
      exclude:
        time_of_day: "02:00-04:00"  # Fenêtre de maintenance
        day_of_week: [saturday, sunday]
      severity: warning
```

### Règles Temporelles

```yaml
alerts:
  rules:
    # Alerte seulement en heures ouvrées
    - name: business_hours_alert
      condition:
        metric: response_time
        operator: ">"
        threshold: 1000
      schedule:
        days: [monday, tuesday, wednesday, thursday, friday]
        hours: "08:00-18:00"
        timezone: Europe/Paris

    # Alerte en dehors des heures ouvrées (plus permissif)
    - name: after_hours_alert
      condition:
        metric: response_time
        operator: ">"
        threshold: 5000
      schedule:
        exclude:
          days: [monday, tuesday, wednesday, thursday, friday]
          hours: "08:00-18:00"
```

## Conditions et Déclencheurs

### Opérateurs Disponibles

```yaml
alerts:
  conditions:
    operators:
      # Comparaison numérique
      ">": "supérieur à"
      ">=": "supérieur ou égal à"
      "<": "inférieur à"
      "<=": "inférieur ou égal à"
      "==": "égal à"
      "!=": "différent de"

      # Comparaison texte
      "contains": "contient"
      "not_contains": "ne contient pas"
      "matches": "correspond à (regex)"
      "not_matches": "ne correspond pas à"

      # Listes
      "in": "dans la liste"
      "not_in": "pas dans la liste"

      # Changements
      "changed": "a changé"
      "increased": "a augmenté"
      "decreased": "a diminué"
```

### Exemples de Conditions

```yaml
alerts:
  rules:
    # Condition simple
    - name: high_response_time
      condition:
        metric: response_time
        operator: ">"
        threshold: 2000

    # Condition avec fenêtre temporelle
    - name: sustained_high_response
      condition:
        metric: response_time
        operator: ">"
        threshold: 1000
        duration: 10m  # Doit durer 10 minutes

    # Condition sur changement
    - name: user_spike
      condition:
        metric: users_count
        operator: increased
        by: 100
        within: 1h

    # Condition sur pattern
    - name: suspicious_login
      condition:
        field: login_location
        operator: not_in
        values: ["France", "Belgique", "Suisse"]

    # Condition avec regex
    - name: invalid_email
      condition:
        field: user_email
        operator: not_matches
        pattern: "^[a-zA-Z0-9._%+-]+@company\\.com$"
```

### Déclencheurs Personnalisés

```yaml
alerts:
  custom_triggers:
    # Déclencheur basé sur script
    - name: custom_check
      type: script
      script: |
        def check(metrics, config):
            # Logique personnalisée
            if metrics['users_count'] > config['threshold']:
                return True, f"Too many users: {metrics['users_count']}"
            return False, None

      severity: warning

    # Déclencheur basé sur ML
    - name: anomaly_detection
      type: ml
      model: isolation_forest
      sensitivity: 0.05
      features:
        - response_time
        - auth_failures
        - query_rate
```

## Formatage des Messages

### Variables Disponibles

```yaml
# Variables standards
{{ level }}          # info, warning, critical
{{ title }}          # Titre de l'alerte
{{ message }}        # Message
{{ timestamp }}      # Date/heure
{{ instance }}       # Instance qui génère l'alerte
{{ environment }}    # Environnement (prod, staging, dev)

# Métriques
{{ value }}          # Valeur de la métrique
{{ threshold }}      # Seuil configuré
{{ metric_name }}    # Nom de la métrique

# Détails
{{ details }}        # Dictionnaire de détails
{{ details.key }}    # Accès à une clé spécifique

# Recommandations
{{ recommendation }} # Recommandation d'action
```

### Filtres Jinja2

```yaml
# Exemples de filtres
{{ value | round(2) }}           # Arrondir à 2 décimales
{{ timestamp | date('%d/%m/%Y') }}  # Formater date
{{ level | upper }}              # Majuscules
{{ message | truncate(100) }}    # Tronquer
{{ details | tojson }}           # Convertir en JSON
{{ value | filesizeformat }}     # Format taille fichier
```

### Templates Personnalisés

```yaml
alerts:
  templates:
    # Template par défaut
    default: |
      [{{ level | upper }}] {{ title }}
      {{ message }}

    # Template détaillé
    detailed: |
      ╔══════════════════════════════════════╗
      ║  LDAP HEALTH MONITOR - {{ level | upper }}
      ╚══════════════════════════════════════╝

      📋 {{ title }}

      ⏰ {{ timestamp | date('%d/%m/%Y %H:%M:%S') }}
      🖥️  Serveur: {{ instance }}
      🌍 Environnement: {{ environment }}

      💬 Message:
      {{ message }}

      {% if details %}
      📊 Détails:
      {% for key, value in details.items() %}
      • {{ key }}: {{ value }}
      {% endfor %}
      {% endif %}

      {% if recommendation %}
      💡 Recommandation:
      {{ recommendation }}
      {% endif %}

    # Template pour Slack
    slack_blocks: |
      [
        {
          "type": "header",
          "text": {
            "type": "plain_text",
            "text": "🚨 {{ title }}"
          }
        },
        {
          "type": "section",
          "fields": [
            {
              "type": "mrkdwn",
              "text": "*Niveau:*\n{{ level | upper }}"
            },
            {
              "type": "mrkdwn",
              "text": "*Heure:*\n{{ timestamp }}"
            }
          ]
        },
        {
          "type": "section",
          "text": {
            "type": "mrkdwn",
            "text": "{{ message }}"
          }
        }
      ]
```

## Throttling et Rate Limiting

### Configuration du Throttling

```yaml
alerts:
  throttling:
    enabled: true

    # Intervalle minimum entre alertes similaires
    min_interval: 300  # 5 minutes

    # Maximum d'alertes par heure
    max_per_hour: 10

    # Maximum d'alertes par jour
    max_per_day: 50

    # Groupement d'alertes similaires
    group_similar: true
    group_window: 300  # 5 minutes

    # Burst allowance (rafales autorisées)
    burst_size: 3
```

### Règles de Throttling

```yaml
alerts:
  throttling:
    rules:
      # Par sévérité
      by_severity:
        info:
          min_interval: 3600  # 1 heure
          max_per_day: 24
        warning:
          min_interval: 300   # 5 minutes
          max_per_hour: 10
        critical:
          min_interval: 60    # 1 minute
          max_per_hour: 20

      # Par type d'alerte
      by_type:
        performance:
          min_interval: 600
        security:
          min_interval: 0  # Pas de throttling
        backup:
          min_interval: 3600

      # Par canal
      by_channel:
        slack:
          max_per_hour: 15
        email:
          max_per_day: 100
```

### Digest d'Alertes

```yaml
alerts:
  digest:
    enabled: true

    # Regrouper les alertes INFO en digest
    levels: [info]

    # Intervalle de génération du digest
    interval: 1h

    # Format
    format: summary  # summary, detailed

    template: |
      Résumé des alertes ({{ count }} alertes)

      {% for alert in alerts %}
      • [{{ alert.timestamp }}] {{ alert.title }}
      {% endfor %}
```

## Escalade des Alertes

### Configuration de l'Escalade

```yaml
alerts:
  escalation:
    enabled: true

    # Niveaux d'escalade
    levels:
      - name: level1
        delay: 0
        channels: [slack]
        recipients:
          - ldap-team@company.com

      - name: level2
        delay: 15m
        condition: not_acknowledged
        channels: [slack, email]
        recipients:
          - ldap-team@company.com
          - ops-manager@company.com
        slack_mention: "@ldap-lead"

      - name: level3
        delay: 30m
        condition: not_resolved
        channels: [slack, email, webhook]
        recipients:
          - ldap-team@company.com
          - ops-manager@company.com
          - cto@company.com
        slack_mention: "@oncall"
        priority: high
```

### Escalade par Sévérité

```yaml
alerts:
  escalation:
    by_severity:
      critical:
        - delay: 0
          recipients: [ldap-team@company.com]
        - delay: 5m
          recipients: [ldap-team@company.com, oncall@company.com]
        - delay: 15m
          recipients: [ldap-team@company.com, oncall@company.com, manager@company.com]

      warning:
        - delay: 0
          recipients: [ldap-team@company.com]
        - delay: 1h
          recipients: [ldap-team@company.com, manager@company.com]
```

## Alertes Personnalisées

### Création d'Alertes Custom

```yaml
alerts:
  custom:
    - name: contractor_expiry
      description: "Contrats expirant bientôt"
      type: scheduled
      schedule: "0 9 * * 1"  # Lundi 9h
      query: |
        SELECT uid, contractEndDate
        FROM users
        WHERE employeeType = 'contractor'
        AND contractEndDate < DATE_ADD(NOW(), INTERVAL 30 DAY)
      severity: warning
      template: |
        Les contrats suivants expirent dans moins de 30 jours:
        {% for user in results %}
        • {{ user.uid }}: {{ user.contractEndDate }}
        {% endfor %}

    - name: unused_groups
      description: "Groupes non utilisés"
      type: on_demand
      query: |
        SELECT cn, modifyTimestamp
        FROM groups
        WHERE member_count = 0
        AND modifyTimestamp < DATE_SUB(NOW(), INTERVAL 6 MONTH)
      severity: info
```

## Testing et Validation

### Test des Alertes

```bash
# Tester l'envoi d'alerte
ldap-health-monitor alert test \
  --level warning \
  --title "Test Alert" \
  --message "Ceci est un test" \
  --channel slack

# Tester toutes les configurations
ldap-health-monitor alert test-all

# Tester un canal spécifique
ldap-health-monitor alert test --channel email
ldap-health-monitor alert test --channel slack
ldap-health-monitor alert test --channel webhook
```

### Validation de la Configuration

```bash
# Valider la configuration des alertes
ldap-health-monitor config validate --section alerts

# Vérifier la connectivité
ldap-health-monitor alert check-connectivity
```

## Exemples Pratiques

### Configuration Minimale

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"

  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    to:
      - admin@company.com

  levels:
    warning: true
    critical: true
```

### Configuration Complète

```yaml
alerts:
  # Canaux
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channels:
      info: "#ldap-info"
      warning: "#ldap-warnings"
      critical: "#ldap-critical"
    mention_on_critical: "@oncall"
    use_blocks: true

  email:
    enabled: true
    smtp_host: smtp.company.com
    smtp_port: 587
    smtp_use_tls: true
    smtp_user: ${SMTP_USER}
    smtp_password: ${SMTP_PASSWORD}
    from: ldap-monitor@company.com
    to:
      - ldap-team@company.com
    format: html

  webhook:
    enabled: true
    endpoints:
      - name: pagerduty
        url: https://events.pagerduty.com/v2/enqueue
        method: POST
        headers:
          Content-Type: application/json

  # Niveaux
  levels:
    info: true
    warning: true
    critical: true

  # Routage
  routing:
    critical:
      channels: [slack, email, webhook]
    warning:
      channels: [slack, email]
    info:
      channels: [email]

  # Throttling
  throttling:
    enabled: true
    min_interval: 300
    max_per_hour: 10
    group_similar: true

  # Escalade
  escalation:
    enabled: true
    levels:
      - delay: 0
        recipients: [ldap-team@company.com]
      - delay: 15m
        recipients: [ldap-team@company.com, oncall@company.com]
```

## Dépannage

### Alertes Non Reçues

```bash
# Vérifier la configuration
ldap-health-monitor config show --section alerts

# Tester l'envoi
ldap-health-monitor alert test --channel slack

# Vérifier les logs
tail -f /var/log/ldap-monitor/alerts.log
```

### Problèmes Slack

```bash
# Vérifier le webhook
curl -X POST "${SLACK_WEBHOOK}" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'

# Vérifier les permissions du webhook
# Le webhook doit avoir accès au canal
```

### Problèmes Email

```bash
# Tester SMTP
telnet smtp.company.com 587

# Tester avec Python
python3 << 'EOF'
import smtplib
server = smtplib.SMTP('smtp.company.com', 587)
server.starttls()
server.login('user', 'password')
print("OK")
server.quit()
EOF
```

## Liens Connexes

- [Configuration du Monitoring](./Monitoring-Configuration.md)
- [Configuration des Audits](./Audit-Configuration.md)
- [Variables d'Environnement](./Environment-Variables.md)
- [Intégrations](../integrations/)
- [Guide de Production](../guides/Production-Deployment.md)
