# Guide de Migration

Guide complet pour migrer depuis d'autres outils LDAP vers LDAP Health Monitor.

## 🎯 Vue d'Ensemble

Ce guide couvre la migration depuis différents outils et systèmes de monitoring LDAP vers LDAP Health Monitor, incluant :

- Migration depuis des outils existants
- Processus de migration étape par étape
- Mapping des données et configurations
- Tests et validation
- Rollback et récupération

## 📋 Outils Sources Supportés

### Outils de Monitoring
- **Nagios/Icinga** avec check_ldap
- **Zabbix** avec templates LDAP
- **Prometheus** avec ldap_exporter
- **Scripts personnalisés** bash/python/perl

### Outils de Gestion
- **phpLDAPadmin**
- **Apache Directory Studio**
- **JXplorer**
- **LDAP Admin**

### Outils d'Audit
- **ldapsearch** scripts
- **Custom Python scripts** (python-ldap)
- **Perl Net::LDAP** scripts

## 🔄 Migration depuis Nagios/Icinga

### État Actuel

Configuration Nagios typique :

```cfg
# Nagios check_ldap
define service {
    use                     generic-service
    host_name               ldap-server
    service_description     LDAP Service
    check_command           check_ldap!dc=example,dc=com
    notifications_enabled   1
}

define command {
    command_name    check_ldap
    command_line    $USER1$/check_ldap -H $HOSTADDRESS$ -b $ARG1$ -w 2 -c 5
}
```

### Migration vers LDAP Health Monitor

**Étape 1 : Analyser la Configuration Actuelle**

```bash
# Extraire les checks LDAP de Nagios
grep -r "check_ldap" /etc/nagios/objects/ > nagios-ldap-checks.txt

# Lister les hôtes LDAP
grep -A 10 "define host" /etc/nagios/objects/hosts.cfg | grep -B 5 "ldap"
```

**Étape 2 : Créer Configuration LDAP Health Monitor**

```yaml
# config/ldap-config.yaml
ldap:
  server: ldaps://ldap-server.example.com
  port: 636
  use_ssl: true
  bind_dn: cn=monitor,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com
  timeout: 5  # Nagios c=5

monitoring:
  enabled: true
  interval: 300  # 5 minutes (Nagios default)

  checks:
    - name: "LDAP Connection"
      type: connection
      warning_threshold: 2
      critical_threshold: 5

    - name: "LDAP Response Time"
      type: response_time
      warning_threshold: 2000
      critical_threshold: 5000

    - name: "LDAP Entries Count"
      type: entries_count
      warning_threshold: 1000
      critical_threshold: 10000

# Alerting (mapping depuis Nagios contacts)
alerts:
  email:
    enabled: true
    smtp_server: localhost
    smtp_port: 25
    from: nagios@example.com
    to:
      - admin@example.com
      - oncall@example.com
```

**Étape 3 : Mapping des Seuils**

| Nagios Check | Paramètre | LDAP Monitor Équivalent |
|--------------|-----------|-------------------------|
| check_ldap -w 2 -c 5 | Warning/Critical temps | monitoring.checks[].warning/critical_threshold |
| check_ldap_entries | Nombre d'entrées | monitoring.checks.entries_count |
| check_ldap_bind | Test de connexion | monitoring.checks.connection |

**Étape 4 : Migration des Notifications**

```python
#!/usr/bin/env python3
# scripts/migrate-nagios-contacts.py

import re
import yaml

def parse_nagios_contacts(nagios_cfg):
    """Parse Nagios contacts.cfg"""
    contacts = []
    with open(nagios_cfg, 'r') as f:
        content = f.read()

    # Regex pour extraire contacts
    contact_blocks = re.findall(
        r'define contact\s*{([^}]+)}',
        content,
        re.MULTILINE | re.DOTALL
    )

    for block in contact_blocks:
        email = re.search(r'email\s+(\S+)', block)
        if email:
            contacts.append(email.group(1))

    return contacts

def create_ldap_monitor_config(contacts):
    """Créer config LDAP Monitor"""
    config = {
        'alerts': {
            'email': {
                'enabled': True,
                'to': contacts
            }
        }
    }
    return config

# Usage
contacts = parse_nagios_contacts('/etc/nagios/objects/contacts.cfg')
config = create_ldap_monitor_config(contacts)

with open('alerts-config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False)

print(f"✓ Migration de {len(contacts)} contacts")
```

