# Guide OpenLDAP

Configuration et utilisation de LDAP Health Monitor avec OpenLDAP.

## 🎯 Spécificités OpenLDAP

OpenLDAP est l'implémentation open-source la plus utilisée du protocole LDAP :

- **Schéma** : Flexibilité dans la définition des schemas
- **Backends** : Support de multiples backends (MDB, BDB, etc.)
- **Overlays** : Modules d'extension puissants
- **Réplication** : SyncRepl pour synchronisation multi-maître
- **Performance** : Très haute performance avec backend MDB

## ⚙️ Configuration pour OpenLDAP

### Configuration Minimale

```yaml
# config/openldap-config.yaml
ldap:
  # Connexion
  server: ldaps://ldap.example.com
  port: 636
  use_ssl: true
  use_tls: false

  # Authentification
  bind_dn: cn=monitor,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}

  # Base DN
  base_dn: dc=example,dc=com

  # Structure
  users_ou: ou=users,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com

  # Schéma OpenLDAP standard
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
  user_uid_attribute: uid
  group_member_attribute: member

  # Performance
  timeout: 10
  retry_max: 3
  retry_delay: 2
  page_size: 500
  search_scope: SUBTREE
```

### Configuration Avancée

```yaml
# config/openldap-advanced.yaml
ldap:
  # Connexion avec failover
  servers:
    - uri: ldaps://ldap01.example.com:636
      priority: 1
    - uri: ldaps://ldap02.example.com:636
      priority: 2

  bind_dn: cn=monitor,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com

  # StartTLS (alternative à LDAPS)
  use_ssl: false
  use_tls: true
  tls_require_cert: demand
  tls_cacert_file: /etc/ssl/certs/ca-bundle.crt

  # Structure organisationnelle
  users_ou: ou=people,dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com
  services_ou: ou=services,dc=example,dc=com

  # Schéma
  user_objectclass: inetOrgPerson
  group_objectclass: groupOfNames
  posix_account_objectclass: posixAccount
  posix_group_objectclass: posixGroup

  user_uid_attribute: uid
  group_member_attribute: member
  group_memberuid_attribute: memberUid

  # Options avancées
  timeout: 15
  network_timeout: 5
  retry_max: 5
  retry_delay: 3
  page_size: 1000
  search_scope: SUBTREE
  deref_aliases: never
  follow_referrals: false

  # Pool de connexions
  pool_size: 20
  pool_lifetime: 3600

# Audit OpenLDAP
audit:
  # Attributs utilisateurs
  required_user_attributes:
    - uid
    - cn
    - sn
    - mail
    - userPassword
    - uidNumber
    - gidNumber
    - homeDirectory
    - loginShell

  # Attributs groupes
  required_group_attributes:
    - cn
    - member
    - gidNumber

  # Seuils
  thresholds:
    inactive_days: 90
    password_age_warning: 80
    password_age_critical: 90

  # Sécurité
  security:
    check_password_policies: true
    check_acls: true
    alert_on_privilege_escalation: true
    privileged_dns:
      - cn=admin,dc=example,dc=com
      - cn=Manager,dc=example,dc=com

# Monitoring OpenLDAP
monitoring:
  enabled: true

  # Connexion cn=Monitor
  monitor_dn: cn=Monitor
  monitor_enabled: true

  # Métriques spécifiques OpenLDAP
  metrics:
    - connections_current
    - connections_total
    - operations_initiated
    - operations_completed
    - entries_sent
    - bytes_sent
    - threads_active
    - threads_pending
    - database_entries

  # Checks
  checks:
    - name: backend_status
      type: backend
      backend: mdb
      interval: 300

    - name: overlay_status
      type: overlay
      overlays: [syncprov, accesslog, memberof]
      interval: 600

    - name: replication_status
      type: replication
      interval: 300
```

## 🔐 Configuration du Serveur OpenLDAP

### Installation OpenLDAP

```bash
#!/bin/bash
# scripts/install-openldap.sh

# Ubuntu/Debian
apt-get update
apt-get install -y slapd ldap-utils

# RHEL/CentOS/Rocky
yum install -y openldap openldap-servers openldap-clients

# Configuration initiale
dpkg-reconfigure slapd

# Vérification
slaptest -u
systemctl status slapd
```

### Configuration Base (slapd.conf)

