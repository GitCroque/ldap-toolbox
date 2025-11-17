# Test de Connexion LDAP

Guide complet pour tester et déboguer votre connexion LDAP.

## 🧪 Tests Rapides

### Test de Santé Basique

```bash
ldap-monitor health
```

**Sortie attendue (connexion réussie)** :
```
✅ LDAP Health Check Results
────────────────────────────────────
Server: ldap.example.com:636
Status: ✓ Healthy
Response Time: 45ms
SSL Certificate: Valid (expires in 287 days)
Total Entries: 1,234
LDAP Version: 3
Vendor: OpenLDAP
```

### Test avec Verbosité

```bash
ldap-monitor --verbose health
```

Affiche les détails de connexion :
```
[DEBUG] Loading configuration from config.yaml
[DEBUG] Connecting to ldap.example.com:636 (SSL: True)
[DEBUG] Binding with DN: cn=admin,dc=example,dc=com
[INFO] Connection established successfully
[DEBUG] Executing health check queries...
```

### Test Avec Timeout Court

```bash
ldap-monitor health --timeout 5
```

Utile pour détecter rapidement les problèmes de réseau.

## 🔍 Tests Détaillés

### 1. Test de Résolution DNS

```bash
# Vérifier que le hostname se résout
nslookup ldap.example.com

# Ou avec dig
dig ldap.example.com
```

### 2. Test de Connectivité Réseau

```bash
# Test de port (LDAP standard)
nc -zv ldap.example.com 389

# Test de port (LDAPS)
nc -zv ldap.example.com 636

# Ou avec telnet
telnet ldap.example.com 636
```

### 3. Test du Certificat SSL

```bash
# Vérifier le certificat SSL
openssl s_client -connect ldap.example.com:636 -showcerts

# Vérifier la date d'expiration
echo | openssl s_client -connect ldap.example.com:636 2>/dev/null | \
  openssl x509 -noout -dates
```

### 4. Test avec ldapsearch (Outil Natif)

```bash
# Test de connexion simple
ldapsearch -x -H ldaps://ldap.example.com:636 \
  -D "cn=admin,dc=example,dc=com" \
  -w "password" \
  -b "dc=example,dc=com" \
  "(objectClass=*)" \
  -LLL

# Compter les entrées
ldapsearch -x -H ldaps://ldap.example.com:636 \
  -D "cn=admin,dc=example,dc=com" \
  -w "password" \
  -b "dc=example,dc=com" \
  "(objectClass=*)" | grep -c "^dn:"
```

## 🐛 Tests de Diagnostic

### Test de Credentials

```bash
# Test avec credentials incorrects
LDAP_BIND_PASSWORD="wrong_password" ldap-monitor health
```

**Sortie attendue** :
```
❌ LDAP Connection Failed
Error: Invalid credentials
```

### Test de Base DN

```bash
# Vérifier que le base DN existe
ldap-monitor search --type entry --query "dc=example,dc=com" --exact
```

### Test de Permissions

```bash
# Vérifier l'accès aux utilisateurs
ldap-monitor export users --limit 1

# Vérifier l'accès aux groupes
ldap-monitor export groups --limit 1
```

## 📊 Tests de Performance

### Mesurer le Temps de Réponse

```bash
# Test simple
time ldap-monitor health

# Test avec plusieurs requêtes
for i in {1..10}; do
  echo "Test $i:"
  time ldap-monitor health
  echo "---"
done
```

### Test de Charge

```bash
# Lancer plusieurs requêtes en parallèle
for i in {1..5}; do
  ldap-monitor health &
done
wait
```

### Test de Pagination

```bash
# Tester avec différentes tailles de page
ldap-monitor export users --page-size 100
ldap-monitor export users --page-size 500
ldap-monitor export users --page-size 1000
```

## 🔧 Configuration de Test

### Créer un Fichier de Test

Créer `config.test.yaml` pour tester différentes configurations :

```yaml
ldap:
  server: "test-ldap.example.com"
  port: 389
  use_ssl: false
  bind_dn: "cn=test,dc=example,dc=com"
  bind_password: "test123"
  base_dn: "dc=test,dc=example,dc=com"
  timeout: 10
```

### Utiliser la Configuration de Test

```bash
ldap-monitor --config config.test.yaml health
```

## ❌ Erreurs Courantes et Solutions

### Erreur: "Connection Refused"

**Symptôme** :
```
❌ LDAP Connection Failed
Error: Connection refused
```

**Solutions** :
1. Vérifier que le serveur LDAP est démarré
2. Vérifier le port (389 pour LDAP, 636 pour LDAPS)
3. Vérifier le firewall :
   ```bash
   # Linux
   sudo firewall-cmd --list-ports

   # macOS
   sudo pfctl -sr
   ```

### Erreur: "Invalid Credentials"

**Symptôme** :
```
❌ LDAP Connection Failed
Error: Invalid credentials (49)
```

**Solutions** :
1. Vérifier le DN de bind :
   ```bash
   echo $LDAP_BIND_DN
   ```
2. Vérifier le mot de passe (attention aux caractères spéciaux)
3. Tester avec ldapsearch :
   ```bash
   ldapsearch -x -H ldaps://ldap.example.com:636 \
     -D "$LDAP_BIND_DN" \
     -w "$LDAP_BIND_PASSWORD" \
     -b "dc=example,dc=com" \
     "(objectClass=*)" -LLL
   ```