**Étape 5 : Test en Parallèle**

```bash
# Garder Nagios actif, tester LDAP Monitor
ldap-monitor test connection
ldap-monitor monitor start --daemon

# Comparer les résultats pendant 24h
tail -f /var/log/ldap-monitor/monitor.log &
tail -f /var/log/nagios/nagios.log | grep LDAP &

# Vérifier concordance
./scripts/compare-monitoring-results.sh
```

**Étape 6 : Basculement**

```bash
# Désactiver checks LDAP dans Nagios
sed -i 's/check_ldap/check_ldap_disabled/' /etc/nagios/objects/services.cfg
systemctl reload nagios

# Activer LDAP Monitor en production
ldap-monitor monitor start --daemon
systemctl enable ldap-monitor
```

## 🔄 Migration depuis Zabbix

### Configuration Zabbix Actuelle

```xml
<!-- Template LDAP Zabbix -->
<zabbix_export>
  <template>
    <name>LDAP Monitoring</name>
    <items>
      <item>
        <name>LDAP Service Status</name>
        <key>net.tcp.service[ldap]</key>
        <delay>60</delay>
      </item>
    </items>
    <triggers>
      <trigger>
        <expression>{LDAP:net.tcp.service[ldap].last()}=0</expression>
        <name>LDAP is down</name>
        <priority>DISASTER</priority>
      </trigger>
    </triggers>
  </template>
</zabbix_export>
```

### Script de Migration

```python
#!/usr/bin/env python3
# scripts/migrate-from-zabbix.py

import json
import yaml
import xml.etree.ElementTree as ET

class ZabbixToLDAPMonitor:

    def __init__(self, zabbix_export_file):
        self.tree = ET.parse(zabbix_export_file)
        self.root = self.tree.getroot()

    def extract_items(self):
        """Extraire items Zabbix"""
        items = []
        for item in self.root.findall('.//item'):
            name = item.find('name').text
            key = item.find('key').text
            delay = int(item.find('delay').text)

            items.append({
                'name': name,
                'key': key,
                'interval': delay
            })

        return items

    def extract_triggers(self):
        """Extraire triggers Zabbix"""
        triggers = []
        for trigger in self.root.findall('.//trigger'):
            name = trigger.find('name').text
            expression = trigger.find('expression').text
            priority = trigger.find('priority').text

            # Mapper priorité Zabbix -> LDAP Monitor
            level_map = {
                'DISASTER': 'critical',
                'HIGH': 'critical',
                'AVERAGE': 'warning',
                'WARNING': 'warning',
                'INFORMATION': 'info'
            }

            triggers.append({
                'name': name,
                'expression': expression,
                'level': level_map.get(priority, 'warning')
            })

        return triggers

    def generate_config(self):
        """Générer config LDAP Monitor"""
        items = self.extract_items()
        triggers = self.extract_triggers()

        config = {
            'monitoring': {
                'enabled': True,
                'interval': min([i['interval'] for i in items]) if items else 300,
                'checks': []
            },
            'alerts': {
                'rules': []
            }
        }

        # Convertir items en checks
        for item in items:
            if 'ldap' in item['key'].lower():
                check = {
                    'name': item['name'],
                    'type': self._map_item_type(item['key']),
                    'interval': item['interval']
                }
                config['monitoring']['checks'].append(check)

        # Convertir triggers en alertes
        for trigger in triggers:
            alert = {
                'name': trigger['name'],
                'level': trigger['level'],
                'condition': self._map_trigger_condition(trigger['expression'])
            }
            config['alerts']['rules'].append(alert)

        return config

    def _map_item_type(self, key):
        """Mapper type d'item Zabbix"""
        mapping = {
            'net.tcp.service': 'connection',
            'ldap.entries': 'entries_count',
            'ldap.response': 'response_time',
            'ldap.bind': 'bind_test'
        }

        for zabbix_key, monitor_type in mapping.items():
            if zabbix_key in key:
                return monitor_type

        return 'custom'

    def _map_trigger_condition(self, expression):
        """Mapper expression trigger Zabbix"""
        # Simplification - adapter selon besoins
        if '.last()=0' in expression:
            return 'connection_failed'
        elif '.avg(' in expression:
            return 'high_response_time'
        else:
            return 'custom'

# Usage
migrator = ZabbixToLDAPMonitor('zabbix-ldap-template.xml')
config = migrator.generate_config()

with open('ldap-monitor-config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

print("✓ Configuration migrée avec succès")
print(f"  - {len(config['monitoring']['checks'])} checks")
print(f"  - {len(config['alerts']['rules'])} alertes")
```