```
# /etc/ldap/slapd.conf (style ancien)

# Includes
include /etc/ldap/schema/core.schema
include /etc/ldap/schema/cosine.schema
include /etc/ldap/schema/inetorgperson.schema
include /etc/ldap/schema/nis.schema

# Module paths
modulepath /usr/lib/ldap
moduleload back_mdb
moduleload memberof
moduleload refint

# Logging
loglevel stats sync

# Database definition
database mdb
suffix "dc=example,dc=com"
rootdn "cn=admin,dc=example,dc=com"
rootpw {SSHA}SecureHashedPassword

# Directory
directory /var/lib/ldap

# Indices
index objectClass eq
index cn,sn,mail eq,pres,sub
index uidNumber,gidNumber eq
index memberUid eq
index member,memberOf eq

# Access Control
access to attrs=userPassword
    by self write
    by anonymous auth
    by * none

access to *
    by self write
    by users read
    by * none

# Size limits
sizelimit 500
```

### Configuration Moderne (cn=config)

```ldif
# Configuration via cn=config (OLC)

# Base database config
dn: olcDatabase={1}mdb,cn=config
objectClass: olcDatabaseConfig
objectClass: olcMdbConfig
olcDatabase: {1}mdb
olcSuffix: dc=example,dc=com
olcRootDN: cn=admin,dc=example,dc=com
olcRootPW: {SSHA}SecureHashedPassword
olcDbDirectory: /var/lib/ldap
olcDbIndex: objectClass eq
olcDbIndex: cn,sn,mail eq,pres,sub
olcDbIndex: uidNumber,gidNumber eq
olcDbIndex: memberUid eq
olcDbIndex: member,memberOf eq
olcDbMaxSize: 1073741824

# Monitoring
dn: cn=module{0},cn=config
objectClass: olcModuleList
cn: module{0}
olcModulePath: /usr/lib/ldap
olcModuleLoad: back_monitor.la

# MemberOf overlay
dn: olcOverlay=memberof,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcMemberOf
olcOverlay: memberof
olcMemberOfDangling: ignore
olcMemberOfRefInt: TRUE
olcMemberOfGroupOC: groupOfNames
olcMemberOfMemberAD: member
olcMemberOfMemberOfAD: memberOf

# Access Log overlay (pour réplication)
dn: olcOverlay=accesslog,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcAccessLogConfig
olcOverlay: accesslog
olcAccessLogDB: cn=accesslog
olcAccessLogOps: writes
olcAccessLogSuccess: TRUE
olcAccessLogPurge: 07+00:00 01+00:00

# SyncProv overlay (réplication)
dn: olcOverlay=syncprov,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcSyncProvConfig
olcOverlay: syncprov
olcSpCheckpoint: 100 10
olcSpSessionlog: 100
```

### Créer Compte de Monitoring

```bash
#!/bin/bash
# scripts/create-monitor-account.sh

# Créer fichier LDIF
cat > monitor-account.ldif << 'EOF'
dn: cn=monitor,dc=example,dc=com
objectClass: simpleSecurityObject
objectClass: organizationalRole
cn: monitor
description: LDAP Monitoring Account
userPassword: {SSHA}GeneratedHashHere
EOF

# Générer hash du mot de passe
PASSWORD_HASH=$(slappasswd -s "YourSecurePassword")
sed -i "s|{SSHA}GeneratedHashHere|$PASSWORD_HASH|" monitor-account.ldif

# Ajouter au serveur
ldapadd -x -D "cn=admin,dc=example,dc=com" -W -f monitor-account.ldif

# Vérifier
ldapsearch -x -D "cn=monitor,dc=example,dc=com" -W \
    -b "dc=example,dc=com" -s base "(objectClass=*)"

echo "✓ Compte de monitoring créé"
```

### Permissions pour Monitoring

```ldif
# acl-monitoring.ldif
# ACL pour compte de monitoring (lecture seule)

dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcAccess
olcAccess: {0}to dn.subtree="dc=example,dc=com"
  by dn.exact="cn=monitor,dc=example,dc=com" read
  by * break

olcAccess: {1}to dn.subtree="cn=Monitor"
  by dn.exact="cn=monitor,dc=example,dc=com" read
  by * none

olcAccess: {2}to attrs=userPassword
  by self write
  by anonymous auth
  by dn.exact="cn=monitor,dc=example,dc=com" read
  by * none

olcAccess: {3}to *
  by self write
  by dn.exact="cn=monitor,dc=example,dc=com" read
  by users read
  by * none
```

```bash
# Appliquer ACL
ldapmodify -Y EXTERNAL -H ldapi:/// -f acl-monitoring.ldif
```

## 🔍 Monitoring Backend cn=Monitor

### Accéder aux Métriques