### Erreur: "SSL Certificate Verification Failed"

**Symptôme** :
```
❌ LDAP Connection Failed
Error: SSL certificate verification failed
```

**Solutions** :

1. **Solution 1** : Désactiver temporairement la vérification (dev uniquement)
   ```yaml
   ldap:
     use_ssl: true
     verify_ssl: false  # ⚠️ Ne pas utiliser en production
   ```

2. **Solution 2** : Ajouter le certificat CA
   ```yaml
   ldap:
     use_ssl: true
     ca_cert_file: "/path/to/ca-cert.pem"
   ```

3. **Solution 3** : Récupérer et installer le certificat
   ```bash
   # Récupérer le certificat
   echo | openssl s_client -connect ldap.example.com:636 2>/dev/null | \
     openssl x509 -outform PEM > ldap-cert.pem

   # L'utiliser dans la config
   ldap:
     ca_cert_file: "./ldap-cert.pem"
   ```

### Erreur: "Timeout"

**Symptôme** :
```
❌ LDAP Connection Failed
Error: Connection timeout after 30s
```

**Solutions** :
1. Augmenter le timeout :
   ```yaml
   ldap:
     timeout: 60
   ```
2. Vérifier la latence réseau :
   ```bash
   ping ldap.example.com
   ```
3. Vérifier les règles de firewall

### Erreur: "No Such Object"

**Symptôme** :
```
❌ Search failed
Error: No such object (32)
```

**Solutions** :
1. Vérifier le base_dn :
   ```bash
   # Lister la racine
   ldapsearch -x -H ldaps://ldap.example.com:636 \
     -D "$LDAP_BIND_DN" \
     -w "$LDAP_BIND_PASSWORD" \
     -b "" \
     -s base \
     "namingContexts"
   ```
2. Corriger dans config.yaml :
   ```yaml
   ldap:
     base_dn: "dc=correct,dc=example,dc=com"
   ```

## ✅ Checklist de Validation

### Connexion

- [ ] Le hostname se résout (DNS)
- [ ] Le port est accessible (telnet/nc)
- [ ] Le certificat SSL est valide (si LDAPS)
- [ ] Les credentials sont corrects
- [ ] Le base DN existe

### Permissions

- [ ] Lecture des utilisateurs fonctionne
- [ ] Lecture des groupes fonctionne
- [ ] Recherche dans l'arbre fonctionne
- [ ] Les attributs nécessaires sont accessibles

### Performance

- [ ] Temps de réponse < 100ms (local)
- [ ] Temps de réponse < 500ms (distant)
- [ ] Pagination fonctionne correctement
- [ ] Pas de timeouts

## 🎯 Tests Automatisés

### Script de Test Complet

Créer `test-connection.sh` :

```bash
#!/bin/bash

echo "🧪 LDAP Connection Test Suite"
echo "================================"

# Test 1: DNS Resolution
echo "1. Testing DNS resolution..."
if nslookup ldap.example.com > /dev/null 2>&1; then
  echo "   ✅ DNS resolution OK"
else
  echo "   ❌ DNS resolution FAILED"
  exit 1
fi

# Test 2: Port Connectivity
echo "2. Testing port connectivity..."
if nc -zv ldap.example.com 636 2>&1 | grep -q "succeeded"; then
  echo "   ✅ Port 636 accessible"
else
  echo "   ❌ Port 636 not accessible"
  exit 1
fi

# Test 3: SSL Certificate
echo "3. Testing SSL certificate..."
CERT_DAYS=$(echo | openssl s_client -connect ldap.example.com:636 2>/dev/null | \
  openssl x509 -noout -enddate | cut -d= -f2)
echo "   ✅ Certificate valid until: $CERT_DAYS"

# Test 4: LDAP Health Check
echo "4. Testing LDAP health..."
if ldap-monitor health > /dev/null 2>&1; then
  echo "   ✅ LDAP health check OK"
else
  echo "   ❌ LDAP health check FAILED"
  exit 1
fi

# Test 5: User Access
echo "5. Testing user access..."
if ldap-monitor export users --limit 1 > /dev/null 2>&1; then
  echo "   ✅ User access OK"
else
  echo "   ❌ User access FAILED"
fi

# Test 6: Group Access
echo "6. Testing group access..."
if ldap-monitor export groups --limit 1 > /dev/null 2>&1; then
  echo "   ✅ Group access OK"
else
  echo "   ❌ Group access FAILED"
fi

echo ""
echo "🎉 All tests completed!"
```

Rendre exécutable et lancer :

```bash
chmod +x test-connection.sh
./test-connection.sh
```

## 📚 Ressources

- [Configuration LDAP](../configuration/LDAP-Configuration.md)
- [Problèmes de Connexion](../troubleshooting/Connection-Issues.md)
- [FAQ](../troubleshooting/FAQ.md)
- [Guide Active Directory](../guides/Active-Directory.md)
- [Guide OpenLDAP](../guides/OpenLDAP.md)

---

**Tests réussis ?** Passez au [Guide de Démarrage Rapide](Quick-Start.md) pour utiliser l'outil.
