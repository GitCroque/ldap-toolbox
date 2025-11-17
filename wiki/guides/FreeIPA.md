# Guide FreeIPA

Configuration et utilisation de LDAP Health Monitor avec FreeIPA (Red Hat Identity Management).

## 🎯 Spécificités FreeIPA

FreeIPA est une solution d'identité intégrée combinant LDAP, Kerberos, DNS, et PKI :

- **LDAP Backend** : Basé sur 389 Directory Server (fork de OpenLDAP)
- **Kerberos** : Authentification SSO intégrée
- **DNS** : Gestion DNS intégrée
- **Certificats** : Autorité de certification intégrée
- **Politiques** : Gestion centralisée des politiques
- **HBAC** : Host-Based Access Control

## ⚙️ Configuration pour FreeIPA

### Configuration Minimale

```yaml
# config/freeipa-config.yaml
ldap:
  # Connexion au serveur FreeIPA
  server: ldaps://ipa.example.com
  port: 636
  use_ssl: true
  use_tls: false

  # Authentification
  # Option 1: Compte LDAP
  bind_dn: uid=admin,cn=users,cn=accounts,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}

  # Base DN FreeIPA
  base_dn: dc=example,dc=com

  # Structure FreeIPA
  users_ou: cn=users,cn=accounts,dc=example,dc=com
  groups_ou: cn=groups,cn=accounts,dc=example,dc=com

  # Schéma FreeIPA
  user_objectclass: person
  group_objectclass: groupOfNames
  user_uid_attribute: uid
  group_member_attribute: member

  # Performance
  timeout: 15
  retry_max: 3
  retry_delay: 3
  page_size: 1000
  search_scope: SUBTREE
```

### Configuration Avancée

```yaml
# config/freeipa-advanced.yaml
ldap:
  # Serveurs multiples (réplication FreeIPA)
  servers:
    - uri: ldaps://ipa01.example.com:636
      priority: 1
    - uri: ldaps://ipa02.example.com:636
      priority: 2
    - uri: ldaps://ipa03.example.com:636
      priority: 3

  # Authentification avec Kerberos (optionnel)
  bind_method: sasl
  sasl_mechanism: GSSAPI
  # OU authentification simple
  bind_dn: uid=ldap-monitor,cn=users,cn=accounts,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}

  base_dn: dc=example,dc=com

  # Structure complète FreeIPA
  users_ou: cn=users,cn=accounts,dc=example,dc=com
  groups_ou: cn=groups,cn=accounts,dc=example,dc=com
  hosts_ou: cn=computers,cn=accounts,dc=example,dc=com
  services_ou: cn=services,cn=accounts,dc=example,dc=com
  sudo_ou: cn=sudorules,cn=sudo,dc=example,dc=com

  # Object classes FreeIPA
  user_objectclass: ipaUser
  group_objectclass: ipaUserGroup
  host_objectclass: ipaHost
  service_objectclass: ipaService

  # Attributs
  user_uid_attribute: uid
  group_member_attribute: member
  host_fqdn_attribute: fqdn

  # SSL/TLS
  use_ssl: true
  verify_ssl: true
  ca_cert: /etc/ipa/ca.crt
  client_cert: /etc/ipa/client.pem
  client_key: /etc/ipa/client.key

  # Options avancées
  timeout: 20
  network_timeout: 10
  retry_max: 5
  retry_delay: 5
  page_size: 1000
  search_scope: SUBTREE
  follow_referrals: true

# Audit FreeIPA
audit:
  # Attributs utilisateurs FreeIPA
  required_user_attributes:
    - uid
    - givenName
    - sn
    - cn
    - mail
    - krbPrincipalName
    - uidNumber
    - gidNumber
    - homeDirectory
    - loginShell
    - memberOf

  # Attributs groupes FreeIPA
  required_group_attributes:
    - cn
    - description
    - member
    - gidNumber

  # Seuils
  thresholds:
    inactive_days: 90
    password_age_warning: 80
    password_age_critical: 90
    kerberos_ticket_warning: 7

  # Sécurité FreeIPA
  security:
    check_kerberos_principals: true
    check_sudo_rules: true
    check_hbac_rules: true
    check_certificates: true
    privileged_groups:
      - cn=admins,cn=groups,cn=accounts,dc=example,dc=com
      - cn=trust admins,cn=groups,cn=accounts,dc=example,dc=com

# Monitoring FreeIPA
monitoring:
  enabled: true

  # Métriques spécifiques FreeIPA
  metrics:
    - users_total
    - groups_total
    - hosts_total
    - services_total
    - sudo_rules_total
    - hbac_rules_total
    - kerberos_principals_total
    - replication_agreements
    - replication_status

  # Checks FreeIPA
  checks:
    - name: ipa_health
      type: freeipa_health
      interval: 300

    - name: replication_status
      type: freeipa_replication
      interval: 600

    - name: certificate_expiry
      type: certificate
      interval: 3600
      warning_days: 30
      critical_days: 7

    - name: kerberos_kdcinfo
      type: kerberos
      interval: 300
```

