# Problèmes de Performance LDAP

Guide complet d'optimisation et de résolution des problèmes de performance pour LDAP Health Monitor.

## Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Diagnostic de Performance](#diagnostic-de-performance)
- [Requêtes Lentes](#requêtes-lentes)
- [Problèmes de Timeout](#problèmes-de-timeout)
- [Utilisation Mémoire](#utilisation-mémoire)
- [Optimisation CPU](#optimisation-cpu)
- [Optimisation Réseau](#optimisation-réseau)
- [Optimisation LDAP](#optimisation-ldap)
- [Tuning Active Directory](#tuning-active-directory)
- [Monitoring de Performance](#monitoring-de-performance)

---

## Vue d'Ensemble

Les problèmes de performance peuvent se manifester de plusieurs façons : requêtes lentes, timeouts, forte utilisation mémoire, ou charge CPU élevée.

### Symptômes Courants

- 🐌 Audits qui prennent plusieurs heures
- ⏱️ Timeouts fréquents sur les grandes requêtes
- 💾 Utilisation mémoire croissante
- 🔥 CPU à 100% pendant l'exécution
- 📊 Dégradation progressive des performances

### Objectifs de Performance

```
┌─────────────────────────────────────────────────────────┐
│ Objectif                    │ Valeur Cible              │
├─────────────────────────────────────────────────────────┤
│ Temps de réponse LDAP       │ < 500ms                   │
│ Audit complet (10k users)   │ < 5 minutes               │
│ Audit complet (100k users)  │ < 30 minutes              │
│ Utilisation mémoire         │ < 2 GB                    │
│ CPU pendant audit           │ < 70%                     │
│ Bande passante réseau       │ < 10 Mbps                 │
└─────────────────────────────────────────────────────────┘
```

---

## Diagnostic de Performance

### Outils de Benchmark

```bash
# Test de performance basique
time ldap-monitor audit health

# Avec profiling
ldap-monitor --profile audit users

# Mesurer les métriques détaillées
ldap-monitor audit users --metrics --output metrics.json

# Benchmark complet
ldap-monitor benchmark --iterations 10 --output benchmark-report.html
```

### Script de Diagnostic Performance

```bash
#!/bin/bash
# performance-diagnostic.sh

echo "=== Diagnostic de Performance LDAP Health Monitor ==="
echo ""

# 1. Configuration actuelle
echo "1. Configuration de performance actuelle:"
grep -A 5 "page_size\|timeout\|parallel" config.yaml
echo ""

# 2. Test de latence réseau
echo "2. Latence réseau vers serveur LDAP:"
SERVER=$(grep "server:" config.yaml | awk '{print $2}' | sed 's/ldap:\/\///' | sed 's/ldaps:\/\///')
ping -c 10 $SERVER | tail -1
echo ""

# 3. Temps de réponse LDAP
echo "3. Temps de réponse LDAP:"
time ldap-monitor test connection 2>&1 | grep "Response time"
echo ""

# 4. Statistiques système
echo "4. Ressources système disponibles:"
echo "  CPU: $(nproc) coeurs"
echo "  RAM totale: $(free -h | awk '/^Mem:/ {print $2}')"
echo "  RAM disponible: $(free -h | awk '/^Mem:/ {print $7}')"
echo "  Disque: $(df -h . | awk 'NR==2 {print $4}') disponible"
echo ""

# 5. Test d'audit rapide
echo "5. Test d'audit (échantillon):"
time ldap-monitor audit users --limit 100 2>&1 | tail -5
echo ""

# 6. Analyse des logs
echo "6. Derniers warnings de performance dans les logs:"
tail -1000 logs/ldap-monitor.log | grep -i "slow\|timeout\|performance\|memory" | tail -10
echo ""

echo "=== Fin du diagnostic ==="
```

### Métriques à Surveiller

```bash
# Temps de réponse moyen
ldap-monitor monitor metrics --filter response_time --period 1h

# Nombre de requêtes par seconde
ldap-monitor monitor metrics --filter queries_per_second

# Utilisation mémoire
ldap-monitor monitor metrics --filter memory_usage

# Graphique de performance
ldap-monitor monitor metrics --graph --output performance.png
```

---

## Requêtes Lentes

### Diagnostic de Requêtes Lentes

**Symptôme:**
```
INFO: Searching for users... (this may take a while)
WARNING: Query took 45 seconds
```

**Identifier les requêtes lentes:**

```bash
# Activer le logging détaillé
export LDAP_MONITOR_LOG_LEVEL=DEBUG

# Exécuter avec profiling
ldap-monitor --profile audit users > profile-output.txt

# Analyser les logs
grep "Query time\|Search time" logs/ldap-monitor.log | sort -k4 -n | tail -20
```

### Optimisation 1: Améliorer les Filtres LDAP

**❌ Filtres inefficaces:**

```python
# Trop large, récupère tout
"(objectClass=*)"

# Pas d'index sur customAttribute
"(customAttribute=value)"

# Wildcard au début (très lent)
"(mail=*@example.com)"
```

**✅ Filtres optimisés:**

```python
# Spécifique et indexé
"(objectClass=inetOrgPerson)"

# Attributs indexés standards
"(uid=jdoe)"
"(cn=John Doe)"

# Wildcard à la fin seulement
"(mail=john*)"

# Combiner avec AND pour réduire le scope
"(&(objectClass=inetOrgPerson)(ou=employees))"
```

**Configuration:**

```yaml
# config.yaml
ldap:
  # Utiliser des filtres plus spécifiques
  user_filter: "(&(objectClass=inetOrgPerson)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"
  group_filter: "(&(objectClass=groupOfNames)(!(cn=temp*)))"

audit:
  # Optimiser les recherches
  use_optimized_filters: true
  exclude_system_objects: true
```

### Optimisation 2: Pagination Efficace

**Problème:** Récupération de trop d'entrées à la fois

**Solution:**

```yaml
# config.yaml
ldap:
  # Ajuster la taille de page
  page_size: 1000  # Maximum pour AD, augmenter pour OpenLDAP

  # Pour OpenLDAP, peut être plus grand
  # page_size: 2000

  # Pour très grandes bases (100k+ objets)
  # page_size: 500  # Plus petit = moins de mémoire
```

**Impact de page_size:**

```
┌────────────┬──────────────┬──────────────┬──────────────┐
│ page_size  │ Mémoire      │ Vitesse      │ Recommandé   │
├────────────┼──────────────┼──────────────┼──────────────┤
│ 100        │ Faible       │ Très lent    │ Jamais       │
│ 500        │ Bas          │ Lent         │ Petite RAM   │
│ 1000       │ Moyen        │ Optimal      │ AD, Défaut   │
│ 2000       │ Élevé        │ Rapide       │ OpenLDAP     │
│ 5000       │ Très élevé   │ Très rapide  │ Local only   │
└────────────┴──────────────┴──────────────┴──────────────┘
```

### Optimisation 3: Attributs Sélectifs

**❌ Récupérer tous les attributs:**

```yaml
# Ralentit les requêtes et consomme de la mémoire
attributes: ["*"]  # ou ALL_ATTRIBUTES
```

**✅ Spécifier uniquement les attributs nécessaires:**

```yaml
# config.yaml
audit:
  # Pour l'audit users, seulement les attributs nécessaires
  user_attributes:
    - uid
    - cn
    - mail
    - sn
    - givenName
    - whenCreated
    - whenChanged
    - memberOf
    - userAccountControl

  # Pour l'audit groups
  group_attributes:
    - cn
    - member
    - description
    - whenCreated
```

**Impact sur la performance:**

```bash
# Test avec tous les attributs (lent)
time ldapsearch -H ldap://server -b "dc=example,dc=com" "(objectClass=inetOrgPerson)" "*"
# Résultat: 45 secondes, 150 MB de données

# Test avec attributs sélectifs (rapide)
time ldapsearch -H ldap://server -b "dc=example,dc=com" "(objectClass=inetOrgPerson)" uid cn mail
# Résultat: 8 secondes, 15 MB de données
```

### Optimisation 4: Limiter le Scope

**Rechercher uniquement où nécessaire:**

```yaml
# config.yaml
ldap:
  # Définir des OUs spécifiques
  users_ou: ou=employees,dc=example,dc=com  # Pas dc=example,dc=com
  groups_ou: ou=groups,dc=example,dc=com

  # Exclure des branches entières
  exclude_ous:
    - ou=disabled,dc=example,dc=com
    - ou=temporary,dc=example,dc=com
    - ou=system,dc=example,dc=com

audit:
  # Auditer seulement les OUs importantes
  audit_ous:
    - ou=employees,dc=example,dc=com
    - ou=contractors,dc=example,dc=com
```

**Commandes avec scope limité:**

```bash
# Auditer une OU spécifique
ldap-monitor audit users --base-dn "ou=employees,dc=example,dc=com"

# Exclure des branches
ldap-monitor audit users --exclude-ou "ou=disabled,dc=example,dc=com"

# Limiter le nombre de résultats pour test
ldap-monitor audit users --limit 1000
```

---

## Problèmes de Timeout

### Erreur: "Query timeout"

**Message:**
```
ERROR: Query timeout after 30 seconds
WARNING: Operation timed out: search_s()
```

### Solution 1: Augmenter les Timeouts

```yaml
# config.yaml
ldap:
  # Timeout de connexion
  timeout: 30  # secondes

  # Timeout de recherche (pour grandes bases)
  search_timeout: 60

  # Timeout pour opérations longues
  operation_timeout: 120

  # Retry avec backoff
  retry_max: 5
  retry_delay: 3
```

### Solution 2: Parallélisation des Requêtes

```yaml
# config.yaml
audit:
  # Activer le traitement parallèle
  parallel_checks: true
  max_workers: 4  # Nombre de threads

  # Paralléliser par OU
  parallel_by_ou: true

advanced:
  # Pool de connexions
  connection_pool_size: 5
  max_concurrent_operations: 10
```

**Exemple de code pour parallélisation:**

```python
# Les audits sont automatiquement parallélisés
ldap-monitor audit users --parallel --workers 4
```

### Solution 3: Streaming des Résultats

**Pour très grandes bases de données:**

```yaml
# config.yaml
advanced:
  # Activer le streaming (traiter au fur et à mesure)
  stream_results: true

  # Taille du buffer de streaming
  stream_buffer_size: 100

  # Traiter par batch
  batch_processing: true
  batch_size: 500
```

### Solution 4: Requêtes Progressives

**Diviser les grandes requêtes:**

```bash
#!/bin/bash
# audit-by-ou.sh - Auditer par OU pour éviter les timeouts

OUS=(
  "ou=dept1,dc=example,dc=com"
  "ou=dept2,dc=example,dc=com"
  "ou=dept3,dc=example,dc=com"
)

for OU in "${OUS[@]}"; do
  echo "Auditing $OU..."
  ldap-monitor audit users --base-dn "$OU" --output "audit-${OU}.json"
  sleep 2  # Pause entre les requêtes
done

# Combiner les résultats
ldap-monitor merge-reports audit-*.json --output audit-complet.json
```

---

## Utilisation Mémoire

### Diagnostic Mémoire

```bash
# Surveiller l'utilisation mémoire en temps réel
watch -n 1 'ps aux | grep ldap-monitor | grep -v grep'

# Profiling mémoire
python -m memory_profiler ldap-monitor audit users

# Avec tracemalloc
ldap-monitor --memory-profile audit users
```

### Symptômes de Problèmes Mémoire

```
WARNING: High memory usage: 3.2 GB
ERROR: MemoryError: Unable to allocate array
WARNING: System swapping detected
```

### Solution 1: Réduire la Consommation Mémoire

```yaml
# config.yaml
ldap:
  # Réduire la taille de page
  page_size: 500  # Au lieu de 2000

advanced:
  # Désactiver le cache si peu de RAM
  cache_enabled: false

  # Limiter les opérations concurrentes
  max_concurrent_operations: 3

  # Activer le streaming
  stream_results: true

  # Traitement par batch avec nettoyage
  batch_processing: true
  batch_size: 100
  clear_batch_memory: true
```

### Solution 2: Mode Low-Memory

```yaml
# config.yaml
performance:
  # Mode optimisé pour faible mémoire
  low_memory_mode: true

  # Limites strictes
  max_memory_mb: 1024
  max_cache_entries: 1000

  # Garbage collection agressif
  gc_aggressive: true
  gc_interval: 100  # Toutes les 100 opérations
```

**Commandes:**

```bash
# Exécuter en mode low-memory
ldap-monitor --low-memory audit users

# Avec limite mémoire stricte
ldap-monitor --max-memory 1GB audit users

# Traiter par petits lots
ldap-monitor audit users --batch-size 100
```

### Solution 3: Processing Incrémental

```bash
#!/bin/bash
# incremental-audit.sh

# Auditer par petits groupes
LETTERS="a b c d e f g h i j k l m n o p q r s t u v w x y z"

for LETTER in $LETTERS; do
  echo "Processing users starting with $LETTER..."

  ldap-monitor audit users \
    --filter "(uid=${LETTER}*)" \
    --output "users-${LETTER}.json"

  # Libérer la mémoire entre chaque exécution
  sleep 5
done

# Fusionner les résultats
ldap-monitor merge-reports users-*.json --output audit-complet.json
```

### Solution 4: Monitoring et Alarmes

```python
# monitor-memory.py
import psutil
import subprocess
import time

MAX_MEMORY_GB = 2.0

while True:
    # Trouver le processus ldap-monitor
    for proc in psutil.process_iter(['name', 'memory_info']):
        if 'ldap-monitor' in proc.info['name']:
            memory_gb = proc.info['memory_info'].rss / (1024 ** 3)

            if memory_gb > MAX_MEMORY_GB:
                print(f"ALERTE: Utilisation mémoire élevée: {memory_gb:.2f} GB")

                # Action: réduire le cache
                subprocess.run(['ldap-monitor', 'cache', 'clear'])

                # Ou: redémarrer le processus
                # proc.kill()
                # subprocess.run(['ldap-monitor', 'monitor', 'restart'])

    time.sleep(10)
```

---

## Optimisation CPU

### Diagnostic CPU

```bash
# Profiling CPU
python -m cProfile -o profile.stats ldap-monitor audit users

# Analyser les stats
python -c "import pstats; p = pstats.Stats('profile.stats'); p.sort_stats('cumulative'); p.print_stats(20)"

# Avec py-spy (sampling profiler)
py-spy record -o profile.svg -- ldap-monitor audit users

# Surveiller en temps réel
top -p $(pgrep -f ldap-monitor)
```

### Solution 1: Optimisation Multi-Threading

```yaml
# config.yaml
audit:
  # Activer parallélisation
  parallel_checks: true

  # Nombre de workers = nombre de CPUs - 1
  max_workers: auto  # ou spécifier: 4

  # Type de parallélisation
  parallel_method: thread  # ou 'process' pour CPU-intensive

advanced:
  # Thread pool pour I/O
  thread_pool_size: 8

  # Process pool pour calculs
  process_pool_size: 4
```

### Solution 2: Optimiser les Opérations Lourdes

**Désactiver les checks intensifs:**

```yaml
# config.yaml
audit:
  # Désactiver les vérifications lourdes
  checks:
    - health      # Léger
    - users       # Moyen
    # - groups    # Lourd si beaucoup de membres
    # - consistency  # Très lourd
    # - security  # Très lourd

  # Options pour réduire la charge
  skip_group_member_validation: true
  skip_nested_group_resolution: true
  skip_cross_references: true
```

### Solution 3: Cache Intelligent

```yaml
# config.yaml
advanced:
  # Activer le cache
  cache_enabled: true

  # TTL approprié
  cache_ttl: 3600  # 1 heure

  # Cache DNS pour éviter les résolutions répétées
  dns_cache_enabled: true
  dns_cache_ttl: 7200

  # Cache des résultats de recherche
  search_cache_enabled: true
  search_cache_max_entries: 10000
```

### Solution 4: Limiter les Opérations

```bash
# Auditer seulement ce qui est nécessaire
ldap-monitor audit users --skip-inactive

# Éviter les calculs coûteux
ldap-monitor audit groups --no-member-count

# Désactiver les cross-checks
ldap-monitor audit all --no-consistency-check
```

---

## Optimisation Réseau

### Diagnostic Réseau

```bash
# Mesurer la bande passante utilisée
iftop -i eth0

# Monitorer les connexions LDAP
netstat -an | grep :389

# Latence réseau
ping -c 100 ldap.example.com | tail -3

# Bande passante et latence
iperf3 -c ldap.example.com
```

### Solution 1: Optimisation de la Connexion

```yaml
# config.yaml
ldap:
  # Keep-alive pour réutiliser les connexions
  keep_alive: true
  keep_alive_interval: 60

  # Connection pooling
  connection_pool_size: 5

  # TCP options
  tcp_keepalive: true
  tcp_no_delay: true  # Désactiver Nagle's algorithm

advanced:
  # Compression (si supporté par le serveur)
  compression: true

  # Multiplexer les requêtes
  multiplexing: true
```

### Solution 2: Réduire le Volume de Données

```yaml
# config.yaml
audit:
  # Sélectionner seulement les attributs nécessaires
  minimal_attributes: true

  # Exclure les attributs volumineux
  exclude_attributes:
    - jpegPhoto
    - userCertificate
    - audio
    - photo

  # Limiter la taille des résultats
  max_entry_size_kb: 100
```

### Solution 3: Optimisation WAN

**Pour connexions lentes ou distantes:**

```yaml
# config.yaml
ldap:
  # Augmenter timeouts pour WAN
  timeout: 60
  search_timeout: 120

  # Réduire page_size pour moins de paquets perdus
  page_size: 500

  # Plus de retries pour réseaux instables
  retry_max: 5
  retry_delay: 5

advanced:
  # Activer compression
  compression: true

  # Buffer plus grand
  socket_buffer_size: 65536
```

---

## Optimisation LDAP

### Indexation sur le Serveur LDAP

**Vérifier les index existants (OpenLDAP):**

```bash
# Sur le serveur LDAP
ldapsearch -Y EXTERNAL -H ldapi:/// -b "olcDatabase={1}mdb,cn=config" olcDbIndex

# Ajouter des index
cat > add-indexes.ldif <<EOF
dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcDbIndex
olcDbIndex: uid eq,pres,sub
-
add: olcDbIndex
olcDbIndex: mail eq,pres,sub
-
add: olcDbIndex
olcDbIndex: cn eq,pres,sub
-
add: olcDbIndex
olcDbIndex: memberOf eq
-
add: olcDbIndex
olcDbIndex: objectClass eq
EOF

sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f add-indexes.ldif
```

**Index recommandés:**

```
┌─────────────────────┬──────────────────────────────────┐
│ Attribut            │ Type d'Index                     │
├─────────────────────┼──────────────────────────────────┤
│ objectClass         │ eq (égalité)                     │
│ uid                 │ eq,pres,sub (égalité, présence, sous-chaîne) │
│ cn                  │ eq,pres,sub                      │
│ mail                │ eq,sub                           │
│ memberOf            │ eq                               │
│ member              │ eq                               │
│ sn                  │ eq,sub                           │
│ givenName           │ eq,sub                           │
└─────────────────────┴──────────────────────────────────┘
```

### Optimisation du Serveur LDAP

**OpenLDAP - Tuning:**

```ldif
# database-tuning.ldif
dn: olcDatabase={1}mdb,cn=config
changetype: modify
replace: olcDbMaxSize
olcDbMaxSize: 10737418240
-
replace: olcDbMaxReaders
olcDbMaxReaders: 256
-
replace: olcDbMaxEntrySize
olcDbMaxEntrySize: 10485760
```

**Configuration serveur (slapd.conf style):**

```
# Limites pour éviter les timeouts
sizelimit unlimited
timelimit 120

# Cache
cachesize 10000
cachefree 2000

# Index
index objectClass eq
index uid eq,pres,sub
index cn eq,pres,sub
index mail eq,sub
index memberOf eq
```

---

## Tuning Active Directory

### Optimisation des Requêtes AD

```yaml
# config.yaml pour Active Directory
ldap:
  server: ldaps://dc01.corp.example.com
  port: 636

  # Taille de page maximale pour AD
  page_size: 1000  # Ne pas dépasser

  # Timeouts pour AD (souvent plus lent)
  timeout: 30
  search_timeout: 60

  # Utiliser le Global Catalog pour requêtes multi-domaines
  # port: 3268  # GC non-SSL
  # port: 3269  # GC SSL

advanced:
  # Désactiver la résolution des SIDs (très lent)
  resolve_sids: false

  # Cache AD spécifique
  ad_cache_enabled: true
  ad_cache_ttl: 7200
```

### Filtres Optimisés pour AD

```yaml
# config.yaml
ldap:
  # Exclure les comptes désactivés (améliore les performances)
  user_filter: "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"

  # Exclure les groupes système
  group_filter: "(&(objectClass=group)(!(isCriticalSystemObject=TRUE)))"

audit:
  # Ne pas auditer les comptes système
  exclude_system_accounts: true

  # Attributs AD spécifiques
  ad_specific_attributes:
    - sAMAccountName
    - userPrincipalName
    - lastLogonTimestamp
    - pwdLastSet
```

### PowerShell pour Monitoring AD

```powershell
# monitor-ad-performance.ps1

# Surveiller les performances LDAP sur DC
Get-Counter '\NTDS\LDAP Searches/sec'
Get-Counter '\NTDS\LDAP Client Sessions'
Get-Counter '\NTDS\LDAP Search Time'

# Vérifier les index
Get-ADObject -SearchBase "CN=Schema,CN=Configuration,DC=corp,DC=example,DC=com" `
  -Filter {objectClass -eq 'attributeSchema' -and searchFlags -gt 0} `
  -Properties lDAPDisplayName,searchFlags

# Statistiques de base de données
Invoke-Command -ComputerName DC01 -ScriptBlock {
  Get-WmiObject -Class Win32_PerfFormattedData_NTDS_NTDS
}
```

---

## Monitoring de Performance

### Dashboard de Performance

```bash
# Démarrer le monitoring en continu
ldap-monitor monitor start --metrics

# Dashboard web (Prometheus + Grafana)
ldap-monitor monitor prometheus --port 9090

# Voir les métriques actuelles
ldap-monitor monitor metrics

# Exporter l'historique
ldap-monitor monitor history --days 7 --output performance-7days.csv
```

### Métriques Prometheus

```yaml
# config.yaml
integrations:
  prometheus:
    enabled: true
    port: 9090
    metrics:
      - ldap_query_duration_seconds
      - ldap_query_total
      - ldap_connection_pool_size
      - ldap_memory_usage_bytes
      - ldap_cpu_usage_percent
      - ldap_cache_hit_ratio
      - ldap_objects_processed_total
```

### Alertes de Performance

```yaml
# config.yaml
alerts:
  performance:
    enabled: true

    # Seuils d'alerte
    thresholds:
      response_time_ms: 1000
      memory_usage_mb: 2048
      cpu_usage_percent: 80
      query_duration_seconds: 30

    # Actions
    actions:
      - type: slack
        message: "⚠️ Performance dégradée: {metric} = {value}"
      - type: email
        to: admin@example.com
```

### Script de Monitoring Continu

```bash
#!/bin/bash
# continuous-performance-monitoring.sh

LOG_FILE="performance-monitoring.log"
INTERVAL=60  # secondes

while true; do
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

  # Mesurer le temps de réponse
  RESPONSE_TIME=$(ldap-monitor test connection 2>&1 | grep -oP 'Response time: \K[0-9]+')

  # Utilisation mémoire du processus
  PID=$(pgrep -f "ldap-monitor monitor")
  if [ ! -z "$PID" ]; then
    MEMORY=$(ps -p $PID -o rss= | awk '{print $1/1024}')
    CPU=$(ps -p $PID -o %cpu= | awk '{print $1}')
  else
    MEMORY=0
    CPU=0
  fi

  # Enregistrer
  echo "$TIMESTAMP,$RESPONSE_TIME,$MEMORY,$CPU" >> $LOG_FILE

  # Alerter si nécessaire
  if [ "$RESPONSE_TIME" -gt 1000 ]; then
    echo "⚠️ ALERTE: Temps de réponse élevé: ${RESPONSE_TIME}ms"
  fi

  sleep $INTERVAL
done
```

### Analyse des Performances

```python
# analyze-performance.py
import pandas as pd
import matplotlib.pyplot as plt

# Charger les données
df = pd.read_csv('performance-monitoring.log',
                 names=['timestamp', 'response_time', 'memory', 'cpu'],
                 parse_dates=['timestamp'])

# Statistiques
print("=== Statistiques de Performance ===")
print(f"Temps de réponse moyen: {df['response_time'].mean():.2f} ms")
print(f"Temps de réponse médian: {df['response_time'].median():.2f} ms")
print(f"Temps de réponse p95: {df['response_time'].quantile(0.95):.2f} ms")
print(f"Temps de réponse max: {df['response_time'].max():.2f} ms")
print(f"Mémoire moyenne: {df['memory'].mean():.2f} MB")
print(f"CPU moyen: {df['cpu'].mean():.2f}%")

# Graphiques
fig, axes = plt.subplots(3, 1, figsize=(12, 10))

# Temps de réponse
axes[0].plot(df['timestamp'], df['response_time'])
axes[0].set_title('Temps de Réponse LDAP')
axes[0].set_ylabel('ms')
axes[0].axhline(y=500, color='orange', linestyle='--', label='Warning')
axes[0].axhline(y=1000, color='red', linestyle='--', label='Critical')
axes[0].legend()

# Mémoire
axes[1].plot(df['timestamp'], df['memory'], color='green')
axes[1].set_title('Utilisation Mémoire')
axes[1].set_ylabel('MB')

# CPU
axes[2].plot(df['timestamp'], df['cpu'], color='blue')
axes[2].set_title('Utilisation CPU')
axes[2].set_ylabel('%')
axes[2].set_xlabel('Temps')

plt.tight_layout()
plt.savefig('performance-analysis.png')
print("\nGraphiques sauvegardés: performance-analysis.png")
```

---

## Best Practices de Performance

### Checklist d'Optimisation

```
☑ Configuration
  ☐ page_size optimal (1000 pour AD, 2000 pour OpenLDAP)
  ☐ Timeouts appropriés (30-60s)
  ☐ Cache activé
  ☐ Attributs sélectifs

☑ Requêtes
  ☐ Filtres spécifiques et indexés
  ☐ Scope limité aux OUs nécessaires
  ☐ Éviter les wildcards au début
  ☐ Exclure les objets système

☑ Système
  ☐ RAM suffisante (4GB+ recommandé)
  ☐ CPU multi-core pour parallélisation
  ☐ Réseau stable et rapide
  ☐ Disque avec I/O rapide pour logs/cache

☑ Serveur LDAP
  ☐ Index appropriés
  ☐ Tuning de la base de données
  ☐ Réplication pour load-balancing
  ☐ Monitoring actif

☑ Application
  ☐ Version à jour de ldap-health-monitor
  ☐ Parallélisation activée
  ☐ Streaming pour grandes bases
  ☐ Monitoring de performance actif
```

### Configuration Optimale par Taille

**Petite base (< 10k objets):**

```yaml
ldap:
  page_size: 1000
  timeout: 10

audit:
  parallel_checks: false
  cache_enabled: true
```

**Base moyenne (10k - 100k objets):**

```yaml
ldap:
  page_size: 1000
  timeout: 30

audit:
  parallel_checks: true
  max_workers: 4

advanced:
  cache_enabled: true
  stream_results: false
```

**Grande base (> 100k objets):**

```yaml
ldap:
  page_size: 500  # Réduire pour moins de mémoire
  timeout: 60

audit:
  parallel_checks: true
  max_workers: 8
  parallel_by_ou: true

advanced:
  cache_enabled: true
  stream_results: true
  batch_processing: true
  low_memory_mode: true
```

---

## Ressources Supplémentaires

### Documentation

- [LDAP Performance Tuning Guide](https://www.openldap.org/doc/admin24/tuning.html)
- [Active Directory Performance](https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/plan/performance)
- [Python ldap3 Performance](https://ldap3.readthedocs.io/en/latest/performance.html)

### Outils de Profiling

```bash
# Installation
pip install memory_profiler py-spy

# Utilisation
memory_profiler ldap-monitor audit users
py-spy top -- ldap-monitor monitor start
```

---

**Page suivante:** [Common Errors](Common-Errors.md)
**Page précédente:** [Connection Issues](Connection-Issues.md)
