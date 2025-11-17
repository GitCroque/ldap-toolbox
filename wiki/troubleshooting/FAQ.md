# FAQ - Questions Fréquentes

## 🚀 Installation & Setup

### Q: Quelle version de Python est requise ?

**R:** Python 3.10 ou supérieur est requis.

```bash
# Vérifier votre version
python3 --version

# Si < 3.10, installer une version récente
# macOS :
brew install python@3.11

# Ubuntu :
sudo apt install python3.11
```

### Q: Dois-je installer sur le serveur LDAP ?

**R:** Non ! L'outil est un client LDAP. Installez-le sur :
- ✅ Votre machine de travail
- ✅ Un serveur de monitoring dédié
- ✅ Un container Docker
- ❌ Pas nécessaire sur le serveur LDAP lui-même

### Q: Puis-je utiliser avec Active Directory ?

**R:** Oui, absolument ! L'outil est compatible avec :
- ✅ Microsoft Active Directory
- ✅ OpenLDAP
- ✅ FreeIPA
- ✅ 389 Directory Server
- ✅ Tout serveur LDAP compatible RFC

Voir le [guide Active Directory](../guides/Active-Directory.md).

## ⚙️ Configuration

### Q: Comment configurer pour Active Directory ?

**R:** Utilisez cette configuration :

```yaml
ldap:
  server: ldaps://dc01.corp.example.com
  port: 636
  bind_dn: serviceaccount@corp.example.com  # Format UPN
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=corp,dc=example,dc=com
  user_objectclass: user
  group_objectclass: group
  user_uid_attribute: sAMAccountName
```

### Q: Où stocker mes credentials ?

**R:** JAMAIS dans config.yaml ! Utilisez des variables d'environnement :

```bash
# Dans .env
LDAP_PASSWORD=your-password

# Puis dans config.yaml
bind_password: ${LDAP_PASSWORD}
```

### Q: Comment tester ma configuration ?

**R:**
```bash
# Valider le fichier
ldap-monitor config validate

# Tester la connexion
ldap-monitor test connection

# Audit rapide
ldap-monitor audit health
```

## 🔍 Audit

### Q: Comment trouver les comptes inactifs ?

**R:**
```bash
# Inactifs depuis 90 jours (défaut)
ldap-monitor audit users --inactive

# Avec seuil personnalisé
ldap-monitor audit users --inactive --days 180

# Export en CSV
ldap-monitor audit users --inactive --export inactive.csv
```

### Q: Puis-je personnaliser les vérifications ?

**R:** Oui, dans config.yaml :

```yaml
audit:
  required_user_attributes:
    - cn
    - mail
    - telephoneNumber
    - department

  thresholds:
    inactive_days: 90
    max_empty_groups: 5
```

### Q: Comment générer un rapport PDF/HTML ?

**R:**
```bash
# HTML
ldap-monitor audit all --format html --output report.html

# PDF (via HTML)
ldap-monitor audit all --format html --output report.html
# Puis convertir avec wkhtmltopdf ou navigateur
```

## 📊 Monitoring

### Q: Comment monitorer en continu ?

**R:**
```bash
# Mode daemon
ldap-monitor monitor start --daemon

# Ou avec systemd
sudo systemctl enable ldap-monitor
sudo systemctl start ldap-monitor
```

### Q: Comment intégrer avec Prometheus ?

**R:**
```bash
# Démarrer le serveur de métriques
ldap-monitor monitor prometheus --port 9090

# Dans prometheus.yml
scrape_configs:
  - job_name: 'ldap-monitor'
    static_configs:
      - targets: ['localhost:9090']
```

### Q: Comment recevoir des alertes Slack ?

**R:** Dans config.yaml :

```yaml
alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#ldap-alerts"
```

Puis :
```bash
# Dans .env
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🛠️ Gestion

### Q: Puis-je désactiver des comptes ?

**R:** Oui :

```bash
# Un compte
ldap-monitor user disable "uid=jdoe,ou=users,dc=example,dc=com"