## 🔐 Configuration FreeIPA Server

### Installation FreeIPA

```bash
#!/bin/bash
# scripts/install-freeipa.sh

# RHEL/CentOS/Rocky Linux
yum install -y ipa-server ipa-server-dns

# Configuration serveur principal
ipa-server-install \
    --domain=example.com \
    --realm=EXAMPLE.COM \
    --ds-password='DirectoryManagerPassword' \
    --admin-password='AdminPassword' \
    --hostname=ipa.example.com \
    --ip-address=192.168.1.10 \
    --setup-dns \
    --forwarder=8.8.8.8 \
    --forwarder=8.8.4.4 \
    --mkhomedir \
    --unattended

# Vérification
ipactl status
kinit admin
ipa user-find
```

### Créer Compte de Monitoring

```bash
#!/bin/bash
# scripts/create-ipa-monitor-account.sh

# S'authentifier en tant qu'admin
kinit admin

# Créer utilisateur de monitoring
ipa user-add ldap-monitor \
    --first=LDAP \
    --last=Monitor \
    --email=ldap-monitor@example.com \
    --password

# Créer rôle de monitoring (lecture seule)
ipa role-add "LDAP Monitor Role" \
    --desc="Read-only monitoring access"

# Ajouter privilèges de lecture
ipa privilege-add "LDAP Read Privilege" \
    --desc="Read access to LDAP"

# Associer permissions au privilège
ipa privilege-add-permission "LDAP Read Privilege" \
    --permissions="System: Read User" \
    --permissions="System: Read Group" \
    --permissions="System: Read Host" \
    --permissions="System: Read Service"

# Associer privilège au rôle
ipa role-add-privilege "LDAP Monitor Role" \
    --privileges="LDAP Read Privilege"

# Ajouter utilisateur au rôle
ipa role-add-member "LDAP Monitor Role" \
    --users=ldap-monitor

# Vérifier
ipa user-show ldap-monitor
ipa role-show "LDAP Monitor Role"

echo "✓ Compte de monitoring créé"
```

### Configuration Réplication FreeIPA

```bash
# Installation replica
ipa-replica-install \
    --setup-ca \
    --setup-dns \
    --forwarder=8.8.8.8 \
    --principal=admin \
    --admin-password='AdminPassword' \
    --unattended

# Vérifier réplication
ipa-replica-manage list
ipa-csreplica-manage list

# Tester réplication LDAP
ipa-replica-manage list -v
```

## 🔍 Audit avec FreeIPA

### Commandes IPA CLI

```bash
# Lister tous les utilisateurs
ipa user-find --all

# Utilisateurs inactifs
ipa user-find --disabled=true

# Groupes et membres
ipa group-find --all
ipa group-show admins --all

# Hôtes
ipa host-find

# Services
ipa service-find

# Règles SUDO
ipa sudorule-find

# Règles HBAC
ipa hbacrule-find

# Certificats
ipa cert-find

# Politiques de mots de passe
ipa pwpolicy-show
```

### Script d'Audit FreeIPA