```bash
# Métriques de connexion
ldapsearch -x -D "cn=monitor,dc=example,dc=com" -W \
    -b "cn=Monitor" \
    "(objectClass=*)" \
    monitorCounter monitorOpInitiated monitorOpCompleted

# Connexions actives
ldapsearch -x -D "cn=monitor,dc=example,dc=com" -W \
    -b "cn=Current,cn=Connections,cn=Monitor" \
    monitorCounter

# Statistiques operations
ldapsearch -x -D "cn=monitor,dc=example,dc=com" -W \
    -b "cn=Operations,cn=Monitor" \
    monitorOpInitiated monitorOpCompleted

# Statistiques database
ldapsearch -x -D "cn=monitor,dc=example,dc=com" -W \
    -b "cn=Database 1,cn=Databases,cn=Monitor" \
    olmMDBEntries olmMDBPagesUsed
```

### Script de Collecte Métriques

```python
#!/usr/bin/env python3
# scripts/collect-openldap-metrics.py

import ldap
import sys
from datetime import datetime

class OpenLDAPMonitor:

    def __init__(self, uri, bind_dn, bind_pw):
        self.uri = uri
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw
        self.conn = None

    def connect(self):
        """Connexion au serveur"""
        try:
            self.conn = ldap.initialize(self.uri)
            self.conn.simple_bind_s(self.bind_dn, self.bind_pw)
            return True
        except ldap.LDAPError as e:
            print(f"Connection error: {e}")
            return False

    def get_connections(self):
        """Obtenir nombre de connexions"""
        try:
            result = self.conn.search_s(
                'cn=Current,cn=Connections,cn=Monitor',
                ldap.SCOPE_BASE,
                '(objectClass=*)',
                ['monitorCounter']
            )

            if result:
                counter = result[0][1].get('monitorCounter', [b'0'])[0]
                return int(counter.decode('utf-8'))

            return 0

        except ldap.LDAPError as e:
            print(f"Error getting connections: {e}")
            return -1

    def get_operations(self):
        """Obtenir statistiques opérations"""
        metrics = {}

        operations = [
            'Bind', 'Unbind', 'Search', 'Compare',
            'Modify', 'ModDN', 'Add', 'Delete'
        ]

        for op in operations:
            try:
                dn = f'cn={op},cn=Operations,cn=Monitor'
                result = self.conn.search_s(
                    dn,
                    ldap.SCOPE_BASE,
                    '(objectClass=*)',
                    ['monitorOpInitiated', 'monitorOpCompleted']
                )

                if result:
                    attrs = result[0][1]
                    initiated = int(attrs.get('monitorOpInitiated', [b'0'])[0])
                    completed = int(attrs.get('monitorOpCompleted', [b'0'])[0])

                    metrics[op.lower()] = {
                        'initiated': initiated,
                        'completed': completed
                    }

            except ldap.LDAPError as e:
                print(f"Error getting {op} stats: {e}")

        return metrics

    def get_database_stats(self):
        """Obtenir statistiques database"""
        try:
            # Backend MDB
            result = self.conn.search_s(
                'cn=Database 1,cn=Databases,cn=Monitor',
                ldap.SCOPE_BASE,
                '(objectClass=*)',
                ['olmMDBEntries', 'olmMDBPagesUsed', 'olmMDBPagesMax']
            )

            if result:
                attrs = result[0][1]
                return {
                    'entries': int(attrs.get('olmMDBEntries', [b'0'])[0]),
                    'pages_used': int(attrs.get('olmMDBPagesUsed', [b'0'])[0]),
                    'pages_max': int(attrs.get('olmMDBPagesMax', [b'0'])[0])
                }

        except ldap.LDAPError as e:
            print(f"Error getting database stats: {e}")

        return {}

    def get_threads(self):
        """Obtenir info threads"""
        try:
            result = self.conn.search_s(
                'cn=Threads,cn=Monitor',
                ldap.SCOPE_BASE,
                '(objectClass=*)',
                ['monitoredInfo']
            )

            if result:
                info = result[0][1].get('monitoredInfo', [b''])[0]
                return info.decode('utf-8')

        except ldap.LDAPError as e:
            print(f"Error getting threads: {e}")

        return ""

    def collect_all(self):
        """Collecter toutes les métriques"""
        if not self.connect():
            return None

        metrics = {
            'timestamp': datetime.now().isoformat(),
            'connections': self.get_connections(),
            'operations': self.get_operations(),
            'database': self.get_database_stats(),
            'threads': self.get_threads()
        }

        self.conn.unbind_s()
        return metrics

    def print_metrics(self, metrics):
        """Afficher métriques"""
        if not metrics:
            return

        print(f"=== OpenLDAP Metrics - {metrics['timestamp']} ===\n")

        print(f"Connections: {metrics['connections']}")
        print(f"Threads: {metrics['threads']}\n")

        print("Operations:")
        for op, stats in metrics['operations'].items():
            print(f"  {op.title():10} - Initiated: {stats['initiated']:8} "
                  f"Completed: {stats['completed']:8}")

        print("\nDatabase:")
        db = metrics['database']
        if db:
            print(f"  Entries: {db.get('entries', 0)}")
            print(f"  Pages Used: {db.get('pages_used', 0)}")
            print(f"  Pages Max: {db.get('pages_max', 0)}")
            if db.get('pages_max', 0) > 0:
                usage = (db.get('pages_used', 0) / db.get('pages_max', 1)) * 100
                print(f"  Usage: {usage:.2f}%")

# Usage
if __name__ == '__main__':
    monitor = OpenLDAPMonitor(
        'ldaps://ldap.example.com',
        'cn=monitor,dc=example,dc=com',
        'password'
    )

    metrics = monitor.collect_all()
    monitor.print_metrics(metrics)
```