# En masse (dry-run d'abord)
ldap-monitor cleanup inactive --days 365 --dry-run
ldap-monitor cleanup inactive --days 365 --confirm
```

### Q: Comment faire un backup ?

**R:**
```bash
# Backup complet LDIF
ldap-monitor backup full --output backup.ldif

# JSON
ldap-monitor backup full --output backup.json --format json

# Avec compression
# (automatique si config.backup.compress = true)
```

### Q: Puis-je modifier des attributs en masse ?

**R:** Oui :

```bash
# Via fichier CSV
# users.csv: dn,attribute,value
# uid=user1,ou=users,dc=example,dc=com,department,IT
# uid=user2,ou=users,dc=example,dc=com,department,HR

ldap-monitor bulk set-attribute --from-file users.csv --dry-run
ldap-monitor bulk set-attribute --from-file users.csv --confirm
```

## 🔒 Sécurité

### Q: Quelles permissions sont nécessaires ?

**R:** Pour l'audit : **Read-only** sur :
- Tous les users
- Tous les groups
- Structure (OUs)
- Attributs : cn, uid, mail, member, etc.

Pour la gestion : **Write** selon les opérations.

### Q: Comment sécuriser les credentials ?

**R:**
1. ✅ Utiliser variables d'environnement
2. ✅ Utiliser TLS/SSL
3. ✅ Compte de service dédié
4. ✅ Permissions minimales
5. ❌ JAMAIS commit .env ou config.yaml

### Q: Mes données LDAP seront-elles commitées par erreur ?

**R:** Non, le .gitignore protège :
- config.yaml
- .env
- *.ldif
- backups/
- exports/
- *.csv avec données

## ⚡ Performance

### Q: L'audit est lent sur ma grande base (100k+ users)

**R:** Optimisez :

```yaml
ldap:
  page_size: 1500     # Augmenter (max 1000 pour AD)
  timeout: 30         # Augmenter si réseau lent

audit:
  parallel_checks: true
  cache_enabled: true
```

Ou limitez :
```bash
# Auditer seulement une OU
ldap-monitor audit users --base-dn "ou=employees,dc=example,dc=com"
```

### Q: Trop de mémoire utilisée

**R:** Réduisez page_size et utilisez streaming :

```yaml
ldap:
  page_size: 500

advanced:
  stream_results: true
  max_concurrent_operations: 5
```

## 🐛 Erreurs Courantes

### Q: "Configuration file not found"

**R:**
```bash
# Créer config.yaml
ldap-monitor config init

# Ou spécifier le chemin
ldap-monitor --config /path/to/config.yaml audit health
```

### Q: "LDAP connection failed"

**R:** Vérifiez :
1. Serveur accessible : `ping ldap.example.com`
2. Port ouvert : `telnet ldap.example.com 389`
3. Credentials corrects
4. TLS/SSL configuré correctement

```bash
# Test avec ldapsearch
ldapsearch -H ldap://server -D "bind_dn" -W -b "base_dn"
```

### Q: "Permission denied" lors de l'installation

**R:**
```bash
# Installer pour l'utilisateur
pip install --user ldap-health-monitor

# Ou utiliser pipx (recommandé)
pipx install ldap-health-monitor
```

### Q: "ModuleNotFoundError: No module named 'ldap3'"

**R:**
```bash
# Réinstaller les dépendances
pip install -r requirements.txt

# Ou
pip install --force-reinstall ldap-health-monitor
```

### Q: macOS: "fatal error: 'sasl/sasl.h' file not found"

**R:**
```bash
# Installer dépendances
brew install openssl libsasl2

# Définir flags
export LDFLAGS="-L$(brew --prefix openssl)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include"

# Réinstaller
pip install --no-cache-dir ldap-health-monitor
```

## 🔄 Workflow

### Q: Workflow recommandé pour audit mensuel ?

**R:**
```bash
#!/bin/bash
# monthly-audit.sh

DATE=$(date +%Y-%m)

# 1. Backup
ldap-monitor backup full --output backup-$DATE.ldif