```python
#!/usr/bin/env python3
# scripts/audit-freeipa.py

import subprocess
import json
from datetime import datetime, timedelta

class FreeIPAAuditor:

    def __init__(self):
        self.kinit_done = False

    def kinit(self, principal='admin', keytab=None):
        """Authentification Kerberos"""
        try:
            if keytab:
                cmd = ['kinit', '-k', '-t', keytab, principal]
            else:
                cmd = ['kinit', principal]

            subprocess.run(cmd, check=True)
            self.kinit_done = True
            return True

        except subprocess.CalledProcessError as e:
            print(f"Kinit failed: {e}")
            return False

    def run_ipa_command(self, command):
        """Exécuter commande IPA"""
        if not self.kinit_done:
            print("Not authenticated. Run kinit() first.")
            return None

        try:
            # Format JSON pour parsing facile
            cmd = ['ipa', '-v'] + command + ['--raw', '--all']
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            # Parser sortie
            # Note: IPA CLI ne retourne pas toujours du JSON valide
            # Adapter selon besoin
            return result.stdout

        except subprocess.CalledProcessError as e:
            print(f"IPA command failed: {e}")
            return None

    def audit_users(self):
        """Audit des utilisateurs"""
        print("=== User Audit ===\n")

        # Tous les utilisateurs
        output = self.run_ipa_command(['user-find'])
        if output:
            # Parser output (simplifié)
            lines = output.split('\n')
            user_count = len([l for l in lines if 'User login:' in l])
            print(f"Total users: {user_count}")

        # Utilisateurs désactivés
        output = self.run_ipa_command(['user-find', '--disabled=true'])
        if output:
            lines = output.split('\n')
            disabled_count = len([l for l in lines if 'User login:' in l])
            print(f"Disabled users: {disabled_count}")

        # Utilisateurs sans email
        output = self.run_ipa_command(['user-find', '--email='])
        if output:
            print("Users without email found")

    def audit_groups(self):
        """Audit des groupes"""
        print("\n=== Group Audit ===\n")

        # Tous les groupes
        output = self.run_ipa_command(['group-find'])
        if output:
            lines = output.split('\n')
            group_count = len([l for l in lines if 'Group name:' in l])
            print(f"Total groups: {group_count}")

        # Groupes privilégiés
        privileged_groups = ['admins', 'trust admins', 'editors']
        for group in privileged_groups:
            output = self.run_ipa_command(['group-show', group])
            if output:
                print(f"\nPrivileged group: {group}")
                # Extraire membres
                members = [
                    l.strip().replace('Member users:', '').strip()
                    for l in output.split('\n')
                    if 'Member users:' in l
                ]
                if members:
                    print(f"  Members: {members[0]}")

    def audit_sudo_rules(self):
        """Audit règles SUDO"""
        print("\n=== SUDO Rules Audit ===\n")

        output = self.run_ipa_command(['sudorule-find', '--enabled=true'])
        if output:
            lines = output.split('\n')
            sudo_count = len([l for l in lines if 'Rule name:' in l])
            print(f"Enabled SUDO rules: {sudo_count}")

            # Extraire règles
            rules = [
                l.strip().replace('Rule name:', '').strip()
                for l in lines
                if 'Rule name:' in l
            ]

            for rule in rules[:5]:  # Top 5
                print(f"  - {rule}")

    def audit_hbac_rules(self):
        """Audit règles HBAC"""
        print("\n=== HBAC Rules Audit ===\n")

        output = self.run_ipa_command(['hbacrule-find', '--enabled=true'])
        if output:
            lines = output.split('\n')
            hbac_count = len([l for l in lines if 'Rule name:' in l])
            print(f"Enabled HBAC rules: {hbac_count}")

    def audit_certificates(self):
        """Audit certificats"""
        print("\n=== Certificate Audit ===\n")

        output = self.run_ipa_command(['cert-find'])
        if output:
            lines = output.split('\n')
            cert_count = len([l for l in lines if 'Serial number:' in l])
            print(f"Total certificates: {cert_count}")

        # Certificats expirant bientôt (via certmonger)
        try:
            result = subprocess.run(
                ['getcert', 'list'],
                capture_output=True,
                text=True
            )

            if 'expires' in result.stdout:
                print("\nCertificate expiration status:")
                # Parser getcert output
                for line in result.stdout.split('\n'):
                    if 'expires' in line:
                        print(f"  {line.strip()}")

        except Exception as e:
            print(f"Could not check certificate expiry: {e}")

    def audit_replication(self):
        """Audit réplication"""
        print("\n=== Replication Audit ===\n")

        try:
            # Liste des agreements
            result = subprocess.run(
                ['ipa-replica-manage', 'list'],
                capture_output=True,
                text=True,
                check=True
            )

            print("Replication agreements:")
            print(result.stdout)

            # Status détaillé
            result = subprocess.run(
                ['ipa-replica-manage', 'list', '-v'],
                capture_output=True,
                text=True
            )

            if 'last update status' in result.stdout.lower():
                print("\nReplication status:")
                for line in result.stdout.split('\n'):
                    if 'update' in line.lower() or 'status' in line.lower():
                        print(f"  {line.strip()}")

        except subprocess.CalledProcessError as e:
            print(f"Could not check replication: {e}")

    def run_full_audit(self):
        """Exécuter audit complet"""
        print(f"=== FreeIPA Audit - {datetime.now()} ===\n")

        self.audit_users()
        self.audit_groups()
        self.audit_sudo_rules()
        self.audit_hbac_rules()
        self.audit_certificates()
        self.audit_replication()

        print("\n=== Audit Complete ===")

# Usage
if __name__ == '__main__':
    auditor = FreeIPAAuditor()

    # Authentification (utiliser keytab en production)
    if auditor.kinit('admin'):
        auditor.run_full_audit()
    else:
        print("Authentication failed")
```

