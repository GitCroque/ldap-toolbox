# Intégration n8n

Guide complet pour intégrer LDAP Health Monitor avec n8n, la plateforme d'automatisation workflow. Créez des automatisations complexes, connectez des services et orchestrez des processus autour de votre infrastructure LDAP.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Prérequis](#prérequis)
- [Installation n8n](#installation-n8n)
- [Configuration LDAP Monitor](#configuration-ldap-monitor)
- [Webhooks n8n](#webhooks-n8n)
- [Workflows Prédéfinis](#workflows-prédéfinis)
- [Cas d'Usage](#cas-dusage)
- [Intégrations Tierces](#intégrations-tierces)
- [Exemples Avancés](#exemples-avancés)
- [Troubleshooting](#troubleshooting)

## 📊 Vue d'ensemble

### Qu'est-ce que n8n ?

n8n est une plateforme d'automatisation open-source qui permet de :
- ✅ **Connecter des services** - 200+ intégrations natives
- ✅ **Créer des workflows** - Interface visuelle drag-and-drop
- ✅ **Automatiser des tâches** - Déclencheurs et actions complexes
- ✅ **Self-hosted** - Contrôle total de vos données

### Architecture

```
┌─────────────────────┐
│  LDAP Monitor       │
│  Webhook Sender     │
└──────────┬──────────┘
           │ HTTPS POST
           ↓
┌─────────────────────┐
│  n8n Workflow       │
│  Webhook Trigger    │
└──────────┬──────────┘
           │
           ├──→ Slack Notification
           ├──→ Create Jira Ticket
           ├──→ Update Google Sheet
           ├──→ Send Email
           └──→ Custom Logic
```

### Avantages de l'intégration

- ✅ **Workflows complexes** - Logique conditionnelle, boucles, branches
- ✅ **Multi-services** - Combinez Slack, Email, Jira, PagerDuty, etc.
- ✅ **Traitement de données** - Transformez, filtrez, agrégez
- ✅ **Historique** - Tracez toutes les exécutions
- ✅ **Personnalisable** - Code JavaScript custom si nécessaire

## 🔧 Prérequis

### Système

- **CPU** : 2 cores minimum
- **RAM** : 2 GB minimum (4 GB recommandé)
- **Disque** : 5 GB
- **OS** : Linux, macOS, Windows, Docker

### Logiciels

- **Node.js** : v18+ (si installation native)
- **Docker** : v20+ (si installation Docker)
- **LDAP Health Monitor** : v1.0.0+

## 📥 Installation n8n

### Méthode 1 : Docker (Recommandé)

**Installation simple :**

```bash
# Créer le répertoire de données
mkdir -p ~/.n8n

# Lancer n8n
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=your-secure-password \
  -e WEBHOOK_URL=https://your-domain.com \
  n8nio/n8n

# Vérifier
docker logs n8n
```

**Avec docker-compose :**

```yaml
# docker-compose.yml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n:latest
    container_name: n8n
    restart: unless-stopped
    ports:
      - "5678:5678"
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_HOST=n8n.example.com
      - N8N_PROTOCOL=https
      - NODE_ENV=production
      - WEBHOOK_URL=https://n8n.example.com/
      - GENERIC_TIMEZONE=Europe/Paris
    volumes:
      - n8n-data:/home/node/.n8n
      - ./workflows:/home/node/.n8n/workflows

volumes:
  n8n-data:
```

```bash
# Lancer
docker-compose up -d

# Vérifier
docker-compose logs -f n8n
```

**Accès :** `http://localhost:5678`

### Méthode 2 : Installation native (npm)

```bash
# Installation globale
npm install -g n8n

# Démarrer n8n
n8n start

# Ou avec configuration
N8N_BASIC_AUTH_ACTIVE=true \
N8N_BASIC_AUTH_USER=admin \
N8N_BASIC_AUTH_PASSWORD=secure-password \
n8n start
```

### Méthode 3 : Installation avec PostgreSQL

**Pour production avec base de données :**

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: postgres:14
    restart: unless-stopped
    environment:
      - POSTGRES_USER=n8n
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
      - POSTGRES_DB=n8n
    volumes:
      - postgres-data:/var/lib/postgresql/data

  n8n:
    image: n8nio/n8n:latest
    restart: unless-stopped
    depends_on:
      - postgres
    ports:
      - "5678:5678"
    environment:
      - DB_TYPE=postgresdb
      - DB_POSTGRESDB_HOST=postgres
      - DB_POSTGRESDB_PORT=5432
      - DB_POSTGRESDB_DATABASE=n8n
      - DB_POSTGRESDB_USER=n8n
      - DB_POSTGRESDB_PASSWORD=${POSTGRES_PASSWORD}
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=admin
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
    volumes:
      - n8n-data:/home/node/.n8n

volumes:
  postgres-data:
  n8n-data:
```

## ⚙️ Configuration LDAP Monitor

### Activer les webhooks n8n

**`config.yaml` :**

```yaml
alerts:
  enabled: true

  # Configuration n8n
  n8n:
    enabled: true

    # URL du webhook n8n
    webhook_url: ${N8N_WEBHOOK_URL}

    # Credentials (si webhook sécurisé)
    auth:
      type: "basic"  # basic, bearer, header
      username: ${N8N_WEBHOOK_USER}
      password: ${N8N_WEBHOOK_PASSWORD}

    # Événements à envoyer
    events:
      - alert  # Toutes les alertes
      - audit_complete  # Audits terminés
      - backup_complete  # Backups terminés
      - server_down  # Serveur down
      - server_up  # Serveur back up
      - user_locked  # Utilisateurs verrouillés
      - password_expired  # Mots de passe expirés

    # Payload
    payload:
      include_timestamp: true
      include_server_info: true
      include_metrics: true
      include_recommendations: true

    # Retry
    retry:
      enabled: true
      max_attempts: 3
      delay: 5  # secondes
```

**`.env` :**

```bash
# n8n Webhook URL
N8N_WEBHOOK_URL=https://n8n.example.com/webhook/ldap-monitor

# Authentication (si requis)
N8N_WEBHOOK_USER=ldap-monitor
N8N_WEBHOOK_PASSWORD=secure-webhook-password
```

## 🔗 Webhooks n8n

### Créer un Webhook dans n8n

**1. Créer un nouveau workflow**

1. Accédez à n8n : `http://localhost:5678`
2. Cliquez sur **"New Workflow"**
3. Nommez-le : **"LDAP Monitor Handler"**

**2. Ajouter un nœud Webhook**

1. Cliquez sur **"+"** pour ajouter un nœud
2. Cherchez **"Webhook"**
3. Configurez :
   - **HTTP Method** : POST
   - **Path** : `ldap-monitor`
   - **Authentication** : Basic Auth (optionnel mais recommandé)
   - **Response Mode** : "When Last Node Finishes"

**3. Tester le webhook**

URL du webhook : `https://n8n.example.com/webhook/ldap-monitor`

```bash
# Test simple
curl -X POST https://n8n.example.com/webhook/ldap-monitor \
  -H "Content-Type: application/json" \
  -d '{
    "event": "test",
    "message": "Test from LDAP Monitor"
  }'

# Avec authentication
curl -X POST https://n8n.example.com/webhook/ldap-monitor \
  -u "username:password" \
  -H "Content-Type: application/json" \
  -d '{
    "event": "alert",
    "severity": "critical",
    "message": "LDAP server down"
  }'
```

### Structure du Payload

**Payload envoyé par LDAP Monitor :**

```json
{
  "event": "alert",
  "timestamp": "2024-01-15T14:35:22Z",
  "severity": "critical",
  "alert_type": "server_down",
  "server": {
    "url": "ldap://ldap.example.com:389",
    "host": "ldap.example.com",
    "port": 389,
    "base_dn": "dc=example,dc=com"
  },
  "alert": {
    "title": "Serveur LDAP Inaccessible",
    "message": "Le serveur LDAP ne répond plus depuis 5 minutes",
    "duration": "5m",
    "detection_time": "2024-01-15T14:30:22Z",
    "last_success": "2024-01-15T14:25:00Z"
  },
  "metrics": {
    "response_time": null,
    "active_connections": 0,
    "failed_attempts": 5
  },
  "recommendations": [
    "Vérifier le statut du serveur",
    "Consulter les logs système",
    "Redémarrer si nécessaire"
  ],
  "links": {
    "dashboard": "https://grafana.example.com/d/ldap",
    "logs": "https://logs.example.com/ldap"
  }
}
```

## 🎯 Workflows Prédéfinis

### Workflow 1 : Alerte Multi-Canal

**Description :** Envoie une alerte vers Slack, Email et crée un ticket Jira.

**Nodes :**

```
Webhook → Switch (par sévérité) → [Slack, Email, Jira]
```

**Configuration :**

1. **Webhook** (réception)
   - Path: `ldap-monitor`
   - Method: POST

2. **Switch** (routage par sévérité)
   ```javascript
   // Règle 1 : Critical
   {{ $json.severity === 'critical' }}

   // Règle 2 : Warning
   {{ $json.severity === 'warning' }}

   // Règle 3 : Info
   {{ $json.severity === 'info' }}
   ```

3. **Slack** (pour critical)
   - Webhook URL: Votre webhook Slack
   - Channel: `#ldap-critical`
   - Message:
   ```
   🔴 ALERTE CRITIQUE LDAP

   {{ $json.alert.title }}
   {{ $json.alert.message }}

   Serveur: {{ $json.server.url }}
   Durée: {{ $json.alert.duration }}

   <{{ $json.links.dashboard }}|Dashboard> | <{{ $json.links.logs }}|Logs>
   ```

4. **Email** (pour critical)
   - To: `oncall@example.com`
   - Subject: `[CRITICAL] {{ $json.alert.title }}`
   - Body: Template HTML

5. **Jira** (pour critical)
   - Project: INFRA
   - Issue Type: Incident
   - Summary: `{{ $json.alert.title }}`
   - Description: `{{ $json.alert.message }}`
   - Priority: Highest

### Workflow 2 : Audit Automatisé avec Reporting

**Description :** Déclenche un audit, traite les résultats, envoie un rapport.

**Nodes :**

```
Webhook → HTTP Request (audit) → Process Data → Google Sheets → Slack
```

**Configuration :**

1. **Webhook** (déclencheur externe)
   - Path: `trigger-audit`

2. **HTTP Request** (déclencher l'audit LDAP)
   - Method: POST
   - URL: `http://ldap-monitor:8080/api/audit/trigger`
   - Body:
   ```json
   {
     "type": "full",
     "format": "json"
   }
   ```

3. **Wait** (attendre la fin de l'audit)
   - Wait: 5 minutes

4. **HTTP Request** (récupérer les résultats)
   - Method: GET
   - URL: `http://ldap-monitor:8080/api/audit/latest`

5. **Code** (traiter les données)
   ```javascript
   const data = items[0].json;

   return [{
     json: {
       date: new Date().toISOString(),
       total_users: data.users.total,
       active_users: data.users.active,
       inactive_users: data.users.inactive,
       total_groups: data.groups.total,
       empty_groups: data.groups.empty,
       issues_count: data.issues.length
     }
   }];
   ```

6. **Google Sheets** (enregistrer)
   - Operation: Append
   - Spreadsheet: "LDAP Audits"
   - Sheet: "Daily"

7. **Slack** (notification)
   - Message:
   ```
   ✅ Audit LDAP terminé

   📊 Statistiques:
   • Utilisateurs: {{ $json.total_users }} ({{ $json.active_users }} actifs)
   • Groupes: {{ $json.total_groups }} ({{ $json.empty_groups }} vides)
   • Problèmes détectés: {{ $json.issues_count }}

   Rapport: https://docs.google.com/spreadsheets/...
   ```

### Workflow 3 : Auto-Remediation

**Description :** Détecte un problème et tente une résolution automatique.

**Nodes :**

```
Webhook → Switch → [Unlock User, Clean Groups, Restart Service]
```

**Configuration :**

1. **Webhook**
   - Path: `ldap-alert`

2. **Switch** (type de problème)
   ```javascript
   // Utilisateur verrouillé
   {{ $json.alert_type === 'user_locked' }}

   // Groupes vides
   {{ $json.alert_type === 'empty_groups' }}

   // Service down
   {{ $json.alert_type === 'server_down' }}
   ```

3. **HTTP Request** (débloquer utilisateur)
   - Method: POST
   - URL: `http://ldap-monitor/api/user/unlock`
   - Body: `{"user": "{{ $json.user_dn }}"}`

4. **HTTP Request** (nettoyer groupes)
   - Method: POST
   - URL: `http://ldap-monitor/api/cleanup/empty-groups`

5. **SSH** (redémarrer service)
   - Host: `ldap-server.example.com`
   - Command: `sudo systemctl restart slapd`

6. **Slack** (notification succès)
   - Message: Action de remédiation effectuée

## 💡 Cas d'Usage

### Cas 1 : Escalade Progressive

**Scenario :** Escalader les alertes si non résolues.

**Workflow :**

```
Webhook → Wait 15min → Check if Resolved → If Not: Escalate
```

**Code Check Resolution :**

```javascript
// Vérifier si le serveur est de nouveau up
const response = await this.helpers.httpRequest({
  method: 'GET',
  url: 'http://ldap-monitor/api/health'
});

if (response.status === 'ok') {
  return [{ json: { resolved: true } }];
} else {
  return [{ json: { resolved: false } }];
}
```

**Escalade :**

1. **Niveau 1** (0 min) : Slack #ldap-alerts
2. **Niveau 2** (15 min) : Email oncall + Slack @channel
3. **Niveau 3** (30 min) : PagerDuty + SMS + Appel manager

### Cas 2 : Détection d'Anomalies

**Scenario :** Détecter des patterns anormaux dans les métriques.

**Workflow :**

```
Schedule (toutes les 5 min) → Get Metrics → Analyze → Alert if Anomaly
```

**Code Analyze :**

```javascript
const items = $input.all();
const currentMetrics = items[0].json;

// Récupérer l'historique (stocké dans n8n)
const historicalData = await this.getWorkflowStaticData('global');
const history = historicalData.metrics || [];

// Calculer la moyenne
const avgResponseTime = history.reduce((a, b) => a + b.response_time, 0) / history.length;

// Détecter anomalie (>2x moyenne)
if (currentMetrics.response_time > avgResponseTime * 2) {
  return [{
    json: {
      anomaly: true,
      current: currentMetrics.response_time,
      expected: avgResponseTime,
      deviation: ((currentMetrics.response_time / avgResponseTime) - 1) * 100
    }
  }];
}

// Ajouter à l'historique (garder 100 derniers)
history.push(currentMetrics);
if (history.length > 100) history.shift();
historicalData.metrics = history;

return [{ json: { anomaly: false } }];
```

### Cas 3 : Synchronisation avec AD

**Scenario :** Synchroniser les changements LDAP vers Active Directory.

**Workflow :**

```
Webhook (user_created) → Validate → Create AD User → Sync Groups → Notify
```

**Nodes :**

1. **Webhook** : Reçoit event `user_created`
2. **Code** : Valide les données
3. **HTTP Request** : Crée l'utilisateur dans AD
4. **Loop** : Pour chaque groupe
5. **HTTP Request** : Ajoute aux groupes AD
6. **Slack** : Notifie la synchro

### Cas 4 : Backup et Archivage

**Scenario :** Automatiser les backups et uploader vers S3.

**Workflow :**

```
Schedule (quotidien) → Trigger Backup → Wait → Download → Upload S3 → Cleanup
```

**Configuration :**

1. **Schedule** : Cron `0 2 * * *` (2h du matin)

2. **HTTP Request** (trigger backup)
   - POST `http://ldap-monitor/api/backup/trigger`

3. **Wait** : 10 minutes

4. **HTTP Request** (récupérer backup)
   - GET `http://ldap-monitor/api/backup/latest`
   - Binary Response: true

5. **AWS S3** (upload)
   - Bucket: `ldap-backups`
   - Key: `backups/{{ $now.format('YYYY-MM-DD') }}.ldif`

6. **HTTP Request** (cleanup anciens backups)
   - POST `http://ldap-monitor/api/backup/cleanup`
   - Body: `{"keep_days": 30}`

## 🔌 Intégrations Tierces

### Jira

**Créer un ticket automatiquement :**

```javascript
// Node Jira
{
  "fields": {
    "project": { "key": "INFRA" },
    "summary": "{{ $json.alert.title }}",
    "description": "{{ $json.alert.message }}\n\nServeur: {{ $json.server.url }}\nDurée: {{ $json.alert.duration }}",
    "issuetype": { "name": "Incident" },
    "priority": { "name": "Highest" },
    "labels": ["ldap", "auto-created"],
    "customfield_10001": "{{ $json.links.dashboard }}"  // Link to dashboard
  }
}
```

### PagerDuty

**Déclencher un incident :**

```javascript
// Node HTTP Request vers PagerDuty
{
  "method": "POST",
  "url": "https://events.pagerduty.com/v2/enqueue",
  "headers": {
    "Authorization": "Token token={{ $credentials.pagerduty_api_key }}"
  },
  "body": {
    "routing_key": "{{ $credentials.integration_key }}",
    "event_action": "trigger",
    "payload": {
      "summary": "{{ $json.alert.title }}",
      "severity": "{{ $json.severity }}",
      "source": "ldap-monitor",
      "custom_details": {
        "server": "{{ $json.server.url }}",
        "duration": "{{ $json.alert.duration }}"
      }
    }
  }
}
```

### ServiceNow

**Créer un incident :**

```javascript
// Node ServiceNow
{
  "short_description": "{{ $json.alert.title }}",
  "description": "{{ $json.alert.message }}",
  "urgency": "1",  // High
  "impact": "1",   // High
  "category": "Infrastructure",
  "subcategory": "LDAP",
  "assignment_group": "Infrastructure Team"
}
```

### Datadog

**Envoyer des événements :**

```javascript
// Node HTTP Request vers Datadog
{
  "method": "POST",
  "url": "https://api.datadoghq.com/api/v1/events",
  "headers": {
    "DD-API-KEY": "{{ $credentials.datadog_api_key }}"
  },
  "body": {
    "title": "{{ $json.alert.title }}",
    "text": "{{ $json.alert.message }}",
    "priority": "normal",
    "tags": [
      "source:ldap-monitor",
      "severity:{{ $json.severity }}",
      "server:{{ $json.server.host }}"
    ],
    "alert_type": "{{ $json.severity }}"
  }
}
```

## 🎨 Exemples Avancés

### Workflow Complexe : Gestion Complète d'Incident

**Architecture :**

```
Webhook
  ├─→ [Critical] → PagerDuty + Jira + Slack @channel
  ├─→ [Warning]  → Jira + Slack
  └─→ [Info]     → Log to Database
       ↓
  Attempt Auto-Remediation
       ├─→ Success → Close Jira + Notify
       └─→ Failed  → Escalate
```

**Export JSON du workflow :**

```json
{
  "name": "LDAP Incident Management",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "ldap-incident",
        "responseMode": "onReceived",
        "authentication": "basicAuth"
      }
    },
    {
      "name": "Switch Severity",
      "type": "n8n-nodes-base.switch",
      "parameters": {
        "rules": {
          "rules": [
            {
              "conditions": {
                "conditions": [
                  {
                    "leftValue": "={{ $json.severity }}",
                    "rightValue": "critical",
                    "operation": "equals"
                  }
                ]
              },
              "renameOutput": "critical"
            }
          ]
        }
      }
    }
  ]
}
```

### Code JavaScript Avancé

**Traitement de données complexe :**

```javascript
// Node Function
const items = $input.all();
const alert = items[0].json;

// Récupérer l'historique des alertes
const staticData = this.getWorkflowStaticData('global');
staticData.alerts = staticData.alerts || [];

// Vérifier si c'est une alerte répétée
const isDuplicate = staticData.alerts.some(a =>
  a.alert_type === alert.alert_type &&
  a.server.url === alert.server.url &&
  (Date.now() - new Date(a.timestamp).getTime()) < 3600000  // 1 heure
);

if (isDuplicate) {
  // Incrémenter le compteur
  const existingAlert = staticData.alerts.find(a =>
    a.alert_type === alert.alert_type &&
    a.server.url === alert.server.url
  );
  existingAlert.count = (existingAlert.count || 1) + 1;
  existingAlert.last_occurrence = alert.timestamp;

  return [{
    json: {
      ...alert,
      is_duplicate: true,
      occurrence_count: existingAlert.count
    }
  }];
} else {
  // Nouvelle alerte
  staticData.alerts.push({
    ...alert,
    count: 1,
    first_occurrence: alert.timestamp
  });

  // Limiter à 100 alertes
  if (staticData.alerts.length > 100) {
    staticData.alerts.shift();
  }

  return [{
    json: {
      ...alert,
      is_duplicate: false,
      occurrence_count: 1
    }
  }];
}
```

## 🐛 Troubleshooting

### Webhook ne reçoit pas les données

```bash
# Vérifier l'URL du webhook
echo $N8N_WEBHOOK_URL

# Tester manuellement
curl -X POST $N8N_WEBHOOK_URL \
  -H "Content-Type: application/json" \
  -d '{"test": true}'

# Vérifier les logs n8n
docker logs n8n

# Vérifier les logs LDAP Monitor
ldap-monitor --debug monitor start --n8n
```

### Erreur d'authentification

**Si webhook sécurisé :**

```yaml
# Dans config.yaml
alerts:
  n8n:
    auth:
      type: "basic"
      username: "correct-username"
      password: "correct-password"
```

### Workflow ne s'exécute pas

**Vérifier dans n8n UI :**
1. Executions → View failed executions
2. Voir les erreurs dans chaque node
3. Vérifier les credentials
4. Tester manuellement chaque node

### Performance lente

**Optimisations :**

```yaml
# Dans n8n (environment)
N8N_PAYLOAD_SIZE_MAX=16  # MB
EXECUTIONS_DATA_PRUNE=true
EXECUTIONS_DATA_MAX_AGE=168  # 7 jours
```

## 📚 Ressources

- [n8n Documentation](https://docs.n8n.io/)
- [n8n Community](https://community.n8n.io/)
- [Workflow Templates](https://n8n.io/workflows)
- [n8n GitHub](https://github.com/n8n-io/n8n)

## 🔗 Liens Connexes

- [Webhooks Génériques](Webhooks.md)
- [Configuration des Alertes](../configuration/Alerts-Configuration.md)
- [Slack Integration](Slack.md)
- [CI/CD Integration](CI-CD.md)
