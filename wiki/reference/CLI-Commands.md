# Référence des Commandes CLI

Guide complet de toutes les commandes disponibles dans LDAP Health Monitor CLI.

## 📑 Table des Matières

- [Synopsis](#synopsis)
- [Commandes de Configuration](#commandes-de-configuration)
- [Commandes d'Audit](#commandes-daudit)
- [Commandes de Monitoring](#commandes-de-monitoring)
- [Commandes de Gestion des Utilisateurs](#commandes-de-gestion-des-utilisateurs)
- [Commandes de Gestion des Groupes](#commandes-de-gestion-des-groupes)
- [Commandes de Nettoyage](#commandes-de-nettoyage)
- [Commandes de Backup](#commandes-de-backup)
- [Commandes d'Export](#commandes-dexport)
- [Commandes de Test](#commandes-de-test)
- [Commandes Utilitaires](#commandes-utilitaires)

## Synopsis

```bash
ldap-monitor [OPTIONS] COMMAND [ARGS]...
```

**Options globales** :
- `--config, -c PATH` : Chemin vers le fichier de configuration
- `--verbose, -v` : Activer la sortie détaillée
- `--help` : Afficher l'aide

## Commandes de Configuration

### config init

Initialise un nouveau fichier de configuration.

**Syntaxe** :
```bash
ldap-monitor config init [OPTIONS]
```

**Options** :
- `--output, -o PATH` : Chemin de sortie pour le fichier de configuration (défaut: `config.yaml`)

**Exemples** :

```bash
# Créer config.yaml dans le répertoire courant
ldap-monitor config init

# Créer un fichier de configuration personnalisé
ldap-monitor config init --output /etc/ldap-monitor/config.yaml

# Créer plusieurs configurations
ldap-monitor config init --output config.prod.yaml
ldap-monitor config init --output config.dev.yaml
```

**Sortie** :
```
✅ Configuration file created: config.yaml
Please edit the file to configure your LDAP settings.
```

---

### config validate

Valide le fichier de configuration.

**Syntaxe** :
```bash
ldap-monitor config validate [OPTIONS]
```

**Exemples** :

```bash
# Valider la configuration par défaut
ldap-monitor config validate

# Valider une configuration spécifique
ldap-monitor --config /etc/ldap-monitor/config.yaml config validate

# Validation avec sortie détaillée
ldap-monitor --verbose config validate
```

**Sortie en cas de succès** :
```
✅ Configuration is valid
```

**Sortie en cas d'erreur** :
```
❌ Configuration error: Missing required field 'ldap.server'
```

**Code de sortie** :
- `0` : Configuration valide
- `1` : Configuration invalide

---

### config show

Affiche la configuration actuelle.

**Syntaxe** :
```bash
ldap-monitor config show [OPTIONS]
```

**Exemples** :

```bash
# Afficher la configuration complète
ldap-monitor config show

# Afficher avec configuration personnalisée
ldap-monitor --config config.prod.yaml config show

# Rediriger vers un fichier
ldap-monitor config show > current-config.json
```

**Sortie** :
```json
{
  "ldap": {
    "server": "ldap.example.com",
    "port": 636,
    "use_ssl": true,
    "base_dn": "dc=example,dc=com"
  },
  "audit": {
    "checks": ["health", "users", "groups"]
  }
}
```

---

## Commandes d'Audit

### audit health

Vérifie la santé du serveur LDAP.

**Syntaxe** :
```bash
ldap-monitor audit health [OPTIONS]
```

**Options** :
- `--output, -o PATH` : Fichier de sortie pour le rapport
- `--format, -f [console|json|html]` : Format de sortie (défaut: `console`)

**Exemples** :

```bash
# Vérification basique de santé
ldap-monitor audit health

# Exporter en JSON
ldap-monitor audit health --format json --output health.json

# Vérification avec configuration spécifique
ldap-monitor --config config.prod.yaml audit health

# Export HTML
ldap-monitor audit health --format html --output health-report.html
```

**Sortie console** :
```
✅ LDAP Health Check
─────────────────────────────────────
Server: ldap.example.com:636
Status: ✓ Healthy
Response Time: 42ms
Connection: Successful
SSL/TLS: Valid (expires in 287 days)

Statistics:
  Total Users: 1,245
  Total Groups: 89
  Active Connections: 12
```

---

### audit users

Audite les utilisateurs LDAP.

**Syntaxe** :
```bash
ldap-monitor audit users [OPTIONS]
```

**Options** :
- `--inactive` : Vérifier les utilisateurs inactifs
- `--missing-attributes` : Vérifier les attributs manquants
- `--output, -o PATH` : Fichier de sortie
- `--format, -f [console|json|csv]` : Format de sortie (défaut: `console`)

**Exemples** :

```bash
# Audit complet des utilisateurs
ldap-monitor audit users

# Vérifier uniquement les utilisateurs inactifs
ldap-monitor audit users --inactive

# Vérifier les attributs manquants
ldap-monitor audit users --missing-attributes

# Audit complet avec export CSV
ldap-monitor audit users --inactive --missing-attributes \
  --format csv --output user-issues.csv

# Avec verbosité
ldap-monitor --verbose audit users --inactive
```

**Sortie** :
```
Found 3 issues

WARNING: Inactive Users Detected
  12 users have not logged in for more than 90 days
  💡 Consider disabling or archiving these accounts

CRITICAL: Missing Required Attributes
  User: uid=jdoe,ou=users,dc=example,dc=com
  Missing: mail, telephoneNumber
  💡 Add required attributes or update schema requirements

INFO: Password Expiration
  5 users have passwords expiring within 7 days
  💡 Send password reset notifications
```

---

### audit groups

Audite les groupes LDAP.

**Syntaxe** :
```bash
ldap-monitor audit groups [OPTIONS]
```

**Options** :
- `--empty` : Afficher les groupes vides
- `--large` : Afficher les groupes volumineux

**Exemples** :

```bash
# Audit de base des groupes
ldap-monitor audit groups

# Identifier les groupes vides
ldap-monitor audit groups --empty

# Identifier les groupes volumineux
ldap-monitor audit groups --large

# Audit complet
ldap-monitor audit groups --empty --large
```

**Sortie** :
```
Found 5 issues

WARNING: Empty Groups
  3 groups have no members
  Groups: cn=old-project,ou=groups,dc=example,dc=com
  💡 Consider removing unused groups

INFO: Large Groups
  Group 'cn=all-employees' has 1,245 members
  💡 Consider splitting into smaller groups for performance
```

---

### audit all

Exécute tous les audits disponibles.

**Syntaxe** :
```bash
ldap-monitor audit all [OPTIONS]
```

**Options** :
- `--output, -o PATH` : Fichier de sortie
- `--format, -f [console|json|html]` : Format de sortie (défaut: `console`)

**Exemples** :

```bash
# Audit complet en console
ldap-monitor audit all

# Générer un rapport HTML complet
ldap-monitor audit all --format html --output audit-report.html

# Export JSON pour automatisation
ldap-monitor audit all --format json --output audit-$(date +%Y%m%d).json

# Audit avec configuration personnalisée
ldap-monitor --config /etc/ldap-monitor/config.yaml audit all
```

**Sortie** :
```
🔍 LDAP Comprehensive Audit Report
═══════════════════════════════════════════════════════

Health Status: ✓ Healthy
Response Time: 45ms
Audit Score: 87/100

📊 Statistics
─────────────────────────────────────
Total Users: 1,245
Total Groups: 89
Active Users: 1,198
Inactive Users: 47

⚠️  Issues Found: 12
─────────────────────────────────────
Critical: 2
Warning: 7
Info: 3

Detailed Issues:
[... liste détaillée des problèmes ...]

💡 Recommendations:
─────────────────────────────────────
1. Remove 3 empty groups
2. Update 12 users with missing attributes
3. Review password policy for 5 expiring accounts
```

---

## Commandes de Monitoring

### monitor start

Démarre le monitoring continu.

**Syntaxe** :
```bash
ldap-monitor monitor start [OPTIONS]
```

**Options** :
- `--daemon, -d` : Exécuter en mode daemon (arrière-plan)

**Exemples** :

```bash
# Démarrer en mode interactif
ldap-monitor monitor start

# Démarrer en mode daemon
ldap-monitor monitor start --daemon

# Avec configuration personnalisée
ldap-monitor --config config.prod.yaml monitor start --daemon
```

**Sortie** :
```
Starting LDAP monitoring...
✓ Connected to ldap.example.com:636
✓ Collecting metrics every 300 seconds
✓ Alerts enabled (Slack, Email)
✓ Prometheus endpoint: http://localhost:9090/metrics

Press Ctrl+C to stop
```

---

### monitor metrics

Affiche les métriques actuelles.

**Syntaxe** :
```bash
ldap-monitor monitor metrics
```

**Exemples** :

```bash
# Afficher les métriques
ldap-monitor monitor metrics

# Avec configuration spécifique
ldap-monitor --config config.prod.yaml monitor metrics

# Rediriger vers fichier
ldap-monitor monitor metrics > metrics-$(date +%Y%m%d-%H%M%S).txt
```

**Sortie** :
```
ldap_users_total: 1245
ldap_groups_total: 89
ldap_active_users: 1198
ldap_inactive_users: 47
ldap_response_time_ms: 42
ldap_connection_status: 1
ldap_ssl_cert_days_remaining: 287
ldap_failed_auth_total: 3
```

---

### monitor prometheus

Démarre le serveur de métriques Prometheus.

**Syntaxe** :
```bash
ldap-monitor monitor prometheus [OPTIONS]
```

**Options** :
- `--port, -p INTEGER` : Port pour le serveur de métriques (défaut: `9090`)

**Exemples** :

```bash
# Démarrer avec port par défaut
ldap-monitor monitor prometheus

# Démarrer sur port personnalisé
ldap-monitor monitor prometheus --port 9091

# Avec configuration spécifique
ldap-monitor --config config.prod.yaml monitor prometheus --port 8080
```

**Sortie** :
```
Prometheus metrics available at http://localhost:9090/metrics
Press Ctrl+C to stop

Collecting metrics...
✓ Metrics updated: 2025-01-15 10:23:45
```

---

## Commandes de Gestion des Utilisateurs

### user search

Recherche des utilisateurs.

**Syntaxe** :
```bash
ldap-monitor user search QUERY
```

**Arguments** :
- `QUERY` : Terme de recherche

**Exemples** :

```bash
# Rechercher par nom
ldap-monitor user search "john"

# Rechercher par email
ldap-monitor user search "john.doe@example.com"

# Rechercher par UID
ldap-monitor user search "jdoe"

# Recherche avec wildcards
ldap-monitor user search "john*"
```

**Sortie** :
```
Found 3 users:
  jdoe (John Doe) - john.doe@example.com
  jsmith (John Smith) - john.smith@example.com
  ajohnson (Alice Johnson) - alice.johnson@example.com
```

---

### user show

Affiche les détails d'un utilisateur.

**Syntaxe** :
```bash
ldap-monitor user show DN
```

**Arguments** :
- `DN` : Distinguished Name de l'utilisateur

**Exemples** :

```bash
# Afficher un utilisateur spécifique
ldap-monitor user show "uid=jdoe,ou=users,dc=example,dc=com"

# Avec guillemets pour les espaces
ldap-monitor user show "cn=John Doe,ou=users,dc=example,dc=com"
```

**Sortie** :
```
DN: uid=jdoe,ou=users,dc=example,dc=com
UID: jdoe
CN: John Doe
Email: john.doe@example.com

All attributes:
  objectClass: ['inetOrgPerson', 'posixAccount']
  uid: jdoe
  cn: John Doe
  sn: Doe
  givenName: John
  mail: john.doe@example.com
  telephoneNumber: +1-555-0123
  employeeNumber: 12345
  departmentNumber: IT
  createTimestamp: 2023-01-15 10:30:00
  modifyTimestamp: 2024-12-01 15:45:00
```

---

### user list

Liste tous les utilisateurs.

**Syntaxe** :
```bash
ldap-monitor user list [OPTIONS]
```

**Options** :
- `--limit, -n INTEGER` : Limite le nombre de résultats

**Exemples** :

```bash
# Lister tous les utilisateurs
ldap-monitor user list

# Limiter à 10 utilisateurs
ldap-monitor user list --limit 10

# Exporter la liste
ldap-monitor user list > users-list.txt
```

**Sortie** :
```
Total users: 1245

jdoe: John Doe (john.doe@example.com)
jsmith: Jane Smith (jane.smith@example.com)
rbrown: Robert Brown (robert.brown@example.com)
...
```

---

## Commandes de Gestion des Groupes

### group search

Recherche des groupes.

**Syntaxe** :
```bash
ldap-monitor group search QUERY
```

**Arguments** :
- `QUERY` : Terme de recherche

**Exemples** :

```bash
# Rechercher un groupe
ldap-monitor group search "developers"

# Recherche partielle
ldap-monitor group search "dev*"

# Recherche sensible à la casse
ldap-monitor group search "IT"
```

**Sortie** :
```
Found 2 groups:
  developers (45 members)
  developers-senior (12 members)
```

---

### group show

Affiche les détails d'un groupe.

**Syntaxe** :
```bash
ldap-monitor group show DN
```

**Arguments** :
- `DN` : Distinguished Name du groupe

**Exemples** :

```bash
# Afficher un groupe
ldap-monitor group show "cn=developers,ou=groups,dc=example,dc=com"
```

**Sortie** :
```
DN: cn=developers,ou=groups,dc=example,dc=com
CN: developers
Description: Development team members
Members: 45
```

---

### group list

Liste tous les groupes.

**Syntaxe** :
```bash
ldap-monitor group list
```

**Exemples** :

```bash
# Lister tous les groupes
ldap-monitor group list

# Exporter la liste
ldap-monitor group list > groups.txt
```

**Sortie** :
```
Total groups: 89

developers: 45 members
marketing: 23 members
sales: 67 members
it-admin: 8 members
...
```

---

### group members

Affiche les membres d'un groupe.

**Syntaxe** :
```bash
ldap-monitor group members DN
```

**Arguments** :
- `DN` : Distinguished Name du groupe

**Exemples** :

```bash
# Lister les membres
ldap-monitor group members "cn=developers,ou=groups,dc=example,dc=com"

# Exporter les membres
ldap-monitor group members "cn=developers,ou=groups,dc=example,dc=com" > dev-members.txt
```

**Sortie** :
```
Members (45):
  uid=jdoe,ou=users,dc=example,dc=com
  uid=jsmith,ou=users,dc=example,dc=com
  uid=rbrown,ou=users,dc=example,dc=com
  ...
```

---

## Commandes de Nettoyage

### cleanup dry-run

Affiche ce qui serait nettoyé (sans modification).

**Syntaxe** :
```bash
ldap-monitor cleanup dry-run
```

**Exemples** :

```bash
# Simuler le nettoyage
ldap-monitor cleanup dry-run

# Avec configuration personnalisée
ldap-monitor --config config.prod.yaml cleanup dry-run
```

**Sortie** :
```
Would remove 3 empty groups:
  - cn=old-project-2022,ou=groups,dc=example,dc=com
  - cn=temp-access,ou=groups,dc=example,dc=com
  - cn=deprecated-team,ou=groups,dc=example,dc=com
```

---

### cleanup empty-groups

Supprime les groupes vides.

**Syntaxe** :
```bash
ldap-monitor cleanup empty-groups [OPTIONS]
```

**Options** :
- `--confirm` : Confirmer la suppression

**Exemples** :

```bash
# Simulation (dry-run par défaut)
ldap-monitor cleanup empty-groups

# Suppression réelle
ldap-monitor cleanup empty-groups --confirm

# Avec verbosité
ldap-monitor --verbose cleanup empty-groups --confirm
```

**Sortie sans --confirm** :
```
Would remove 3 empty groups
Use --confirm to actually delete
```

**Sortie avec --confirm** :
```
✅ Removed 3 empty groups
  - cn=old-project-2022,ou=groups,dc=example,dc=com
  - cn=temp-access,ou=groups,dc=example,dc=com
  - cn=deprecated-team,ou=groups,dc=example,dc=com
```

---

## Commandes de Backup

### backup full

Crée un backup complet de l'annuaire LDAP.

**Syntaxe** :
```bash
ldap-monitor backup full [OPTIONS]
```

**Options** :
- `--output, -o PATH` : Fichier de sortie (requis)
- `--format, -f [ldif|json|yaml]` : Format de backup (défaut: `ldif`)

**Exemples** :

```bash
# Backup LDIF standard
ldap-monitor backup full --output backup.ldif

# Backup au format JSON
ldap-monitor backup full --output backup.json --format json

# Backup avec date dans le nom
ldap-monitor backup full --output backup-$(date +%Y%m%d).ldif

# Backup YAML
ldap-monitor backup full --output backup.yaml --format yaml

# Backup compressé (pipe vers gzip)
ldap-monitor backup full --output backup.ldif && gzip backup.ldif
```

**Sortie** :
```
Creating backup...
✅ Backup saved to backup.ldif
  Size: 12.5 MB
  Entries: 1,334
  Duration: 3.2s
```

---

## Commandes d'Export

### export users

Exporte les utilisateurs vers un fichier.

**Syntaxe** :
```bash
ldap-monitor export users [OPTIONS]
```

**Options** :
- `--output, -o PATH` : Fichier de sortie (requis)
- `--format, -f [csv|json|yaml]` : Format d'export (défaut: `csv`)

**Exemples** :

```bash
# Export CSV
ldap-monitor export users --output users.csv

# Export JSON
ldap-monitor export users --output users.json --format json

# Export YAML
ldap-monitor export users --output users.yaml --format yaml

# Export avec date
ldap-monitor export users --output users-$(date +%Y%m%d).csv
```

**Sortie** :
```
Exporting users...
✅ Users exported to users.csv
  Total users: 1,245
  File size: 256 KB
```

---

## Commandes de Test

### test connection

Test la connexion au serveur LDAP.

**Syntaxe** :
```bash
ldap-monitor test connection
```

**Exemples** :

```bash
# Test simple
ldap-monitor test connection

# Test avec configuration spécifique
ldap-monitor --config config.prod.yaml test connection

# Test avec verbosité
ldap-monitor --verbose test connection
```

**Sortie en cas de succès** :
```
Testing LDAP connection...
✅ Connection successful (42ms)
  Server: ldap.example.com:636
  SSL/TLS: Enabled
  Base DN: dc=example,dc=com
```

**Sortie en cas d'échec** :
```
Testing LDAP connection...
❌ Connection failed: Unable to connect to server
  Server: ldap.example.com:636
  Error: Connection timeout after 10s
```

**Code de sortie** :
- `0` : Connexion réussie
- `1` : Échec de connexion

---

## Commandes Utilitaires

### version

Affiche la version du logiciel.

**Syntaxe** :
```bash
ldap-monitor version
```

**Exemples** :

```bash
# Afficher la version
ldap-monitor version
```

**Sortie** :
```
LDAP Health Monitor v1.0.0
Python: 3.11.5
ldap3: 2.9.1
```

---

## Aide et Documentation

### --help

Affiche l'aide pour une commande.

**Syntaxe** :
```bash
ldap-monitor --help
ldap-monitor COMMAND --help
ldap-monitor COMMAND SUBCOMMAND --help
```

**Exemples** :

```bash
# Aide générale
ldap-monitor --help

# Aide pour une commande
ldap-monitor audit --help

# Aide pour une sous-commande
ldap-monitor audit users --help

# Aide pour config
ldap-monitor config --help
```

---

## Combinaisons de Commandes

### Pipelines et Automatisation

```bash
# Audit et export JSON
ldap-monitor audit all --format json --output audit.json

# Test et backup si succès
ldap-monitor test connection && ldap-monitor backup full -o backup.ldif

# Monitoring avec export périodique
ldap-monitor monitor metrics >> metrics-$(date +%Y%m%d).log

# Chaîner plusieurs opérations
ldap-monitor test connection && \
  ldap-monitor audit all --format html -o report.html && \
  ldap-monitor backup full -o backup-$(date +%Y%m%d).ldif
```

### Scripts d'Automatisation

```bash
#!/bin/bash
# Audit quotidien automatisé

DATE=$(date +%Y%m%d)
CONFIG="/etc/ldap-monitor/config.yaml"

# Test de connexion
if ! ldap-monitor --config "$CONFIG" test connection; then
    echo "Connexion LDAP échouée"
    exit 1
fi

# Audit complet
ldap-monitor --config "$CONFIG" audit all \
    --format html \
    --output "/var/reports/audit-${DATE}.html"

# Backup hebdomadaire (le lundi)
if [ $(date +%u) -eq 1 ]; then
    ldap-monitor --config "$CONFIG" backup full \
        --output "/var/backups/ldap-${DATE}.ldif"
fi
```

---

## Voir Aussi

- [Options Globales](Global-Options.md) - Options et variables d'environnement
- [Formats d'Export](Export-Formats.md) - Spécifications des formats
- [Codes de Sortie](Exit-Codes.md) - Codes de retour et erreurs
- [Configuration](../configuration/Config-File-Structure.md) - Structure du fichier de configuration
- [Exemples d'Usage](../examples/Use-Cases.md) - Cas d'usage complets

---

**Note** : Toutes les commandes qui modifient l'annuaire LDAP nécessitent les permissions appropriées. Utilisez toujours `--confirm` pour les opérations destructives et testez d'abord en mode dry-run.