# 2. Audit complet
ldap-monitor audit all --format html --output audit-$DATE.html

# 3. Exporter données
ldap-monitor export users --output users-$DATE.csv

# 4. Envoyer rapport
mail -s "LDAP Audit $DATE" -a audit-$DATE.html admin@example.com < /dev/null
```

Cron :
```cron
0 2 1 * * /usr/local/bin/monthly-audit.sh
```

### Q: Comment automatiser le nettoyage ?

**R:**
```bash
#!/bin/bash
# weekly-cleanup.sh

# 1. Backup avant nettoyage
ldap-monitor backup full --output pre-cleanup-$(date +%Y%m%d).ldif

# 2. Dry-run
ldap-monitor cleanup dry-run > cleanup-report.txt

# 3. Si OK, exécuter
if [ -s cleanup-report.txt ]; then
  ldap-monitor cleanup empty-groups --confirm
  ldap-monitor cleanup orphans --confirm
fi

# 4. Audit post-cleanup
ldap-monitor audit all --format json --output post-cleanup-audit.json
```

## 📚 Intégrations

### Q: Intégration avec n8n ?

**R:** Dans config.yaml :

```yaml
integrations:
  n8n:
    enabled: true
    webhook_url: ${N8N_WEBHOOK}
    events:
      - alert
      - audit_complete
```

Dans n8n, créer webhook qui reçoit JSON.

### Q: Exporter vers Excel ?

**R:**
```bash
# Export CSV (ouvrable dans Excel)
ldap-monitor export users --format csv --output users.csv

# Ou via pandas (script Python)
import pandas as pd
df = pd.read_csv('users.csv')
df.to_excel('users.xlsx', index=False)
```

### Q: Intégration CI/CD ?

**R:** Voir [CI/CD Integration Guide](../integrations/CI-CD.md).

Exemple GitHub Actions :
```yaml
- name: LDAP Audit
  run: ldap-monitor audit all --format json
  env:
    LDAP_PASSWORD: ${{ secrets.LDAP_PASSWORD }}
```

## 💡 Cas d'Usage

### Q: Trouver tous les comptes sans manager

**R:**
```bash
ldap-monitor audit users --missing-attributes --required manager
```

### Q: Lister groupes avec plus de 50 membres

**R:**
```bash
ldap-monitor audit groups --large --threshold 50
```

### Q: Trouver doublons d'email

**R:**
```bash
ldap-monitor audit users --check-duplicates
```

### Q: Exporter organigramme (managers)

**R:**
```bash
ldap-monitor export users \
  --attributes "uid,cn,mail,manager" \
  --format csv \
  --output orgchart.csv
```

## 🆘 Support

### Q: Où obtenir de l'aide ?

**R:**
- 📖 [Documentation complète](../Home.md)
- 🐛 [GitHub Issues](https://github.com/yourusername/ldap-health-monitor/issues)
- 💬 [Discussions](https://github.com/yourusername/ldap-health-monitor/discussions)
- 📧 Email : support@example.com

### Q: Comment contribuer ?

**R:** Voir [Contributing Guide](../development/Contributing.md)

### Q: Comment reporter un bug ?

**R:**
1. Vérifier si déjà reporté
2. Créer issue GitHub avec :
   - Version : `ldap-monitor --version`
   - OS et Python version
   - Config (masquer credentials)
   - Erreur complète
   - Steps to reproduce

## 📊 Statistiques

### Q: Comment voir des stats globales ?

**R:**
```bash
ldap-monitor audit health
# Affiche :
# - Nombre users/groups/OUs
# - Temps de réponse
# - Score de santé
```

### Q: Exporter métriques historiques ?

**R:**
```bash
ldap-monitor monitor history --days 30 --format csv --output metrics-30days.csv
```

---

**Vous ne trouvez pas votre réponse ?**

- Consultez le [Troubleshooting Guide](Common-Errors.md)
- Posez votre question sur [GitHub Discussions](https://github.com/yourusername/ldap-health-monitor/discussions)
