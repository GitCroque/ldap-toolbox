# Intégration Slack

Guide complet pour configurer les notifications Slack avec LDAP Health Monitor. Recevez des alertes en temps réel sur l'état de votre infrastructure LDAP directement dans Slack.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Prérequis](#prérequis)
- [Configuration Slack App](#configuration-slack-app)
- [Webhooks Entrants](#webhooks-entrants)
- [Configuration LDAP Monitor](#configuration-ldap-monitor)
- [Types de Notifications](#types-de-notifications)
- [Messages Personnalisés](#messages-personnalisés)
- [Blocks API](#blocks-api)
- [Bot Slack Avancé](#bot-slack-avancé)
- [Gestion des Alertes](#gestion-des-alertes)
- [Exemples Pratiques](#exemples-pratiques)
- [Troubleshooting](#troubleshooting)

## 📊 Vue d'ensemble

### Fonctionnalités

- ✅ **Alertes temps réel** - Notifications instantanées sur les problèmes LDAP
- ✅ **Messages riches** - Blocks API avec boutons et formatage avancé
- ✅ **Canaux multiples** - Routage des alertes par sévérité
- ✅ **Mentions intelligentes** - @channel pour les alertes critiques
- ✅ **Threads** - Regroupement des alertes similaires
- ✅ **Emojis et couleurs** - Indicateurs visuels de statut

### Architecture

```
┌─────────────────────┐
│  LDAP Monitor       │
│  Alert Manager      │
└──────────┬──────────┘
           │ HTTPS POST
           ↓
┌─────────────────────┐
│  Slack Webhook API  │
│  (Incoming Webhook) │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Slack Channel      │
│  #ldap-alerts       │
└─────────────────────┘
```

## 🔧 Prérequis

### Accès Slack

- **Workspace Admin** ou permissions pour créer des apps
- **Canal dédié** pour les alertes (ex: `#ldap-monitoring`)
- **Slack Plan** : Gratuit ou payant (toutes fonctionnalités disponibles)

### LDAP Health Monitor

- Version **1.0.0+**
- Module `alerts` activé
- Connexion internet pour accéder à l'API Slack

## 🔐 Configuration Slack App

### Méthode 1 : Incoming Webhooks (Simple)

#### 1. Créer un Incoming Webhook

**Via Slack App Directory :**

1. Accédez à `https://api.slack.com/apps`
2. Cliquez sur **"Create New App"**
3. Sélectionnez **"From scratch"**
4. Nommez l'app : **"LDAP Health Monitor"**
5. Sélectionnez votre workspace

**Activer Incoming Webhooks :**

1. Dans le menu latéral : **Features → Incoming Webhooks**
2. Activez **"Activate Incoming Webhooks"**
3. Cliquez sur **"Add New Webhook to Workspace"**
4. Sélectionnez le canal (ex: `#ldap-alerts`)
5. Cliquez **"Allow"**

**Récupérer l'URL du webhook :**

```
https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN
```

⚠️ **Conservez cette URL en sécurité !**

#### 2. Tester le Webhook

```bash
# Test simple
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test from LDAP Monitor"}' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Test avec formatage
curl -X POST \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "Test LDAP Monitor",
    "attachments": [{
      "color": "good",
      "text": "✅ LDAP server is healthy",
      "footer": "LDAP Health Monitor"
    }]
  }' \
  https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Méthode 2 : Bot avec OAuth (Avancé)

#### 1. Créer le Bot

1. Dans **Slack App → OAuth & Permissions**
2. Ajoutez les **Bot Token Scopes** :
   - `chat:write` - Poster des messages
   - `chat:write.public` - Poster dans les canaux publics
   - `channels:read` - Lire les infos des canaux
   - `users:read` - Lire les infos utilisateurs

3. Cliquez **"Install to Workspace"**
4. Récupérez le **Bot User OAuth Token** : `xoxb-...`

#### 2. Inviter le Bot

```
/invite @LDAP Health Monitor
```

## ⚙️ Configuration LDAP Monitor

### Configuration de base

Éditez `config.yaml` :

```yaml
alerts:
  # Activer les alertes
  enabled: true

  # Configuration Slack
  slack:
    enabled: true

    # Webhook URL (méthode recommandée : variable d'env)
    webhook_url: ${SLACK_WEBHOOK_URL}

    # Canal par défaut
    channel: "#ldap-alerts"

    # Nom d'utilisateur du bot
    username: "LDAP Monitor"

    # Icône du bot (emoji ou URL)
    icon_emoji: ":warning:"
    # icon_url: "https://example.com/ldap-icon.png"

    # Mentions
    mention_on_critical: "@channel"  # Mentionner @channel sur alertes critiques
    mention_on_warning: "@here"      # Mentionner @here sur warnings

    # Sévérités à notifier
    severities:
      - critical
      - warning
      - info

    # Types d'événements
    events:
      - server_down
      - high_response_time
      - audit_failed
      - user_locked
      - password_expired

    # Format des messages
    use_blocks: true              # Utiliser Blocks API (recommandé)
    use_threads: true             # Grouper alertes similaires en threads
    include_server_info: true     # Inclure infos du serveur
    include_timestamp: true       # Inclure timestamp

    # Throttling
    throttle:
      enabled: true
      max_messages_per_minute: 10
      group_similar_alerts: true
      grouping_window: 300        # 5 minutes
```

### Variables d'environnement

**`.env` :**

```bash
# Slack Webhook URL
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_WORKSPACE_ID/YOUR_CHANNEL_ID/YOUR_WEBHOOK_TOKEN

# Ou Bot Token (pour méthode OAuth)
SLACK_BOT_TOKEN=xoxb-your-bot-token

# Canal par défaut (optionnel, override le config.yaml)
SLACK_CHANNEL=#ldap-alerts
```

**Charger les variables :**

```bash
# Bash/Zsh
export $(cat .env | xargs)

# Ou avec direnv
echo 'dotenv' > .envrc
direnv allow

# Ou avec systemd
# Voir section systemd ci-dessous
```

### Configuration avancée - Canaux multiples

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK_URL}

    # Routage par sévérité
    routing:
      critical:
        channel: "#ldap-critical"
        mention: "@channel"
        color: "danger"

      warning:
        channel: "#ldap-warnings"
        mention: "@here"
        color: "warning"

      info:
        channel: "#ldap-info"
        mention: ""
        color: "good"

    # Webhooks multiples (si plusieurs canaux)
    webhooks:
      critical: ${SLACK_WEBHOOK_CRITICAL}
      warnings: ${SLACK_WEBHOOK_WARNINGS}
      info: ${SLACK_WEBHOOK_INFO}
```

## 📨 Types de Notifications

### 1. Alerte Serveur Down

**Déclencheur :** Serveur LDAP inaccessible

**Message Slack :**

```
🔴 ALERTE CRITIQUE - Serveur LDAP Down
@channel

Serveur: ldap.example.com:389
Status: INACCESSIBLE
Durée: 5 minutes
Dernière réponse: 2024-01-15 14:32:00

Action requise: Vérifier le serveur immédiatement
```

### 2. Temps de Réponse Élevé

**Déclencheur :** Latence > seuil configuré

**Message :**

```
⚠️ WARNING - Temps de Réponse Élevé

Serveur: ldap.example.com
Temps de réponse: 5.2s (seuil: 2s)
Durée: 15 minutes

Recommandation: Vérifier la charge du serveur
```

### 3. Audit Terminé

**Déclencheur :** Audit complété avec succès

**Message :**

```
✅ Audit LDAP Terminé

Type: Audit Complet
Durée: 2m 34s
Utilisateurs analysés: 1,523
Groupes analysés: 245

Résultats:
• 12 utilisateurs inactifs
• 3 groupes vides
• 5 mots de passe expirés

Rapport: /reports/audit-2024-01-15.html
```

### 4. Utilisateurs Verrouillés

**Déclencheur :** Détection de comptes verrouillés

**Message :**

```
🔒 Comptes Utilisateurs Verrouillés

Nombre: 3 utilisateurs
Serveur: ldap.example.com

Utilisateurs:
• john.doe@example.com
• jane.smith@example.com
• bob.wilson@example.com

Action: Débloquer via ldap-monitor user unlock
```

## 🎨 Messages Personnalisés avec Blocks API

### Message Simple (Legacy)

```python
{
  "text": "Serveur LDAP down",
  "attachments": [{
    "color": "danger",
    "fields": [
      {"title": "Serveur", "value": "ldap.example.com", "short": true},
      {"title": "Status", "value": "DOWN", "short": true}
    ]
  }]
}
```

### Message avec Blocks (Moderne)

```yaml
# Dans config.yaml - Template de message personnalisé
alerts:
  slack:
    message_templates:
      server_down:
        blocks:
          - type: header
            text:
              type: plain_text
              text: "🔴 SERVEUR LDAP INACCESSIBLE"

          - type: section
            fields:
              - type: mrkdwn
                text: "*Serveur:*\n{{ server_url }}"
              - type: mrkdwn
                text: "*Status:*\n❌ DOWN"
              - type: mrkdwn
                text: "*Durée:*\n{{ duration }}"
              - type: mrkdwn
                text: "*Impact:*\nAUTHENTIFICATION IMPOSSIBLE"

          - type: section
            text:
              type: mrkdwn
              text: "*Actions à prendre:*\n1. Vérifier le serveur\n2. Consulter les logs\n3. Redémarrer si nécessaire"

          - type: actions
            elements:
              - type: button
                text:
                  type: plain_text
                  text: "Voir les Logs"
                url: "https://logs.example.com/ldap"
                style: "danger"

              - type: button
                text:
                  type: plain_text
                  text: "Dashboard Grafana"
                url: "https://grafana.example.com/d/ldap"

          - type: context
            elements:
              - type: mrkdwn
                text: "LDAP Health Monitor | {{ timestamp }}"
```

### Exemple Complet de Block Message

**JSON à envoyer via webhook :**

```json
{
  "channel": "#ldap-alerts",
  "username": "LDAP Monitor",
  "icon_emoji": ":warning:",
  "blocks": [
    {
      "type": "header",
      "text": {
        "type": "plain_text",
        "text": "⚠️ Alerte LDAP - Temps de Réponse Élevé"
      }
    },
    {
      "type": "section",
      "fields": [
        {
          "type": "mrkdwn",
          "text": "*Serveur:*\nldap.example.com:389"
        },
        {
          "type": "mrkdwn",
          "text": "*Sévérité:*\n⚠️ WARNING"
        },
        {
          "type": "mrkdwn",
          "text": "*Temps de réponse:*\n5.2s (seuil: 2s)"
        },
        {
          "type": "mrkdwn",
          "text": "*Durée:*\n15 minutes"
        }
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Métriques actuelles:*\n```\nConnexions actives: 450\nCPU: 78%\nMémoire: 6.2 GB / 8 GB\nQuery rate: 150 req/s\n```"
      }
    },
    {
      "type": "divider"
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Recommandations:*\n• Vérifier la charge du serveur\n• Analyser les slow queries\n• Considérer scale up si persistant"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "📊 Grafana Dashboard"
          },
          "url": "https://grafana.example.com/d/ldap",
          "style": "primary"
        },
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "📝 Voir les Logs"
          },
          "url": "https://logs.example.com/ldap"
        },
        {
          "type": "button",
          "text": {
            "type": "plain_text",
            "text": "🔕 Acknowledge"
          },
          "value": "ack_alert_12345"
        }
      ]
    },
    {
      "type": "context",
      "elements": [
        {
          "type": "mrkdwn",
          "text": "🤖 LDAP Health Monitor v1.0.0 | 2024-01-15 14:35:22 UTC"
        }
      ]
    }
  ]
}
```

**Résultat visuel :**

```
┌────────────────────────────────────────────┐
│ ⚠️ Alerte LDAP - Temps de Réponse Élevé   │
├────────────────────────────────────────────┤
│ Serveur:             Sévérité:             │
│ ldap.example.com     ⚠️ WARNING            │
│                                             │
│ Temps de réponse:    Durée:                │
│ 5.2s (seuil: 2s)     15 minutes            │
├────────────────────────────────────────────┤
│ Métriques actuelles:                        │
│ Connexions actives: 450                     │
│ CPU: 78%                                    │
│ Mémoire: 6.2 GB / 8 GB                      │
│ Query rate: 150 req/s                       │
├────────────────────────────────────────────┤
│ Recommandations:                            │
│ • Vérifier la charge du serveur            │
│ • Analyser les slow queries                │
│ • Considérer scale up si persistant        │
├────────────────────────────────────────────┤
│ [📊 Grafana] [📝 Logs] [🔕 Acknowledge]    │
├────────────────────────────────────────────┤
│ 🤖 LDAP Health Monitor v1.0.0 | 14:35:22   │
└────────────────────────────────────────────┘
```

## 🤖 Bot Slack Avancé

### Configuration OAuth

**`config.yaml` :**

```yaml
alerts:
  slack:
    enabled: true
    mode: "bot"  # Au lieu de "webhook"

    # Bot token
    bot_token: ${SLACK_BOT_TOKEN}

    # Canaux autorisés
    channels:
      - "#ldap-alerts"
      - "#ldap-critical"

    # Fonctionnalités bot
    bot_features:
      # Commandes interactives
      interactive_messages: true

      # Boutons d'action
      actions:
        - name: "acknowledge"
          label: "✓ Acknowledge"
          style: "primary"

        - name: "snooze"
          label: "💤 Snooze 1h"
          style: "default"

        - name: "resolve"
          label: "✅ Resolve"
          style: "danger"

      # Réactions emoji
      reactions:
        acknowledged: "white_check_mark"
        resolved: "heavy_check_mark"
        investigating: "eyes"
```

### Commandes Slash

**Créer des slash commands dans Slack App :**

1. **Slack App → Slash Commands**
2. **Create New Command**

**Exemples de commandes :**

| Commande | Description | URL |
|----------|-------------|-----|
| `/ldap-status` | Statut serveur LDAP | `https://your-api.com/slack/status` |
| `/ldap-audit` | Lancer un audit | `https://your-api.com/slack/audit` |
| `/ldap-health` | Health check | `https://your-api.com/slack/health` |

**Exemple d'endpoint pour `/ldap-status` :**

```python
# API Flask simple
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/slack/status', methods=['POST'])
def ldap_status():
    # Récupérer le serveur LDAP status
    status = get_ldap_status()

    return jsonify({
        "response_type": "in_channel",
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*LDAP Server Status*\n"
                            f"Status: {'✅ UP' if status.up else '❌ DOWN'}\n"
                            f"Response time: {status.response_time}ms\n"
                            f"Active connections: {status.connections}"
                }
            }
        ]
    })
```

## 🎯 Gestion des Alertes

### Throttling et Rate Limiting

**Éviter le spam de notifications :**

```yaml
alerts:
  slack:
    throttle:
      # Grouper alertes similaires
      enabled: true
      grouping_window: 300  # 5 minutes

      # Limite de messages
      max_messages_per_minute: 10

      # Digest des alertes
      digest:
        enabled: true
        interval: 600  # 10 minutes
        min_alerts: 3  # Au moins 3 alertes pour faire un digest
```

**Exemple de digest :**

```
📊 Digest des Alertes LDAP (10 dernières minutes)

⚠️ 5 alertes de temps de réponse élevé
🔒 3 utilisateurs verrouillés
ℹ️ 2 audits terminés

Détails: /reports/digest-2024-01-15-1435.html
```

### Filtrage Intelligent

```yaml
alerts:
  slack:
    filters:
      # Ne pas notifier pendant maintenance
      maintenance_mode: false

      # Ignorer certains serveurs
      excluded_servers:
        - "ldap-test.example.com"
        - "ldap-dev.example.com"

      # Heures de silence
      quiet_hours:
        enabled: true
        start: "22:00"
        end: "08:00"
        timezone: "Europe/Paris"
        severity_override:  # Notifier quand même pour critical
          - critical

      # Jours de silence
      quiet_days:
        - "Saturday"
        - "Sunday"
```

## 📋 Exemples Pratiques

### Exemple 1 : Notification Complète d'Audit

```bash
# Lancer un audit avec notification Slack
ldap-monitor audit all \
  --format html \
  --output /reports/audit-$(date +%Y%m%d).html \
  --notify slack

# Ou avec la config par défaut
ldap-monitor audit all --notify
```

**Message Slack résultant :**

```json
{
  "blocks": [
    {
      "type": "header",
      "text": {"type": "plain_text", "text": "✅ Audit LDAP Terminé"}
    },
    {
      "type": "section",
      "fields": [
        {"type": "mrkdwn", "text": "*Type:*\nAudit Complet"},
        {"type": "mrkdwn", "text": "*Durée:*\n2m 34s"},
        {"type": "mrkdwn", "text": "*Utilisateurs:*\n1,523 analysés"},
        {"type": "mrkdwn", "text": "*Groupes:*\n245 analysés"}
      ]
    },
    {
      "type": "section",
      "text": {
        "type": "mrkdwn",
        "text": "*Problèmes détectés:*\n• 12 utilisateurs inactifs (>90j)\n• 3 groupes vides\n• 5 mots de passe expirés\n• 2 attributs manquants"
      }
    },
    {
      "type": "actions",
      "elements": [
        {
          "type": "button",
          "text": {"type": "plain_text", "text": "📄 Voir le Rapport"},
          "url": "https://reports.example.com/audit-20240115.html"
        }
      ]
    }
  ]
}
```

### Exemple 2 : Monitoring en Mode Daemon

```bash
# Démarrer le daemon avec Slack
ldap-monitor monitor start \
  --interval 300 \
  --slack \
  --slack-channel "#ldap-monitoring"
```

**Créer un service systemd avec Slack :**

```bash
sudo tee /etc/systemd/system/ldap-monitor.service << EOF
[Unit]
Description=LDAP Health Monitor with Slack Alerts
After=network.target

[Service]
Type=simple
User=ldap-monitor
EnvironmentFile=/etc/ldap-monitor/.env
WorkingDirectory=/opt/ldap-monitor
ExecStart=/usr/local/bin/ldap-monitor monitor start --slack
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl start ldap-monitor
sudo systemctl enable ldap-monitor
```

### Exemple 3 : Script Personnalisé

```bash
#!/bin/bash
# check-ldap-with-slack.sh

# Configuration
WEBHOOK_URL="${SLACK_WEBHOOK_URL}"
CHANNEL="#ldap-alerts"

# Fonction d'envoi Slack
send_slack() {
    local message="$1"
    local color="$2"

    curl -X POST "$WEBHOOK_URL" \
      -H 'Content-Type: application/json' \
      -d "{
        \"channel\": \"$CHANNEL\",
        \"username\": \"LDAP Monitor\",
        \"icon_emoji\": \":warning:\",
        \"attachments\": [{
          \"color\": \"$color\",
          \"text\": \"$message\",
          \"footer\": \"LDAP Health Monitor\",
          \"ts\": $(date +%s)
        }]
      }"
}

# Exécuter l'audit
if ldap-monitor audit health --quiet; then
    send_slack "✅ LDAP server is healthy" "good"
else
    send_slack "❌ LDAP server health check FAILED" "danger"
    exit 1
fi
```

## 🐛 Troubleshooting

### Webhook ne fonctionne pas

```bash
# Vérifier l'URL du webhook
echo $SLACK_WEBHOOK_URL

# Tester manuellement
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H 'Content-Type: application/json' \
  -d '{"text":"Test message"}'

# Vérifier les logs LDAP Monitor
ldap-monitor --debug monitor start --slack
```

### Messages non reçus

**Vérifier la configuration :**

```bash
# Valider le config.yaml
ldap-monitor config validate

# Tester l'envoi manuel
ldap-monitor test slack-notification

# Vérifier les permissions du bot
# Dans Slack App → OAuth & Permissions
```

### Erreur 403 Forbidden

**Cause :** Webhook URL invalide ou révoquée

**Solution :**
1. Régénérer un nouveau webhook
2. Mettre à jour `SLACK_WEBHOOK_URL`
3. Redémarrer ldap-monitor

### Messages tronqués

**Cause :** Limite de 3000 caractères par message

**Solution :**

```yaml
alerts:
  slack:
    # Tronquer les longs messages
    truncate_long_messages: true
    max_message_length: 2500

    # Ou envoyer en plusieurs messages
    split_long_messages: true
```

## 📚 Ressources

- [Slack API Documentation](https://api.slack.com/)
- [Block Kit Builder](https://app.slack.com/block-kit-builder)
- [Incoming Webhooks Guide](https://api.slack.com/messaging/webhooks)
- [Bot Users Guide](https://api.slack.com/bot-users)

## 🔗 Liens Connexes

- [Configuration des Alertes](../configuration/Alerts-Configuration.md)
- [Email Integration](Email.md)
- [Webhooks Génériques](Webhooks.md)
- [Système d'Alertes](../features/monitoring/Alerts-System.md)
