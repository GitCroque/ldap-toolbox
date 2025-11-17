# Erreurs Courantes

Guide complet des erreurs courantes, codes de sortie, et exceptions pour LDAP Health Monitor.

## Table des Matières

- [Vue d'Ensemble](#vue-densemble)
- [Erreurs de Configuration](#erreurs-de-configuration)
- [Erreurs LDAP](#erreurs-ldap)
- [Erreurs Python](#erreurs-python)
- [Codes de Sortie](#codes-de-sortie)
- [Exceptions ldap3](#exceptions-ldap3)
- [Erreurs de Permissions](#erreurs-de-permissions)
- [Erreurs de Format](#erreurs-de-format)
- [Solutions Rapides](#solutions-rapides)

---

## Vue d'Ensemble

Ce guide répertorie toutes les erreurs courantes que vous pouvez rencontrer avec LDAP Health Monitor, leurs causes, et leurs solutions.

### Format des Erreurs

```
┌─────────────────────────────────────────────────────────────┐
│ Type d'Erreur                                               │
├─────────────────────────────────────────────────────────────┤
│ Message d'erreur complet                                    │
│                                                             │
│ Cause: Explication de la cause                              │
│ Solution: Étapes pour résoudre                              │
│ Code: Code de sortie ou exception                           │
│ Logs: Exemple de logs d'erreur                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Erreurs de Configuration

### Erreur: "Configuration file not found"

**Message:**
```
ERROR: Configuration file not found: config.yaml
FileNotFoundError: [Errno 2] No such file or directory: 'config.yaml'
```

**Cause:** Le fichier config.yaml n'existe pas dans le répertoire courant.

**Solution 1: Créer le fichier de configuration**

```bash
# Initialiser la configuration
ldap-monitor config init

# Cela crée config.yaml avec les valeurs par défaut
```

**Solution 2: Spécifier le chemin du fichier**

```bash
# Utiliser un fichier de configuration ailleurs
ldap-monitor --config /path/to/config.yaml audit health

# Définir une variable d'environnement
export LDAP_MONITOR_CONFIG=/path/to/config.yaml
ldap-monitor audit health
```

**Code de sortie:** 2

---

### Erreur: "Invalid YAML syntax"

**Message:**
```
ERROR: Invalid YAML syntax in config.yaml
yaml.scanner.ScannerError: mapping values are not allowed here
  in "config.yaml", line 15, column 18
```

**Cause:** Erreur de syntaxe dans le fichier YAML.

**Erreurs courantes:**

```yaml
# ❌ Mauvais: tabulation au lieu d'espaces
ldap:
→   server: ldap.example.com  # Tabulation

# ✅ Bon: espaces uniquement
ldap:
  server: ldap.example.com  # 2 espaces

# ❌ Mauvais: : sans espace
ldap:
  server:ldap.example.com

# ✅ Bon: espace après :
ldap:
  server: ldap.example.com

# ❌ Mauvais: quotes mal fermées
bind_password: "mypassword

# ✅ Bon: quotes correctes
bind_password: "mypassword"
```

**Solution: Valider et corriger la syntaxe**

```bash
# Valider le fichier
ldap-monitor config validate

# Utiliser un validateur YAML en ligne
# https://www.yamllint.com/

# Ou avec Python
python -c "import yaml; yaml.safe_load(open('config.yaml'))"
```

**Code de sortie:** 2

---

### Erreur: "Required field missing"

**Message:**
```
ERROR: Configuration validation failed
ValidationError: Required field 'server' missing in ldap configuration
```

**Cause:** Champ obligatoire manquant dans la configuration.

**Champs obligatoires:**

```yaml
# Minimum requis
ldap:
  server: ldap.example.com    # Obligatoire
  port: 389                   # Obligatoire
  bind_dn: cn=admin,dc=example,dc=com  # Obligatoire
  bind_password: ${LDAP_PASSWORD}      # Obligatoire
  base_dn: dc=example,dc=com          # Obligatoire
```

**Solution:**

```bash
# Vérifier la configuration complète
ldap-monitor config show

# Copier depuis l'exemple
cp config.example.yaml config.yaml
# Puis éditer avec vos valeurs
```

**Code de sortie:** 2

---

### Erreur: "Environment variable not set"

**Message:**
```
ERROR: Environment variable LDAP_PASSWORD is not set
ValueError: Cannot resolve ${LDAP_PASSWORD} in configuration
```

**Cause:** Variable d'environnement référencée mais non définie.

**Solution 1: Définir la variable**

```bash
# Dans le terminal
export LDAP_PASSWORD="your-password"

# Vérifier
echo $LDAP_PASSWORD

# Permanent (ajout à ~/.bashrc ou ~/.zshrc)
echo 'export LDAP_PASSWORD="your-password"' >> ~/.bashrc
source ~/.bashrc
```

**Solution 2: Utiliser un fichier .env**

```bash
# Créer .env
cat > .env <<EOF
LDAP_PASSWORD=your-password
SLACK_WEBHOOK=https://hooks.slack.com/...
SMTP_PASSWORD=email-password
EOF

# Charger automatiquement
# L'application charge .env si présent

# Ou charger manuellement
export $(cat .env | xargs)
```

**Solution 3: Mettre la valeur directement (non recommandé)**

```yaml
# ⚠️ Uniquement pour test local - ne jamais commiter!
ldap:
  bind_password: "actual-password-here"
```

**Code de sortie:** 2

---

## Erreurs LDAP

### Erreur: Result Code 32 - "No Such Object"

**Message:**
```
ERROR: ldap3.core.exceptions.LDAPNoSuchObjectResult
Result: 32
Description: noSuchObject
Message: The specified object does not exist in the directory
```

**Cause:** L'objet ou le DN spécifié n'existe pas.

**Scénarios courants:**

1. DN de bind incorrect
2. Base DN incorrect
3. Objet supprimé
4. Mauvaise OU

**Solution:**

```bash
# Rechercher le DN correct
ldapsearch -x -H ldap://server -b "dc=example,dc=com" "(cn=admin)" dn

# Vérifier la structure
ldapsearch -x -H ldap://server -b "" -s base namingContexts

# Tester différentes bases
ldap-monitor test connection --base-dn "dc=example,dc=com"
```

**Exemple de log:**
```
2025-11-17 14:00:00 - ldap.connector - ERROR - noSuchObject (32)
2025-11-17 14:00:00 - ldap.connector - ERROR - Failed to bind as: cn=admin,ou=wrong,dc=example,dc=com
2025-11-17 14:00:00 - ldap.connector - HINT - Verify the DN exists using ldapsearch
```

**Code LDAP:** 32

---

### Erreur: Result Code 49 - "Invalid Credentials"

**Message:**
```
ERROR: ldap3.core.exceptions.LDAPInvalidCredentialsResult
Result: 49
Description: invalidCredentials
Message: The supplied credential is invalid
```

**Cause:** Identifiants incorrects.

**Sub-codes Active Directory:**

```
52e: Credentials invalid
525: User not found
530: Not permitted to logon at this time
531: Not permitted to logon at this workstation
532: Password expired
533: Account disabled
701: Account expired
773: User must reset password
775: User account locked
```

**Solution:**

```bash
# Tester avec ldapsearch
ldapsearch -H ldap://server \
  -D "cn=admin,dc=example,dc=com" \
  -w "password" \
  -b "dc=example,dc=com" \
  "(objectClass=*)"

# Si succès, vérifier config.yaml et variables d'environnement
echo $LDAP_PASSWORD

# Réinitialiser le mot de passe si nécessaire
# OpenLDAP:
ldappasswd -H ldap://server -D "cn=admin,dc=example,dc=com" -W -S

# Active Directory:
# Sur le DC:
Set-ADAccountPassword -Identity "serviceaccount" -NewPassword (ConvertTo-SecureString "NewPass" -AsPlainText -Force)
```

**Code LDAP:** 49

---

### Erreur: Result Code 50 - "Insufficient Access Rights"

**Message:**
```
ERROR: ldap3.core.exceptions.LDAPInsufficientAccessRightsResult
Result: 50
Description: insufficientAccessRights
Message: The user has insufficient access rights
```

**Cause:** Le compte n'a pas les permissions nécessaires.

**Permissions minimales requises:**

```
Pour audit (lecture seule):
- Read sur tous les users
- Read sur tous les groups
- Read sur la structure (OUs)
- Read sur les attributs: cn, uid, mail, member, etc.

Pour gestion:
- Write selon les opérations
```

**Solution OpenLDAP:**

```ldif
# grant-permissions.ldif
dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcAccess
olcAccess: {0}to dn.subtree="ou=users,dc=example,dc=com"
  by dn="cn=monitor-svc,dc=example,dc=com" read
  by * none
-
add: olcAccess
olcAccess: {1}to dn.subtree="ou=groups,dc=example,dc=com"
  by dn="cn=monitor-svc,dc=example,dc=com" read
  by * none
```

**Solution Active Directory:**

```powershell
# PowerShell sur DC
# Créer groupe de lecture
New-ADGroup -Name "LDAP Readers" -GroupScope DomainLocal -Path "OU=Service Groups,DC=corp,DC=example,DC=com"

# Ajouter le compte de service
Add-ADGroupMember -Identity "LDAP Readers" -Members "svc-ldapmonitor"

# Donner permissions de lecture
$acl = Get-Acl "AD:\DC=corp,DC=example,DC=com"
$user = Get-ADUser "svc-ldapmonitor"
$sid = [System.Security.Principal.SecurityIdentifier] $user.SID
$ace = New-Object System.DirectoryServices.ActiveDirectoryAccessRule(
    $sid,
    "ReadProperty,GenericRead",
    "Allow",
    [guid]::Empty,
    "Descendents"
)
$acl.AddAccessRule($ace)
Set-Acl -Path "AD:\DC=corp,DC=example,DC=com" -AclObject $acl
```

**Code LDAP:** 50

---

### Erreur: Result Code 1 - "Operations Error"

**Message:**
```
ERROR: ldap3.core.exceptions.LDAPOperationsResult
Result: 1
Description: operationsError
Message: An operations error occurred
```

**Cause:** Erreur générique du serveur (souvent configuration).

**Causes courantes:**

1. Recherche sans base DN appropriée (AD)
2. Serveur surchargé
3. Problème de configuration serveur
4. Requête trop complexe

**Solution:**

```yaml
# config.yaml
ldap:
  # S'assurer que base_dn est correct
  base_dn: dc=example,dc=com

  # Pour Active Directory, essayer le Global Catalog
  # port: 3268  # ou 3269 pour SSL

  # Réduire la complexité des requêtes
  page_size: 500  # au lieu de 1000
```

```bash
# Vérifier les logs du serveur LDAP
# OpenLDAP:
sudo tail -f /var/log/slapd.log

# Active Directory:
# Event Viewer sur le DC
```

**Code LDAP:** 1

---

### Erreur: Result Code 4 - "Size Limit Exceeded"

**Message:**
```
ERROR: ldap3.core.exceptions.LDAPSizeLimitExceededResult
Result: 4
Description: sizeLimitExceeded
Message: Size limit exceeded
```

**Cause:** Le nombre de résultats dépasse la limite du serveur.

**Solution:**

```yaml
# config.yaml
ldap:
  # Utiliser la pagination
  page_size: 1000  # Ajuster selon le serveur

  # Activer explicitement la pagination
  paged_search: true
```

```bash
# Augmenter la limite sur le serveur (OpenLDAP)
# Dans slapd.conf ou cn=config:
# sizelimit unlimited

# Active Directory (limite par défaut: 1000)
# Pas configurable, utiliser la pagination
```

**Code LDAP:** 4

---

### Erreur: Result Code 53 - "Unwilling to Perform"

**Message:**
```
ERROR: ldap3.core.exceptions.LDAPUnwillingToPerformResult
Result: 53
Description: unwillingToPerform
Message: The server is unwilling to perform the operation
```

**Cause:** Le serveur refuse l'opération (souvent sécurité).

**Causes courantes:**

1. Tentative de modification du mot de passe sans SSL/TLS
2. Opération non autorisée par la politique
3. Attribut en lecture seule
4. Violation de contrainte

**Solution:**

```yaml
# config.yaml
ldap:
  # Utiliser SSL pour les modifications de mot de passe
  use_ssl: true
  port: 636

  # Ou STARTTLS
  use_tls: true
```

**Code LDAP:** 53

---

## Erreurs Python

### Erreur: "ModuleNotFoundError"

**Message:**
```
ModuleNotFoundError: No module named 'ldap3'
```

**Cause:** Dépendances Python non installées.

**Solution:**

```bash
# Installer les dépendances
pip install -r requirements.txt

# Ou réinstaller l'application
pip install --upgrade ldap-health-monitor

# Ou forcer la réinstallation
pip install --force-reinstall ldap-health-monitor

# Vérifier l'installation
pip show ldap-health-monitor
pip list | grep ldap
```

---

### Erreur: "ImportError: cannot import name"

**Message:**
```
ImportError: cannot import name 'LDAPConnector' from 'src.core.connector'
```

**Cause:** Version incompatible ou installation corrompue.

**Solution:**

```bash
# Désinstaller complètement
pip uninstall ldap-health-monitor ldap3 -y

# Nettoyer le cache
pip cache purge

# Réinstaller
pip install ldap-health-monitor

# Ou depuis le code source
git clone https://github.com/yourusername/ldap-health-monitor.git
cd ldap-health-monitor
pip install -e .
```

---

### Erreur: "KeyError"

**Message:**
```
KeyError: 'mail'
ERROR: Attribute 'mail' not found in LDAP entry
```

**Cause:** Attribut manquant dans l'objet LDAP.

**Solution:**

```yaml
# config.yaml
audit:
  # Ne pas exiger certains attributs
  required_user_attributes:
    - cn
    - uid
    # - mail  # Peut être absent

  # Gérer les attributs manquants
  allow_missing_attributes: true
  default_missing_value: "N/A"
```

```bash
# Auditer avec tolérance d'erreur
ldap-monitor audit users --ignore-missing-attributes
```

---

### Erreur: "MemoryError"

**Message:**
```
MemoryError: Unable to allocate 1.2 GiB for an array
```

**Cause:** Mémoire insuffisante pour l'opération.

**Solution:** Voir [Performance Issues - Utilisation Mémoire](Performance-Issues.md#utilisation-mémoire)

```yaml
# config.yaml
ldap:
  page_size: 500  # Réduire

advanced:
  low_memory_mode: true
  stream_results: true
```

---

## Codes de Sortie

### Table des Codes de Sortie

```
┌──────┬────────────────────────────────────────────────────┐
│ Code │ Description                                        │
├──────┼────────────────────────────────────────────────────┤
│ 0    │ Succès - Aucune erreur                             │
│ 1    │ Erreur générale                                    │
│ 2    │ Erreur de configuration                            │
│ 3    │ Erreur de connexion LDAP                           │
│ 4    │ Erreur d'authentification                          │
│ 5    │ Erreur de permission                               │
│ 6    │ Erreur de validation                               │
│ 7    │ Timeout                                            │
│ 8    │ Fichier non trouvé                                 │
│ 9    │ Erreur de format                                   │
│ 10   │ Opération annulée par l'utilisateur               │
│ 11   │ Ressource non disponible                           │
│ 12   │ Erreur réseau                                      │
│ 13   │ Erreur SSL/TLS                                     │
│ 130  │ Interrompu par SIGINT (Ctrl+C)                     │
└──────┴────────────────────────────────────────────────────┘
```

### Utilisation des Codes de Sortie

```bash
# Capturer le code de sortie
ldap-monitor audit health
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
  echo "Succès"
elif [ $EXIT_CODE -eq 3 ]; then
  echo "Problème de connexion LDAP"
  # Réessayer ou alerter
elif [ $EXIT_CODE -eq 4 ]; then
  echo "Problème d'authentification"
  # Vérifier les credentials
else
  echo "Erreur inconnue: $EXIT_CODE"
fi
```

### Script avec Gestion des Codes

```bash
#!/bin/bash
# run-audit-with-retry.sh

MAX_RETRIES=3
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
  ldap-monitor audit health
  EXIT_CODE=$?

  case $EXIT_CODE in
    0)
      echo "✓ Audit réussi"
      exit 0
      ;;
    3)
      echo "⚠ Erreur de connexion, retry $((RETRY_COUNT+1))/$MAX_RETRIES"
      sleep 5
      RETRY_COUNT=$((RETRY_COUNT+1))
      ;;
    4)
      echo "✗ Erreur d'authentification - impossible de réessayer"
      exit 4
      ;;
    *)
      echo "✗ Erreur inconnue: $EXIT_CODE"
      exit $EXIT_CODE
      ;;
  esac
done

echo "✗ Échec après $MAX_RETRIES tentatives"
exit 1
```

---

## Exceptions ldap3

### Hiérarchie des Exceptions

```python
LDAPException (base)
├── LDAPOperationsResult
│   ├── LDAPNoSuchObjectResult (32)
│   ├── LDAPInvalidCredentialsResult (49)
│   ├── LDAPInsufficientAccessRightsResult (50)
│   ├── LDAPOperationsError (1)
│   ├── LDAPSizeLimitExceededResult (4)
│   ├── LDAPTimeLimitExceededResult (3)
│   └── LDAPUnwillingToPerformResult (53)
├── LDAPSocketOpenError
├── LDAPSocketSendError
├── LDAPSocketReceiveError
├── LDAPSessionTerminatedByServerError
└── LDAPInvalidFilterError
```

### Gestion des Exceptions

```python
# exemple-error-handling.py
from ldap3.core.exceptions import (
    LDAPException,
    LDAPInvalidCredentialsResult,
    LDAPNoSuchObjectResult,
    LDAPSocketOpenError
)

try:
    connector.connect()
except LDAPInvalidCredentialsResult as e:
    print(f"Identifiants invalides: {e}")
    print("Vérifier bind_dn et bind_password dans config.yaml")
    exit(4)
except LDAPNoSuchObjectResult as e:
    print(f"Objet non trouvé: {e}")
    print("Vérifier bind_dn et base_dn dans config.yaml")
    exit(3)
except LDAPSocketOpenError as e:
    print(f"Impossible d'ouvrir la connexion: {e}")
    print("Vérifier que le serveur LDAP est accessible")
    exit(3)
except LDAPException as e:
    print(f"Erreur LDAP: {e}")
    exit(1)
```

---

## Erreurs de Permissions

### Erreur: "Permission denied" (Fichiers)

**Message:**
```
PermissionError: [Errno 13] Permission denied: 'logs/ldap-monitor.log'
```

**Cause:** Pas de permission pour écrire dans le répertoire.

**Solution:**

```bash
# Créer le répertoire avec bonnes permissions
mkdir -p logs
chmod 755 logs

# Changer le propriétaire si nécessaire
sudo chown $USER:$USER logs

# Vérifier les permissions
ls -la logs/

# Alternative: Utiliser un autre répertoire
ldap-monitor --log-dir /tmp/ldap-logs audit health
```

---

### Erreur: "Permission denied" (Installation)

**Message:**
```
ERROR: Could not install packages due to an EnvironmentError: [Errno 13] Permission denied: '/usr/local/lib/python3.10'
```

**Cause:** Installation sans droits admin.

**Solution:**

```bash
# Option 1: Installation utilisateur
pip install --user ldap-health-monitor

# Option 2: Utiliser pipx (recommandé)
python3 -m pip install --user pipx
pipx install ldap-health-monitor

# Option 3: Virtual environment
python3 -m venv venv
source venv/bin/activate
pip install ldap-health-monitor

# Option 4: Avec sudo (non recommandé)
sudo pip install ldap-health-monitor
```

---

## Erreurs de Format

### Erreur: "Invalid DN format"

**Message:**
```
ERROR: Invalid DN format: 'admin'
LDAPInvalidDnError: DN must be a string in LDAP format
```

**Cause:** DN mal formaté.

**Formats valides:**

```yaml
# ✅ OpenLDAP
bind_dn: cn=admin,dc=example,dc=com
bind_dn: uid=jdoe,ou=users,dc=example,dc=com

# ✅ Active Directory (UPN)
bind_dn: serviceaccount@corp.example.com

# ✅ Active Directory (DN)
bind_dn: CN=Service Account,OU=Service Accounts,DC=corp,DC=example,DC=com

# ❌ Invalides
bind_dn: admin
bind_dn: cn=admin
bind_dn: admin@example
```

---

### Erreur: "Invalid filter syntax"

**Message:**
```
ERROR: Invalid LDAP filter syntax
LDAPInvalidFilterError: malformed filter
```

**Cause:** Filtre LDAP mal formé.

**Syntaxe correcte:**

```bash
# ✅ Valides
"(objectClass=*)"
"(uid=jdoe)"
"(&(objectClass=user)(cn=John*))"
"(|(mail=*@example.com)(mail=*@test.com))"

# ❌ Invalides
"objectClass=user"  # Manque parenthèses
"(objectClass=user"  # Manque parenthèse fermante
"(&(uid=test))"     # & sans deuxième condition
```

---

## Solutions Rapides

### Diagnostic Automatique

```bash
#!/bin/bash
# auto-fix.sh - Tentative de résolution automatique

echo "=== Diagnostic et Correction Automatique ==="

# 1. Vérifier installation
if ! command -v ldap-monitor &> /dev/null; then
  echo "⚠ ldap-monitor non trouvé, installation..."
  pip install ldap-health-monitor
fi

# 2. Vérifier configuration
if [ ! -f config.yaml ]; then
  echo "⚠ config.yaml manquant, création..."
  ldap-monitor config init
  echo "✗ Éditer config.yaml avec vos paramètres"
  exit 2
fi

# 3. Valider configuration
if ! ldap-monitor config validate &> /dev/null; then
  echo "✗ Configuration invalide"
  ldap-monitor config validate
  exit 2
fi

# 4. Vérifier variables d'environnement
if [ -z "$LDAP_PASSWORD" ]; then
  echo "⚠ LDAP_PASSWORD non définie"
  if [ -f .env ]; then
    echo "  Charger depuis .env..."
    export $(cat .env | grep -v '^#' | xargs)
  else
    echo "✗ Définir LDAP_PASSWORD"
    exit 2
  fi
fi

# 5. Créer les répertoires nécessaires
mkdir -p logs reports backups
chmod 755 logs reports backups

# 6. Tester la connexion
echo "Test de connexion..."
if ldap-monitor test connection; then
  echo "✓ Configuration correcte"
  exit 0
else
  EXIT_CODE=$?
  echo "✗ Erreur de connexion (code: $EXIT_CODE)"
  echo "  Voir logs/ldap-monitor.log pour plus de détails"
  exit $EXIT_CODE
fi
```

### Réinitialisation Complète

```bash
#!/bin/bash
# reset-all.sh - Réinitialiser complètement l'installation

echo "⚠️  ATTENTION: Cela va supprimer toute la configuration!"
read -p "Continuer? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Annulé"
  exit 0
fi

echo "Réinitialisation..."

# 1. Sauvegarder
if [ -f config.yaml ]; then
  cp config.yaml config.yaml.backup.$(date +%Y%m%d-%H%M%S)
fi

# 2. Nettoyer
rm -rf logs/* reports/* backups/*
rm -f config.yaml

# 3. Désinstaller
pip uninstall ldap-health-monitor -y

# 4. Nettoyer cache
pip cache purge

# 5. Réinstaller
pip install ldap-health-monitor

# 6. Recréer configuration
ldap-monitor config init

echo "✓ Réinitialisation terminée"
echo "  config.yaml.backup.* contient votre ancienne configuration"
echo "  Éditer config.yaml avec vos paramètres"
```

### Collecteur de Logs pour Support

```bash
#!/bin/bash
# collect-debug-info.sh - Collecter les infos pour le support

OUTPUT="debug-info-$(date +%Y%m%d-%H%M%S).txt"

echo "=== LDAP Health Monitor Debug Info ===" > $OUTPUT
echo "Date: $(date)" >> $OUTPUT
echo "" >> $OUTPUT

echo "=== System Info ===" >> $OUTPUT
uname -a >> $OUTPUT
echo "Python: $(python3 --version)" >> $OUTPUT
echo "pip: $(pip --version)" >> $OUTPUT
echo "" >> $OUTPUT

echo "=== Installed Packages ===" >> $OUTPUT
pip list | grep -E "ldap|yaml|click|rich" >> $OUTPUT
echo "" >> $OUTPUT

echo "=== Configuration (masqué) ===" >> $OUTPUT
if [ -f config.yaml ]; then
  # Masquer les mots de passe
  sed 's/password:.*/password: ***MASKED***/' config.yaml >> $OUTPUT
else
  echo "config.yaml not found" >> $OUTPUT
fi
echo "" >> $OUTPUT

echo "=== Environment Variables ===" >> $OUTPUT
env | grep -E "LDAP|PATH|PYTHON" >> $OUTPUT
echo "" >> $OUTPUT

echo "=== Recent Logs ===" >> $OUTPUT
if [ -f logs/ldap-monitor.log ]; then
  tail -100 logs/ldap-monitor.log >> $OUTPUT
else
  echo "No logs found" >> $OUTPUT
fi
echo "" >> $OUTPUT

echo "=== Connection Test ===" >> $OUTPUT
ldap-monitor --verbose test connection >> $OUTPUT 2>&1
echo "" >> $OUTPUT

echo "✓ Informations collectées dans: $OUTPUT"
echo "  Vérifier que les mots de passe sont masqués avant d'envoyer!"
```

---

## Erreurs Spécifiques par OS

### macOS

**Erreur: "fatal error: 'sasl/sasl.h' file not found"**

```bash
# Installer les dépendances
brew install openssl libsasl2

# Définir les flags de compilation
export LDFLAGS="-L$(brew --prefix openssl)/lib -L$(brew --prefix libsasl2)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include -I$(brew --prefix libsasl2)/include"

# Réinstaller
pip install --no-cache-dir ldap-health-monitor
```

### Linux

**Erreur: "libldap not found"**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install libldap2-dev libsasl2-dev python3-dev

# RHEL/CentOS
sudo yum install openldap-devel python3-devel

# Puis réinstaller
pip install --no-cache-dir ldap-health-monitor
```

### Windows

**Erreur: "Microsoft Visual C++ 14.0 is required"**

```bash
# Option 1: Installer Build Tools
# Télécharger depuis: https://visualstudio.microsoft.com/downloads/
# Installer "Build Tools for Visual Studio"

# Option 2: Utiliser wheel pré-compilé
pip install --only-binary :all: ldap-health-monitor

# Option 3: Utiliser conda
conda install -c conda-forge ldap3
pip install ldap-health-monitor --no-deps
```

---

## Tableau de Référence Rapide

### Erreurs par Code

```
┌──────┬─────────────────────┬────────────────────────────────┐
│ Code │ Exception           │ Solution Rapide                │
├──────┼─────────────────────┼────────────────────────────────┤
│ 1    │ Operations Error    │ Vérifier base_dn               │
│ 4    │ Size Limit          │ Activer pagination             │
│ 32   │ No Such Object      │ Vérifier DN existe             │
│ 49   │ Invalid Credentials │ Vérifier mot de passe          │
│ 50   │ Insufficient Rights │ Vérifier permissions           │
│ 53   │ Unwilling           │ Activer SSL/TLS                │
└──────┴─────────────────────┴────────────────────────────────┘
```

### Commandes de Diagnostic

```bash
# Test complet
ldap-monitor --verbose test connection

# Validation configuration
ldap-monitor config validate

# Vérifier version
ldap-monitor --version

# Logs en temps réel
tail -f logs/ldap-monitor.log

# Test manuel LDAP
ldapsearch -H ldap://server -D "bind_dn" -W -b "base_dn"
```

---

## Ressources d'Aide

### Documentation

- [FAQ](FAQ.md)
- [Connection Issues](Connection-Issues.md)
- [Performance Issues](Performance-Issues.md)
- [Debugging Guide](Debugging.md)

### Support

- GitHub Issues: https://github.com/yourusername/ldap-health-monitor/issues
- Discussions: https://github.com/yourusername/ldap-health-monitor/discussions
- Email: support@example.com

### Outils Externes

```bash
# Installer outils de diagnostic
pip install ldap-utils

# Tests réseau
apt-get install ldap-utils  # Ubuntu
yum install openldap-clients  # RHEL

# Monitoring
pip install py-spy memory_profiler
```

---

**Page suivante:** [Debugging Guide](Debugging.md)
**Page précédente:** [Performance Issues](Performance-Issues.md)