## 🔄 Migration depuis Scripts Personnalisés

### Scripts ldapsearch Typiques

```bash
#!/bin/bash
# old-scripts/check-ldap-health.sh

# Variables
LDAP_SERVER="ldap.example.com"
BASE_DN="dc=example,dc=com"
BIND_DN="cn=monitor,dc=example,dc=com"
BIND_PW="password"

# Check connexion
ldapsearch -x -H ldaps://$LDAP_SERVER \
  -D "$BIND_DN" -w "$BIND_PW" \
  -b "$BASE_DN" -s base "(objectclass=*)" || exit 1

# Compter utilisateurs
USER_COUNT=$(ldapsearch -x -H ldaps://$LDAP_SERVER \
  -D "$BIND_DN" -w "$BIND_PW" \
  -b "ou=users,$BASE_DN" "(objectClass=inetOrgPerson)" | \
  grep "numEntries:" | awk '{print $3}')

echo "Users: $USER_COUNT"

# Compter groupes
GROUP_COUNT=$(ldapsearch -x -H ldaps://$LDAP_SERVER \
  -D "$BIND_DN" -w "$BIND_PW" \
  -b "ou=groups,$BASE_DN" "(objectClass=groupOfNames)" | \
  grep "numEntries:" | awk '{print $3}')

echo "Groups: $GROUP_COUNT"
```

### Équivalent LDAP Health Monitor

```yaml
# config/migration-from-scripts.yaml
ldap:
  server: ldaps://ldap.example.com
  port: 636
  bind_dn: cn=monitor,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com

monitoring:
  enabled: true
  interval: 300

  metrics:
    - users_total
    - groups_total
    - response_time
    - connection_status
```

```bash
# Remplacer scripts par commandes LDAP Monitor
ldap-monitor test connection  # Remplace check connexion
ldap-monitor audit users --count  # Remplace comptage users
ldap-monitor audit groups --count  # Remplace comptage groups

# Automatiser avec monitoring daemon
ldap-monitor monitor start --daemon
```

### Script de Conversion Automatique

