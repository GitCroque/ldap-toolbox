# Guide de Débogage

Guide complet de débogage, logging et méthodologie de résolution de problèmes pour LDAP Health Monitor.

## Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Niveaux de Logging](#niveaux-de-logging)
- [Mode Debug](#mode-debug)
- [Analyse des Logs](#analyse-des-logs)
- [Méthodologie de Débogage](#méthodologie-de-débogage)
- [Outils de Débogage](#outils-de-débogage)
- [Profiling et Tracing](#profiling-et-tracing)
- [Débogage Réseau](#débogage-réseau)
- [Cas Pratiques](#cas-pratiques)
- [Scripts Utiles](#scripts-utiles)

---

## Vue d'Ensemble

Le débogage efficace nécessite une compréhension des différents niveaux de logging, des outils disponibles, et d'une méthodologie systématique.

### Philosophie du Débogage

```
┌─────────────────────────────────────────────────────────┐
│ 1. OBSERVER    → Collecter les informations            │
│ 2. ISOLER      → Identifier la source du problème      │
│ 3. REPRODUIRE  → Confirmer le comportement             │
│ 4. CORRIGER    → Appliquer la solution                 │
│ 5. VÉRIFIER    → Valider la correction                 │
└─────────────────────────────────────────────────────────┘
```

---

## Niveaux de Logging

### Configuration des Niveaux

```yaml
# config.yaml
logging:
  # Niveaux disponibles: DEBUG, INFO, WARNING, ERROR, CRITICAL
  level: INFO

  # Format des messages
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

  # Fichier de log
  file: logs/ldap-monitor.log

  # Rotation des logs
  max_bytes: 10485760  # 10 MB
  backup_count: 5

  # Aussi afficher dans la console
  console: true
```

### Hiérarchie des Niveaux

```
┌───────────┬────────────────────────────────────────────────┐
│ Niveau    │ Utilisation                                    │
├───────────┼────────────────────────────────────────────────┤
│ DEBUG     │ Informations détaillées pour le débogage      │
│           │ - Chaque requête LDAP                          │
│           │ - Valeurs des variables                        │
│           │ - Flux d'exécution détaillé                   │
│           │                                                │
│ INFO      │ Confirmations que tout fonctionne              │
│           │ - Démarrage/arrêt                              │
│           │ - Opérations principales réussies             │
│           │ - Statistiques                                 │
│           │                                                │
│ WARNING   │ Quelque chose d'inattendu mais pas critique   │
│           │ - Performances dégradées                       │
│           │ - Attributs manquants                          │
│           │ - Retry automatiques                           │
│           │                                                │
│ ERROR     │ Problème empêchant une fonction               │
│           │ - Échec de connexion                           │
│           │ - Requête échouée                              │
│           │ - Exception attrapée                           │
│           │                                                │
│ CRITICAL  │ Erreur grave, l'application peut crasher      │
│           │ - Impossible de continuer                      │
│           │ - Corruption de données                        │
│           │ - Ressources épuisées                          │
└───────────┴────────────────────────────────────────────────┘
```

### Exemples de Messages par Niveau

**DEBUG:**
```
2025-11-17 10:00:00 - ldap.connector - DEBUG - Creating connection to ldaps://ldap.example.com:636
2025-11-17 10:00:00 - ldap.connector - DEBUG - SSL configuration: validate=True, version=TLSv1_2
2025-11-17 10:00:01 - ldap.connector - DEBUG - Binding as: cn=admin,dc=example,dc=com
2025-11-17 10:00:01 - ldap.connector - DEBUG - Search filter: (&(objectClass=inetOrgPerson)(uid=*))
2025-11-17 10:00:01 - ldap.connector - DEBUG - Search base: ou=users,dc=example,dc=com
2025-11-17 10:00:02 - ldap.connector - DEBUG - Retrieved 1523 entries in 1.2s
```

**INFO:**
```
2025-11-17 10:00:00 - ldap.monitor - INFO - LDAP Health Monitor v1.0.0 starting
2025-11-17 10:00:01 - ldap.connector - INFO - Connected to ldap.example.com:636
2025-11-17 10:00:02 - ldap.audit - INFO - Starting user audit
2025-11-17 10:00:45 - ldap.audit - INFO - Audit completed: 1523 users, 45 issues found
2025-11-17 10:00:45 - ldap.monitor - INFO - Shutting down gracefully
```

**WARNING:**
```
2025-11-17 10:05:23 - ldap.audit - WARNING - User uid=jdoe missing required attribute 'mail'
2025-11-17 10:05:30 - ldap.connector - WARNING - Slow query detected: 5.2s for group membership
2025-11-17 10:06:15 - ldap.monitor - WARNING - Memory usage high: 2.1 GB
```

**ERROR:**
```
2025-11-17 10:10:00 - ldap.connector - ERROR - Connection failed: [Errno 111] Connection refused
2025-11-17 10:10:00 - ldap.connector - ERROR - Retry attempt 1/3 failed
2025-11-17 10:10:05 - ldap.audit - ERROR - Failed to retrieve group members for cn=admins
```

**CRITICAL:**
```
2025-11-17 10:15:00 - ldap.connector - CRITICAL - All connection attempts exhausted
2025-11-17 10:15:00 - ldap.monitor - CRITICAL - Unable to continue without LDAP connection
2025-11-17 10:15:00 - ldap.monitor - CRITICAL - Terminating application
```

---

## Mode Debug

### Activer le Mode Debug

**Méthode 1: Option en ligne de commande**

```bash
# Debug global
ldap-monitor --debug audit health

# Verbose (entre INFO et DEBUG)
ldap-monitor --verbose audit health

# Debug très détaillé
ldap-monitor --debug --trace audit health
```

**Méthode 2: Variable d'environnement**

```bash
# Définir le niveau de log
export LDAP_MONITOR_LOG_LEVEL=DEBUG
ldap-monitor audit health

# Avec trace détaillée
export LDAP_MONITOR_TRACE=1
ldap-monitor audit health
```

**Méthode 3: Configuration**

```yaml
# config.yaml
logging:
  level: DEBUG

  # Options de debug supplémentaires
  debug_options:
    # Logger toutes les requêtes LDAP
    log_ldap_queries: true

    # Logger les données (attention: sensible!)
    log_data: false  # Ne pas activer en production

    # Logger les timings
    log_timings: true

    # Logger le stack trace complet
    log_stack_trace: true
```

### Debug Sélectif par Module

```yaml
# config.yaml
logging:
  level: INFO  # Niveau global

  # Niveaux par module
  module_levels:
    ldap.connector: DEBUG      # Debug pour les connexions
    ldap.audit: INFO           # Info pour l'audit
    ldap.monitor: WARNING      # Warnings seulement
    ldap.reporters: ERROR      # Erreurs seulement
```

**En ligne de commande:**

```bash
# Debug pour un module spécifique
ldap-monitor --debug-module ldap.connector audit health

# Debug pour plusieurs modules
ldap-monitor --debug-module ldap.connector --debug-module ldap.audit audit health
```

### Mode Debug Interactif

```bash
# Démarrer en mode interactif avec debug
ldap-monitor --debug --interactive

# Console Python avec contexte chargé
>>> connector.test_connection()
(True, 125.3, None)

>>> config.ldap.server
'ldap.example.com'

>>> # Exécuter des commandes de débogage
>>> import pdb; pdb.set_trace()
```

---

## Analyse des Logs

### Structure des Logs

**Format standard:**
```
TIMESTAMP - MODULE - LEVEL - MESSAGE
2025-11-17 10:00:00 - ldap.connector - INFO - Connected successfully
```

**Format avec contexte:**
```
2025-11-17 10:00:00 - ldap.connector - INFO - Connected successfully
  Server: ldap.example.com:636
  Protocol: LDAPS
  Bind DN: cn=admin,dc=example,dc=com
  Response Time: 125ms
```

### Commandes d'Analyse

**Filtrer par niveau:**

```bash
# Seulement les erreurs
grep "ERROR" logs/ldap-monitor.log

# Erreurs et critical
grep -E "ERROR|CRITICAL" logs/ldap-monitor.log

# Avec contexte (5 lignes avant/après)
grep -C 5 "ERROR" logs/ldap-monitor.log
```

**Filtrer par module:**

```bash
# Tous les logs du connecteur
grep "ldap.connector" logs/ldap-monitor.log

# Connexions seulement
grep "ldap.connector.*Connect" logs/ldap-monitor.log
```

**Filtrer par période:**

```bash
# Logs d'aujourd'hui
grep "$(date +%Y-%m-%d)" logs/ldap-monitor.log

# Logs entre 10h et 11h
grep "2025-11-17 10:" logs/ldap-monitor.log

# Logs des 5 dernières minutes
tail -f logs/ldap-monitor.log | grep --line-buffered "$(date +%Y-%m-%d\ %H:%M)"
```

**Statistiques:**

```bash
# Compter par niveau
grep -o "- [A-Z]* -" logs/ldap-monitor.log | sort | uniq -c

# Compter les erreurs par type
grep "ERROR" logs/ldap-monitor.log | cut -d'-' -f4 | sort | uniq -c | sort -rn

# Top 10 des messages les plus fréquents
grep "ERROR" logs/ldap-monitor.log | cut -d'-' -f4- | sort | uniq -c | sort -rn | head -10
```

### Scripts d'Analyse

**Script d'analyse de logs:**

```bash
#!/bin/bash
# analyze-logs.sh - Analyse complète des logs

LOG_FILE="logs/ldap-monitor.log"

echo "=== Analyse des Logs LDAP Health Monitor ==="
echo "Fichier: $LOG_FILE"
echo "Taille: $(du -h $LOG_FILE | cut -f1)"
echo ""

# Compteurs par niveau
echo "=== Répartition par Niveau ==="
grep -o "- [A-Z]* -" $LOG_FILE | sort | uniq -c | sort -rn
echo ""

# Dernières erreurs
echo "=== 10 Dernières Erreurs ==="
grep "ERROR" $LOG_FILE | tail -10
echo ""

# Erreurs critiques
CRITICAL_COUNT=$(grep -c "CRITICAL" $LOG_FILE)
if [ $CRITICAL_COUNT -gt 0 ]; then
  echo "=== ⚠️  $CRITICAL_COUNT Erreurs CRITICAL ==="
  grep "CRITICAL" $LOG_FILE
  echo ""
fi

# Warnings récents
echo "=== Warnings de la dernière heure ==="
HOUR_AGO=$(date -d '1 hour ago' +%Y-%m-%d\ %H)
grep "$HOUR_AGO" $LOG_FILE | grep "WARNING" | tail -20
echo ""

# Patterns d'erreurs
echo "=== Patterns d'Erreurs les Plus Fréquents ==="
grep "ERROR" $LOG_FILE | sed 's/[0-9]\+/N/g' | sort | uniq -c | sort -rn | head -5
echo ""

# Statistiques temporelles
echo "=== Activité par Heure ==="
cut -d' ' -f2 $LOG_FILE | cut -d':' -f1 | sort | uniq -c
echo ""

# Temps de réponse
echo "=== Temps de Réponse Moyens ==="
grep "Response time:" $LOG_FILE | awk '{print $NF}' | sed 's/ms//' | awk '{sum+=$1; count++} END {print "Moyenne: " sum/count " ms"}'
echo ""

echo "=== Fin de l'analyse ==="
```

**Script de monitoring en temps réel:**

```bash
#!/bin/bash
# tail-logs.sh - Monitoring en temps réel avec couleurs

LOG_FILE="logs/ldap-monitor.log"

# Couleurs
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Monitoring: $LOG_FILE (Ctrl+C pour quitter)"
echo ""

tail -f $LOG_FILE | while read line; do
  if echo "$line" | grep -q "CRITICAL"; then
    echo -e "${RED}${line}${NC}"
  elif echo "$line" | grep -q "ERROR"; then
    echo -e "${RED}${line}${NC}"
  elif echo "$line" | grep -q "WARNING"; then
    echo -e "${YELLOW}${line}${NC}"
  elif echo "$line" | grep -q "INFO"; then
    echo -e "${GREEN}${line}${NC}"
  elif echo "$line" | grep -q "DEBUG"; then
    echo -e "${BLUE}${line}${NC}"
  else
    echo "$line"
  fi
done
```

---

## Méthodologie de Débogage

### Approche Systématique

**1. Définir le Problème**

```
Questions à se poser:
- Quel est le symptôme exact?
- Quand le problème est-il apparu?
- Le problème est-il reproductible?
- Quelles sont les conditions de reproduction?
- Y a-t-il eu des changements récents?
```

**2. Collecter les Informations**

```bash
# Informations système
ldap-monitor --version
python3 --version
uname -a

# Configuration
ldap-monitor config show

# Logs récents
tail -100 logs/ldap-monitor.log

# État du système
free -h
df -h
top -b -n 1 | head -20
```

**3. Isoler la Cause**

```bash
# Test minimal
ldap-monitor test connection

# Test avec debug
ldap-monitor --debug test connection

# Test composant par composant
ldap-monitor --debug audit health
ldap-monitor --debug audit users --limit 10
ldap-monitor --debug audit groups --limit 10
```

**4. Formuler une Hypothèse**

```
Exemples d'hypothèses:
- "Le problème vient de la connexion LDAP"
  → Tester: ldap-monitor test connection
  → Tester: telnet ldap.example.com 389

- "Le problème vient des permissions"
  → Tester: ldapsearch avec les mêmes credentials
  → Vérifier: logs du serveur LDAP

- "Le problème vient de la configuration"
  → Tester: ldap-monitor config validate
  → Comparer: avec config.example.yaml
```

**5. Tester l'Hypothèse**

```bash
# Créer un test reproductible
cat > test-hypothesis.sh <<'EOF'
#!/bin/bash
set -e

echo "Test de l'hypothèse: Connexion LDAP"

# Test 1: Réseau
ping -c 1 ldap.example.com || exit 1

# Test 2: Port
nc -zv ldap.example.com 389 || exit 1

# Test 3: LDAP avec ldapsearch
ldapsearch -H ldap://ldap.example.com -b "" -s base || exit 1

# Test 4: LDAP avec l'application
ldap-monitor test connection || exit 1

echo "Tous les tests passés"
EOF

chmod +x test-hypothesis.sh
./test-hypothesis.sh
```

**6. Appliquer la Solution**

```bash
# Documenter la solution
cat > solution.md <<'EOF'
# Solution au Problème

## Problème
Description du problème

## Cause Identifiée
Cause racine

## Solution Appliquée
Étapes de la solution

## Vérification
Comment vérifier que c'est résolu

## Prévention
Comment éviter à l'avenir
EOF
```

**7. Vérifier la Résolution**

```bash
# Tests de régression
ldap-monitor test connection
ldap-monitor audit health
ldap-monitor audit users --limit 100

# Monitoring continue
ldap-monitor monitor start --daemon
sleep 300  # 5 minutes
ldap-monitor monitor status
```

### Checklist de Débogage

```
☐ 1. Identifier le Problème
  ☐ Message d'erreur exact
  ☐ Code de sortie
  ☐ Stacktrace complet
  ☐ Contexte (quand, comment, fréquence)

☐ 2. Vérifier les Bases
  ☐ Configuration valide
  ☐ Variables d'environnement définies
  ☐ Fichiers/répertoires existent
  ☐ Permissions correctes

☐ 3. Vérifier la Connectivité
  ☐ Réseau accessible
  ☐ DNS résolu
  ☐ Port ouvert
  ☐ Serveur LDAP actif

☐ 4. Vérifier l'Authentification
  ☐ Credentials corrects
  ☐ DN valide
  ☐ Compte actif
  ☐ Permissions suffisantes

☐ 5. Consulter les Logs
  ☐ Logs de l'application
  ☐ Logs du serveur LDAP
  ☐ Logs système
  ☐ Logs réseau (si pertinent)

☐ 6. Isoler le Problème
  ☐ Reproduire en isolation
  ☐ Tester chaque composant
  ☐ Éliminer les variables

☐ 7. Rechercher des Solutions
  ☐ Documentation
  ☐ FAQ
  ☐ GitHub Issues
  ☐ Recherche web

☐ 8. Tester la Solution
  ☐ Appliquer la correction
  ☐ Vérifier le résultat
  ☐ Tests de régression
```

---

## Outils de Débogage

### Outils Intégrés

**1. Test de Connexion**

```bash
# Test basique
ldap-monitor test connection

# Test avec détails
ldap-monitor test connection --verbose

# Test avec timeout custom
ldap-monitor test connection --timeout 30

# Test multiple fois
for i in {1..10}; do
  echo "Test $i:"
  ldap-monitor test connection
  sleep 2
done
```

**2. Validation de Configuration**

```bash
# Valider
ldap-monitor config validate

# Montrer la configuration chargée
ldap-monitor config show

# Montrer seulement une section
ldap-monitor config show ldap
ldap-monitor config show audit

# Tester avec configuration alternative
ldap-monitor --config config-test.yaml config validate
```

**3. Mode Dry-Run**

```bash
# Dry-run pour voir ce qui serait fait
ldap-monitor cleanup --dry-run

# Avec détails
ldap-monitor cleanup --dry-run --verbose

# Sauvegarder la sortie
ldap-monitor cleanup --dry-run > dry-run-output.txt
```

### Outils Externes

**1. ldapsearch**

```bash
# Test de connexion basique
ldapsearch -H ldap://server -D "bind_dn" -w "password" -b "base_dn" "(objectClass=*)" dn

# Avec debug LDAP
ldapsearch -d 1 -H ldap://server -D "bind_dn" -w "password" -b "base_dn"

# Test SSL
ldapsearch -H ldaps://server -D "bind_dn" -w "password" -b "base_dn"

# Test STARTTLS
ldapsearch -H ldap://server -Z -D "bind_dn" -w "password" -b "base_dn"
```

**2. Outils réseau**

```bash
# Test de port
nc -zv ldap.example.com 389
telnet ldap.example.com 389

# Trace réseau
traceroute ldap.example.com
mtr ldap.example.com

# Capturer le trafic (root required)
sudo tcpdump -i any -n port 389 -w ldap-traffic.pcap

# Analyser avec tshark
tshark -r ldap-traffic.pcap -Y ldap
```

**3. SSL/TLS debugging**

```bash
# Test SSL/TLS
openssl s_client -connect ldap.example.com:636 -showcerts

# Vérifier certificat
openssl s_client -connect ldap.example.com:636 2>/dev/null | openssl x509 -text -noout

# Test STARTTLS
openssl s_client -connect ldap.example.com:389 -starttls ldap
```

---

## Profiling et Tracing

### Profiling CPU

```bash
# Avec cProfile
python -m cProfile -o profile.stats -m ldap_monitor audit users

# Analyser les résultats
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"

# Avec py-spy (sampling profiler, pas besoin de modifier le code)
pip install py-spy
py-spy record -o profile.svg -- ldap-monitor audit users

# Top en temps réel
py-spy top -- ldap-monitor monitor start
```

### Profiling Mémoire

```bash
# Avec memory_profiler
pip install memory_profiler
python -m memory_profiler ldap-monitor audit users

# Avec tracemalloc (built-in)
ldap-monitor --memory-profile audit users

# Avec memray (nouveau)
pip install memray
memray run ldap-monitor audit users
memray flamegraph output.bin
```

### Tracing

```bash
# Tracer l'exécution
strace -o trace.log ldap-monitor audit health

# Tracer seulement les appels réseau
strace -e trace=network ldap-monitor test connection

# Tracer avec timestamps
strace -tt -o trace.log ldap-monitor audit users

# Analyser les traces
grep "connect" trace.log
grep "sendto\|recvfrom" trace.log
```

### Python Debugger (pdb)

```python
# Ajouter un breakpoint dans le code
import pdb; pdb.set_trace()

# Ou utiliser le nouveau breakpoint() (Python 3.7+)
breakpoint()
```

**Commandes pdb:**

```
h        - Help
l        - List code
n        - Next line
s        - Step into
c        - Continue
p var    - Print variable
pp var   - Pretty print
w        - Where (stack trace)
u        - Up in stack
d        - Down in stack
b line   - Set breakpoint
cl       - Clear breakpoints
q        - Quit
```

---

## Débogage Réseau

### Capturer le Trafic LDAP

```bash
# Capturer tout le trafic LDAP
sudo tcpdump -i any port 389 -w ldap.pcap

# Capturer LDAPS
sudo tcpdump -i any port 636 -w ldaps.pcap

# Capturer avec timestamps haute résolution
sudo tcpdump -i any port 389 -tt -w ldap.pcap

# Afficher en temps réel
sudo tcpdump -i any port 389 -A
```

### Analyser avec Wireshark

```bash
# Installer
sudo apt-get install wireshark tshark

# Analyser
wireshark ldap.pcap

# Filtres Wireshark utiles:
# ldap                          - Tout le trafic LDAP
# ldap.protocolOp == 0          - Bind requests
# ldap.protocolOp == 1          - Bind responses
# ldap.protocolOp == 3          - Search requests
# ldap.protocolOp == 4          - Search entries
# ldap.resultCode != 0          - Erreurs LDAP
```

### Statistiques Réseau

```bash
# Latence
ping -c 100 ldap.example.com | tail -3

# Bande passante
iperf3 -c ldap.example.com

# Connexions actives
netstat -an | grep :389

# Statistiques détaillées
ss -s
ss -tan | grep :389
```

---

## Cas Pratiques

### Cas 1: Connexion Échoue Aléatoirement

**Symptômes:**
```
Parfois fonctionne, parfois timeout
```

**Débogage:**

```bash
# 1. Tester en boucle
for i in {1..100}; do
  echo "Test $i: $(date)"
  ldap-monitor test connection || echo "FAILED"
  sleep 1
done | tee connection-test.log

# 2. Analyser les échecs
grep "FAILED" connection-test.log | wc -l

# 3. Vérifier les patterns
grep -B 2 "FAILED" connection-test.log

# 4. Tester la stabilité réseau
mtr --report -c 100 ldap.example.com

# 5. Vérifier le load-balancer (si applicable)
# Peut être round-robin avec serveur défaillant
```

**Solution:**
- Configurer retry avec backoff
- Utiliser keepalive
- Vérifier le load-balancer

---

### Cas 2: Performance Dégradée Progressivement

**Symptômes:**
```
Commence rapide, ralentit avec le temps
```

**Débogage:**

```bash
# 1. Profiler avec timestamps
ldap-monitor --debug --profile audit users 2>&1 | tee profile.log

# 2. Extraire les timings
grep "took" profile.log | awk '{print $NF}' > timings.txt

# 3. Analyser la progression
gnuplot <<EOF
set terminal png
set output 'performance.png'
plot 'timings.txt' with lines title 'Query Time'
EOF

# 4. Vérifier la mémoire
while true; do
  ps aux | grep ldap-monitor | grep -v grep | awk '{print $6}'
  sleep 5
done > memory-usage.log

# 5. Chercher les fuites mémoire
diff <(head -10 memory-usage.log) <(tail -10 memory-usage.log)
```

**Solution:**
- Activer le garbage collection agressif
- Utiliser le streaming
- Ajouter des pauses entre les batches

---

### Cas 3: Erreur Intermittente Difficile à Reproduire

**Symptômes:**
```
Erreur rare, pas de pattern clair
```

**Débogage:**

```bash
# 1. Logger tout en DEBUG
export LDAP_MONITOR_LOG_LEVEL=DEBUG

# 2. Exécuter en boucle avec capture
cat > run-until-error.sh <<'EOF'
#!/bin/bash
COUNTER=0
while true; do
  COUNTER=$((COUNTER+1))
  echo "Run $COUNTER: $(date)"

  ldap-monitor audit health > run-$COUNTER.log 2>&1
  EXIT_CODE=$?

  if [ $EXIT_CODE -ne 0 ]; then
    echo "ERROR on run $COUNTER!"
    cp logs/ldap-monitor.log error-logs-$COUNTER.log
    echo "Logs saved to error-logs-$COUNTER.log"
    exit 1
  fi

  sleep 10
done
EOF

chmod +x run-until-error.sh
./run-until-error.sh

# 3. Quand erreur capturée, comparer avec run réussi
diff run-1.log run-ERROR.log
diff logs/ldap-monitor.log.1 error-logs-ERROR.log
```

---

## Scripts Utiles

### Script de Debug Complet

```bash
#!/bin/bash
# full-debug.sh - Collecte complète d'informations de debug

OUTPUT_DIR="debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p $OUTPUT_DIR

echo "Collecte des informations de debug dans: $OUTPUT_DIR"

# 1. Informations système
echo "=== System Info ===" > $OUTPUT_DIR/system-info.txt
uname -a >> $OUTPUT_DIR/system-info.txt
echo "" >> $OUTPUT_DIR/system-info.txt
free -h >> $OUTPUT_DIR/system-info.txt
echo "" >> $OUTPUT_DIR/system-info.txt
df -h >> $OUTPUT_DIR/system-info.txt

# 2. Versions
echo "=== Versions ===" > $OUTPUT_DIR/versions.txt
python3 --version >> $OUTPUT_DIR/versions.txt 2>&1
ldap-monitor --version >> $OUTPUT_DIR/versions.txt 2>&1
pip list | grep -E "ldap|yaml" >> $OUTPUT_DIR/versions.txt

# 3. Configuration (masquée)
echo "=== Configuration ===" > $OUTPUT_DIR/config.txt
sed 's/password:.*/password: ***MASKED***/' config.yaml >> $OUTPUT_DIR/config.txt 2>&1

# 4. Variables d'environnement
echo "=== Environment ===" > $OUTPUT_DIR/environment.txt
env | grep -E "LDAP|PATH|PYTHON" | sed 's/PASSWORD=.*/PASSWORD=***MASKED***/' >> $OUTPUT_DIR/environment.txt

# 5. Test de connexion avec debug
echo "=== Connection Test ===" > $OUTPUT_DIR/connection-test.txt
ldap-monitor --debug test connection >> $OUTPUT_DIR/connection-test.txt 2>&1

# 6. Logs récents
if [ -f logs/ldap-monitor.log ]; then
  tail -500 logs/ldap-monitor.log > $OUTPUT_DIR/recent-logs.txt
fi

# 7. Tests réseau
SERVER=$(grep "server:" config.yaml | awk '{print $2}' | sed 's/ldap:\/\///' | sed 's/ldaps:\/\///')
echo "=== Network Tests ===" > $OUTPUT_DIR/network-tests.txt
ping -c 5 $SERVER >> $OUTPUT_DIR/network-tests.txt 2>&1
echo "" >> $OUTPUT_DIR/network-tests.txt
traceroute -m 10 $SERVER >> $OUTPUT_DIR/network-tests.txt 2>&1

# 8. Créer archive
tar -czf $OUTPUT_DIR.tar.gz $OUTPUT_DIR/

echo ""
echo "✓ Informations collectées dans: $OUTPUT_DIR.tar.gz"
echo "  Vérifier que les mots de passe sont masqués avant de partager!"
```

### Script de Monitoring Continue

```bash
#!/bin/bash
# continuous-monitor.sh - Monitoring avec alertes

LOG_FILE="continuous-monitor.log"
CHECK_INTERVAL=60  # secondes
ALERT_EMAIL="admin@example.com"

while true; do
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

  # Test de connexion
  if ldap-monitor test connection > /dev/null 2>&1; then
    STATUS="OK"
  else
    STATUS="FAILED"

    # Alerter
    echo "ALERT: LDAP connection failed at $TIMESTAMP" | mail -s "LDAP Alert" $ALERT_EMAIL

    # Collecter debug info
    ./full-debug.sh
  fi

  # Logger
  echo "$TIMESTAMP - Connection: $STATUS" | tee -a $LOG_FILE

  # Attendre
  sleep $CHECK_INTERVAL
done
```

---

## Best Practices de Débogage

### À Faire

```
✓ Activer DEBUG uniquement quand nécessaire
✓ Commencer par les logs existants
✓ Reproduire le problème de manière isolée
✓ Documenter les étapes de reproduction
✓ Tester une hypothèse à la fois
✓ Garder une trace de ce qui a été testé
✓ Comparer avec une configuration qui fonctionne
✓ Vérifier les changements récents
✓ Consulter la documentation et FAQ
✓ Demander de l'aide avec informations complètes
```

### À Éviter

```
✗ Logger les mots de passe
✗ Laisser DEBUG en production
✗ Modifier plusieurs choses à la fois
✗ Ignorer les warnings
✗ Assumer sans vérifier
✗ Sauter les étapes de base
✗ Oublier de vérifier les logs du serveur LDAP
✗ Ne pas tester la solution
✗ Ne pas documenter la résolution
```

### Sécurité du Debug

```bash
# Ne JAMAIS logger les mots de passe
# Masquer automatiquement
grep -v "password" logs/ldap-monitor.log

# Ou utiliser sed
sed 's/password=.*/password=***MASKED***/' logs/ldap-monitor.log

# Vérifier avant de partager
grep -i "password\|secret\|key" debug-info.txt
```

---

## Ressources Supplémentaires

### Documentation

- [Common Errors](Common-Errors.md) - Erreurs courantes et solutions
- [Connection Issues](Connection-Issues.md) - Problèmes de connexion
- [Performance Issues](Performance-Issues.md) - Optimisation
- [FAQ](FAQ.md) - Questions fréquentes

### Outils Recommandés

```bash
# Installation des outils de debug
pip install py-spy memory_profiler

# Outils système
sudo apt-get install tcpdump wireshark strace ltrace

# Outils LDAP
sudo apt-get install ldap-utils
```

### Communauté

- GitHub Issues: https://github.com/yourusername/ldap-health-monitor/issues
- Discussions: https://github.com/yourusername/ldap-health-monitor/discussions
- Stack Overflow: Tag `ldap-health-monitor`

---

**Fin du Guide de Débogage**

Ce guide couvre les aspects essentiels du débogage. Pour des cas spécifiques, consultez les autres guides de troubleshooting.

**Pages connexes:**
- [Connection Issues](Connection-Issues.md)
- [Performance Issues](Performance-Issues.md)
- [Common Errors](Common-Errors.md)
- [FAQ](FAQ.md)
