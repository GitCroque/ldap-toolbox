# Problèmes de Connexion LDAP

Guide complet de résolution des problèmes de connexion pour LDAP Health Monitor.

## Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Diagnostic Rapide](#diagnostic-rapide)
- [Erreurs de Connexion](#erreurs-de-connexion)
- [Erreurs SSL/TLS](#erreurs-ssltls)
- [Problèmes d'Authentification](#problèmes-dauthentification)
- [Problèmes Réseau](#problèmes-réseau)
- [Active Directory](#active-directory)
- [Exemples de Logs](#exemples-de-logs)
- [Scripts de Diagnostic](#scripts-de-diagnostic)

---

## Vue d'Ensemble

Les problèmes de connexion sont les plus fréquents lors de la première configuration de LDAP Health Monitor. Ce guide vous aidera à identifier et résoudre rapidement ces problèmes.

### Symptômes Courants

- ❌ `Cannot connect to LDAP server`
- ❌ `Connection timeout`
- ❌ `Authentication failed`
- ❌ `SSL/TLS handshake failed`
- ❌ `Invalid credentials`
- ❌ `Network unreachable`

### Processus de Connexion LDAP

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Résolution DNS      → ldap.example.com → 10.0.1.50      │
│ 2. Connexion TCP       → Port 389/636                       │
│ 3. Négociation SSL/TLS → Si activé                          │
│ 4. Bind LDAP           → Authentification                   │
│ 5. Requête de Test     → Vérification fonctionnelle         │
└─────────────────────────────────────────────────────────────┘
```

---

## Diagnostic Rapide

### Test de Connexion Basique

```bash
# Test de connexion simple
ldap-monitor test connection

# Avec mode verbose
ldap-monitor --verbose test connection

# Test avec configuration spécifique
ldap-monitor --config /path/to/config.yaml test connection
```

### Checklist de Diagnostic

```bash
# 1. Vérifier la configuration
ldap-monitor config validate

# 2. Tester la résolution DNS
ping ldap.example.com
nslookup ldap.example.com

# 3. Vérifier la connectivité réseau
telnet ldap.example.com 389
# ou pour LDAPS
openssl s_client -connect ldap.example.com:636

# 4. Tester avec ldapsearch
ldapsearch -H ldap://ldap.example.com -D "cn=admin,dc=example,dc=com" -W -b "dc=example,dc=com"

# 5. Vérifier les credentials
echo $LDAP_PASSWORD

# 6. Consulter les logs
tail -f logs/ldap-monitor.log
```

### Commande de Diagnostic Automatique

```bash
#!/bin/bash
# diagnostic.sh - Script de diagnostic automatique

echo "=== Diagnostic LDAP Health Monitor ==="
echo ""

# Configuration
CONFIG_FILE="config.yaml"
LOG_FILE="logs/ldap-monitor.log"

# Extraire serveur et port depuis config
SERVER=$(grep "server:" $CONFIG_FILE | awk '{print $2}' | sed 's/ldap:\/\///' | sed 's/ldaps:\/\///')
PORT=$(grep "port:" $CONFIG_FILE | awk '{print $2}')

echo "1. Configuration validée"
ldap-monitor config validate
echo ""

echo "2. Résolution DNS"
nslookup $SERVER
echo ""

echo "3. Connectivité TCP"
timeout 5 bash -c "echo >/dev/tcp/$SERVER/$PORT" 2>/dev/null && echo "✓ Port $PORT ouvert" || echo "✗ Port $PORT fermé"
echo ""

echo "4. Test de connexion LDAP"
ldap-monitor test connection 2>&1
echo ""

echo "5. Dernières erreurs dans les logs"
tail -n 20 $LOG_FILE | grep -i "error\|warning\|failed"
echo ""

echo "=== Fin du diagnostic ==="
```

---

## Erreurs de Connexion

### Erreur: "Cannot connect to LDAP server"

**Message complet:**
```
ERROR: Cannot connect to LDAP server: [Errno 111] Connection refused
```

**Causes possibles:**

1. Le serveur LDAP n'est pas démarré
2. Pare-feu bloque la connexion
3. Mauvais port configuré
4. Serveur inaccessible depuis votre réseau

**Solution 1: Vérifier que le serveur LDAP est actif**

```bash
# Pour slapd (OpenLDAP)
sudo systemctl status slapd

# Pour Active Directory
# Sur le contrôleur de domaine Windows:
Get-Service NTDS
Get-Service ADWS

# Démarrer le service si nécessaire
sudo systemctl start slapd
```

**Solution 2: Vérifier la connectivité réseau**

```bash
# Test ping
ping -c 4 ldap.example.com

# Test du port LDAP (389)
telnet ldap.example.com 389

# Ou avec nc (netcat)
nc -zv ldap.example.com 389

# Pour LDAPS (636)
nc -zv ldap.example.com 636
```

**Solution 3: Vérifier la configuration du pare-feu**

```bash
# Sur le serveur LDAP (Linux)
sudo iptables -L -n | grep 389
sudo firewall-cmd --list-all

# Ouvrir le port si nécessaire
sudo firewall-cmd --permanent --add-port=389/tcp
sudo firewall-cmd --permanent --add-port=636/tcp
sudo firewall-cmd --reload

# Sur le client (vérifier sortant)
sudo iptables -L OUTPUT -n
```

**Solution 4: Corriger la configuration**

```yaml
# config.yaml
ldap:
  # Essayer avec IP directement
  server: 10.0.1.50
  port: 389

  # Ou avec hostname complet
  server: ldap.example.com
  port: 389

  # Pour LDAPS
  server: ldap.example.com
  port: 636
  use_ssl: true
```

**Exemple de log:**
```
2025-11-17 10:23:45 - ldap.connector - ERROR - Connection attempt 1 failed: [Errno 111] Connection refused
2025-11-17 10:23:47 - ldap.connector - ERROR - Connection attempt 2 failed: [Errno 111] Connection refused
2025-11-17 10:23:50 - ldap.connector - ERROR - Connection attempt 3 failed: [Errno 111] Connection refused
2025-11-17 10:23:50 - ldap.connector - CRITICAL - Failed to connect after 3 attempts
```

---

### Erreur: "Connection timeout"

**Message complet:**
```
ERROR: Connection timeout after 10 seconds
ldap3.core.exceptions.LDAPSocketOpenError: socket connection error
```

**Causes possibles:**

1. Le serveur est surchargé ou lent à répondre
2. Problèmes réseau (latence élevée, perte de paquets)
3. Timeout configuré trop court
4. Proxy/pare-feu qui drop les connexions

**Solution 1: Augmenter le timeout**

```yaml
# config.yaml
ldap:
  server: ldap.example.com
  port: 389
  timeout: 30  # Augmenter de 10 à 30 secondes
  retry_max: 5
  retry_delay: 3
```

**Solution 2: Diagnostiquer les problèmes réseau**

```bash
# Mesurer la latence
ping -c 10 ldap.example.com

# Tracer la route
traceroute ldap.example.com

# Test de performance réseau
mtr ldap.example.com

# Vérifier les pertes de paquets
ping -c 100 ldap.example.com | tail -3
```

**Solution 3: Utiliser un serveur LDAP plus proche**

```yaml
# Si vous avez plusieurs serveurs LDAP
ldap:
  # Utiliser le réplica le plus proche
  server: ldap-replica-local.example.com
  port: 389
```

**Solution 4: Vérifier la charge du serveur LDAP**

```bash
# Sur le serveur LDAP
# Vérifier CPU et mémoire
top -b -n 1 | head -20

# Vérifier les connexions actives
netstat -an | grep :389 | wc -l

# Logs du serveur LDAP
sudo tail -f /var/log/slapd.log

# Pour Active Directory
# Sur le contrôleur de domaine
Get-Counter '\NTDS\LDAP Client Sessions'
Get-Counter '\NTDS\LDAP Searches/sec'
```

**Exemple de log:**
```
2025-11-17 10:30:12 - ldap.connector - INFO - Attempting to connect to ldap.example.com:389
2025-11-17 10:30:22 - ldap.connector - WARNING - Connection attempt 1 timeout after 10s
2025-11-17 10:30:35 - ldap.connector - WARNING - Connection attempt 2 timeout after 13s
2025-11-17 10:30:51 - ldap.connector - ERROR - Connection failed: timeout
```

---

## Erreurs SSL/TLS

### Erreur: "SSL certificate verification failed"

**Message complet:**
```
ERROR: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate
```

**Causes possibles:**

1. Certificat auto-signé
2. Certificat expiré
3. Certificat pour un autre domaine
4. CA racine non reconnue

**Solution 1: Certificat auto-signé (environnement de test)**

```yaml
# config.yaml - UNIQUEMENT POUR TEST!
ldap:
  server: ldaps://ldap.example.com
  port: 636
  use_ssl: true

advanced:
  # ⚠️ À utiliser uniquement en développement
  tls_validate: false
  tls_version: "TLSv1_2"
```

**Solution 2: Ajouter le CA au système (production)**

```bash
# Récupérer le certificat du serveur
echo | openssl s_client -connect ldap.example.com:636 2>/dev/null | openssl x509 -out ldap-cert.pem

# Vérifier le certificat
openssl x509 -in ldap-cert.pem -text -noout

# Installer le CA (Ubuntu/Debian)
sudo cp ldap-cert.pem /usr/local/share/ca-certificates/ldap-ca.crt
sudo update-ca-certificates

# Installer le CA (RHEL/CentOS)
sudo cp ldap-cert.pem /etc/pki/ca-trust/source/anchors/
sudo update-ca-trust

# macOS
sudo security add-trusted-cert -d -r trustRoot -k /Library/Keychains/System.keychain ldap-cert.pem
```

**Solution 3: Spécifier le fichier CA**

```yaml
# config.yaml
ldap:
  server: ldaps://ldap.example.com
  port: 636
  use_ssl: true

advanced:
  tls_ca_file: /path/to/ldap-ca.pem
  tls_validate: true
```

**Solution 4: Vérifier et renouveler le certificat**

```bash
# Vérifier la validité du certificat
echo | openssl s_client -connect ldap.example.com:636 2>/dev/null | openssl x509 -noout -dates

# Sortie:
# notBefore=Oct  1 00:00:00 2024 GMT
# notAfter=Sep 30 23:59:59 2025 GMT

# Vérifier le CN (Common Name)
echo | openssl s_client -connect ldap.example.com:636 2>/dev/null | openssl x509 -noout -subject

# Si expiré, renouveler sur le serveur LDAP
# Pour Let's Encrypt:
sudo certbot renew
sudo systemctl restart slapd
```

**Exemple de log:**
```
2025-11-17 11:05:23 - ldap.connector - INFO - Connecting with SSL to ldaps://ldap.example.com:636
2025-11-17 11:05:23 - ldap.connector - ERROR - SSL handshake failed
2025-11-17 11:05:23 - ldap.connector - ERROR - [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate in certificate chain
2025-11-17 11:05:23 - ldap.connector - INFO - Certificate details: CN=ldap.example.com, Issuer=Self-Signed
```

---

### Erreur: "SSL/TLS handshake failed"

**Message complet:**
```
ERROR: [SSL] PEM lib (_ssl.c:4012)
ERROR: SSL handshake failed: wrong version number
```

**Causes possibles:**

1. Mauvaise combinaison port/protocole
2. Version TLS non supportée
3. Connexion non-SSL sur port SSL
4. Problème de cipher suites

**Solution 1: Vérifier port et protocole**

```yaml
# config.yaml

# ❌ MAUVAIS: SSL sur port non-SSL
ldap:
  server: ldap.example.com
  port: 389
  use_ssl: true  # Port 389 est généralement non-SSL

# ✅ BON: Port et protocole cohérents
ldap:
  server: ldap.example.com
  port: 636
  use_ssl: true

# ✅ Alternative: STARTTLS sur port 389
ldap:
  server: ldap.example.com
  port: 389
  use_ssl: false
  use_tls: true  # Utilise STARTTLS
```

**Solution 2: Tester la configuration SSL du serveur**

```bash
# Test SSL/TLS sur port 636
openssl s_client -connect ldap.example.com:636 -showcerts

# Test STARTTLS sur port 389
openssl s_client -connect ldap.example.com:389 -starttls ldap

# Lister les cipher suites supportées
nmap --script ssl-enum-ciphers -p 636 ldap.example.com

# Test des versions TLS
openssl s_client -connect ldap.example.com:636 -tls1_2
openssl s_client -connect ldap.example.com:636 -tls1_3
```

**Solution 3: Configurer la version TLS**

```yaml
# config.yaml
ldap:
  server: ldaps://ldap.example.com
  port: 636
  use_ssl: true

advanced:
  tls_version: "TLSv1_2"  # ou "TLSv1_3"
  tls_ciphers: "HIGH:!aNULL:!eNULL:!EXPORT:!DES:!MD5:!PSK:!RC4"
```

**Exemple de log:**
```
2025-11-17 11:15:45 - ldap.connector - INFO - Initiating SSL connection
2025-11-17 11:15:45 - ldap.connector - DEBUG - Using TLS version: TLSv1_2
2025-11-17 11:15:45 - ldap.connector - ERROR - SSL handshake failed: wrong version number
2025-11-17 11:15:45 - ldap.connector - DEBUG - Server may not support SSL on port 389
2025-11-17 11:15:45 - ldap.connector - HINT - Try use_tls: true instead of use_ssl: true
```

---

## Problèmes d'Authentification

### Erreur: "Invalid credentials"

**Message complet:**
```
ERROR: ldap3.core.exceptions.LDAPInvalidCredentialsResult:
result: 49, description: invalidCredentials
```

**Causes possibles:**

1. Mot de passe incorrect
2. Format du DN incorrect
3. Compte désactivé ou verrouillé
4. Mot de passe expiré

**Solution 1: Vérifier les credentials**

```bash
# Vérifier que la variable d'environnement est définie
echo $LDAP_PASSWORD

# Tester avec ldapsearch
ldapsearch -H ldap://ldap.example.com \
  -D "cn=admin,dc=example,dc=com" \
  -w "$LDAP_PASSWORD" \
  -b "dc=example,dc=com" \
  "(objectClass=*)" \
  dn

# Si succès, le problème est dans la configuration
```

**Solution 2: Vérifier le format du DN**

```yaml
# config.yaml

# ❌ Formats incorrects
bind_dn: admin  # Incomplet
bind_dn: cn=admin  # Incomplet
bind_dn: admin@example.com  # Format AD dans config OpenLDAP

# ✅ Format OpenLDAP correct
bind_dn: cn=admin,dc=example,dc=com

# ✅ Format Active Directory correct (UPN)
bind_dn: serviceaccount@corp.example.com

# ✅ Format Active Directory correct (DN)
bind_dn: CN=Service Account,OU=Service Accounts,DC=corp,DC=example,DC=com
```

**Solution 3: Vérifier l'état du compte**

```bash
# Sur le serveur LDAP
# Vérifier si le compte existe
ldapsearch -x -LLL -b "dc=example,dc=com" "(cn=admin)"

# Vérifier le statut du compte (Active Directory)
# Sur le DC:
Get-ADUser -Identity "serviceaccount" -Properties LockedOut,Enabled,PasswordExpired

# Déverrouiller si nécessaire
Unlock-ADAccount -Identity "serviceaccount"
Set-ADUser -Identity "serviceaccount" -PasswordNeverExpires $true
```

**Solution 4: Réinitialiser le mot de passe**

```bash
# OpenLDAP - générer un nouveau hash
slappasswd -s newpassword

# Modifier le mot de passe
ldapmodify -H ldap://localhost -D "cn=admin,dc=example,dc=com" -W <<EOF
dn: cn=admin,dc=example,dc=com
changetype: modify
replace: userPassword
userPassword: {SSHA}generatedHashHere
EOF

# Active Directory
# Sur le DC:
Set-ADAccountPassword -Identity "serviceaccount" -NewPassword (ConvertTo-SecureString "NewP@ssw0rd" -AsPlainText -Force)
```

**Exemple de log:**
```
2025-11-17 11:30:15 - ldap.connector - INFO - Attempting bind as: cn=admin,dc=example,dc=com
2025-11-17 11:30:15 - ldap.connector - ERROR - Bind failed: invalidCredentials (49)
2025-11-17 11:30:15 - ldap.connector - DEBUG - Authentication attempt 1/3 failed
2025-11-17 11:30:17 - ldap.connector - ERROR - Bind failed: invalidCredentials (49)
2025-11-17 11:30:17 - ldap.connector - CRITICAL - All authentication attempts failed
```

---

### Erreur: "Bind DN not found"

**Message complet:**
```
ERROR: ldap3.core.exceptions.LDAPNoSuchObjectResult:
result: 32, description: noSuchObject
```

**Causes possibles:**

1. DN incorrect ou inexistant
2. Base DN incorrect
3. Compte supprimé
4. Mauvaise OU spécifiée

**Solution 1: Rechercher le DN correct**

```bash
# Rechercher par nom d'utilisateur
ldapsearch -x -H ldap://ldap.example.com \
  -b "dc=example,dc=com" \
  "(uid=admin)" \
  dn

# Rechercher par email
ldapsearch -x -H ldap://ldap.example.com \
  -b "dc=example,dc=com" \
  "(mail=admin@example.com)" \
  dn

# Lister tous les DNs sous la base
ldapsearch -x -H ldap://ldap.example.com \
  -b "dc=example,dc=com" \
  -s one \
  dn
```

**Solution 2: Vérifier la structure LDAP**

```bash
# Afficher la structure (rootDSE)
ldapsearch -x -H ldap://ldap.example.com -b "" -s base +

# Lister les naming contexts
ldapsearch -x -H ldap://ldap.example.com \
  -b "" \
  -s base \
  namingContexts

# Explorer la hiérarchie
ldapsearch -x -H ldap://ldap.example.com \
  -b "dc=example,dc=com" \
  -s one \
  objectClass
```

**Exemple de log:**
```
2025-11-17 11:45:30 - ldap.connector - INFO - Attempting to bind: cn=admin,ou=wrong,dc=example,dc=com
2025-11-17 11:45:30 - ldap.connector - ERROR - noSuchObject (32): The specified object does not exist
2025-11-17 11:45:30 - ldap.connector - HINT - Verify the DN exists in the directory
2025-11-17 11:45:30 - ldap.connector - HINT - Check base_dn in configuration
```

---

## Problèmes Réseau

### Erreur: "Network unreachable"

**Message complet:**
```
ERROR: [Errno 101] Network is unreachable
ERROR: Cannot reach LDAP server at ldap.example.com:389
```

**Diagnostic réseau complet:**

```bash
#!/bin/bash
# network-diagnostic.sh

SERVER="ldap.example.com"
PORT=389

echo "=== Diagnostic Réseau LDAP ==="
echo ""

# 1. Résolution DNS
echo "1. Résolution DNS:"
host $SERVER
dig $SERVER
echo ""

# 2. Routage
echo "2. Table de routage:"
ip route get $(dig +short $SERVER | head -1)
echo ""

# 3. Connectivité ICMP
echo "3. Test ICMP (ping):"
ping -c 4 $SERVER
echo ""

# 4. Traceroute
echo "4. Trace route:"
traceroute -m 15 $SERVER
echo ""

# 5. Test port TCP
echo "5. Test du port $PORT:"
timeout 5 bash -c "echo >/dev/tcp/$SERVER/$PORT" && echo "✓ Connecté" || echo "✗ Échec"
echo ""

# 6. Firewall local
echo "6. Règles firewall locales:"
sudo iptables -L OUTPUT -n | grep $PORT
echo ""

# 7. Interfaces réseau
echo "7. Interfaces réseau actives:"
ip addr show
echo ""

# 8. DNS configuration
echo "8. Configuration DNS:"
cat /etc/resolv.conf
echo ""

echo "=== Fin du diagnostic ==="
```

---

## Active Directory

### Configuration Active Directory

**Configuration recommandée:**

```yaml
# config.yaml pour Active Directory
ldap:
  # Utiliser LDAPS pour la production
  server: ldaps://dc01.corp.example.com
  port: 636
  use_ssl: true

  # Authentication AD (format UPN recommandé)
  bind_dn: svc-ldapmonitor@corp.example.com
  bind_password: ${LDAP_PASSWORD}

  # Base DN pour AD
  base_dn: dc=corp,dc=example,dc=com

  # Schema AD
  user_objectclass: user
  group_objectclass: group
  user_uid_attribute: sAMAccountName
  group_member_attribute: member

  # Performance pour AD
  page_size: 1000  # Maximum pour AD
  timeout: 30

  # OUs spécifiques
  users_ou: ou=Users,dc=corp,dc=example,dc=com
  groups_ou: ou=Groups,dc=corp,dc=example,dc=com
```

### Erreurs Active Directory Spécifiques

**Erreur: "Operations error" (Code 1)**

```
ERROR: ldap3.core.exceptions.LDAPOperationsResult: result: 1
```

**Cause:** Recherche sans base DN correcte dans AD

**Solution:**
```yaml
ldap:
  # S'assurer que base_dn correspond à votre domaine AD
  base_dn: dc=corp,dc=example,dc=com

  # Utiliser le Global Catalog si nécessaire (port 3268/3269)
  # server: ldaps://dc01.corp.example.com
  # port: 3269  # Global Catalog SSL
```

---

## Exemples de Logs

### Connexion Réussie

```
2025-11-17 12:00:00 - ldap.connector - INFO - Starting connection to ldaps://ldap.example.com:636
2025-11-17 12:00:00 - ldap.connector - DEBUG - SSL enabled: True, TLS enabled: False
2025-11-17 12:00:00 - ldap.connector - DEBUG - Creating server object: ldap.example.com:636
2025-11-17 12:00:01 - ldap.connector - DEBUG - SSL handshake successful
2025-11-17 12:00:01 - ldap.connector - INFO - Attempting bind as: cn=admin,dc=example,dc=com
2025-11-17 12:00:01 - ldap.connector - INFO - Bind successful
2025-11-17 12:00:01 - ldap.connector - DEBUG - Connection established in 1.2s
2025-11-17 12:00:01 - ldap.connector - INFO - Test search successful
2025-11-17 12:00:01 - ldap.connector - INFO - ✓ Connection healthy - Response time: 125ms
```

### Échec de Connexion SSL

```
2025-11-17 12:05:00 - ldap.connector - INFO - Starting connection to ldaps://ldap.example.com:636
2025-11-17 12:05:00 - ldap.connector - DEBUG - SSL enabled: True
2025-11-17 12:05:00 - ldap.connector - WARNING - Attempting SSL connection
2025-11-17 12:05:01 - ldap.connector - ERROR - SSL handshake failed
2025-11-17 12:05:01 - ldap.connector - ERROR - [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self signed certificate
2025-11-17 12:05:01 - ldap.connector - DEBUG - Certificate CN: ldap.example.com
2025-11-17 12:05:01 - ldap.connector - DEBUG - Certificate Issuer: Self-Signed
2025-11-17 12:05:01 - ldap.connector - DEBUG - Certificate Expires: 2025-12-31
2025-11-17 12:05:01 - ldap.connector - HINT - Add CA certificate to system trust store
2025-11-17 12:05:01 - ldap.connector - HINT - Or set tls_validate: false for testing only
```

---

## Scripts de Diagnostic

### Script de Test Complet

```bash
#!/bin/bash
# complete-connection-test.sh

CONFIG="config.yaml"
LOG_DIR="logs"

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Fonctions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Extraire configuration
SERVER=$(grep "server:" $CONFIG | awk '{print $2}' | sed 's/ldaps:\/\///' | sed 's/ldap:\/\///')
PORT=$(grep "port:" $CONFIG | awk '{print $2}')
BASE_DN=$(grep "base_dn:" $CONFIG | awk '{print $2}')

echo "================================================"
echo "Test de Connexion LDAP - Diagnostic Complet"
echo "================================================"
echo ""

# Test 1: Configuration
echo "Test 1: Validation de la configuration"
if ldap-monitor config validate >/dev/null 2>&1; then
    print_success "Configuration valide"
else
    print_error "Configuration invalide"
    ldap-monitor config validate
    exit 1
fi
echo ""

# Test 2: DNS
echo "Test 2: Résolution DNS"
if host $SERVER >/dev/null 2>&1; then
    IP=$(host $SERVER | awk '/has address/ {print $4}' | head -1)
    print_success "DNS résolu: $SERVER → $IP"
else
    print_error "Échec de résolution DNS pour $SERVER"
    exit 1
fi
echo ""

# Test 3: Connectivité TCP
echo "Test 3: Connectivité TCP"
if timeout 5 bash -c "echo >/dev/tcp/$SERVER/$PORT" 2>/dev/null; then
    print_success "Port $PORT accessible"
else
    print_error "Port $PORT inaccessible"
    echo "  Vérifier le pare-feu et que le service est démarré"
    exit 1
fi
echo ""

# Test 4: SSL/TLS
echo "Test 4: Certificat SSL/TLS (si applicable)"
if [ "$PORT" -eq 636 ]; then
    CERT_INFO=$(echo | openssl s_client -connect $SERVER:$PORT 2>/dev/null | openssl x509 -noout -dates 2>/dev/null)
    if [ $? -eq 0 ]; then
        print_success "Certificat SSL valide"
        echo "  $CERT_INFO"
    else
        print_warning "Problème avec le certificat SSL"
    fi
else
    print_warning "SSL non configuré (port $PORT)"
fi
echo ""

# Test 5: Connexion LDAP
echo "Test 5: Test de connexion LDAP"
if ldap-monitor test connection >/dev/null 2>&1; then
    print_success "Connexion LDAP réussie"

    # Afficher les détails
    RESPONSE=$(ldap-monitor test connection 2>&1)
    RESPONSE_TIME=$(echo "$RESPONSE" | grep -i "response time" | awk '{print $NF}')
    if [ ! -z "$RESPONSE_TIME" ]; then
        echo "  Temps de réponse: $RESPONSE_TIME"
    fi
else
    print_error "Échec de connexion LDAP"
    ldap-monitor --verbose test connection
    exit 1
fi
echo ""

# Test 6: Health check
echo "Test 6: Health check"
if ldap-monitor audit health >/dev/null 2>&1; then
    print_success "Health check réussi"
else
    print_warning "Health check a détecté des problèmes"
    echo "  Exécuter: ldap-monitor audit health pour plus de détails"
fi
echo ""

echo "================================================"
echo "Tous les tests de connexion sont passés!"
echo "================================================"
```

---

## Ressources Supplémentaires

### Commandes Utiles

```bash
# Tester avec différents niveaux de verbosité
ldap-monitor --verbose test connection
ldap-monitor --debug test connection

# Forcer la reconnexion
ldap-monitor test connection --force-reconnect

# Test avec configuration alternative
ldap-monitor --config config-test.yaml test connection

# Valider avant de tester
ldap-monitor config validate && ldap-monitor test connection
```

### Logs à Consulter

```bash
# Logs de l'application
tail -f logs/ldap-monitor.log

# Logs système du serveur LDAP (sur le serveur)
# OpenLDAP
sudo tail -f /var/log/slapd.log

# Active Directory (sur DC Windows)
# Event Viewer → Windows Logs → Directory Service
```

### Documentation Externe

- [ldap3 Documentation](https://ldap3.readthedocs.io/)
- [OpenLDAP Admin Guide](https://www.openldap.org/doc/admin24/)
- [Active Directory LDAP](https://docs.microsoft.com/en-us/windows/win32/ad/active-directory-ldap)

---

**Page suivante:** [Performance Issues](Performance-Issues.md)