## 🔄 Configuration Réplication

### Master-Slave (Provider-Consumer)

```ldif
# Provider configuration
dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcSyncRepl
olcSyncRepl: rid=001
  provider=ldaps://slave.example.com:636
  bindmethod=simple
  binddn="cn=replicator,dc=example,dc=com"
  credentials=SecurePassword
  searchbase="dc=example,dc=com"
  scope=sub
  schemachecking=on
  type=refreshAndPersist
  retry="60 +"
  timeout=1

# Consumer configuration
dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcUpdateRef
olcUpdateRef: ldaps://master.example.com:636
```

### Multi-Master

```ldif
# Server 1
dn: cn=config
changetype: modify
replace: olcServerID
olcServerID: 1 ldaps://ldap01.example.com

dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcSyncRepl
olcSyncRepl: rid=001
  provider=ldaps://ldap02.example.com:636
  bindmethod=simple
  binddn="cn=replicator,dc=example,dc=com"
  credentials=SecurePassword
  searchbase="dc=example,dc=com"
  type=refreshAndPersist
  retry="60 +"

add: olcMirrorMode
olcMirrorMode: TRUE

# Server 2
dn: cn=config
changetype: modify
replace: olcServerID
olcServerID: 2 ldaps://ldap02.example.com

dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcSyncRepl
olcSyncRepl: rid=002
  provider=ldaps://ldap01.example.com:636
  bindmethod=simple
  binddn="cn=replicator,dc=example,dc=com"
  credentials=SecurePassword
  searchbase="dc=example,dc=com"
  type=refreshAndPersist
  retry="60 +"

add: olcMirrorMode
olcMirrorMode: TRUE
```

### Test de Réplication

```bash
#!/bin/bash
# scripts/test-replication.sh

MASTER="ldaps://ldap01.example.com"
SLAVE="ldaps://ldap02.example.com"
BIND_DN="cn=admin,dc=example,dc=com"
BIND_PW="password"
BASE_DN="dc=example,dc=com"

# Créer entrée test sur master
TEST_DN="cn=test-repl-$(date +%s),ou=users,$BASE_DN"

cat > test-entry.ldif << EOF
dn: $TEST_DN
objectClass: inetOrgPerson
cn: test-repl-$(date +%s)
sn: Test
mail: test@example.com
EOF

# Ajouter sur master
ldapadd -H "$MASTER" -D "$BIND_DN" -w "$BIND_PW" -f test-entry.ldif

# Attendre réplication (ajuster selon besoin)
sleep 5

# Vérifier sur slave
if ldapsearch -H "$SLAVE" -D "$BIND_DN" -w "$BIND_PW" \
    -b "$TEST_DN" -s base "(objectClass=*)" > /dev/null 2>&1; then
    echo "✓ Replication OK"
else
    echo "✗ Replication FAILED"
fi

# Nettoyage
ldapdelete -H "$MASTER" -D "$BIND_DN" -w "$BIND_PW" "$TEST_DN"
```

## 🛠️ Opérations avec LDAP Health Monitor

### Audit Complet OpenLDAP

```bash
# Health check
ldap-monitor audit health

# Audit utilisateurs
ldap-monitor audit users --all

# Audit groupes
ldap-monitor audit groups --all

# Audit structure
ldap-monitor audit structure

# Audit sécurité
ldap-monitor audit security --comprehensive

# Rapport complet
ldap-monitor audit all \
    --format html \
    --output /var/reports/openldap-audit-$(date +%Y%m%d).html
```

### Monitoring Continu

```bash
# Démarrer monitoring daemon
ldap-monitor monitor start --daemon

# Métriques en temps réel
ldap-monitor monitor metrics --live

# Historique métriques
ldap-monitor monitor history --days 7

# Alertes
ldap-monitor monitor alerts --active
```

## 📖 Voir Aussi

- [Active Directory Guide](Active-Directory.md)
- [FreeIPA Guide](FreeIPA.md)
- [Performance Tuning](Performance-Tuning.md)
- [Configuration](../configuration/LDAP-Configuration.md)
