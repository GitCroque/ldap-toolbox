# Audit de santé du serveur LDAP

## Introduction

L'audit de santé (Health Check) est la première ligne de défense pour surveiller la disponibilité et les performances de votre serveur LDAP. Il effectue une série de vérifications essentielles pour s'assurer que votre infrastructure LDAP fonctionne correctement.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Vérifications effectuées](#vérifications-effectuées)
3. [Utilisation de base](#utilisation-de-base)
4. [Temps de réponse](#temps-de-réponse)
5. [Certificats SSL/TLS](#certificats-ssltls)
6. [Statistiques du serveur](#statistiques-du-serveur)
7. [Interprétation des résultats](#interprétation-des-résultats)
8. [Exemples pratiques](#exemples-pratiques)
9. [Automatisation et monitoring](#automatisation-et-monitoring)
10. [Dépannage](#dépannage)

## Vue d'ensemble

### Qu'est-ce que l'audit de santé ?

L'audit de santé vérifie les aspects fondamentaux du serveur LDAP :

- **Connectivité** : Le serveur est-il accessible ?
- **Performance** : Quel est le temps de réponse ?
- **Sécurité** : Les certificats SSL/TLS sont-ils valides ?
- **Capacité** : Combien d'objets contient l'annuaire ?

### Quand l'utiliser ?

- **Monitoring quotidien** : Vérification automatique chaque jour
- **Diagnostic rapide** : Premier réflexe en cas de problème
- **Validation post-maintenance** : Après une mise à jour ou changement
- **Documentation** : Capture d'état pour l'historique

### Architecture du health check

```
┌────────────────┐
│   CLI Client   │
└────────┬───────┘
         │
    ┌────▼──────┐
    │ Config    │
    └────┬──────┘
         │
    ┌────▼──────────┐
    │HealthChecker  │
    └────┬──────────┘
         │
    ┌────▼──────────────────────────┐
    │  test_connection()            │
    │  _check_certificate()         │
    │  _get_statistics()            │
    └────┬──────────────────────────┘
         │
    ┌────▼───────────┐
    │ LDAP Server    │
    └────────────────┘
```

## Vérifications effectuées

### 1. Test de connectivité

Établit une connexion au serveur LDAP et mesure le temps de réponse.

**Code source :**
```python
# src/audit/health.py
success, response_time, error = self.connector.test_connection()
```

**Critères de succès :**
- Connexion établie avec succès
- Authentification réussie
- Réponse reçue du serveur

**Causes d'échec possibles :**
- Serveur inaccessible (down)
- Pare-feu bloquant la connexion
- Identifiants incorrects
- Timeout de connexion

### 2. Mesure du temps de réponse

Chronomètre le temps nécessaire pour obtenir une réponse du serveur.

**Seuils par défaut :**
- **Normal** : < 500ms
- **Warning** : 500-2000ms
- **Critical** : > 2000ms

**Configuration des seuils :**
```yaml
audit:
  thresholds:
    response_time_warning_ms: 500
    response_time_critical_ms: 2000
```

### 3. Vérification des certificats SSL/TLS

Examine la validité et la date d'expiration des certificats.

**Vérifications :**
- Certificat présent et valide
- Date d'expiration
- Chaîne de certification
- Correspondance du hostname

**Seuils d'alerte :**
```yaml
audit:
  thresholds:
    ssl_cert_expiry_warning_days: 30
```

### 4. Collecte des statistiques

Compte les objets principaux de l'annuaire :
- Nombre total d'utilisateurs
- Nombre total de groupes
- Nombre d'unités organisationnelles (OUs)

**Requêtes LDAP :**
```python
# Comptage des utilisateurs
user_filter = f"(objectClass={config.ldap.user_objectclass})"
users = connector.search(users_ou, user_filter, ["dn"])
stats["users_total"] = len(users)

# Comptage des groupes
group_filter = f"(objectClass={config.ldap.group_objectclass})"
groups = connector.search(groups_ou, group_filter, ["dn"])
stats["groups_total"] = len(groups)

# Comptage des OUs
ous = connector.search(base_dn, "(objectClass=organizationalUnit)", ["dn"])
stats["ous_total"] = len(ous)
```

### 5. Informations du serveur

Récupère les métadonnées du serveur LDAP :
- Nom et version du serveur
- Nom DNS
- Capacités supportées

## Utilisation de base

### Commande simple

```bash
ldap-health-monitor audit health
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
```

### Avec configuration personnalisée

```bash
ldap-health-monitor --config /etc/ldap-monitor/config.yaml audit health
```

### Export JSON

```bash
ldap-health-monitor audit health --format json --output health-check.json
```

**Sortie JSON :**
```json
{
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
}
```

### Export HTML

```bash
ldap-health-monitor audit health --format html --output health-report.html
```

## Temps de réponse

### Comprendre les mesures

Le temps de réponse mesure la latence entre l'envoi d'une requête et la réception de la réponse.

**Composants du temps de réponse :**
```
Temps total = Réseau + Traitement serveur + Sérialisation
```

### Interprétation des temps

| Temps | Statut | Signification | Action |
|-------|--------|---------------|--------|
| < 100ms | Excellent | Serveur très réactif | Aucune |
| 100-500ms | Bon | Performance normale | Monitoring |
| 500-1000ms | Acceptable | Peut être amélioré | Investigation |
| 1000-2000ms | Lent | Problème probable | Action requise |
| > 2000ms | Critique | Problème majeur | Action immédiate |

### Exemple de résultats par temps

**Temps normal (120ms) :**
```
┌─────────────────────────────────┐
│ Server Status: ✅ Healthy       │
│ Response Time: 120ms            │
└─────────────────────────────────┘
```

**Temps élevé (850ms) :**
```
┌──────────────────────────────────┐
│ Server Status: ⚠️  Warning       │
│ Response Time: 850ms             │
└──────────────────────────────────┘

🔍 Issues Found:
  ⚠️  Elevated response time
     Server response time is 850ms (warning threshold: 500ms)
     💡 Monitor server performance
```

**Temps critique (2300ms) :**
```
┌──────────────────────────────────┐
│ Server Status: ❌ Critical       │
│ Response Time: 2300ms            │
└──────────────────────────────────┘

🔍 Issues Found:
  🔴 High response time
     Server response time is 2300ms (critical threshold: 2000ms)
     💡 Check server load and network connectivity
```

### Facteurs affectant le temps de réponse

**Côté réseau :**
- Latence réseau
- Bande passante disponible
- Équipements réseau (switches, routeurs)
- Pare-feu et proxies

**Côté serveur :**
- Charge CPU
- Mémoire disponible
- I/O disque
- Nombre de connexions actives
- Taille de la base de données

**Optimisations possibles :**
```yaml
# Augmenter les caches serveur
ldap:
  # Configuration OpenLDAP
  cachesize: 10000
  idlcachesize: 30000

  # Indexation optimale
  indexes:
    - uid
    - cn
    - mail
    - memberOf
```

### Monitoring des tendances

**Script de collecte :**
```bash
#!/bin/bash
# collect-response-times.sh

while true; do
  TIMESTAMP=$(date +%s)
  RESPONSE_TIME=$(ldap-health-monitor audit health --format json | jq -r '.response_time')
  echo "$TIMESTAMP,$RESPONSE_TIME" >> /var/log/ldap-response-times.csv
  sleep 60
done
```

**Analyse avec gnuplot :**
```gnuplot
set datafile separator ","
set xdata time
set timefmt "%s"
set format x "%H:%M"
set xlabel "Heure"
set ylabel "Temps de réponse (ms)"
set title "Performance LDAP - 24h"
plot "ldap-response-times.csv" using 1:2 with lines title "Response time"
```

## Certificats SSL/TLS

### Vérifications SSL

L'audit vérifie automatiquement les certificats si SSL/TLS est activé :

```yaml
ldap:
  use_ssl: true
  # ou
  use_tls: true
```

### Statuts possibles

**Certificat valide :**
```
✅ Aucun problème de certificat détecté
Expiration : 15 janvier 2026 (dans 425 jours)
```

**Certificat expirant bientôt :**
```
⚠️  SSL certificate expiring soon
   Certificate expires in 25 days
   💡 Plan certificate renewal
```

**Certificat expiré :**
```
🔴 SSL certificate expired
   Certificate expired 5 days ago
   💡 Renew SSL certificate immediately
```

**Erreur de vérification :**
```
⚠️  Cannot check SSL certificate
   Failed to retrieve certificate: Connection timeout
   💡 Verify SSL/TLS configuration
```

### Détails du certificat

**Informations collectées :**
```json
{
  "certificate": {
    "subject": "CN=ldap.example.com",
    "issuer": "CN=Let's Encrypt Authority X3",
    "notBefore": "Nov  1 00:00:00 2025 GMT",
    "notAfter": "Jan 15 23:59:59 2026 GMT",
    "serialNumber": "03:E7:...",
    "subjectAltName": [
      "DNS:ldap.example.com",
      "DNS:ldap1.example.com"
    ]
  }
}
```

### Renouvellement automatique

**Script avec Let's Encrypt :**
```bash
#!/bin/bash
# /usr/local/bin/check-and-renew-cert.sh

DAYS_LEFT=$(ldap-health-monitor audit health --format json | \
  jq -r '.details.issues[] | select(.category=="security") | .description' | \
  grep -oP '\d+(?= days)')

if [ "$DAYS_LEFT" -lt 30 ]; then
  echo "Certificat expire dans $DAYS_LEFT jours - renouvellement..."
  certbot renew --quiet
  systemctl reload slapd
fi
```

### Configuration pour différents scénarios

**SSL direct (ldaps://) :**
```yaml
ldap:
  server: ldap.example.com
  port: 636
  use_ssl: true
  verify_cert: true
```

**StartTLS (ldap:// avec upgrade) :**
```yaml
ldap:
  server: ldap.example.com
  port: 389
  use_tls: true
  verify_cert: true
```

**Développement (sans vérification) :**
```yaml
ldap:
  server: localhost
  port: 636
  use_ssl: true
  verify_cert: false  # ⚠️ À éviter en production !
```

## Statistiques du serveur

### Métriques collectées

Les statistiques donnent un aperçu rapide de la taille de l'annuaire :

```
📊 Statistics:
┌──────────────────┬───────┐
│ Users Total      │  1234 │
│ Groups Total     │   156 │
│ OUs Total        │    23 │
└──────────────────┴───────┘
```

### Utilisation des statistiques

**Monitoring de croissance :**
```bash
# Script de tracking
#!/bin/bash
DATE=$(date +%Y-%m-%d)
STATS=$(ldap-health-monitor audit health --format json | jq '.details.statistics')
echo "$DATE $STATS" >> /var/log/ldap-growth.log
```

**Analyse de tendances :**
```bash
# Graphique de croissance
cat /var/log/ldap-growth.log | \
  jq -r '[.users_total, .groups_total] | @csv' | \
  gnuplot -e "set terminal png; plot '-' using 1 title 'Users', '' using 2 title 'Groups'"
```

**Alertes de capacité :**
```bash
#!/bin/bash
USERS=$(ldap-health-monitor audit health --format json | jq -r '.details.statistics.users_total')
MAX_USERS=10000

if [ $USERS -gt $MAX_USERS ]; then
  echo "Limite d'utilisateurs atteinte: $USERS/$MAX_USERS" | \
    mail -s "LDAP Capacity Alert" admin@example.com
fi
```

### Statistiques avancées

**Avec queries personnalisées :**
```python
# Ajout de statistiques personnalisées
def _get_statistics(self):
    stats = {}

    # Statistiques de base
    stats["users_total"] = len(connector.search(...))

    # Statistiques avancées
    stats["users_active"] = len(connector.search(
        search_filter="(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
    ))

    stats["users_disabled"] = stats["users_total"] - stats["users_active"]

    return stats
```

## Interprétation des résultats

### Status : Healthy (Sain)

**Signification :**
- Serveur accessible et fonctionnel
- Temps de réponse acceptable
- Certificats valides
- Aucun problème critique

**Action recommandée :**
- Continuer le monitoring régulier
- Archiver le rapport pour historique
- Aucune intervention nécessaire

**Exemple :**
```
✅ LDAP server is healthy
Score: 100/100
0 issues found
```

### Status : Warning (Avertissement)

**Signification :**
- Serveur fonctionnel mais avec problèmes mineurs
- Temps de réponse élevé
- Certificat expirant bientôt
- Nécessite attention

**Action recommandée :**
- Investiguer la cause
- Planifier une intervention
- Augmenter la fréquence de monitoring
- Documenter le problème

**Exemple :**
```
⚠️  LDAP server has warnings
Score: 85/100
2 issues found:
  - Elevated response time (850ms)
  - SSL certificate expiring in 25 days
```

### Status : Critical (Critique)

**Signification :**
- Problème majeur affectant le service
- Serveur inaccessible ou très lent
- Certificat expiré
- Action immédiate requise

**Action recommandée :**
- Intervention immédiate
- Notification de l'équipe
- Investigation approfondie
- Documentation de l'incident

**Exemple :**
```
❌ LDAP server has critical issues
Score: 30/100
1 critical issue found:
  - Cannot connect to LDAP server: Connection refused
```

## Exemples pratiques

### Exemple 1 : Monitoring quotidien simple

**Objectif :** Vérifier la santé chaque matin

```bash
#!/bin/bash
# /usr/local/bin/ldap-morning-check.sh

echo "=== LDAP Health Check - $(date) ===" | tee -a /var/log/ldap-health.log
ldap-health-monitor audit health | tee -a /var/log/ldap-health.log
echo "" >> /var/log/ldap-health.log
```

**Cron :**
```cron
0 8 * * * /usr/local/bin/ldap-morning-check.sh
```

### Exemple 2 : Alertes par email

**Objectif :** Recevoir un email si problème détecté

```bash
#!/bin/bash
# /usr/local/bin/ldap-health-alert.sh

RESULT=$(ldap-health-monitor audit health --format json)
STATUS=$(echo "$RESULT" | jq -r '.status')
MESSAGE=$(echo "$RESULT" | jq -r '.message')

if [ "$STATUS" != "healthy" ]; then
  echo "Status: $STATUS" | mail -s "⚠️ LDAP Health Alert" admin@example.com
  echo "$RESULT" | jq '.' | mail -s "LDAP Health Details" admin@example.com
fi
```

### Exemple 3 : Dashboard web simple

**Objectif :** Page web affichant le statut

```bash
#!/bin/bash
# /var/www/html/ldap-status/update.sh

ldap-health-monitor audit health --format html --output /var/www/html/ldap-status/index.html

# Ajout du timestamp
sed -i "s/<body>/<body><p>Last update: $(date)<\/p>/" /var/www/html/ldap-status/index.html
```

**Cron toutes les 5 minutes :**
```cron
*/5 * * * * /var/www/html/ldap-status/update.sh
```

### Exemple 4 : Intégration Prometheus

**Objectif :** Exposer les métriques pour Prometheus

```bash
#!/bin/bash
# /usr/local/bin/ldap-metrics-exporter.sh

RESULT=$(ldap-health-monitor audit health --format json)

# Extraire les métriques
STATUS=$(echo "$RESULT" | jq -r '.status')
RESPONSE_TIME=$(echo "$RESULT" | jq -r '.response_time')
USERS=$(echo "$RESULT" | jq -r '.details.statistics.users_total')
GROUPS=$(echo "$RESULT" | jq -r '.details.statistics.groups_total')

# Convertir status en nombre
STATUS_VALUE=0
[ "$STATUS" = "healthy" ] && STATUS_VALUE=1
[ "$STATUS" = "warning" ] && STATUS_VALUE=2
[ "$STATUS" = "critical" ] && STATUS_VALUE=3

# Générer métriques Prometheus
cat > /var/lib/node_exporter/textfile_collector/ldap_health.prom <<EOF
# HELP ldap_health_status LDAP server health status
# TYPE ldap_health_status gauge
ldap_health_status $STATUS_VALUE

# HELP ldap_response_time_milliseconds LDAP server response time
# TYPE ldap_response_time_milliseconds gauge
ldap_response_time_milliseconds $RESPONSE_TIME

# HELP ldap_users_total Total number of LDAP users
# TYPE ldap_users_total gauge
ldap_users_total $USERS

# HELP ldap_groups_total Total number of LDAP groups
# TYPE ldap_groups_total gauge
ldap_groups_total $GROUPS
EOF
```

### Exemple 5 : Graphiques de performance

**Objectif :** Visualiser les tendances avec Grafana

```bash
#!/bin/bash
# collect-metrics.sh

while true; do
  TIMESTAMP=$(date +%s)
  RESULT=$(ldap-health-monitor audit health --format json)

  # InfluxDB line protocol
  echo "ldap_health,host=$(hostname) \
    response_time=$(echo "$RESULT" | jq -r '.response_time'),\
    users_total=$(echo "$RESULT" | jq -r '.details.statistics.users_total'),\
    groups_total=$(echo "$RESULT" | jq -r '.details.statistics.groups_total') \
    $TIMESTAMP" | \
  curl -XPOST 'http://influxdb:8086/write?db=monitoring' --data-binary @-

  sleep 60
done
```

### Exemple 6 : Tests avant/après maintenance

**Objectif :** Comparer l'état avant et après

```bash
#!/bin/bash
# maintenance-wrapper.sh

echo "=== État AVANT maintenance ==="
ldap-health-monitor audit health --format json --output before.json
ldap-health-monitor audit health

read -p "Continuer avec la maintenance ? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Effectuer la maintenance
  systemctl stop slapd
  # ... opérations de maintenance ...
  systemctl start slapd

  sleep 5

  echo "=== État APRÈS maintenance ==="
  ldap-health-monitor audit health --format json --output after.json
  ldap-health-monitor audit health

  # Comparaison
  echo "=== Comparaison ==="
  echo "Response time before: $(jq -r '.response_time' before.json)ms"
  echo "Response time after: $(jq -r '.response_time' after.json)ms"
fi
```

## Automatisation et monitoring

### Script complet de monitoring

```bash
#!/bin/bash
# /usr/local/bin/ldap-health-monitor-daemon.sh

CONFIG="/etc/ldap-health-monitor/config.yaml"
LOG_DIR="/var/log/ldap-health-monitor"
ALERT_EMAIL="admin@example.com"
CHECK_INTERVAL=300  # 5 minutes

mkdir -p "$LOG_DIR"

while true; do
  TIMESTAMP=$(date +%Y%m%d-%H%M%S)
  RESULT=$(ldap-health-monitor -c "$CONFIG" audit health --format json)

  # Sauvegarder le résultat
  echo "$RESULT" > "$LOG_DIR/latest.json"
  echo "$RESULT" >> "$LOG_DIR/history-$(date +%Y%m%d).jsonl"

  # Vérifier le status
  STATUS=$(echo "$RESULT" | jq -r '.status')
  RESPONSE_TIME=$(echo "$RESULT" | jq -r '.response_time')

  case "$STATUS" in
    healthy)
      logger -t ldap-health "LDAP is healthy (${RESPONSE_TIME}ms)"
      ;;
    warning)
      MESSAGE=$(echo "$RESULT" | jq -r '.message')
      logger -t ldap-health "WARNING: $MESSAGE"
      echo "$RESULT" | jq '.' | mail -s "⚠️ LDAP Warning" "$ALERT_EMAIL"
      ;;
    critical)
      MESSAGE=$(echo "$RESULT" | jq -r '.message')
      logger -t ldap-health "CRITICAL: $MESSAGE"
      echo "$RESULT" | jq '.' | mail -s "🔴 LDAP CRITICAL" "$ALERT_EMAIL"
      # Notification supplémentaire (SMS, Slack, etc.)
      ;;
  esac

  sleep "$CHECK_INTERVAL"
done
```

### Service systemd

```ini
# /etc/systemd/system/ldap-health-monitor.service
[Unit]
Description=LDAP Health Monitor Daemon
After=network.target

[Service]
Type=simple
User=ldap-monitor
Group=ldap-monitor
ExecStart=/usr/local/bin/ldap-health-monitor-daemon.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Activation :**
```bash
systemctl daemon-reload
systemctl enable ldap-health-monitor
systemctl start ldap-health-monitor
```

## Dépannage

### Problème : Connexion impossible

**Symptômes :**
```
❌ Cannot connect to LDAP server: Connection refused
```

**Diagnostic :**
```bash
# Vérifier que le serveur écoute
netstat -tlnp | grep :389

# Tester avec ldapsearch
ldapsearch -x -H ldap://server:389 -b "" -s base

# Vérifier pare-feu
iptables -L | grep 389
firewall-cmd --list-ports
```

**Solutions :**
- Vérifier que slapd est démarré
- Ouvrir les ports nécessaires
- Vérifier la configuration réseau
- Valider les identifiants

### Problème : Temps de réponse élevé

**Symptômes :**
```
⚠️  Elevated response time
   Server response time is 1850ms
```

**Diagnostic :**
```bash
# Charge serveur
top -b -n 1 | grep slapd
vmstat 1 5

# I/O disque
iostat -x 1 5

# Connexions actives
netstat -an | grep :389 | wc -l

# Logs serveur
tail -f /var/log/slapd/slapd.log
```

**Solutions :**
- Optimiser les index LDAP
- Augmenter les ressources serveur
- Nettoyer les connexions obsolètes
- Optimiser les requêtes

### Problème : Erreur SSL

**Symptômes :**
```
⚠️  Cannot check SSL certificate
   Failed to retrieve certificate: SSL handshake failed
```

**Diagnostic :**
```bash
# Tester SSL manuellement
openssl s_client -connect ldap.example.com:636 -showcerts

# Vérifier le certificat
openssl x509 -in /etc/ssl/certs/ldap-cert.pem -text -noout

# Tester avec ldapsearch
ldapsearch -x -H ldaps://server:636 -d 1
```

**Solutions :**
- Vérifier la validité du certificat
- Renouveler le certificat expiré
- Corriger les permissions des fichiers
- Vérifier la chaîne de certification

### Problème : Statistiques manquantes

**Symptômes :**
```json
{
  "statistics": {
    "error": "Permission denied"
  }
}
```

**Diagnostic :**
```bash
# Vérifier les permissions
ldapsearch -x -D "$BIND_DN" -w "$PASSWORD" -b "$BASE_DN" "(objectClass=*)"

# Vérifier les ACLs
ldapsearch -Y EXTERNAL -H ldapi:/// -b "cn=config" "olcAccess"
```

**Solutions :**
- Accorder les permissions de lecture
- Utiliser un compte avec droits suffisants
- Ajuster les ACLs OpenLDAP

## Conclusion

L'audit de santé est un outil essentiel pour maintenir un serveur LDAP fiable. En l'intégrant dans votre routine de monitoring, vous pouvez détecter et résoudre les problèmes avant qu'ils n'affectent vos utilisateurs.

**Points clés à retenir :**
- Exécuter quotidiennement
- Configurer des alertes automatiques
- Surveiller les tendances
- Documenter les incidents
- Ajuster les seuils à votre environnement

Pour aller plus loin :
- [Audit des groupes](./Groups-Audit.md)
- [Audit de sécurité](./Security-Audit.md)
- [Génération de rapports](./Audit-Reports.md)