```python
#!/usr/bin/env python3
# scripts/convert-bash-scripts.py

import re
import yaml
from pathlib import Path

class BashToLDAPMonitor:

    def __init__(self, script_path):
        self.script_path = Path(script_path)
        with open(script_path, 'r') as f:
            self.content = f.read()

        self.config = {
            'ldap': {},
            'monitoring': {'checks': []},
            'audit': {}
        }

    def extract_ldap_params(self):
        """Extraire paramètres LDAP du script bash"""
        patterns = {
            'server': r'LDAP_SERVER[=\s]+"?([^"\s]+)"?',
            'base_dn': r'BASE_DN[=\s]+"?([^"\s]+)"?',
            'bind_dn': r'BIND_DN[=\s]+"?([^"\s]+)"?',
            'port': r':\s*(\d{3,4})'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, self.content)
            if match:
                value = match.group(1)

                # Traitement spécial pour server
                if key == 'server':
                    if not value.startswith('ldap'):
                        value = f'ldaps://{value}'

                self.config['ldap'][key] = value

        # Déterminer SSL
        if 'ldaps://' in self.content or '-ZZ' in self.content:
            self.config['ldap']['use_ssl'] = True

    def extract_checks(self):
        """Extraire les checks du script"""
        checks = []

        # Rechercher ldapsearch
        ldapsearch_pattern = r'ldapsearch\s+([^|]+)'
        searches = re.findall(ldapsearch_pattern, self.content)

        for search in searches:
            check = self._parse_ldapsearch(search)
            if check:
                checks.append(check)

        self.config['monitoring']['checks'] = checks

    def _parse_ldapsearch(self, search_cmd):
        """Parser commande ldapsearch"""
        check = {'type': 'custom'}

        # Base DN
        base_match = re.search(r'-b\s+"?([^"\s]+)"?', search_cmd)
        if base_match:
            base = base_match.group(1)

            # Déterminer type de check
            if 'ou=users' in base.lower() or 'ou=people' in base.lower():
                check['type'] = 'users_count'
                check['name'] = 'User Count Check'
            elif 'ou=groups' in base.lower():
                check['type'] = 'groups_count'
                check['name'] = 'Group Count Check'
            else:
                check['type'] = 'connection'
                check['name'] = 'LDAP Connection Check'

        # Filter
        filter_match = re.search(r'"(\([^)]+\))"', search_cmd)
        if filter_match:
            check['filter'] = filter_match.group(1)

        return check

    def extract_thresholds(self):
        """Extraire seuils d'alerte"""
        # Rechercher comparaisons numériques
        threshold_pattern = r'\[\s*\$(\w+)\s*(-gt|-lt|-ge|-le)\s*(\d+)\s*\]'
        thresholds = re.findall(threshold_pattern, self.content)

        for var, op, value in thresholds:
            alert_type = self._map_threshold_type(var)
            level = 'warning' if op in ['-gt', '-ge'] else 'critical'

            if 'alerts' not in self.config:
                self.config['alerts'] = {'rules': []}

            self.config['alerts']['rules'].append({
                'name': f'{alert_type.title()} Threshold',
                'type': alert_type,
                'operator': op.replace('-', ''),
                'value': int(value),
                'level': level
            })

    def _map_threshold_type(self, var_name):
        """Mapper nom de variable vers type d'alerte"""
        var_lower = var_name.lower()

        if 'user' in var_lower:
            return 'user_count'
        elif 'group' in var_lower:
            return 'group_count'
        elif 'response' in var_lower or 'time' in var_lower:
            return 'response_time'
        else:
            return 'custom'

    def generate_config(self):
        """Générer configuration complète"""
        self.extract_ldap_params()
        self.extract_checks()
        self.extract_thresholds()

        return self.config

    def generate_replacement_script(self):
        """Générer script de remplacement"""
        script = "#!/bin/bash\n"
        script += "# Auto-generated replacement for " + str(self.script_path) + "\n\n"

        # Générer commandes équivalentes
        for check in self.config['monitoring']['checks']:
            if check['type'] == 'connection':
                script += "ldap-monitor test connection\n"
            elif check['type'] == 'users_count':
                script += "ldap-monitor audit users --count\n"
            elif check['type'] == 'groups_count':
                script += "ldap-monitor audit groups --count\n"

        return script

# Usage
converter = BashToLDAPMonitor('old-scripts/check-ldap-health.sh')
config = converter.generate_config()
replacement_script = converter.generate_replacement_script()

# Sauvegarder config
with open('migrated-config.yaml', 'w') as f:
    yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

# Sauvegarder script de remplacement
with open('new-check-script.sh', 'w') as f:
    f.write(replacement_script)

print("✓ Migration terminée")
print(f"  Config: migrated-config.yaml")
print(f"  Script: new-check-script.sh")
```

## 📊 Migration des Données Historiques

### Export depuis Anciens Systèmes

