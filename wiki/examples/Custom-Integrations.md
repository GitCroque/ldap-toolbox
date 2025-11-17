# Intégrations Personnalisées - LDAP Health Monitor

Guide complet pour créer des intégrations personnalisées avec LDAP Health Monitor : webhooks, API, reporters custom, et intégrations tierces.

## 📋 Table des Matières

- [Webhooks Personnalisés](#webhooks-personnalisés)
- [API REST Custom](#api-rest-custom)
- [Reporters Personnalisés](#reporters-personnalisés)
- [Intégrations Messaging](#intégrations-messaging)
- [Intégrations SIEM](#intégrations-siem)
- [Intégrations ITSM](#intégrations-itsm)
- [Intégrations Monitoring](#intégrations-monitoring)

---

## Webhooks Personnalisés

### Configuration Webhooks Avancée

```yaml
# config-custom-webhooks.yaml
integrations:
  webhooks:
    enabled: true

    # Webhook générique
    generic:
      - name: "ServiceNow Incident"
        url: https://instance.service-now.com/api/now/table/incident
        method: POST
        events:
          - critical_issue
          - security_violation

        headers:
          Content-Type: "application/json"
          Authorization: "Basic ${SERVICENOW_AUTH}"

        payload_template: |
          {
            "short_description": "LDAP: {{ event.title }}",
            "description": "{{ event.description }}\n\nSeverity: {{ event.severity }}\nTimestamp: {{ event.timestamp }}",
            "severity": "{{ event.severity | servicenow_severity }}",
            "category": "LDAP",
            "assignment_group": "LDAP-Support",
            "caller_id": "ldap-monitor"
          }

        retry:
          enabled: true
          max_attempts: 3
          delay_seconds: 5
          backoff_multiplier: 2

      - name: "Jira Issue Creation"
        url: https://company.atlassian.net/rest/api/3/issue
        method: POST
        events:
          - compliance_issue
          - audit_failure

        headers:
          Content-Type: "application/json"
          Authorization: "Basic ${JIRA_AUTH}"

        payload_template: |
          {
            "fields": {
              "project": {
                "key": "LDAP"
              },
              "summary": "{{ event.title }}",
              "description": {
                "type": "doc",
                "version": 1,
                "content": [{
                  "type": "paragraph",
                  "content": [{
                    "type": "text",
                    "text": "{{ event.description }}"
                  }]
                }]
              },
              "issuetype": {
                "name": "Bug"
              },
              "priority": {
                "name": "{{ event.severity | jira_priority }}"
              },
              "labels": ["ldap-monitor", "automated"]
            }
          }

      - name: "Custom Webhook with Authentication"
        url: https://api.company.com/ldap/events
        method: POST
        events: ["*"]  # Tous les événements

        authentication:
          type: oauth2
          token_url: https://auth.company.com/oauth/token
          client_id: ${OAUTH_CLIENT_ID}
          client_secret: ${OAUTH_CLIENT_SECRET}
          scope: "ldap:write"

        headers:
          Content-Type: "application/json"
          X-API-Version: "2.0"

        payload_template: |
          {
            "event_type": "{{ event.type }}",
            "severity": "{{ event.severity }}",
            "timestamp": "{{ event.timestamp | iso8601 }}",
            "source": "ldap-monitor",
            "data": {{ event | tojson }}
          }

        # Conditions de déclenchement
        conditions:
          - field: severity
            operator: in
            values: [critical, high]

          - field: affected_users
            operator: gt
            value: 10

      - name: "Microsoft Teams"
        url: ${TEAMS_WEBHOOK}
        method: POST
        events:
          - critical_issue
          - daily_summary

        payload_template: |
          {
            "@type": "MessageCard",
            "@context": "https://schema.org/extensions",
            "summary": "{{ event.title }}",
            "themeColor": "{{ event.severity | teams_color }}",
            "title": "LDAP Health Monitor Alert",
            "sections": [{
              "activityTitle": "{{ event.title }}",
              "activitySubtitle": "{{ event.timestamp }}",
              "facts": [
                {"name": "Severity", "value": "{{ event.severity }}"},
                {"name": "Type", "value": "{{ event.type }}"},
                {"name": "Affected", "value": "{{ event.affected_count }}"}
              ],
              "text": "{{ event.description }}"
            }],
            "potentialAction": [{
              "@type": "OpenUri",
              "name": "View Details",
              "targets": [{
                "os": "default",
                "uri": "https://monitor.company.com/events/{{ event.id }}"
              }]
            }]
          }
```

### Script Webhook Handler

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/integrations/webhook_handler.py

import requests
import json
import time
from typing import Dict, Any, Optional
from jinja2 import Template
import logging

logger = logging.getLogger(__name__)


class WebhookHandler:
    """Gestionnaire de webhooks personnalisés"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = requests.Session()

    def send_webhook(self, webhook_config: Dict, event: Dict) -> bool:
        """Envoie un événement à un webhook"""

        # Vérifier les conditions
        if not self._check_conditions(webhook_config.get('conditions', []), event):
            logger.debug(f"Event {event['type']} doesn't match conditions")
            return True

        # Vérifier si l'événement est dans la liste des événements supportés
        events = webhook_config.get('events', [])
        if '*' not in events and event['type'] not in events:
            logger.debug(f"Event {event['type']} not in webhook events list")
            return True

        # Préparer la requête
        url = self._render_template(webhook_config['url'], event)
        method = webhook_config.get('method', 'POST')
        headers = self._prepare_headers(webhook_config.get('headers', {}), event)
        payload = self._prepare_payload(webhook_config.get('payload_template'), event)

        # Authentification
        auth = self._get_authentication(webhook_config.get('authentication'))

        # Retry configuration
        retry_config = webhook_config.get('retry', {})
        max_attempts = retry_config.get('max_attempts', 1)
        delay = retry_config.get('delay_seconds', 5)
        backoff = retry_config.get('backoff_multiplier', 1)

        # Envoyer avec retry
        for attempt in range(max_attempts):
            try:
                response = self.session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=payload,
                    auth=auth,
                    timeout=30
                )

                response.raise_for_status()

                logger.info(f"Webhook sent successfully to {webhook_config['name']}")
                return True

            except requests.exceptions.RequestException as e:
                logger.error(f"Webhook attempt {attempt + 1}/{max_attempts} failed: {e}")

                if attempt < max_attempts - 1:
                    sleep_time = delay * (backoff ** attempt)
                    logger.info(f"Retrying in {sleep_time} seconds...")
                    time.sleep(sleep_time)
                else:
                    logger.error(f"All webhook attempts failed for {webhook_config['name']}")
                    return False

        return False

    def _check_conditions(self, conditions: list, event: Dict) -> bool:
        """Vérifie si l'événement correspond aux conditions"""
        if not conditions:
            return True

        for condition in conditions:
            field = condition['field']
            operator = condition['operator']
            value = event.get(field)

            if operator == 'in':
                if value not in condition['values']:
                    return False

            elif operator == 'gt':
                if value <= condition['value']:
                    return False

            elif operator == 'lt':
                if value >= condition['value']:
                    return False

            elif operator == 'eq':
                if value != condition['value']:
                    return False

        return True

    def _prepare_headers(self, headers_config: Dict, event: Dict) -> Dict:
        """Prépare les headers avec template rendering"""
        headers = {}
        for key, value in headers_config.items():
            headers[key] = self._render_template(value, event)
        return headers

    def _prepare_payload(self, template_str: Optional[str], event: Dict) -> Dict:
        """Prépare le payload à partir du template"""
        if not template_str:
            return event

        # Ajouter des filtres personnalisés
        rendered = self._render_template(template_str, event)
        return json.loads(rendered)

    def _render_template(self, template_str: str, event: Dict) -> str:
        """Rend un template Jinja2"""
        template = Template(template_str)

        # Filtres personnalisés
        template.globals['servicenow_severity'] = self._servicenow_severity
        template.globals['jira_priority'] = self._jira_priority
        template.globals['teams_color'] = self._teams_color

        return template.render(event=event)

    def _get_authentication(self, auth_config: Optional[Dict]) -> Optional[Any]:
        """Gère l'authentification"""
        if not auth_config:
            return None

        auth_type = auth_config.get('type')

        if auth_type == 'basic':
            return (auth_config['username'], auth_config['password'])

        elif auth_type == 'oauth2':
            token = self._get_oauth2_token(auth_config)
            self.session.headers['Authorization'] = f"Bearer {token}"
            return None

        return None

    def _get_oauth2_token(self, auth_config: Dict) -> str:
        """Obtient un token OAuth2"""
        response = requests.post(
            auth_config['token_url'],
            data={
                'grant_type': 'client_credentials',
                'client_id': auth_config['client_id'],
                'client_secret': auth_config['client_secret'],
                'scope': auth_config.get('scope', '')
            }
        )
        response.raise_for_status()
        return response.json()['access_token']

    @staticmethod
    def _servicenow_severity(severity: str) -> int:
        """Convertit la sévérité en format ServiceNow"""
        mapping = {
            'critical': 1,
            'high': 2,
            'medium': 3,
            'low': 4
        }
        return mapping.get(severity, 3)

    @staticmethod
    def _jira_priority(severity: str) -> str:
        """Convertit la sévérité en priorité Jira"""
        mapping = {
            'critical': 'Highest',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low'
        }
        return mapping.get(severity, 'Medium')

    @staticmethod
    def _teams_color(severity: str) -> str:
        """Convertit la sévérité en couleur Teams"""
        mapping = {
            'critical': 'FF0000',  # Rouge
            'high': 'FFA500',      # Orange
            'medium': 'FFFF00',    # Jaune
            'low': '00FF00'        # Vert
        }
        return mapping.get(severity, '0078D4')


# Test du handler
if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    # Event de test
    test_event = {
        'type': 'critical_issue',
        'severity': 'critical',
        'title': 'LDAP Connection Failed',
        'description': 'Unable to connect to LDAP server',
        'timestamp': '2024-01-15T10:30:00Z',
        'affected_count': 50,
        'id': 'evt-12345'
    }

    # Config de test
    webhook_config = {
        'name': 'Test Webhook',
        'url': 'https://webhook.site/unique-id',
        'method': 'POST',
        'events': ['critical_issue'],
        'headers': {
            'Content-Type': 'application/json'
        },
        'payload_template': '{{ event | tojson }}'
    }

    handler = WebhookHandler({})
    handler.send_webhook(webhook_config, test_event)
```

---

## API REST Custom

### Serveur API Flask

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/api/server.py

from flask import Flask, request, jsonify
from flask_restful import Api, Resource
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import subprocess
import json
from typing import Dict, Any

app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()

# Users (en production, utiliser une base de données)
users = {
    "admin": generate_password_hash("admin_password"),
    "readonly": generate_password_hash("readonly_password")
}

LDAP_CONFIG = "/etc/ldap-monitor/config.yaml"


@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username


class HealthCheck(Resource):
    """Endpoint de health check"""

    @auth.login_required
    def get(self):
        """GET /api/health"""
        try:
            result = subprocess.run(
                ['ldap-monitor', '-c', LDAP_CONFIG, 'audit', 'health', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                data = json.loads(result.stdout)
                return {'status': 'success', 'data': data}, 200
            else:
                return {'status': 'error', 'message': result.stderr}, 500

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500


class Users(Resource):
    """Endpoint pour les utilisateurs"""

    @auth.login_required
    def get(self):
        """GET /api/users"""
        try:
            # Query parameters
            limit = request.args.get('limit', 100, type=int)
            search = request.args.get('search', '')

            cmd = ['ldap-monitor', '-c', LDAP_CONFIG, 'user', 'list']

            if limit:
                cmd.extend(['--limit', str(limit)])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                # Parser le résultat
                users = self._parse_user_list(result.stdout)

                if search:
                    users = [u for u in users if search.lower() in u.get('uid', '').lower()]

                return {
                    'status': 'success',
                    'count': len(users),
                    'data': users
                }, 200
            else:
                return {'status': 'error', 'message': result.stderr}, 500

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500

    def _parse_user_list(self, output: str) -> list:
        """Parse la sortie de user list"""
        users = []
        for line in output.strip().split('\n'):
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    uid, rest = parts
                    users.append({
                        'uid': uid.strip(),
                        'info': rest.strip()
                    })
        return users


class UserDetail(Resource):
    """Endpoint pour les détails d'un utilisateur"""

    @auth.login_required
    def get(self, user_dn):
        """GET /api/users/<dn>"""
        try:
            result = subprocess.run(
                ['ldap-monitor', '-c', LDAP_CONFIG, 'user', 'show', user_dn],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                user_data = self._parse_user_detail(result.stdout)
                return {'status': 'success', 'data': user_data}, 200
            else:
                return {'status': 'error', 'message': 'User not found'}, 404

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500

    def _parse_user_detail(self, output: str) -> Dict[str, Any]:
        """Parse la sortie de user show"""
        user = {}
        for line in output.strip().split('\n'):
            if ':' in line:
                key, value = line.split(':', 1)
                user[key.strip()] = value.strip()
        return user


class Audit(Resource):
    """Endpoint pour les audits"""

    @auth.login_required
    def post(self):
        """POST /api/audit"""
        data = request.get_json()

        audit_type = data.get('type', 'all')
        output_format = data.get('format', 'json')

        try:
            cmd = ['ldap-monitor', '-c', LDAP_CONFIG, 'audit', audit_type]

            if output_format:
                cmd.extend(['--format', output_format])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # Audit peut prendre du temps
            )

            if result.returncode == 0:
                if output_format == 'json':
                    audit_data = json.loads(result.stdout)
                else:
                    audit_data = result.stdout

                return {
                    'status': 'success',
                    'data': audit_data
                }, 200
            else:
                return {'status': 'error', 'message': result.stderr}, 500

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500


class Metrics(Resource):
    """Endpoint pour les métriques"""

    @auth.login_required
    def get(self):
        """GET /api/metrics"""
        try:
            result = subprocess.run(
                ['ldap-monitor', '-c', LDAP_CONFIG, 'monitor', 'metrics', '--format', 'json'],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                metrics = json.loads(result.stdout)
                return {'status': 'success', 'data': metrics}, 200
            else:
                return {'status': 'error', 'message': result.stderr}, 500

        except Exception as e:
            return {'status': 'error', 'message': str(e)}, 500


# Enregistrer les endpoints
api.add_resource(HealthCheck, '/api/health')
api.add_resource(Users, '/api/users')
api.add_resource(UserDetail, '/api/users/<path:user_dn>')
api.add_resource(Audit, '/api/audit')
api.add_resource(Metrics, '/api/metrics')


@app.route('/')
def index():
    """Page d'accueil de l'API"""
    return jsonify({
        'name': 'LDAP Health Monitor API',
        'version': '1.0.0',
        'endpoints': {
            'GET /api/health': 'Health check',
            'GET /api/users': 'List users',
            'GET /api/users/<dn>': 'Get user details',
            'POST /api/audit': 'Run audit',
            'GET /api/metrics': 'Get metrics'
        }
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
```

### Client API Python

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/api/client.py

import requests
from typing import Dict, List, Optional, Any


class LDAPMonitorClient:
    """Client Python pour l'API LDAP Health Monitor"""

    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.session.auth = (username, password)
        self.session.headers.update({'Content-Type': 'application/json'})

    def health_check(self) -> Dict[str, Any]:
        """Effectue un health check"""
        response = self.session.get(f"{self.base_url}/api/health")
        response.raise_for_status()
        return response.json()

    def list_users(self, limit: int = 100, search: str = '') -> List[Dict]:
        """Liste les utilisateurs"""
        params = {'limit': limit}
        if search:
            params['search'] = search

        response = self.session.get(f"{self.base_url}/api/users", params=params)
        response.raise_for_status()
        return response.json()['data']

    def get_user(self, user_dn: str) -> Dict[str, Any]:
        """Récupère les détails d'un utilisateur"""
        response = self.session.get(f"{self.base_url}/api/users/{user_dn}")
        response.raise_for_status()
        return response.json()['data']

    def run_audit(self, audit_type: str = 'all', output_format: str = 'json') -> Dict:
        """Lance un audit"""
        data = {
            'type': audit_type,
            'format': output_format
        }
        response = self.session.post(f"{self.base_url}/api/audit", json=data)
        response.raise_for_status()
        return response.json()['data']

    def get_metrics(self) -> Dict[str, Any]:
        """Récupère les métriques"""
        response = self.session.get(f"{self.base_url}/api/metrics")
        response.raise_for_status()
        return response.json()['data']


# Exemple d'utilisation
if __name__ == '__main__':
    client = LDAPMonitorClient(
        base_url='http://localhost:5000',
        username='admin',
        password='admin_password'
    )

    # Health check
    health = client.health_check()
    print(f"Health status: {health['data']['status']}")

    # Lister les utilisateurs
    users = client.list_users(limit=10)
    print(f"Found {len(users)} users")

    # Lancer un audit
    audit = client.run_audit(audit_type='users')
    print(f"Audit completed with {len(audit.get('issues', []))} issues")
```

---

## Reporters Personnalisés

### Reporter Markdown Custom

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/reporters/markdown_reporter.py

from datetime import datetime
from typing import Dict, List, Any
import os


class MarkdownReporter:
    """Reporter pour générer des rapports en Markdown"""

    def __init__(self, output_file: str):
        self.output_file = output_file

    def generate_report(self, audit_data: Dict[str, Any]) -> str:
        """Génère un rapport Markdown complet"""

        md = []

        # Header
        md.append(f"# LDAP Health Monitor Report")
        md.append(f"\n**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Table of Contents
        md.append("## Table of Contents\n")
        md.append("- [Summary](#summary)")
        md.append("- [Health Status](#health-status)")
        md.append("- [Issues](#issues)")
        md.append("- [Metrics](#metrics)")
        md.append("- [Recommendations](#recommendations)\n")

        # Summary
        md.append("## Summary\n")
        md.append(self._generate_summary(audit_data))

        # Health Status
        md.append("\n## Health Status\n")
        md.append(self._generate_health_status(audit_data.get('health', {})))

        # Issues
        md.append("\n## Issues\n")
        md.append(self._generate_issues(audit_data.get('issues', [])))

        # Metrics
        md.append("\n## Metrics\n")
        md.append(self._generate_metrics(audit_data.get('metrics', {})))

        # Recommendations
        md.append("\n## Recommendations\n")
        md.append(self._generate_recommendations(audit_data.get('issues', [])))

        # Write to file
        content = '\n'.join(md)
        with open(self.output_file, 'w') as f:
            f.write(content)

        return content

    def _generate_summary(self, audit_data: Dict) -> str:
        """Génère le résumé"""
        issues = audit_data.get('issues', [])
        critical = len([i for i in issues if i.get('severity') == 'critical'])
        high = len([i for i in issues if i.get('severity') == 'high'])
        medium = len([i for i in issues if i.get('severity') == 'medium'])
        low = len([i for i in issues if i.get('severity') == 'low'])

        md = []
        md.append("| Metric | Value |")
        md.append("|--------|-------|")
        md.append(f"| **Total Issues** | {len(issues)} |")
        md.append(f"| 🔴 Critical | {critical} |")
        md.append(f"| 🟠 High | {high} |")
        md.append(f"| 🟡 Medium | {medium} |")
        md.append(f"| 🟢 Low | {low} |")
        md.append(f"| **Health Score** | {audit_data.get('score', 0)}/100 |")

        return '\n'.join(md)

    def _generate_health_status(self, health: Dict) -> str:
        """Génère le statut de santé"""
        status = health.get('status', 'unknown')
        emoji = {
            'healthy': '✅',
            'warning': '⚠️',
            'critical': '❌',
            'unknown': '❓'
        }.get(status, '❓')

        md = [f"**Status:** {emoji} {status.upper()}\n"]

        if health.get('details'):
            md.append("### Details\n")
            for key, value in health['details'].items():
                md.append(f"- **{key}:** {value}")

        return '\n'.join(md)

    def _generate_issues(self, issues: List[Dict]) -> str:
        """Génère la liste des problèmes"""
        if not issues:
            return "✅ No issues found!"

        # Grouper par sévérité
        by_severity = {}
        for issue in issues:
            severity = issue.get('severity', 'unknown')
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)

        md = []

        for severity in ['critical', 'high', 'medium', 'low']:
            if severity not in by_severity:
                continue

            severity_issues = by_severity[severity]
            emoji = {
                'critical': '🔴',
                'high': '🟠',
                'medium': '🟡',
                'low': '🟢'
            }.get(severity, '⚪')

            md.append(f"\n### {emoji} {severity.upper()} ({len(severity_issues)})\n")

            for i, issue in enumerate(severity_issues, 1):
                md.append(f"#### {i}. {issue.get('title', 'Untitled')}\n")
                md.append(f"**Description:** {issue.get('description', 'N/A')}\n")

                if issue.get('affected_objects'):
                    md.append(f"**Affected:** {len(issue['affected_objects'])} objects\n")

                if issue.get('recommendation'):
                    md.append(f"**Recommendation:** {issue['recommendation']}\n")

                md.append("---\n")

        return '\n'.join(md)

    def _generate_metrics(self, metrics: Dict) -> str:
        """Génère les métriques"""
        if not metrics:
            return "No metrics available."

        md = []
        md.append("| Metric | Value |")
        md.append("|--------|-------|")

        for key, value in metrics.items():
            md.append(f"| {key.replace('_', ' ').title()} | {value} |")

        return '\n'.join(md)

    def _generate_recommendations(self, issues: List[Dict]) -> str:
        """Génère les recommandations"""
        recommendations = set()

        for issue in issues:
            if issue.get('recommendation'):
                recommendations.add(issue['recommendation'])

        if not recommendations:
            return "No specific recommendations at this time."

        md = []
        for i, rec in enumerate(sorted(recommendations), 1):
            md.append(f"{i}. {rec}")

        return '\n'.join(md)


# Test du reporter
if __name__ == '__main__':
    # Données de test
    test_data = {
        'health': {
            'status': 'warning',
            'details': {
                'connection_time': '250ms',
                'user_count': 1523,
                'group_count': 234
            }
        },
        'issues': [
            {
                'severity': 'critical',
                'title': 'Weak Password Policy',
                'description': 'Password policy does not meet security requirements',
                'recommendation': 'Update password policy to require 12+ characters'
            },
            {
                'severity': 'high',
                'title': 'Inactive Users',
                'description': '45 users have been inactive for over 90 days',
                'affected_objects': ['user1', 'user2'],
                'recommendation': 'Disable or remove inactive users'
            }
        ],
        'metrics': {
            'total_users': 1523,
            'active_users': 1478,
            'total_groups': 234,
            'empty_groups': 12
        },
        'score': 75
    }

    reporter = MarkdownReporter('test-report.md')
    reporter.generate_report(test_data)
    print("Report generated: test-report.md")
```

### Reporter Slack Interactif

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/reporters/slack_interactive_reporter.py

import requests
from typing import Dict, List, Any


class SlackInteractiveReporter:
    """Reporter pour envoyer des rapports interactifs à Slack"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    def send_audit_report(self, audit_data: Dict[str, Any]) -> bool:
        """Envoie un rapport d'audit interactif"""

        issues = audit_data.get('issues', [])
        critical = len([i for i in issues if i.get('severity') == 'critical'])
        high = len([i for i in issues if i.get('severity') == 'high'])

        # Déterminer la couleur selon la sévérité
        if critical > 0:
            color = 'danger'
            emoji = '🔴'
        elif high > 0:
            color = 'warning'
            emoji = '🟠'
        else:
            color = 'good'
            emoji = '✅'

        # Construire le message
        payload = {
            'attachments': [
                {
                    'color': color,
                    'title': f'{emoji} LDAP Health Monitor Report',
                    'fields': [
                        {
                            'title': 'Total Issues',
                            'value': str(len(issues)),
                            'short': True
                        },
                        {
                            'title': 'Health Score',
                            'value': f"{audit_data.get('score', 0)}/100",
                            'short': True
                        },
                        {
                            'title': '🔴 Critical',
                            'value': str(critical),
                            'short': True
                        },
                        {
                            'title': '🟠 High',
                            'value': str(high),
                            'short': True
                        }
                    ],
                    'footer': 'LDAP Health Monitor',
                    'ts': int(datetime.now().timestamp())
                }
            ]
        }

        # Ajouter les problèmes critiques
        if critical > 0:
            critical_issues = [i for i in issues if i.get('severity') == 'critical']
            fields = []

            for issue in critical_issues[:5]:  # Limiter à 5
                fields.append({
                    'title': issue.get('title'),
                    'value': issue.get('description')[:100],
                    'short': False
                })

            payload['attachments'].append({
                'color': 'danger',
                'title': 'Critical Issues',
                'fields': fields
            })

        # Envoyer
        response = requests.post(self.webhook_url, json=payload)
        return response.status_code == 200

    def send_daily_summary(self, metrics: Dict[str, Any]) -> bool:
        """Envoie un résumé quotidien"""

        payload = {
            'text': '📊 LDAP Daily Summary',
            'attachments': [
                {
                    'color': 'good',
                    'fields': [
                        {
                            'title': 'Total Users',
                            'value': str(metrics.get('total_users', 0)),
                            'short': True
                        },
                        {
                            'title': 'Active Users',
                            'value': str(metrics.get('active_users', 0)),
                            'short': True
                        },
                        {
                            'title': 'Total Groups',
                            'value': str(metrics.get('total_groups', 0)),
                            'short': True
                        },
                        {
                            'title': 'Connection Time',
                            'value': f"{metrics.get('connection_time', 0)}ms",
                            'short': True
                        }
                    ]
                }
            ]
        }

        response = requests.post(self.webhook_url, json=payload)
        return response.status_code == 200
```

---

## Intégrations SIEM

### Splunk Integration

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/integrations/splunk_integration.py

import requests
import json
from datetime import datetime
from typing import Dict, Any, List


class SplunkIntegration:
    """Intégration avec Splunk HEC (HTTP Event Collector)"""

    def __init__(self, hec_url: str, hec_token: str, index: str = 'ldap_monitor'):
        self.hec_url = hec_url.rstrip('/')
        self.hec_token = hec_token
        self.index = index
        self.headers = {
            'Authorization': f'Splunk {hec_token}',
            'Content-Type': 'application/json'
        }

    def send_event(self, event_type: str, data: Dict[str, Any], source: str = 'ldap-monitor') -> bool:
        """Envoie un événement à Splunk"""

        payload = {
            'time': datetime.now().timestamp(),
            'index': self.index,
            'source': source,
            'sourcetype': f'ldap:{event_type}',
            'event': {
                'type': event_type,
                'timestamp': datetime.now().isoformat(),
                **data
            }
        }

        try:
            response = requests.post(
                f'{self.hec_url}/services/collector/event',
                headers=self.headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            return True

        except requests.exceptions.RequestException as e:
            print(f"Error sending to Splunk: {e}")
            return False

    def send_audit_results(self, audit_data: Dict[str, Any]) -> bool:
        """Envoie les résultats d'audit"""

        # Événement principal
        self.send_event('audit_completed', {
            'total_issues': len(audit_data.get('issues', [])),
            'score': audit_data.get('score', 0),
            'health_status': audit_data.get('health', {}).get('status')
        })

        # Envoyer chaque problème comme événement séparé
        for issue in audit_data.get('issues', []):
            self.send_event('issue_detected', issue)

        return True

    def send_metrics(self, metrics: Dict[str, Any]) -> bool:
        """Envoie les métriques"""
        return self.send_event('metrics', metrics)

    def query_events(self, search_query: str, earliest_time: str = '-24h') -> List[Dict]:
        """Interroge Splunk (nécessite les credentials d'API)"""
        # Implémentation simplifiée
        pass
```

### ELK Stack Integration

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/integrations/elasticsearch_integration.py

from elasticsearch import Elasticsearch
from datetime import datetime
from typing import Dict, Any, List


class ElasticsearchIntegration:
    """Intégration avec Elasticsearch"""

    def __init__(self, hosts: List[str], api_key: str = None, index_prefix: str = 'ldap-monitor'):
        self.es = Elasticsearch(
            hosts=hosts,
            api_key=api_key
        )
        self.index_prefix = index_prefix

    def index_audit(self, audit_data: Dict[str, Any]) -> bool:
        """Indexe un rapport d'audit"""

        index_name = f"{self.index_prefix}-audits-{datetime.now().strftime('%Y.%m')}"

        doc = {
            'timestamp': datetime.now().isoformat(),
            'type': 'audit',
            'score': audit_data.get('score', 0),
            'total_issues': len(audit_data.get('issues', [])),
            'health': audit_data.get('health', {}),
            'metrics': audit_data.get('metrics', {})
        }

        try:
            response = self.es.index(index=index_name, document=doc)
            return response['result'] == 'created'

        except Exception as e:
            print(f"Error indexing audit: {e}")
            return False

    def index_issues(self, issues: List[Dict]) -> bool:
        """Indexe les problèmes individuellement"""

        index_name = f"{self.index_prefix}-issues-{datetime.now().strftime('%Y.%m')}"

        for issue in issues:
            doc = {
                'timestamp': datetime.now().isoformat(),
                **issue
            }

            try:
                self.es.index(index=index_name, document=doc)
            except Exception as e:
                print(f"Error indexing issue: {e}")

        return True

    def search_issues(self, severity: str = None, days: int = 7) -> List[Dict]:
        """Recherche des problèmes"""

        index_pattern = f"{self.index_prefix}-issues-*"

        query = {
            'bool': {
                'must': [
                    {
                        'range': {
                            'timestamp': {
                                'gte': f'now-{days}d/d'
                            }
                        }
                    }
                ]
            }
        }

        if severity:
            query['bool']['must'].append({
                'term': {'severity': severity}
            })

        try:
            response = self.es.search(
                index=index_pattern,
                query=query,
                size=100
            )

            return [hit['_source'] for hit in response['hits']['hits']]

        except Exception as e:
            print(f"Error searching: {e}")
            return []
```

---

## Intégrations ITSM

### ServiceNow Integration Complète

```python
#!/usr/bin/env python3
# /opt/ldap-monitor/integrations/servicenow_integration.py

import requests
from typing import Dict, Any, Optional, List


class ServiceNowIntegration:
    """Intégration complète avec ServiceNow"""

    def __init__(self, instance: str, username: str, password: str):
        self.base_url = f"https://{instance}.service-now.com"
        self.auth = (username, password)
        self.headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

    def create_incident(self, issue: Dict[str, Any]) -> Optional[str]:
        """Crée un incident pour un problème LDAP"""

        # Mapper la sévérité LDAP → ServiceNow
        severity_map = {
            'critical': '1',
            'high': '2',
            'medium': '3',
            'low': '4'
        }

        payload = {
            'short_description': f"LDAP: {issue.get('title', 'Unknown issue')}",
            'description': issue.get('description', ''),
            'severity': severity_map.get(issue.get('severity'), '3'),
            'category': 'LDAP',
            'subcategory': 'Health Monitor',
            'assignment_group': 'LDAP Support',
            'caller_id': 'ldap-monitor',
            'impact': severity_map.get(issue.get('severity'), '3'),
            'urgency': severity_map.get(issue.get('severity'), '3')
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/now/table/incident",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            incident_number = response.json()['result']['number']
            print(f"Created incident: {incident_number}")

            # Ajouter les détails techniques comme notes
            if issue.get('technical_details'):
                self.add_work_note(
                    incident_number,
                    f"Technical Details:\n{issue['technical_details']}"
                )

            return incident_number

        except requests.exceptions.RequestException as e:
            print(f"Error creating incident: {e}")
            return None

    def add_work_note(self, incident_number: str, note: str) -> bool:
        """Ajoute une note de travail à un incident"""

        # Récupérer le sys_id de l'incident
        response = requests.get(
            f"{self.base_url}/api/now/table/incident",
            auth=self.auth,
            headers=self.headers,
            params={'sysparm_query': f'number={incident_number}'},
            timeout=30
        )

        if response.status_code == 200:
            results = response.json().get('result', [])
            if results:
                sys_id = results[0]['sys_id']

                # Ajouter la note
                update = requests.patch(
                    f"{self.base_url}/api/now/table/incident/{sys_id}",
                    auth=self.auth,
                    headers=self.headers,
                    json={'work_notes': note},
                    timeout=30
                )

                return update.status_code == 200

        return False

    def resolve_incident(self, incident_number: str, resolution_notes: str) -> bool:
        """Résout un incident"""

        response = requests.get(
            f"{self.base_url}/api/now/table/incident",
            auth=self.auth,
            headers=self.headers,
            params={'sysparm_query': f'number={incident_number}'},
            timeout=30
        )

        if response.status_code == 200:
            results = response.json().get('result', [])
            if results:
                sys_id = results[0]['sys_id']

                update = requests.patch(
                    f"{self.base_url}/api/now/table/incident/{sys_id}",
                    auth=self.auth,
                    headers=self.headers,
                    json={
                        'state': '6',  # Resolved
                        'close_code': 'Solved (Permanently)',
                        'close_notes': resolution_notes
                    },
                    timeout=30
                )

                return update.status_code == 200

        return False

    def create_change_request(self, description: str, justification: str) -> Optional[str]:
        """Crée une demande de changement"""

        payload = {
            'short_description': description,
            'description': description,
            'justification': justification,
            'category': 'LDAP',
            'type': 'Normal',
            'assignment_group': 'LDAP Support'
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/now/table/change_request",
                auth=self.auth,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            response.raise_for_status()

            change_number = response.json()['result']['number']
            print(f"Created change request: {change_number}")

            return change_number

        except requests.exceptions.RequestException as e:
            print(f"Error creating change request: {e}")
            return None
```

Ce guide couvre les principales intégrations personnalisées possibles avec LDAP Health Monitor. Pour des cas d'usage complets, consultez [Use-Cases.md](./Use-Cases.md).