## 🔌 Intégration avec LDAP Health Monitor

### Configuration Kerberos (optionnel)

```yaml
# config/freeipa-kerberos.yaml
ldap:
  server: ldaps://ipa.example.com
  port: 636

  # Authentification SASL/GSSAPI
  bind_method: sasl
  sasl_mechanism: GSSAPI
  sasl_realm: EXAMPLE.COM

  # Ou utiliser keytab
  use_keytab: true
  keytab_file: /etc/ldap-monitor/ldap-monitor.keytab
  principal: ldap-monitor@EXAMPLE.COM

  base_dn: dc=example,dc=com
```

### Script de Configuration Kerberos

```bash
#!/bin/bash
# scripts/setup-kerberos-auth.sh

# S'authentifier en tant qu'admin
kinit admin

# Créer principal pour service
ipa service-add ldap-monitor/$(hostname)@EXAMPLE.COM

# Générer keytab
ipa-getkeytab \
    -s ipa.example.com \
    -p ldap-monitor/$(hostname)@EXAMPLE.COM \
    -k /etc/ldap-monitor/ldap-monitor.keytab

# Permissions
chown ldapmon:ldapmon /etc/ldap-monitor/ldap-monitor.keytab
chmod 600 /etc/ldap-monitor/ldap-monitor.keytab

# Test
kinit -k -t /etc/ldap-monitor/ldap-monitor.keytab \
    ldap-monitor/$(hostname)@EXAMPLE.COM

klist

echo "✓ Kerberos authentication configured"
```

## 📊 Monitoring FreeIPA

### Health Check FreeIPA

```bash
# Status général
ipactl status

# Health check intégré
ipa-healthcheck --failures-only

# Output JSON
ipa-healthcheck --output-type=json --output-file=/tmp/ipa-health.json

# Sources spécifiques
ipa-healthcheck --source=ipahealthcheck.ipa.roles
ipa-healthcheck --source=ipahealthcheck.ipa.replication
ipa-healthcheck --source=ipahealthcheck.ipa.certificates
```

### Intégration avec LDAP Monitor

