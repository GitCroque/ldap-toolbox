# Formats d'Export

Guide complet des formats d'export et de sortie disponibles dans LDAP Health Monitor.

## 📑 Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Format Console](#format-console)
- [Format JSON](#format-json)
- [Format HTML](#format-html)
- [Format CSV](#format-csv)
- [Format Prometheus](#format-prometheus)
- [Format LDIF](#format-ldif)
- [Format YAML](#format-yaml)
- [Comparaison des Formats](#comparaison-des-formats)
- [Exemples d'Usage](#exemples-dusage)

## Vue d'Ensemble

LDAP Health Monitor supporte plusieurs formats d'export pour s'adapter à différents cas d'usage :

| Format | Usage Principal | Sortie | Lisibilité | Automatisation |
|--------|-----------------|--------|------------|----------------|
| **Console** | Affichage terminal | stdout | ⭐⭐⭐⭐⭐ | ⭐ |
| **JSON** | Automatisation, APIs | fichier | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **HTML** | Rapports, Documentation | fichier | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **CSV** | Tableurs, Analyse | fichier | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Prometheus** | Monitoring, Métriques | HTTP | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| **LDIF** | Backup, Migration | fichier | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **YAML** | Configuration, Backup | fichier | ⭐⭐⭐⭐ | ⭐⭐⭐ |

---

## Format Console

Format de sortie par défaut pour l'affichage dans le terminal avec formatage coloré et structuré.

### Caractéristiques

- **Extension** : Aucune (stdout)
- **Encoding** : UTF-8
- **Colorisation** : Oui (ANSI colors)
- **Taille** : Variable
- **Structure** : Texte formaté avec bordures et icônes

### Spécifications

```
Format de base :
┌─────────────────────────────────────┐
│ [Icône] Titre de Section            │
├─────────────────────────────────────┤
│ Clé: Valeur                         │
│ Autre Clé: Autre Valeur             │
└─────────────────────────────────────┘

Codes couleur ANSI :
- ✅ Vert (succès) : \033[92m
- ⚠️  Jaune (warning) : \033[93m
- ❌ Rouge (erreur) : \033[91m
- 🔵 Bleu (info) : \033[94m
- ⚪ Gris (détails) : \033[90m
```

### Exemple - Health Check

```
✅ LDAP Health Check Results
════════════════════════════════════════════════════════
Server: ldap.example.com:636
Status: ✓ Healthy
Response Time: 42ms
Connection: Successful
SSL/TLS: Valid (expires in 287 days)

📊 Statistics
────────────────────────────────────────────────────────
Total Users: 1,245
Total Groups: 89
Active Users: 1,198
Inactive Users: 47 (3.8%)
Empty Groups: 3
Large Groups: 5

🔒 Security
────────────────────────────────────────────────────────
SSL Certificate: Valid
Password Policy: Enforced
Account Lockout: Enabled
Audit Logging: Active
```

### Exemple - Audit Report

```
🔍 LDAP Comprehensive Audit Report
════════════════════════════════════════════════════════
Generated: 2025-01-15 14:30:45
Duration: 3.2s
Audit Score: 87/100

⚠️  Issues Found: 12
────────────────────────────────────────────────────────
Critical: 2
Warning: 7
Info: 3

CRITICAL: Password Policy Violation
  • 2 users with passwords older than 365 days
  • Affected: uid=jdoe, uid=asmith
  💡 Recommendation: Force password reset

WARNING: Inactive Users
  • 12 users inactive for more than 90 days
  💡 Recommendation: Review and disable unused accounts

INFO: Empty Groups
  • 3 groups with no members
  💡 Recommendation: Clean up or document purpose
```

### Usage

```bash
# Sortie console par défaut
ldap-monitor audit health

# Forcer la console même si redirection
ldap-monitor audit health --format console

# Désactiver les couleurs (pour logs)
ldap-monitor audit health --no-color

# Rediriger vers fichier (couleurs désactivées automatiquement)
ldap-monitor audit health > audit.txt
```

---

## Format JSON

Format structuré pour l'automatisation, l'intégration avec d'autres outils et le stockage de données.

### Caractéristiques

- **Extension** : `.json`
- **MIME Type** : `application/json`
- **Encoding** : UTF-8
- **Indentation** : 2 espaces
- **Schema** : JSON Schema compatible

### Spécifications

```json
{
  "timestamp": "ISO 8601 datetime",
  "version": "string",
  "report_type": "health|audit|metrics|backup",
  "data": {
    "... structure spécifique au type de rapport ..."
  },
  "metadata": {
    "config_file": "string",
    "duration_seconds": "float",
    "ldap_server": "string"
  }
}
```

### Exemple - Health Check

```json
{
  "timestamp": "2025-01-15T14:30:45.123456Z",
  "version": "1.0.0",
  "report_type": "health",
  "data": {
    "status": "healthy",
    "response_time_ms": 42,
    "connection": {
      "server": "ldap.example.com",
      "port": 636,
      "ssl_enabled": true,
      "ssl_valid": true,
      "ssl_expiry_days": 287
    },
    "statistics": {
      "total_users": 1245,
      "total_groups": 89,
      "active_users": 1198,
      "inactive_users": 47,
      "empty_groups": 3,
      "large_groups": 5
    },
    "performance": {
      "bind_time_ms": 15,
      "search_time_ms": 27,
      "total_time_ms": 42
    }
  },
  "metadata": {
    "config_file": "config.yaml",
    "duration_seconds": 0.45,
    "ldap_server": "ldap.example.com:636",
    "base_dn": "dc=example,dc=com"
  }
}
```

### Exemple - Audit Report

```json
{
  "timestamp": "2025-01-15T14:30:45.123456Z",
  "version": "1.0.0",
  "report_type": "audit",
  "data": {
    "score": 87,
    "health": {
      "status": "healthy",
      "response_time_ms": 42
    },
    "issues": [
      {
        "level": "critical",
        "category": "security",
        "title": "Password Policy Violation",
        "description": "2 users with passwords older than 365 days",
        "affected_dn": [
          "uid=jdoe,ou=users,dc=example,dc=com",
          "uid=asmith,ou=users,dc=example,dc=com"
        ],
        "recommendation": "Force password reset",
        "details": {
          "threshold_days": 365,
          "oldest_password_days": 428
        }
      },
      {
        "level": "warning",
        "category": "users",
        "title": "Inactive Users",
        "description": "12 users inactive for more than 90 days",
        "recommendation": "Review and disable unused accounts",
        "details": {
          "threshold_days": 90,
          "count": 12,
          "percentage": 0.96
        }
      }
    ],
    "statistics": {
      "total_issues": 12,
      "critical_issues": 2,
      "warning_issues": 7,
      "info_issues": 3
    },
    "recommendations": [
      "Force password reset for 2 users",
      "Review and disable 12 inactive accounts",
      "Clean up 3 empty groups"
    ]
  },
  "metadata": {
    "config_file": "config.yaml",
    "duration_seconds": 3.2,
    "ldap_server": "ldap.example.com:636",
    "checks_performed": [
      "health",
      "users",
      "groups",
      "structure",
      "security",
      "consistency"
    ]
  }
}
```

### Exemple - User Export

```json
{
  "timestamp": "2025-01-15T14:30:45.123456Z",
  "version": "1.0.0",
  "report_type": "user_export",
  "data": {
    "users": [
      {
        "dn": "uid=jdoe,ou=users,dc=example,dc=com",
        "uid": "jdoe",
        "cn": "John Doe",
        "sn": "Doe",
        "givenName": "John",
        "mail": "john.doe@example.com",
        "telephoneNumber": "+1-555-0123",
        "status": "active",
        "created": "2023-01-15T10:30:00Z",
        "modified": "2024-12-01T15:45:00Z",
        "last_logon": "2025-01-14T09:15:30Z",
        "attributes": {
          "employeeNumber": "12345",
          "department": "IT",
          "title": "Software Engineer"
        }
      }
    ],
    "total_count": 1245
  },
  "metadata": {
    "config_file": "config.yaml",
    "duration_seconds": 1.8,
    "export_date": "2025-01-15T14:30:45.123456Z"
  }
}
```

### Usage

```bash
# Export JSON
ldap-monitor audit health --format json --output health.json

# Pretty print avec jq
ldap-monitor audit all --format json --output - | jq '.'

# Extraire des données spécifiques
ldap-monitor audit all --format json --output - | \
  jq '.data.issues[] | select(.level=="critical")'

# Combiner avec autres outils
ldap-monitor export users --format json --output users.json
cat users.json | jq '.data.users[].mail' | sort
```

### Validation du Schema

```bash
# Installer jsonschema
pip install jsonschema

# Valider un export
jsonschema -i audit.json audit-schema.json
```

---

## Format HTML

Format de rapport pour documentation et visualisation dans un navigateur web.

### Caractéristiques

- **Extension** : `.html`
- **MIME Type** : `text/html`
- **Encoding** : UTF-8
- **Style** : CSS intégré (Bootstrap-like)
- **JavaScript** : Optionnel (pour graphiques)
- **Responsive** : Oui

### Spécifications

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LDAP Audit Report - 2025-01-15</title>
    <style>
        /* Styles CSS intégrés */
        body { font-family: system-ui, sans-serif; }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        /* ... plus de styles ... */
    </style>
</head>
<body>
    <!-- Contenu du rapport -->
</body>
</html>
```

### Exemple - Structure HTML

```html
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <title>LDAP Audit Report - 2025-01-15</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .card {
            background: white;
            padding: 20px;
            margin-bottom: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        .metric {
            display: inline-block;
            margin: 10px 20px 10px 0;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
        }
        .metric-label {
            color: #6c757d;
            font-size: 0.9em;
        }
        table {
            width: 100%;
            border-collapse: collapse;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }
        th {
            background: #f8f9fa;
            font-weight: 600;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 LDAP Comprehensive Audit Report</h1>
        <p>Generated: 2025-01-15 14:30:45 | Server: ldap.example.com:636</p>
    </div>

    <div class="card">
        <h2>Health Status: <span class="status-healthy">✓ Healthy</span></h2>
        <div class="metrics">
            <div class="metric">
                <div class="metric-value">42ms</div>
                <div class="metric-label">Response Time</div>
            </div>
            <div class="metric">
                <div class="metric-value status-healthy">87/100</div>
                <div class="metric-label">Audit Score</div>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>📊 Statistics</h2>
        <table>
            <tr>
                <th>Metric</th>
                <th>Value</th>
                <th>Status</th>
            </tr>
            <tr>
                <td>Total Users</td>
                <td>1,245</td>
                <td><span class="status-healthy">✓</span></td>
            </tr>
            <tr>
                <td>Inactive Users</td>
                <td>47 (3.8%)</td>
                <td><span class="status-warning">⚠</span></td>
            </tr>
        </table>
    </div>

    <div class="card">
        <h2>⚠️ Issues Found (12)</h2>
        <div class="issue status-critical">
            <h3>CRITICAL: Password Policy Violation</h3>
            <p>2 users with passwords older than 365 days</p>
            <p><strong>💡 Recommendation:</strong> Force password reset</p>
        </div>
    </div>
</body>
</html>
```

### Usage

```bash
# Générer rapport HTML
ldap-monitor audit all --format html --output audit-report.html

# Ouvrir dans le navigateur
# macOS
open audit-report.html

# Linux
xdg-open audit-report.html

# Windows
start audit-report.html

# Générer et ouvrir
ldap-monitor audit all --format html --output report.html && open report.html
```

---

## Format CSV

Format de données tabulaires pour les tableurs et l'analyse de données.

### Caractéristiques

- **Extension** : `.csv`
- **MIME Type** : `text/csv`
- **Encoding** : UTF-8 with BOM
- **Séparateur** : `,` (virgule)
- **Quote** : `"` (guillemets doubles)
- **Ligne de séparation** : `\n` (LF) ou `\r\n` (CRLF)

### Spécifications

```
RFC 4180 compliant
- Première ligne = en-têtes
- Champs entre guillemets si contiennent: virgules, guillemets, sauts de ligne
- Guillemets échappés par doublement: ""
- UTF-8 avec BOM pour Excel
```

### Exemple - User Export

```csv
dn,uid,cn,sn,givenName,mail,telephoneNumber,status,department,last_logon
"uid=jdoe,ou=users,dc=example,dc=com",jdoe,John Doe,Doe,John,john.doe@example.com,+1-555-0123,active,IT,2025-01-14T09:15:30Z
"uid=jsmith,ou=users,dc=example,dc=com",jsmith,Jane Smith,Smith,Jane,jane.smith@example.com,+1-555-0124,active,Marketing,2025-01-15T08:30:00Z
"uid=rbrown,ou=users,dc=example,dc=com",rbrown,Robert Brown,Brown,Robert,robert.brown@example.com,+1-555-0125,inactive,Sales,2024-10-15T14:20:00Z
```

### Exemple - Audit Issues

```csv
level,category,title,description,affected_dn,recommendation
critical,security,Password Policy Violation,"2 users with passwords older than 365 days","uid=jdoe,ou=users,dc=example,dc=com",Force password reset
warning,users,Inactive Users,12 users inactive for more than 90 days,,Review and disable unused accounts
info,groups,Empty Groups,3 groups with no members,"cn=old-project,ou=groups,dc=example,dc=com",Clean up or document purpose
```

### Exemple - Metrics

```csv
timestamp,metric_name,value,labels
2025-01-15T14:30:45Z,ldap_users_total,1245,"server=ldap.example.com"
2025-01-15T14:30:45Z,ldap_groups_total,89,"server=ldap.example.com"
2025-01-15T14:30:45Z,ldap_response_time_ms,42,"server=ldap.example.com"
2025-01-15T14:30:45Z,ldap_inactive_users,47,"server=ldap.example.com,threshold=90days"
```

### Usage

```bash
# Export users en CSV
ldap-monitor export users --format csv --output users.csv

# Import dans Excel (avec BOM UTF-8)
# Le fichier s'ouvre directement avec encodage correct

# Analyse avec csvkit
csvstat users.csv
csvgrep -c status -m inactive users.csv

# Conversion CSV vers JSON
csvjson users.csv > users.json

# Analyse avec Python pandas
python -c "import pandas as pd; df = pd.read_csv('users.csv'); print(df.describe())"
```

---

## Format Prometheus

Format de métriques pour le monitoring et l'intégration avec Prometheus/Grafana.

### Caractéristiques

- **Protocole** : HTTP
- **Endpoint** : `/metrics`
- **MIME Type** : `text/plain; version=0.0.4`
- **Encoding** : UTF-8
- **Format** : Exposition format de Prometheus

### Spécifications

```
# HELP metric_name Description of the metric
# TYPE metric_name metric_type
metric_name{label1="value1",label2="value2"} metric_value timestamp

Metric types:
- counter: Valeur qui augmente uniquement (ex: requêtes totales)
- gauge: Valeur qui peut augmenter ou diminuer (ex: utilisateurs actifs)
- histogram: Distribution de valeurs
- summary: Distribution avec quantiles
```

### Exemple - Metrics Output

```prometheus
# HELP ldap_users_total Total number of LDAP users
# TYPE ldap_users_total gauge
ldap_users_total{server="ldap.example.com",base_dn="dc=example,dc=com"} 1245

# HELP ldap_groups_total Total number of LDAP groups
# TYPE ldap_groups_total gauge
ldap_groups_total{server="ldap.example.com",base_dn="dc=example,dc=com"} 89

# HELP ldap_active_users Number of active LDAP users
# TYPE ldap_active_users gauge
ldap_active_users{server="ldap.example.com"} 1198

# HELP ldap_inactive_users Number of inactive LDAP users
# TYPE ldap_inactive_users gauge
ldap_inactive_users{server="ldap.example.com",threshold_days="90"} 47

# HELP ldap_response_time_milliseconds LDAP server response time in milliseconds
# TYPE ldap_response_time_milliseconds gauge
ldap_response_time_milliseconds{server="ldap.example.com",operation="bind"} 15
ldap_response_time_milliseconds{server="ldap.example.com",operation="search"} 27

# HELP ldap_connection_status LDAP connection status (1=connected, 0=disconnected)
# TYPE ldap_connection_status gauge
ldap_connection_status{server="ldap.example.com"} 1

# HELP ldap_ssl_cert_expiry_days Days until SSL certificate expires
# TYPE ldap_ssl_cert_expiry_days gauge
ldap_ssl_cert_expiry_days{server="ldap.example.com"} 287

# HELP ldap_failed_auth_total Total number of failed authentication attempts
# TYPE ldap_failed_auth_total counter
ldap_failed_auth_total{server="ldap.example.com"} 3

# HELP ldap_audit_score Current audit score (0-100)
# TYPE ldap_audit_score gauge
ldap_audit_score{server="ldap.example.com"} 87

# HELP ldap_issues_total Total number of audit issues by severity
# TYPE ldap_issues_total gauge
ldap_issues_total{server="ldap.example.com",severity="critical"} 2
ldap_issues_total{server="ldap.example.com",severity="warning"} 7
ldap_issues_total{server="ldap.example.com",severity="info"} 3
```

### Usage

```bash
# Démarrer serveur Prometheus
ldap-monitor monitor prometheus --port 9090

# Accéder aux métriques
curl http://localhost:9090/metrics

# Configuration Prometheus (prometheus.yml)
scrape_configs:
  - job_name: 'ldap-monitor'
    scrape_interval: 60s
    static_configs:
      - targets: ['localhost:9090']
        labels:
          environment: 'production'

# Requêtes PromQL
# Utilisateurs inactifs
ldap_inactive_users

# Taux de changement des échecs d'auth
rate(ldap_failed_auth_total[5m])

# Score d'audit moyen
avg_over_time(ldap_audit_score[1h])
```

---

## Format LDIF

Format standard LDAP Data Interchange Format pour les backups et migrations.

### Caractéristiques

- **Extension** : `.ldif`
- **MIME Type** : `text/plain`
- **Encoding** : UTF-8
- **Standard** : RFC 2849
- **Usage** : Backup, migration, import/export

### Spécifications

```ldif
version: 1

# Commentaire
dn: distinguished_name
attribute1: value1
attribute2: value2
attribute3:: base64_encoded_value

dn: next_entry
...
```

### Exemple - Full Backup

```ldif
version: 1

dn: dc=example,dc=com
objectClass: top
objectClass: domain
dc: example

dn: ou=users,dc=example,dc=com
objectClass: top
objectClass: organizationalUnit
ou: users
description: User accounts

dn: uid=jdoe,ou=users,dc=example,dc=com
objectClass: inetOrgPerson
objectClass: posixAccount
uid: jdoe
cn: John Doe
sn: Doe
givenName: John
mail: john.doe@example.com
telephoneNumber: +1-555-0123
uidNumber: 10001
gidNumber: 10001
homeDirectory: /home/jdoe
loginShell: /bin/bash
userPassword:: e1NTSEF9base64encodedpasswordhash

dn: ou=groups,dc=example,dc=com
objectClass: top
objectClass: organizationalUnit
ou: groups

dn: cn=developers,ou=groups,dc=example,dc=com
objectClass: groupOfNames
cn: developers
description: Development team
member: uid=jdoe,ou=users,dc=example,dc=com
member: uid=jsmith,ou=users,dc=example,dc=com
```

### Usage

```bash
# Backup complet
ldap-monitor backup full --output backup.ldif --format ldif

# Backup compressé
ldap-monitor backup full --output backup.ldif
gzip backup.ldif

# Import LDIF (avec ldapadd)
ldapadd -x -D "cn=admin,dc=example,dc=com" -W -f backup.ldif

# Modification LDIF (avec ldapmodify)
ldapmodify -x -D "cn=admin,dc=example,dc=com" -W -f changes.ldif
```

---

## Format YAML

Format lisible pour configuration et exports structurés.

### Caractéristiques

- **Extension** : `.yaml` ou `.yml`
- **MIME Type** : `text/yaml`
- **Encoding** : UTF-8
- **Indentation** : 2 espaces
- **Usage** : Configuration, backup lisible

### Exemple - User Export

```yaml
version: "1.0.0"
timestamp: "2025-01-15T14:30:45Z"
export_type: users
data:
  users:
    - dn: uid=jdoe,ou=users,dc=example,dc=com
      uid: jdoe
      cn: John Doe
      sn: Doe
      givenName: John
      mail: john.doe@example.com
      telephoneNumber: +1-555-0123
      status: active
      attributes:
        employeeNumber: "12345"
        department: IT
        title: Software Engineer
    - dn: uid=jsmith,ou=users,dc=example,dc=com
      uid: jsmith
      cn: Jane Smith
      sn: Smith
      givenName: Jane
      mail: jane.smith@example.com
      status: active
  total_count: 1245
```

### Usage

```bash
# Export YAML
ldap-monitor backup full --output backup.yaml --format yaml

# Conversion YAML vers JSON
python -c "import yaml, json; print(json.dumps(yaml.safe_load(open('backup.yaml'))))"

# Validation YAML
yamllint backup.yaml
```

---

## Comparaison des Formats

### Par Cas d'Usage

**Monitoring en temps réel** :
```bash
# ✅ Console
ldap-monitor monitor metrics

# ✅ Prometheus
ldap-monitor monitor prometheus
```

**Rapports pour direction** :
```bash
# ✅ HTML
ldap-monitor audit all --format html --output report.html
```

**Automatisation/CI/CD** :
```bash
# ✅ JSON
ldap-monitor audit all --format json --output audit.json
```

**Analyse de données** :
```bash
# ✅ CSV
ldap-monitor export users --format csv --output users.csv
```

**Backup/Migration** :
```bash
# ✅ LDIF
ldap-monitor backup full --output backup.ldif
```

---

## Exemples d'Usage

### Pipeline de Reporting Complet

```bash
#!/bin/bash
# complete-reporting.sh

DATE=$(date +%Y%m%d)

# Console pour logs
ldap-monitor audit all | tee console-${DATE}.log

# JSON pour archivage
ldap-monitor audit all --format json --output audit-${DATE}.json

# HTML pour documentation
ldap-monitor audit all --format html --output report-${DATE}.html

# CSV pour analyse
ldap-monitor export users --format csv --output users-${DATE}.csv

# Backup LDIF
ldap-monitor backup full --output backup-${DATE}.ldif
```

### Monitoring Multi-Format

```bash
# Prometheus pour Grafana
ldap-monitor monitor prometheus --port 9090 &

# JSON pour archivage périodique
while true; do
    ldap-monitor monitor metrics \
        --format json \
        --output metrics-$(date +%Y%m%d-%H%M%S).json
    sleep 300
done
```

---

## Voir Aussi

- [Commandes CLI](CLI-Commands.md) - Référence des commandes
- [Options Globales](Global-Options.md) - Options et variables
- [Codes de Sortie](Exit-Codes.md) - Codes de retour
- [Exemples](../examples/Use-Cases.md) - Cas d'usage complets

---

**Note** : Tous les formats supportent UTF-8. Pour les exports volumineux, considérez la compression (gzip, bzip2) après génération.
