# Webhooks Génériques

Guide complet pour intégrer LDAP Health Monitor avec des webhooks génériques. Connectez-vous à n'importe quel service supportant les webhooks : Zapier, IFTTT, Make, services custom, et plus encore.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Concepts de base](#concepts-de-base)
- [Configuration](#configuration)
- [Format du Payload](#format-du-payload)
- [Authentification](#authentification)
- [Zapier](#zapier)
- [IFTTT](#ifttt)
- [Make (Integromat)](#make-integromat)
- [Webhooks Custom](#webhooks-custom)
- [Exemples Pratiques](#exemples-pratiques)
- [Sécurité](#sécurité)
- [Troubleshooting](#troubleshooting)

## 📊 Vue d'ensemble

### Qu'est-ce qu'un Webhook ?

Un webhook est une méthode de communication HTTP qui permet à une application d'envoyer des données en temps réel vers une URL spécifique lorsqu'un événement se produit.

```
┌─────────────────────┐
│  LDAP Monitor       │
│  Event occurs       │
└──────────┬──────────┘
           │ HTTP POST
           ↓
┌─────────────────────┐
│  Webhook Endpoint   │
│  https://...        │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Your Application   │
│  Process data       │
└─────────────────────┘
```

### Avantages

- ✅ **Temps réel** - Notifications instantanées
- ✅ **Découplé** - Pas besoin de polling
- ✅ **Flexible** - Fonctionne avec n'importe quel service HTTP
- ✅ **Scalable** - Peut gérer de multiples destinations
- ✅ **Universel** - Standard largement adopté

### Cas d'usage

- Envoyer des alertes vers des services externes
- Déclencher des workflows d'automatisation
- Intégrer avec des systèmes propriétaires
- Logger les événements dans des bases de données
- Synchroniser avec des outils de ticketing

## 🎓 Concepts de base

### Événements

LDAP Monitor peut déclencher des webhooks sur ces événements :

| Événement | Description | Quand |
|-----------|-------------|-------|
| `alert` | Alerte générique | Tout problème détecté |
| `server_down` | Serveur inaccessible | Connexion échouée |
| `server_up` | Serveur rétabli | Après une panne |
| `high_response_time` | Latence élevée | Temps de réponse > seuil |
| `audit_started` | Audit démarré | Début d'audit |
| `audit_completed` | Audit terminé | Fin d'audit |
| `backup_completed` | Backup terminé | Sauvegarde réussie |
| `backup_failed` | Backup échoué | Erreur de sauvegarde |
| `user_locked` | Utilisateur verrouillé | Compte bloqué détecté |
| `user_unlocked` | Utilisateur déverrouillé | Compte débloqué |
| `password_expired` | Mot de passe expiré | Expiration détectée |
| `group_empty` | Groupe vide | Groupe sans membres |

### Méthodes HTTP

LDAP Monitor supporte :

- **POST** (défaut, recommandé) - Envoie les données dans le body
- **PUT** - Alternative à POST
- **GET** - Données dans les query parameters (limité)

### Types de Contenu

- **application/json** (défaut, recommandé)
- **application/x-www-form-urlencoded**
- **multipart/form-data**

## ⚙️ Configuration

### Configuration de base

**`config.yaml` :**

```yaml
alerts:
  enabled: true

  # Webhooks génériques
  webhooks:
    enabled: true

    # Endpoints
    endpoints:
      # Endpoint principal
      - name: "primary"
        url: "https://hooks.example.com/ldap-monitor"
        enabled: true

      # Endpoint de backup
      - name: "backup"
        url: "https://backup-hooks.example.com/ldap"
        enabled: true
        failover: true  # Utilisé si primary échoue

      # Endpoint pour events spécifiques
      - name: "critical-only"
        url: "https://critical.example.com/webhook"
        enabled: true
        events:
          - server_down
          - backup_failed
        severities:
          - critical

    # Configuration globale
    method: "POST"
    content_type: "application/json"
    timeout: 30  # secondes
    verify_ssl: true

    # Headers custom
    headers:
      User-Agent: "LDAP-Health-Monitor/1.0"
      X-Monitor-Version: "1.0.0"

    # Retry
    retry:
      enabled: true
      max_attempts: 3
      delay: 5  # secondes
      backoff: "exponential"  # linear, exponential

    # Événements à envoyer
    events:
      - alert
      - server_down
      - audit_completed
      - backup_failed

    # Payload
    payload:
      format: "standard"  # standard, custom
      include_timestamp: true
      include_server_info: true
      include_metrics: true
```

### Configuration avec variables d'environnement

**`.env` :**

```bash
# Webhook URLs
WEBHOOK_PRIMARY_URL=https://hooks.example.com/ldap-monitor
WEBHOOK_BACKUP_URL=https://backup.example.com/webhook
WEBHOOK_ZAPIER_URL=https://hooks.zapier.com/hooks/catch/123456/abcdef/

# Authentification
WEBHOOK_API_KEY=your-api-key-here
WEBHOOK_SECRET=your-webhook-secret
```

**`config.yaml` avec env vars :**

```yaml
alerts:
  webhooks:
    enabled: true
    endpoints:
      - name: "primary"
        url: ${WEBHOOK_PRIMARY_URL}
        headers:
          Authorization: "Bearer ${WEBHOOK_API_KEY}"

      - name: "zapier"
        url: ${WEBHOOK_ZAPIER_URL}
```

### Configuration avancée - Multiples endpoints

```yaml
alerts:
  webhooks:
    enabled: true

    # Routage par sévérité
    routing:
      critical:
        - url: "https://pagerduty.example.com/webhook"
          name: "PagerDuty"
        - url: "https://oncall.example.com/alert"
          name: "OnCall System"

      warning:
        - url: "https://slack-webhook.example.com"
          name: "Slack Warnings"

      info:
        - url: "https://logs.example.com/ingest"
          name: "Log Aggregator"

    # Templates de payload par endpoint
    templates:
      default: |
        {
          "event": "{{ event }}",
          "severity": "{{ severity }}",
          "message": "{{ message }}",
          "timestamp": "{{ timestamp }}"
        }

      pagerduty: |
        {
          "routing_key": "{{ routing_key }}",
          "event_action": "trigger",
          "payload": {
            "summary": "{{ alert.title }}",
            "severity": "{{ severity }}",
            "source": "ldap-monitor"
          }
        }
```

## 📦 Format du Payload

### Payload Standard

**Structure par défaut envoyée :**

```json
{
  "event": "alert",
  "event_id": "evt_1234567890",
  "timestamp": "2024-01-15T14:35:22.123Z",
  "severity": "critical",
  "alert_type": "server_down",

  "source": {
    "application": "ldap-health-monitor",
    "version": "1.0.0",
    "hostname": "monitor-server.example.com"
  },

  "server": {
    "url": "ldap://ldap.example.com:389",
    "host": "ldap.example.com",
    "port": 389,
    "base_dn": "dc=example,dc=com",
    "type": "OpenLDAP"
  },

  "alert": {
    "title": "Serveur LDAP Inaccessible",
    "message": "Le serveur LDAP ne répond plus depuis 5 minutes",
    "description": "Tentatives de connexion échouées. Dernière réponse reçue à 14:25:00.",
    "duration": "5m",
    "detection_time": "2024-01-15T14:30:22Z",
    "last_success": "2024-01-15T14:25:00Z"
  },

  "metrics": {
    "response_time": null,
    "active_connections": 0,
    "failed_attempts": 5,
    "uptime_percentage": 99.2
  },

  "recommendations": [
    "Vérifier le statut du serveur avec systemctl",
    "Consulter les logs dans /var/log/slapd.log",
    "Tester la connectivité réseau",
    "Redémarrer le service si nécessaire"
  ],

  "links": {
    "dashboard": "https://grafana.example.com/d/ldap-overview",
    "logs": "https://logs.example.com/ldap",
    "documentation": "https://wiki.example.com/ldap-troubleshooting"
  },

  "context": {
    "environment": "production",
    "datacenter": "eu-west-1",
    "tags": ["ldap", "infrastructure", "critical"]
  }
}
```

### Payload Personnalisé

**Définir un template custom :**

```yaml
alerts:
  webhooks:
    payload:
      format: "custom"
      template: |
        {
          "title": "LDAP Alert: {{ alert.title }}",
          "description": "{{ alert.message }}",
          "severity_level": "{{ severity }}",
          "server_name": "{{ server.host }}",
          "timestamp_unix": {{ timestamp_unix }},
          "is_critical": {{ severity == 'critical' }},
          "metadata": {
            "monitor_version": "{{ version }}",
            "event_id": "{{ event_id }}"
          }
        }
```

### Payload par Type d'Événement

**Audit Completed :**

```json
{
  "event": "audit_completed",
  "timestamp": "2024-01-15T14:35:22Z",
  "severity": "info",

  "audit": {
    "type": "full",
    "duration": "2m34s",
    "started_at": "2024-01-15T14:32:48Z",
    "completed_at": "2024-01-15T14:35:22Z"
  },

  "statistics": {
    "users": {
      "total": 1523,
      "active": 1450,
      "inactive": 73,
      "locked": 2,
      "password_expired": 5
    },
    "groups": {
      "total": 245,
      "empty": 3,
      "large": 12,
      "total_members": 3456
    }
  },

  "issues": [
    {
      "type": "inactive_user",
      "severity": "warning",
      "count": 73,
      "description": "73 utilisateurs inactifs depuis plus de 90 jours"
    },
    {
      "type": "empty_group",
      "severity": "info",
      "count": 3,
      "description": "3 groupes sans membres"
    }
  ],

  "report": {
    "format": "html",
    "url": "https://reports.example.com/audit-20240115.html",
    "size_bytes": 156789
  }
}
```

## 🔐 Authentification

### 1. Aucune authentification

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://public-webhook.example.com"
        auth: false
```

### 2. Bearer Token

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://api.example.com/webhook"
        auth:
          type: "bearer"
          token: ${WEBHOOK_TOKEN}

# Header envoyé :
# Authorization: Bearer your-token-here
```

### 3. Basic Auth

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://api.example.com/webhook"
        auth:
          type: "basic"
          username: ${WEBHOOK_USER}
          password: ${WEBHOOK_PASSWORD}

# Header envoyé :
# Authorization: Basic base64(username:password)
```

### 4. API Key (Header)

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://api.example.com/webhook"
        auth:
          type: "apikey"
          header: "X-API-Key"
          value: ${API_KEY}

# Header envoyé :
# X-API-Key: your-api-key
```

### 5. Query Parameter

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://api.example.com/webhook"
        auth:
          type: "query"
          param: "api_key"
          value: ${API_KEY}

# URL finale :
# https://api.example.com/webhook?api_key=your-api-key
```

### 6. HMAC Signature

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://api.example.com/webhook"
        auth:
          type: "hmac"
          algorithm: "sha256"
          secret: ${WEBHOOK_SECRET}
          header: "X-Signature"

# Header envoyé :
# X-Signature: sha256=abc123def456...
```

### 7. Custom Headers

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://api.example.com/webhook"
        headers:
          X-API-Key: ${API_KEY}
          X-Client-ID: ${CLIENT_ID}
          X-Custom-Header: "custom-value"
```

## 🔄 Zapier

### Configuration Zapier

**1. Créer un Zap :**

1. Accédez à [Zapier](https://zapier.com)
2. Cliquez **"Create Zap"**
3. **Trigger** : Webhooks by Zapier
4. **Event** : Catch Hook
5. Copiez l'URL du webhook

**2. Configurer LDAP Monitor :**

```yaml
alerts:
  webhooks:
    endpoints:
      - name: "zapier"
        url: "https://hooks.zapier.com/hooks/catch/123456/abcdef/"
        enabled: true
```

**3. Tester :**

```bash
# Déclencher un test
ldap-monitor test webhook --name zapier

# Ou curl
curl -X POST https://hooks.zapier.com/hooks/catch/123456/abcdef/ \
  -H "Content-Type: application/json" \
  -d '{"event":"test","message":"Test from LDAP Monitor"}'
```

**4. Dans Zapier, configurer l'action :**

- **Option 1 :** Gmail - Send Email
- **Option 2 :** Google Sheets - Create Row
- **Option 3 :** Slack - Send Message
- **Option 4 :** Trello - Create Card

**Exemple - Créer une carte Trello :**

**Mapping des champs :**

- **List** : "LDAP Alerts"
- **Card Name** : `{{ alert__title }}`
- **Card Description** :
  ```
  Severity: {{ severity }}
  Server: {{ server__host }}
  Message: {{ alert__message }}
  Time: {{ timestamp }}

  Dashboard: {{ links__dashboard }}
  ```
- **Labels** : `{{ severity }}`
- **Due Date** : (si critical, +2 heures)

## 🌐 IFTTT

### Configuration IFTTT

**1. Créer un Applet :**

1. Accédez à [IFTTT](https://ifttt.com)
2. **Create** → **If This** → **Webhooks**
3. **Event Name** : `ldap_alert`
4. Notez l'URL : `https://maker.ifttt.com/trigger/ldap_alert/with/key/YOUR_KEY`

**2. Configurer LDAP Monitor :**

```yaml
alerts:
  webhooks:
    endpoints:
      - name: "ifttt"
        url: "https://maker.ifttt.com/trigger/ldap_alert/with/key/${IFTTT_KEY}"
        payload:
          format: "custom"
          template: |
            {
              "value1": "{{ alert.title }}",
              "value2": "{{ severity }}",
              "value3": "{{ server.host }}"
            }
```

**3. Configurer l'action IFTTT :**

- **Option 1 :** Notifications - Send notification
- **Option 2 :** Email - Send email
- **Option 3 :** Google Drive - Append to spreadsheet
- **Option 4 :** Smart Home - Trigger actions

**Exemple - Notification mobile :**

- **Notification** : `LDAP Alert: {{Value1}}`
- **Link** : Dashboard URL

**Exemple - Log vers Google Sheets :**

- **Spreadsheet name** : "LDAP Logs"
- **Formatted row** :
  ```
  {{OccurredAt}} ||| {{Value1}} ||| {{Value2}} ||| {{Value3}}
  ```

## 🎯 Make (Integromat)

### Configuration Make

**1. Créer un Scenario :**

1. Accédez à [Make](https://www.make.com)
2. **Create a new scenario**
3. Ajoutez **Webhooks** → **Custom webhook**
4. **Create a webhook** et copiez l'URL

**2. Configurer LDAP Monitor :**

```yaml
alerts:
  webhooks:
    endpoints:
      - name: "make"
        url: "https://hook.eu1.make.com/abcdefghijklmnop"
```

**3. Construire le workflow :**

**Modules possibles :**

1. **Webhook** (trigger)
2. **Router** (routage par sévérité)
   - Route 1 : severity = critical
   - Route 2 : severity = warning
   - Route 3 : severity = info

3. **Actions :**
   - **Slack** - Send message
   - **Jira** - Create issue
   - **Google Sheets** - Add row
   - **HTTP** - Make request (custom API)
   - **Email** - Send email

**Exemple de scénario :**

```
Webhook
  ├─→ [Filter: Critical] → PagerDuty + Jira
  ├─→ [Filter: Warning] → Slack
  └─→ [Filter: Info] → Google Sheets
```

## 🛠️ Webhooks Custom

### Créer un serveur webhook simple

**Python (Flask) :**

```python
from flask import Flask, request, jsonify
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

@app.route('/webhook/ldap', methods=['POST'])
def ldap_webhook():
    """Endpoint pour recevoir les webhooks LDAP Monitor"""

    # Récupérer les données
    data = request.get_json()

    # Logger
    logging.info(f"Received webhook: {data.get('event')}")
    logging.info(f"Severity: {data.get('severity')}")
    logging.info(f"Server: {data.get('server', {}).get('host')}")

    # Traitement custom
    if data.get('severity') == 'critical':
        # Envoyer SMS, créer ticket, etc.
        handle_critical_alert(data)

    elif data.get('event') == 'audit_completed':
        # Traiter les résultats d'audit
        process_audit_results(data)

    # Retourner une réponse
    return jsonify({
        "status": "success",
        "message": "Webhook received",
        "event_id": data.get('event_id')
    }), 200

def handle_critical_alert(data):
    """Traiter une alerte critique"""
    # Votre logique ici
    print(f"CRITICAL ALERT: {data.get('alert', {}).get('title')}")

def process_audit_results(data):
    """Traiter les résultats d'audit"""
    stats = data.get('statistics', {})
    print(f"Audit completed: {stats}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Node.js (Express) :**

```javascript
const express = require('express');
const app = express();

app.use(express.json());

app.post('/webhook/ldap', (req, res) => {
    const data = req.body;

    console.log(`Received webhook: ${data.event}`);
    console.log(`Severity: ${data.severity}`);

    // Traitement
    if (data.severity === 'critical') {
        handleCriticalAlert(data);
    }

    // Réponse
    res.json({
        status: 'success',
        event_id: data.event_id
    });
});

function handleCriticalAlert(data) {
    // Votre logique
    console.log(`CRITICAL: ${data.alert.title}`);
}

app.listen(5000, () => {
    console.log('Webhook server listening on port 5000');
});
```

**Déploiement avec Nginx :**

```nginx
# /etc/nginx/sites-available/webhook

server {
    listen 80;
    server_name webhook.example.com;

    location /webhook/ldap {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### AWS Lambda Webhook

**Lambda Function (Python) :**

```python
import json
import boto3

def lambda_handler(event, context):
    """AWS Lambda handler pour webhooks LDAP Monitor"""

    # Parser le body
    body = json.loads(event['body'])

    # Logger dans CloudWatch
    print(f"Event: {body.get('event')}")
    print(f"Severity: {body.get('severity')}")

    # Traitement selon le type
    if body.get('severity') == 'critical':
        # Envoyer SNS notification
        sns = boto3.client('sns')
        sns.publish(
            TopicArn='arn:aws:sns:eu-west-1:123456:ldap-critical',
            Subject=f"LDAP Alert: {body.get('alert', {}).get('title')}",
            Message=json.dumps(body, indent=2)
        )

    # Stocker dans DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table('ldap-events')
    table.put_item(Item={
        'event_id': body.get('event_id'),
        'timestamp': body.get('timestamp'),
        'event': body.get('event'),
        'severity': body.get('severity'),
        'data': json.dumps(body)
    })

    return {
        'statusCode': 200,
        'body': json.dumps({'status': 'success'})
    }
```

**API Gateway Configuration :**

1. Créer une API Gateway REST API
2. Créer une resource `/webhook`
3. Créer une méthode POST
4. Intégrer avec la Lambda function
5. Déployer
6. Utiliser l'URL dans LDAP Monitor config

## 💡 Exemples Pratiques

### Exemple 1 : Logger dans une Base de Données

**Configuration :**

```yaml
alerts:
  webhooks:
    endpoints:
      - name: "database-logger"
        url: "https://api.example.com/log-event"
        auth:
          type: "bearer"
          token: ${DB_API_TOKEN}
```

**Serveur (pseudo-code) :**

```python
@app.route('/log-event', methods=['POST'])
def log_event():
    data = request.get_json()

    # Insérer dans la base
    db.execute("""
        INSERT INTO ldap_events (event_id, timestamp, event, severity, data)
        VALUES (?, ?, ?, ?, ?)
    """, (
        data['event_id'],
        data['timestamp'],
        data['event'],
        data['severity'],
        json.dumps(data)
    ))

    return jsonify({'status': 'logged'})
```

### Exemple 2 : Déclencher un Pipeline CI/CD

**Configuration :**

```yaml
alerts:
  webhooks:
    endpoints:
      - name: "gitlab-pipeline"
        url: "https://gitlab.com/api/v4/projects/123/trigger/pipeline"
        method: "POST"
        headers:
          PRIVATE-TOKEN: ${GITLAB_TOKEN}
        payload:
          format: "custom"
          template: |
            {
              "ref": "main",
              "variables": {
                "LDAP_EVENT": "{{ event }}",
                "LDAP_SEVERITY": "{{ severity }}"
              }
            }
```

### Exemple 3 : Mise à Jour Dashboard Custom

**Configuration :**

```yaml
alerts:
  webhooks:
    endpoints:
      - name: "dashboard-update"
        url: "https://dashboard.example.com/api/metrics/update"
        method: "PUT"
        payload:
          format: "custom"
          template: |
            {
              "metric": "ldap_server_status",
              "value": {{ 1 if event == 'server_up' else 0 }},
              "timestamp": "{{ timestamp }}",
              "tags": {
                "server": "{{ server.host }}",
                "severity": "{{ severity }}"
              }
            }
```

## 🔒 Sécurité

### Meilleures Pratiques

**1. Toujours utiliser HTTPS :**

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://secure.example.com/webhook"  # ✅
      # PAS http:// ❌
```

**2. Authentification obligatoire :**

```yaml
alerts:
  webhooks:
    endpoints:
      - url: "https://api.example.com/webhook"
        auth:
          type: "bearer"
          token: ${WEBHOOK_TOKEN}  # Depuis env var
```

**3. Vérifier les certificats SSL :**

```yaml
alerts:
  webhooks:
    verify_ssl: true  # ✅ Défaut
    # verify_ssl: false  # ❌ Dangereux, seulement pour dev
```

**4. Limiter les informations sensibles :**

```yaml
alerts:
  webhooks:
    payload:
      sanitize: true
      exclude_fields:
        - "credentials"
        - "password"
        - "secret"
```

**5. Utiliser des secrets rotatifs :**

```bash
# Rotation régulière des tokens
# .env
WEBHOOK_TOKEN_V1=old-token
WEBHOOK_TOKEN_V2=new-token  # Utiliser celui-ci
```

**6. Validation côté serveur :**

```python
# Valider la signature HMAC
import hmac
import hashlib

def verify_webhook(request, secret):
    signature = request.headers.get('X-Signature')
    payload = request.data

    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, f"sha256={expected}")
```

## 🐛 Troubleshooting

### Webhook ne reçoit rien

```bash
# Tester l'URL manuellement
curl -X POST https://your-webhook.com/endpoint \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Vérifier les logs LDAP Monitor
ldap-monitor --debug monitor start

# Test webhook spécifique
ldap-monitor test webhook --name "primary"
```

### Erreur 401 Unauthorized

```yaml
# Vérifier l'authentification
alerts:
  webhooks:
    endpoints:
      - url: "..."
        auth:
          type: "bearer"
          token: "verify-this-token"
```

### Timeout

```yaml
# Augmenter le timeout
alerts:
  webhooks:
    timeout: 60  # Au lieu de 30
```

### SSL Certificate Error

```bash
# Vérifier le certificat
openssl s_client -connect webhook.example.com:443

# Temporairement désactiver (DEV ONLY)
alerts:
  webhooks:
    verify_ssl: false
```

## 📚 Ressources

- [Webhooks Specification](https://www.webhooks.org/)
- [Zapier Webhooks](https://zapier.com/apps/webhook/integrations)
- [IFTTT Webhooks](https://ifttt.com/maker_webhooks)
- [Make Webhooks](https://www.make.com/en/help/tools/webhooks)

## 🔗 Liens Connexes

- [n8n Integration](n8n.md)
- [Slack Integration](Slack.md)
- [Configuration des Alertes](../configuration/Alerts-Configuration.md)
- [CI/CD Integration](CI-CD.md)