```bash
#!/bin/bash
# scripts/export-historical-data.sh

# Export depuis base de données Zabbix
mysql -u zabbix -p zabbix_db -e "
  SELECT FROM_UNIXTIME(clock) as timestamp, value
  FROM history
  WHERE itemid IN (
    SELECT itemid FROM items
    WHERE key_ LIKE '%ldap%'
  )
  ORDER BY clock DESC
  LIMIT 10000
" > zabbix-ldap-history.csv

# Export depuis logs Nagios
grep "LDAP" /var/log/nagios/nagios.log | \
  awk '{print $1, $2, $NF}' > nagios-ldap-history.csv

echo "✓ Données historiques exportées"
```

### Import dans LDAP Health Monitor

```python
#!/usr/bin/env python3
# scripts/import-historical-data.py

import csv
import sqlite3
from datetime import datetime

def import_to_ldap_monitor(csv_file, db_path):
    """Importer données historiques"""

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Créer table si nécessaire
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS metrics_history (
            timestamp INTEGER,
            metric_name TEXT,
            value REAL,
            source TEXT
        )
    ''')

    # Lire et importer CSV
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)

        for row in reader:
            timestamp = datetime.strptime(
                row['timestamp'],
                '%Y-%m-%d %H:%M:%S'
            ).timestamp()

            cursor.execute('''
                INSERT INTO metrics_history
                (timestamp, metric_name, value, source)
                VALUES (?, ?, ?, ?)
            ''', (
                int(timestamp),
                row.get('metric', 'imported'),
                float(row.get('value', 0)),
                'migration'
            ))

    conn.commit()
    conn.close()

    print(f"✓ Import terminé: {csv_file}")

# Usage
import_to_ldap_monitor(
    'zabbix-ldap-history.csv',
    '/var/lib/ldap-monitor/metrics.db'
)
```

## ✅ Checklist de Migration

### Phase de Préparation

- [ ] Inventorier tous les outils LDAP actuels
- [ ] Documenter configurations existantes
- [ ] Identifier toutes les sources de données
- [ ] Lister tous les destinataires d'alertes
- [ ] Planifier fenêtre de migration
- [ ] Préparer plan de rollback

### Phase de Test

- [ ] Installer LDAP Health Monitor en environnement de test
- [ ] Migrer configuration
- [ ] Tester tous les checks
- [ ] Valider les alertes
- [ ] Comparer résultats avec système actuel
- [ ] Ajuster les seuils si nécessaire

### Phase de Migration

- [ ] Déployer en production (parallèle)
- [ ] Monitorer pendant période d'observation (48-72h)
- [ ] Vérifier concordance des résultats
- [ ] Former les équipes
- [ ] Basculer complètement
- [ ] Désactiver ancien système

### Phase Post-Migration

- [ ] Vérifier toutes les alertes fonctionnent
- [ ] Confirmer réception des notifications
- [ ] Optimiser la configuration
- [ ] Documenter les changements
- [ ] Archiver anciennes configurations
- [ ] Désinstaller anciens outils (après période de rétention)

## 🔧 Dépannage Migration

### Problèmes Courants

**Les seuils ne correspondent pas**
```bash
# Comparer résultats
./scripts/compare-thresholds.sh

# Ajuster dans config
vim config/monitoring-config.yaml
```

**Alertes manquantes**
```bash
# Vérifier configuration alertes
ldap-monitor config validate --section alerts

# Tester manuellement
ldap-monitor alerts test
```

**Données historiques incorrectes**
```bash
# Vérifier import
sqlite3 /var/lib/ldap-monitor/metrics.db "SELECT COUNT(*) FROM metrics_history"

# Réimporter si nécessaire
./scripts/import-historical-data.py --reimport
```

## 📖 Voir Aussi

- [Configuration LDAP](../configuration/LDAP-Configuration.md)
- [Monitoring](../features/monitoring/Overview.md)
- [Automation](Cron-Automation.md)
- [Production Deployment](Production-Monitoring.md)