```python
#!/usr/bin/env python3
# scripts/freeipa-health-integration.py

import subprocess
import json
import sys

def run_ipa_healthcheck():
    """Exécuter ipa-healthcheck et parser résultat"""
    try:
        result = subprocess.run(
            ['ipa-healthcheck', '--output-type=json'],
            capture_output=True,
            text=True,
            check=True
        )

        checks = json.loads(result.stdout)
        return checks

    except subprocess.CalledProcessError as e:
        print(f"Health check failed: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"Failed to parse health check output: {e}")
        return []

def analyze_health_results(checks):
    """Analyser résultats"""
    critical = []
    warnings = []
    success = []

    for check in checks:
        result = check.get('result', 'UNKNOWN')
        source = check.get('source', 'unknown')
        check_name = check.get('check', 'unknown')

        if result == 'ERROR' or result == 'CRITICAL':
            critical.append({
                'source': source,
                'check': check_name,
                'kw': check.get('kw', {})
            })
        elif result == 'WARNING':
            warnings.append({
                'source': source,
                'check': check_name,
                'kw': check.get('kw', {})
            })
        elif result == 'SUCCESS':
            success.append({
                'source': source,
                'check': check_name
            })

    return {
        'critical': critical,
        'warnings': warnings,
        'success': success,
        'total': len(checks)
    }

def print_summary(analysis):
    """Afficher résumé"""
    print("=== FreeIPA Health Check Summary ===\n")
    print(f"Total checks: {analysis['total']}")
    print(f"Success: {len(analysis['success'])}")
    print(f"Warnings: {len(analysis['warnings'])}")
    print(f"Critical: {len(analysis['critical'])}")

    if analysis['critical']:
        print("\n⚠️  CRITICAL ISSUES:")
        for issue in analysis['critical']:
            print(f"  - {issue['source']}.{issue['check']}")
            if issue['kw']:
                print(f"    Details: {issue['kw']}")

    if analysis['warnings']:
        print("\n⚠️  WARNINGS:")
        for warning in analysis['warnings']:
            print(f"  - {warning['source']}.{warning['check']}")

    # Exit code pour monitoring
    if analysis['critical']:
        return 2
    elif analysis['warnings']:
        return 1
    else:
        return 0

# Usage
if __name__ == '__main__':
    checks = run_ipa_healthcheck()
    if checks:
        analysis = analyze_health_results(checks)
        exit_code = print_summary(analysis)
        sys.exit(exit_code)
    else:
        print("No health check results")
        sys.exit(3)
```

## 🛠️ Opérations avec FreeIPA

### Audit via LDAP Monitor

```bash
# Health check FreeIPA
ldap-monitor audit health --freeipa-native

# Audit utilisateurs
ldap-monitor audit users \
    --include-kerberos \
    --check-principals

# Audit groupes avec HBAC
ldap-monitor audit groups \
    --check-hbac-rules

# Audit hôtes
ldap-monitor audit hosts \
    --check-certificates

# Audit règles SUDO
ldap-monitor audit sudo-rules

# Rapport complet FreeIPA
ldap-monitor audit all \
    --freeipa-mode \
    --include-kerberos \
    --include-sudo \
    --include-hbac \
    --format html \
    --output /var/reports/freeipa-audit.html
```

### Monitoring avec Métriques

```bash
# Collecter métriques FreeIPA
ldap-monitor monitor metrics \
    --include-replication \
    --include-certificates \
    --format prometheus

# Export pour Grafana
ldap-monitor export metrics \
    --backend prometheus \
    --output /var/lib/prometheus/freeipa-metrics.prom
```

## 🔧 Troubleshooting

### Problèmes de Connexion

```bash
# Test basique
ldap-monitor test connection

# Vérifier Kerberos
klist
kinit admin
ipa ping

# Vérifier certificats
openssl s_client -connect ipa.example.com:636 -showcerts

# Logs FreeIPA
journalctl -u ipa
tail -f /var/log/dirsrv/slapd-*/access
tail -f /var/log/dirsrv/slapd-*/errors
```

### Problèmes de Réplication

```bash
# Vérifier status
ipa-replica-manage list -v

# Re-initialiser réplication
ipa-replica-manage re-initialize \
    --from ipa01.example.com

# Forcer sync
ipa-replica-manage force-sync \
    --from ipa01.example.com
```

## 📖 Voir Aussi

- [Active Directory Guide](Active-Directory.md)
- [OpenLDAP Guide](OpenLDAP.md)
- [Security Audit](../features/audit/Security-Audit.md)
- [Multi-Server Setup](Multi-Server.md)
