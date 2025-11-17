# Génération de rapports d'audit

## Introduction

Les rapports d'audit sont essentiels pour communiquer les résultats des audits, suivre les tendances et documenter l'état de votre infrastructure LDAP. Ce guide couvre tous les formats de rapports disponibles et comment les personnaliser.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Format Console](#format-console)
3. [Format JSON](#format-json)
4. [Format HTML](#format-html)
5. [Format CSV](#format-csv)
6. [Format Prometheus](#format-prometheus)
7. [Personnalisation des rapports](#personnalisation-des-rapports)
8. [Automatisation](#automatisation)
9. [Intégrations](#intégrations)
10. [Exemples pratiques](#exemples-pratiques)
11. [Tableaux de bord](#tableaux-de-bord)
12. [Bonnes pratiques](#bonnes-pratiques)

## Vue d'ensemble

### Formats disponibles

| Format | Usage | Avantages | Cas d'utilisation |
|--------|-------|-----------|-------------------|
| Console | Terminal | Lecture immédiate | Vérification rapide, debugging |
| JSON | Programmation | Traitement automatisé | Intégration, archivage |
| HTML | Documentation | Visuel, partageable | Rapports, présentations |
| CSV | Analyse | Excel/LibreOffice | Statistiques, graphiques |
| Prometheus | Monitoring | Métriques temps réel | Alerting, dashboards |

### Architecture des reporters

```
┌────────────────┐
│  AuditReport   │ (Modèle de données)
└───────┬────────┘
        │
    ┌───▼──────────────────────┐
    │     Reporters            │
    ├──────────────────────────┤
    │ • ConsoleReporter        │
    │ • JSONReporter           │
    │ • HTMLReporter           │
    │ • CSVReporter            │
    │ • PrometheusReporter     │
    └───┬──────────────────────┘
        │
    ┌───▼──────────┐
    │    Output    │
    └──────────────┘
```

### Structure d'un rapport

```python
AuditReport {
    timestamp: datetime
    score: int (0-100)
    health: HealthCheckResult
    issues: List[AuditIssue]
    statistics: Dict
    recommendations: List[str]
}
```

## Format Console

### Utilisation de base

```bash
ldap-health-monitor audit all
```

**Sortie exemple :**
```
┌───────────────────────────────────────┐
│      LDAP Health Check                │
├───────────────────────────────────────┤
│ Server Status: ✅ Healthy             │
│ Response Time: 127ms                  │
│                                       │
│ LDAP server is healthy                │
└───────────────────────────────────────┘

📊 Statistics:
┌──────────────────┬───────┐
│ Object Type      │ Count │
├──────────────────┼───────┤
│ Users Total      │  1234 │
│ Groups Total     │   156 │
│ OUs Total        │    23 │
└──────────────────┴───────┘

📊 Audit Report - 2025-11-17 10:30:45
Score: 85/100

Groups
  ⚠️  12 empty groups
     Found 12 groups with no members
     💡 Remove unused empty groups

  ℹ️  5 large groups
     Found 5 groups with more than 100 members
     💡 Consider splitting large groups

Security
  ⚠️  SSL certificate expiring soon
     Certificate expires in 25 days
     💡 Plan certificate renewal

💡 Recommendations:
  • Remove unused empty groups
  • Plan certificate renewal
  • Consider splitting large groups for better management
```

### Personnalisation de la sortie console

**Codes de couleur :**
```python
# src/reporters/console.py

from rich.console import Console
from rich.theme import Theme

custom_theme = Theme({
    "info": "cyan",
    "warning": "yellow",
    "error": "bold red",
    "success": "bold green",
})

console = Console(theme=custom_theme)
```

**Filtrage par niveau :**
```bash
# Afficher seulement les warnings et critical
ldap-health-monitor audit all | grep -E "WARNING|CRITICAL"

# Afficher avec moins de détails
ldap-health-monitor audit all --verbose=false
```

### Options de formatage

**Compact :**
```bash
ldap-health-monitor audit health --format console --style compact
```

**Détaillé :**
```bash
ldap-health-monitor audit all --format console --style detailed
```

**Tableau seulement :**
```bash
ldap-health-monitor audit groups --format console --style table
```

## Format JSON

### Structure JSON complète

```json
{
  "timestamp": "2025-11-17T10:30:45.123456",
  "score": 85,
  "health": {
    "status": "healthy",
    "response_time": 127.5,
    "message": "LDAP server is healthy",
    "details": {
      "response_time_ms": 127.5,
      "server_info": {
        "vendor": "OpenLDAP",
        "version": "2.4.57",
        "hostname": "ldap.example.com"
      },
      "statistics": {
        "users_total": 1234,
        "groups_total": 156,
        "ous_total": 23
      },
      "issues": []
    }
  },
  "issues": [
    {
      "level": "warning",
      "category": "groups",
      "title": "12 empty groups",
      "description": "Found 12 groups with no members",
      "recommendation": "Remove unused empty groups",
      "details": {
        "count": 12,
        "sample": [
          "cn=OldProject,ou=Groups,dc=example,dc=com",
          "cn=TempTeam,ou=Groups,dc=example,dc=com"
        ]
      }
    },
    {
      "level": "warning",
      "category": "security",
      "title": "SSL certificate expiring soon",
      "description": "Certificate expires in 25 days",
      "recommendation": "Plan certificate renewal",
      "details": {
        "days_remaining": 25,
        "expiry_date": "2025-12-12"
      }
    }
  ],
  "statistics": {
    "users_total": 1234,
    "groups_total": 156,
    "ous_total": 23,
    "empty_groups": 12
  },
  "recommendations": [
    "Remove unused empty groups",
    "Plan certificate renewal",
    "Consider splitting large groups for better management"
  ]
}
```

### Génération de rapport JSON

```bash
ldap-health-monitor audit all --format json --output report.json
```

### Traitement avec jq

**Extraire le score :**
```bash
jq -r '.score' report.json
```

**Lister les problèmes critiques :**
```bash
jq -r '.issues[] | select(.level=="critical") | .title' report.json
```

**Compter les problèmes par niveau :**
```bash
jq -r '.issues | group_by(.level) | map({level: .[0].level, count: length})' report.json
```

**Extraire les statistiques :**
```bash
jq -r '.statistics' report.json
```

**Créer un résumé :**
```bash
jq -r '"Score: \(.score)/100\nIssues: \(.issues | length)\nCritical: \([.issues[] | select(.level=="critical")] | length)"' report.json
```

### Validation du schéma JSON

**Schema JSON :**
```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "LDAP Audit Report",
  "type": "object",
  "required": ["timestamp", "score", "issues"],
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time"
    },
    "score": {
      "type": "integer",
      "minimum": 0,
      "maximum": 100
    },
    "issues": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["level", "category", "title"],
        "properties": {
          "level": {
            "type": "string",
            "enum": ["info", "warning", "critical"]
          },
          "category": {
            "type": "string"
          },
          "title": {
            "type": "string"
          }
        }
      }
    }
  }
}
```

**Validation :**
```bash
jsonschema -i report.json schema.json
```

## Format HTML

### Génération de rapport HTML

```bash
ldap-health-monitor audit all --format html --output report.html
```

### Structure du rapport HTML

**Template par défaut :**
```html
<!DOCTYPE html>
<html>
<head>
    <title>LDAP Audit Report</title>
    <meta charset="utf-8">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h1 {
            color: #333;
            border-bottom: 3px solid #007bff;
            padding-bottom: 10px;
        }
        .score {
            font-size: 48px;
            font-weight: bold;
            text-align: center;
            margin: 20px 0;
        }
        .score.good { color: #28a745; }
        .score.warning { color: #ffc107; }
        .score.critical { color: #dc3545; }

        .issue {
            margin: 15px 0;
            padding: 15px;
            border-left: 4px solid;
            border-radius: 4px;
        }
        .issue.info {
            border-color: #17a2b8;
            background: #d1ecf1;
        }
        .issue.warning {
            border-color: #ffc107;
            background: #fff3cd;
        }
        .issue.critical {
            border-color: #dc3545;
            background: #f8d7da;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        .stat-box {
            padding: 20px;
            background: #f8f9fa;
            border-radius: 4px;
            text-align: center;
        }
        .stat-box .value {
            font-size: 32px;
            font-weight: bold;
            color: #007bff;
        }
        .stat-box .label {
            color: #666;
            margin-top: 5px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #007bff;
            color: white;
            font-weight: bold;
        }
        tr:hover {
            background: #f5f5f5;
        }

        .recommendations {
            background: #e7f3ff;
            padding: 20px;
            border-radius: 4px;
            margin: 20px 0;
        }
        .recommendations ul {
            margin: 10px 0;
        }
        .recommendations li {
            margin: 5px 0;
        }

        .metadata {
            color: #666;
            font-size: 0.9em;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 LDAP Audit Report</h1>

        <div class="metadata">
            <p><strong>Generated:</strong> {{ report.timestamp }}</p>
            <p><strong>Server:</strong> ldap.example.com</p>
        </div>

        <div class="score {{ score_class }}">
            {{ report.score }}/100
        </div>

        <h2>📈 Statistics</h2>
        <div class="stats">
            <div class="stat-box">
                <div class="value">{{ report.statistics.users_total }}</div>
                <div class="label">Total Users</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ report.statistics.groups_total }}</div>
                <div class="label">Total Groups</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ report.statistics.ous_total }}</div>
                <div class="label">Organizational Units</div>
            </div>
            <div class="stat-box">
                <div class="value">{{ report.issues|length }}</div>
                <div class="label">Issues Found</div>
            </div>
        </div>

        <h2>🔍 Issues</h2>
        {% for issue in report.issues %}
        <div class="issue {{ issue.level }}">
            <h3>{{ issue.title }}</h3>
            <p>{{ issue.description }}</p>
            {% if issue.recommendation %}
            <p><strong>💡 Recommendation:</strong> {{ issue.recommendation }}</p>
            {% endif %}
            {% if issue.details %}
            <details>
                <summary>Details</summary>
                <pre>{{ issue.details|tojson(indent=2) }}</pre>
            </details>
            {% endif %}
        </div>
        {% endfor %}

        <div class="recommendations">
            <h2>💡 Recommendations</h2>
            <ul>
            {% for rec in report.recommendations %}
                <li>{{ rec }}</li>
            {% endfor %}
            </ul>
        </div>

        <div class="metadata">
            <p>Generated by LDAP Health Monitor v1.0.0</p>
        </div>
    </div>
</body>
</html>
```

### Personnalisation du template

**Créer un template personnalisé :**
```python
# custom_template.py

from jinja2 import Template

custom_template = """
<!DOCTYPE html>
<html>
<head>
    <title>{{ company_name }} - LDAP Audit</title>
    <link rel="stylesheet" href="corporate-style.css">
</head>
<body>
    <header>
        <img src="logo.png" alt="Company Logo">
        <h1>LDAP Infrastructure Audit Report</h1>
    </header>

    <main>
        <!-- Custom content -->
        {{ custom_content }}
    </main>

    <footer>
        <p>Confidential - {{ company_name }}</p>
    </footer>
</body>
</html>
"""

# Utilisation
template = Template(custom_template)
html = template.render(
    company_name="Acme Corp",
    custom_content=report_content
)
```

### Export PDF depuis HTML

```bash
#!/bin/bash
# generate-pdf-report.sh

# Générer HTML
ldap-health-monitor audit all --format html --output report.html

# Convertir en PDF avec wkhtmltopdf
wkhtmltopdf \
  --enable-local-file-access \
  --page-size A4 \
  --margin-top 10mm \
  --margin-bottom 10mm \
  report.html \
  report.pdf

echo "PDF report generated: report.pdf"
```

**Avec Puppeteer (Node.js) :**
```javascript
// generate-pdf.js
const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch();
  const page = await browser.newPage();

  await page.goto('file:///path/to/report.html', {
    waitUntil: 'networkidle0'
  });

  await page.pdf({
    path: 'report.pdf',
    format: 'A4',
    printBackground: true,
    margin: {
      top: '10mm',
      bottom: '10mm',
      left: '10mm',
      right: '10mm'
    }
  });

  await browser.close();
  console.log('PDF generated: report.pdf');
})();
```

## Format CSV

### Génération de rapport CSV

```bash
ldap-health-monitor audit groups --format csv --output groups.csv
```

**Sortie exemple :**
```csv
level,category,title,description,recommendation,count,sample
warning,groups,"12 empty groups","Found 12 groups with no members","Remove unused empty groups",12,"cn=OldProject,ou=Groups,dc=example,dc=com;cn=TempTeam,ou=Groups,dc=example,dc=com"
info,groups,"5 large groups","Found 5 groups with more than 100 members","Consider splitting large groups",5,"cn=AllEmployees,ou=Groups,dc=example,dc=com;cn=Engineering,ou=Groups,dc=example,dc=com"
```

### Analyse avec Excel/LibreOffice

**Import dans Excel :**
1. Ouvrir Excel
2. Données → À partir d'un fichier texte/CSV
3. Sélectionner groups.csv
4. Configurer le délimiteur (virgule)
5. Importer

**Créer un tableau croisé dynamique :**
```
Lignes: category
Colonnes: level
Valeurs: Nombre de title
```

### Graphiques avec Python

```python
#!/usr/bin/env python3
# analyze-csv-report.py

import pandas as pd
import matplotlib.pyplot as plt

# Charger le CSV
df = pd.read_csv('groups.csv')

# Compter par niveau
level_counts = df['level'].value_counts()

# Créer un graphique en barres
plt.figure(figsize=(10, 6))
level_counts.plot(kind='bar', color=['blue', 'orange', 'red'])
plt.title('Issues by Level')
plt.xlabel('Level')
plt.ylabel('Count')
plt.xticks(rotation=0)
plt.tight_layout()
plt.savefig('issues-by-level.png')

# Compter par catégorie
category_counts = df['category'].value_counts()

# Graphique en camembert
plt.figure(figsize=(10, 6))
category_counts.plot(kind='pie', autopct='%1.1f%%')
plt.title('Issues by Category')
plt.ylabel('')
plt.tight_layout()
plt.savefig('issues-by-category.png')

print("Graphs generated:")
print("  - issues-by-level.png")
print("  - issues-by-category.png")
```

### Export vers base de données

```python
#!/usr/bin/env python3
# export-to-database.py

import pandas as pd
import sqlite3

# Charger le CSV
df = pd.read_csv('audit-report.csv')

# Connexion à la base de données
conn = sqlite3.connect('ldap-audits.db')

# Créer la table
df.to_sql('audit_issues', conn, if_exists='append', index=False)

# Requêtes
print("Critical issues:")
critical = pd.read_sql_query(
    "SELECT * FROM audit_issues WHERE level='critical'",
    conn
)
print(critical)

conn.close()
```

## Format Prometheus

### Configuration Prometheus

```bash
# Démarrer le serveur de métriques
ldap-health-monitor monitor prometheus --port 9090
```

**Métriques exposées :**
```prometheus
# HELP ldap_health_status LDAP server health status (0=unknown, 1=healthy, 2=warning, 3=critical)
# TYPE ldap_health_status gauge
ldap_health_status 1

# HELP ldap_response_time_milliseconds LDAP server response time in milliseconds
# TYPE ldap_response_time_milliseconds gauge
ldap_response_time_milliseconds 127.5

# HELP ldap_users_total Total number of LDAP users
# TYPE ldap_users_total gauge
ldap_users_total 1234

# HELP ldap_groups_total Total number of LDAP groups
# TYPE ldap_groups_total gauge
ldap_groups_total 156

# HELP ldap_audit_issues_total Total number of audit issues by level
# TYPE ldap_audit_issues_total gauge
ldap_audit_issues_total{level="info"} 5
ldap_audit_issues_total{level="warning"} 3
ldap_audit_issues_total{level="critical"} 0

# HELP ldap_audit_score LDAP audit score (0-100)
# TYPE ldap_audit_score gauge
ldap_audit_score 85
```

### Configuration du scraping

**prometheus.yml :**
```yaml
scrape_configs:
  - job_name: 'ldap-health-monitor'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 60s
```

### Requêtes PromQL

**Alertes :**
```promql
# Alerte si le score < 70
ldap_audit_score < 70

# Alerte si temps de réponse > 500ms
ldap_response_time_milliseconds > 500

# Alerte si problèmes critiques
ldap_audit_issues_total{level="critical"} > 0
```

### Règles d'alerte

**alert.rules :**
```yaml
groups:
  - name: ldap_alerts
    interval: 60s
    rules:
      - alert: LDAPAuditScoreLow
        expr: ldap_audit_score < 70
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LDAP audit score is low"
          description: "Score is {{ $value }}/100"

      - alert: LDAPCriticalIssues
        expr: ldap_audit_issues_total{level="critical"} > 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "LDAP has critical issues"
          description: "{{ $value }} critical issues detected"

      - alert: LDAPHighResponseTime
        expr: ldap_response_time_milliseconds > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "LDAP response time is high"
          description: "Response time is {{ $value }}ms"
```

## Personnalisation des rapports

### Créer un reporter personnalisé

```python
# custom_reporter.py

from typing import Any, Dict
from src.core.models import AuditReport

class CustomReporter:
    """Reporter personnalisé pour format spécifique"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def export_report(self, report: AuditReport, output_path: str):
        """Exporte le rapport dans un format personnalisé"""

        # Format personnalisé (exemple: Markdown)
        markdown = self._generate_markdown(report)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown)

    def _generate_markdown(self, report: AuditReport) -> str:
        """Génère un rapport Markdown"""

        md = f"""# LDAP Audit Report

**Date:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
**Score:** {report.score}/100

## Summary

- Total Issues: {len(report.issues)}
- Critical: {sum(1 for i in report.issues if i.level == 'critical')}
- Warnings: {sum(1 for i in report.issues if i.level == 'warning')}
- Info: {sum(1 for i in report.issues if i.level == 'info')}

## Statistics

| Metric | Value |
|--------|-------|
"""

        for key, value in report.statistics.items():
            md += f"| {key.replace('_', ' ').title()} | {value} |\n"

        md += "\n## Issues\n\n"

        for issue in report.issues:
            emoji = {'info': 'ℹ️', 'warning': '⚠️', 'critical': '🔴'}.get(issue.level, '')
            md += f"### {emoji} {issue.title}\n\n"
            md += f"**Level:** {issue.level.upper()}\n\n"
            md += f"{issue.description}\n\n"
            if issue.recommendation:
                md += f"**Recommendation:** {issue.recommendation}\n\n"

        md += "## Recommendations\n\n"
        for rec in report.recommendations:
            md += f"- {rec}\n"

        return md
```

### Filtres et transformations

**Filtrer par niveau :**
```python
def filter_by_level(report: AuditReport, level: str) -> AuditReport:
    """Filtrer les problèmes par niveau"""
    filtered_issues = [i for i in report.issues if i.level == level]

    return AuditReport(
        timestamp=report.timestamp,
        score=report.score,
        health=report.health,
        issues=filtered_issues,
        statistics=report.statistics,
        recommendations=report.recommendations
    )

# Utilisation
critical_only = filter_by_level(report, 'critical')
```

**Grouper par catégorie :**
```python
def group_by_category(report: AuditReport) -> Dict[str, List[AuditIssue]]:
    """Grouper les problèmes par catégorie"""
    from collections import defaultdict

    grouped = defaultdict(list)
    for issue in report.issues:
        grouped[issue.category].append(issue)

    return dict(grouped)
```

## Automatisation

### Script d'automatisation complet

```bash
#!/bin/bash
# automated-reporting.sh

CONFIG="/etc/ldap-health-monitor/config.yaml"
OUTPUT_DIR="/var/reports/ldap/$(date +%Y/%m)"
DATE=$(date +%Y-%m-%d)

mkdir -p "$OUTPUT_DIR"

echo "=== Automated LDAP Audit Reporting ==="
echo "Date: $DATE"
echo "Output: $OUTPUT_DIR"
echo ""

# 1. Audit complet
echo "Running full audit..."
ldap-health-monitor -c "$CONFIG" audit all \
  --format json \
  --output "$OUTPUT_DIR/audit-$DATE.json"

# 2. Générer tous les formats
echo "Generating reports..."

# HTML
ldap-health-monitor -c "$CONFIG" audit all \
  --format html \
  --output "$OUTPUT_DIR/audit-$DATE.html"

# CSV
ldap-health-monitor -c "$CONFIG" audit all \
  --format csv \
  --output "$OUTPUT_DIR/audit-$DATE.csv"

# PDF
wkhtmltopdf "$OUTPUT_DIR/audit-$DATE.html" "$OUTPUT_DIR/audit-$DATE.pdf"

# 3. Générer des graphiques
echo "Generating charts..."
python3 /usr/local/bin/generate-charts.py "$OUTPUT_DIR/audit-$DATE.csv"

# 4. Extraire métriques clés
echo "Extracting key metrics..."
SCORE=$(jq -r '.score' "$OUTPUT_DIR/audit-$DATE.json")
CRITICAL=$(jq -r '[.issues[] | select(.level=="critical")] | length' "$OUTPUT_DIR/audit-$DATE.json")
WARNINGS=$(jq -r '[.issues[] | select(.level=="warning")] | length' "$OUTPUT_DIR/audit-$DATE.json")

# 5. Créer un résumé
cat > "$OUTPUT_DIR/summary-$DATE.txt" << EOF
LDAP Audit Summary - $DATE
========================================

Score: $SCORE/100
Critical Issues: $CRITICAL
Warnings: $WARNINGS

Status: $([ $SCORE -ge 80 ] && echo "GOOD" || echo "NEEDS ATTENTION")

Full report: audit-$DATE.html
EOF

# 6. Envoyer les notifications
echo "Sending notifications..."

if [ $CRITICAL -gt 0 ]; then
  # Notification urgente
  mail -s "🔴 CRITICAL: LDAP Audit Found $CRITICAL Critical Issues" \
    -a "$OUTPUT_DIR/audit-$DATE.pdf" \
    admin@example.com < "$OUTPUT_DIR/summary-$DATE.txt"
elif [ $SCORE -lt 70 ]; then
  # Avertissement
  mail -s "⚠️ LDAP Audit Score: $SCORE/100" \
    -a "$OUTPUT_DIR/audit-$DATE.pdf" \
    admin@example.com < "$OUTPUT_DIR/summary-$DATE.txt"
else
  # Rapport normal
  mail -s "✅ LDAP Audit Complete: $SCORE/100" \
    -a "$OUTPUT_DIR/summary-$DATE.txt" \
    team@example.com <<< "Daily audit completed successfully. Score: $SCORE/100"
fi

# 7. Archiver les anciens rapports
find /var/reports/ldap -type f -name "audit-*.json" -mtime +90 -delete

echo "Done!"
```

### Crontab

```cron
# Audit quotidien à 2h du matin
0 2 * * * /usr/local/bin/automated-reporting.sh

# Audit hebdomadaire détaillé (lundi à 6h)
0 6 * * 1 /usr/local/bin/weekly-detailed-audit.sh

# Audit mensuel complet (1er du mois)
0 8 1 * * /usr/local/bin/monthly-full-audit.sh
```

## Intégrations

### Slack

```bash
#!/bin/bash
# send-to-slack.sh

WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
REPORT_FILE="$1"

SCORE=$(jq -r '.score' "$REPORT_FILE")
CRITICAL=$(jq -r '[.issues[] | select(.level=="critical")] | length' "$REPORT_FILE")

# Déterminer la couleur
if [ $CRITICAL -gt 0 ]; then
  COLOR="danger"
  EMOJI=":red_circle:"
elif [ $SCORE -lt 70 ]; then
  COLOR="warning"
  EMOJI=":warning:"
else
  COLOR="good"
  EMOJI=":white_check_mark:"
fi

# Créer le message
MESSAGE=$(cat <<EOF
{
  "attachments": [
    {
      "color": "$COLOR",
      "title": "$EMOJI LDAP Audit Report",
      "fields": [
        {
          "title": "Score",
          "value": "$SCORE/100",
          "short": true
        },
        {
          "title": "Critical Issues",
          "value": "$CRITICAL",
          "short": true
        }
      ],
      "footer": "LDAP Health Monitor",
      "ts": $(date +%s)
    }
  ]
}
EOF
)

# Envoyer à Slack
curl -X POST -H 'Content-type: application/json' \
  --data "$MESSAGE" \
  "$WEBHOOK_URL"
```

### Microsoft Teams

```python
#!/usr/bin/env python3
# send-to-teams.py

import json
import requests
from datetime import datetime

def send_to_teams(report_file, webhook_url):
    """Envoie le rapport à Microsoft Teams"""

    with open(report_file) as f:
        report = json.load(f)

    # Déterminer la couleur
    if any(i['level'] == 'critical' for i in report['issues']):
        color = "FF0000"  # Rouge
        status = "🔴 Critical Issues"
    elif report['score'] < 70:
        color = "FFA500"  # Orange
        status = "⚠️ Needs Attention"
    else:
        color = "00FF00"  # Vert
        status = "✅ Good"

    # Créer le message
    message = {
        "@type": "MessageCard",
        "@context": "https://schema.org/extensions",
        "themeColor": color,
        "title": "LDAP Audit Report",
        "summary": f"Score: {report['score']}/100",
        "sections": [
            {
                "activityTitle": status,
                "facts": [
                    {"name": "Score", "value": f"{report['score']}/100"},
                    {"name": "Total Issues", "value": str(len(report['issues']))},
                    {"name": "Critical", "value": str(sum(1 for i in report['issues'] if i['level'] == 'critical'))},
                    {"name": "Warnings", "value": str(sum(1 for i in report['issues'] if i['level'] == 'warning'))},
                ],
                "markdown": True
            }
        ],
        "potentialAction": [
            {
                "@type": "OpenUri",
                "name": "View Full Report",
                "targets": [
                    {"os": "default", "uri": "https://reports.example.com/ldap/latest"}
                ]
            }
        ]
    }

    # Envoyer
    response = requests.post(webhook_url, json=message)
    response.raise_for_status()

if __name__ == "__main__":
    import sys
    send_to_teams(sys.argv[1], sys.argv[2])
```

### Grafana

**Dashboard JSON :**
```json
{
  "dashboard": {
    "title": "LDAP Health Monitor",
    "panels": [
      {
        "title": "Audit Score",
        "type": "gauge",
        "targets": [
          {
            "expr": "ldap_audit_score"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "min": 0,
            "max": 100,
            "thresholds": {
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 70, "color": "yellow"},
                {"value": 85, "color": "green"}
              ]
            }
          }
        }
      },
      {
        "title": "Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "ldap_response_time_milliseconds"
          }
        ]
      },
      {
        "title": "Issues by Level",
        "type": "piechart",
        "targets": [
          {
            "expr": "ldap_audit_issues_total"
          }
        ]
      }
    ]
  }
}
```

## Exemples pratiques

### Exemple 1 : Rapport exécutif mensuel

```python
#!/usr/bin/env python3
# executive-monthly-report.py

import json
from datetime import datetime
import matplotlib.pyplot as plt
from pathlib import Path

def generate_executive_report(month, year):
    """Génère un rapport exécutif mensuel"""

    report_dir = Path(f"/var/reports/ldap/{year}/{month:02d}")
    reports = list(report_dir.glob("audit-*.json"))

    # Collecter les données du mois
    scores = []
    dates = []

    for report_file in sorted(reports):
        with open(report_file) as f:
            data = json.load(f)
            scores.append(data['score'])
            dates.append(datetime.fromisoformat(data['timestamp']))

    # Créer les graphiques
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))

    # Graphique 1: Évolution du score
    axes[0, 0].plot(dates, scores, marker='o')
    axes[0, 0].set_title('Audit Score Evolution')
    axes[0, 0].set_ylabel('Score')
    axes[0, 0].grid(True)

    # Graphique 2: Distribution des scores
    axes[0, 1].hist(scores, bins=10, color='skyblue', edgecolor='black')
    axes[0, 1].set_title('Score Distribution')
    axes[0, 1].set_xlabel('Score')
    axes[0, 1].set_ylabel('Frequency')

    # Graphique 3: Tendance
    from numpy import polyfit, poly1d
    z = polyfit(range(len(scores)), scores, 1)
    p = poly1d(z)
    axes[1, 0].plot(dates, scores, 'o', label='Actual')
    axes[1, 0].plot(dates, p(range(len(scores))), 'r--', label='Trend')
    axes[1, 0].set_title('Trend Analysis')
    axes[1, 0].legend()
    axes[1, 0].grid(True)

    # Graphique 4: Statistiques
    stats_text = f"""
    Monthly Statistics:

    Average Score: {sum(scores)/len(scores):.1f}
    Minimum Score: {min(scores)}
    Maximum Score: {max(scores)}
    Trend: {'Improving' if z[0] > 0 else 'Declining'}
    """
    axes[1, 1].text(0.1, 0.5, stats_text, fontsize=12, verticalalignment='center')
    axes[1, 1].axis('off')

    plt.tight_layout()
    plt.savefig(f'/var/reports/ldap/executive-{year}-{month:02d}.png', dpi=300)

    print(f"Executive report generated: executive-{year}-{month:02d}.png")

if __name__ == "__main__":
    generate_executive_report(11, 2025)
```

### Exemple 2 : Tableau de bord temps réel

```html
<!-- realtime-dashboard.html -->
<!DOCTYPE html>
<html>
<head>
    <title>LDAP Health Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #f5f5f5;
        }
        .dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 20px;
        }
        .widget {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .score {
            font-size: 48px;
            font-weight: bold;
            text-align: center;
        }
    </style>
</head>
<body>
    <h1>LDAP Health Dashboard</h1>
    <div class="dashboard">
        <div class="widget">
            <h2>Current Score</h2>
            <div class="score" id="score">--</div>
        </div>

        <div class="widget">
            <h2>Response Time</h2>
            <canvas id="responseTimeChart"></canvas>
        </div>

        <div class="widget">
            <h2>Issues by Level</h2>
            <canvas id="issuesChart"></canvas>
        </div>

        <div class="widget">
            <h2>Recent Issues</h2>
            <div id="recentIssues"></div>
        </div>
    </div>

    <script>
        // Fetch data every 60 seconds
        async function fetchData() {
            const response = await fetch('/api/audit/latest');
            const data = await response.json();
            updateDashboard(data);
        }

        function updateDashboard(data) {
            // Update score
            document.getElementById('score').textContent = data.score + '/100';

            // Update charts
            updateResponseTimeChart(data.health.response_time);
            updateIssuesChart(data.issues);
            updateRecentIssues(data.issues);
        }

        // Initialize and refresh
        fetchData();
        setInterval(fetchData, 60000);
    </script>
</body>
</html>
```

## Tableaux de bord

### Kibana

**Index pattern :**
```json
{
  "index_patterns": ["ldap-audit-*"],
  "mappings": {
    "properties": {
      "timestamp": {"type": "date"},
      "score": {"type": "integer"},
      "issues": {
        "type": "nested",
        "properties": {
          "level": {"type": "keyword"},
          "category": {"type": "keyword"},
          "title": {"type": "text"}
        }
      }
    }
  }
}
```

### Tableau

**Connexion aux données :**
- Connecter à la base PostgreSQL
- Ou importer les CSV
- Créer des vues et dashboards interactifs

## Bonnes pratiques

### Conservation des rapports

**Structure recommandée :**
```
/var/reports/ldap/
├── current/
│   └── latest.json
├── daily/
│   ├── 2025/
│   │   ├── 11/
│   │   │   ├── audit-2025-11-17.json
│   │   │   ├── audit-2025-11-17.html
│   │   │   └── audit-2025-11-17.pdf
├── weekly/
│   └── 2025/
│       └── W47-summary.html
├── monthly/
│   └── 2025/
│       ├── 11-executive.pdf
│       └── 11-detailed.html
└── archive/
    └── 2024/
```

### Rotation des logs

```bash
# /etc/logrotate.d/ldap-audit-reports
/var/reports/ldap/daily/*/*.json {
    monthly
    rotate 12
    compress
    delaycompress
    notifempty
    missingok
}
```

### Sécurité des rapports

```bash
# Permissions restrictives
chmod 600 /var/reports/ldap/**/*.json
chown ldap-monitor:ldap-monitor /var/reports/ldap/**/*.json

# Chiffrement des rapports sensibles
gpg --encrypt --recipient admin@example.com audit-report.pdf
```

## Conclusion

Les rapports d'audit sont essentiels pour communiquer l'état de votre infrastructure LDAP. En utilisant les bons formats et en automatisant la génération, vous maintenez une visibilité constante sur la santé de votre annuaire.

**Points clés :**
- Choisir le bon format selon l'usage
- Automatiser la génération
- Archiver pour l'historique
- Intégrer avec les outils existants
- Sécuriser les rapports sensibles

Pour aller plus loin :
- [Vue d'ensemble des audits](./Overview.md)
- [Audit de santé](./Health-Check.md)
- [Audit de sécurité](./Security-Audit.md)
