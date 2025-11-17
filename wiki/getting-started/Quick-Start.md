# Guide de Démarrage Rapide

Ce guide vous permet de démarrer avec LDAP Health Monitor en quelques minutes.

## 🚀 Installation Rapide

```bash
# Cloner le repository
git clone https://github.com/yourusername/ldap-health-monitor.git
cd ldap-health-monitor

# Installation avec make
make install

# Ou installation manuelle
pip install -e .
```

## ⚙️ Configuration Minimale

### 1. Créer le fichier de configuration

```bash
cp config.example.yaml config.yaml
cp .env.example .env
```

### 2. Éditer config.yaml

Configuration minimale pour démarrer :

```yaml
ldap:
  server: "ldap.example.com"
  port: 636
  use_ssl: true
  bind_dn: "${LDAP_BIND_DN}"
  bind_password: "${LDAP_BIND_PASSWORD}"
  base_dn: "dc=example,dc=com"

schema:
  users:
    object_class: "inetOrgPerson"
    base_ou: "ou=users,dc=example,dc=com"

  groups:
    object_class: "groupOfNames"
    base_ou: "ou=groups,dc=example,dc=com"
```

### 3. Configurer les variables d'environnement

Éditer le fichier `.env` :

```bash
LDAP_BIND_DN=cn=admin,dc=example,dc=com
LDAP_BIND_PASSWORD=votre_mot_de_passe_securise
```

⚠️ **IMPORTANT** : Ne jamais commiter le fichier `.env` dans Git !

## 🧪 Test de Connexion

Vérifier que la connexion fonctionne :

```bash
ldap-monitor health
```

Sortie attendue :
```
✅ LDAP Health Check Results
────────────────────────────────────
Server: ldap.example.com:636
Status: ✓ Healthy
Response Time: 45ms
SSL Certificate: Valid (expires in 287 days)
```

## 📊 Premier Audit

### Audit Complet

Lancer un audit complet de votre annuaire LDAP :

```bash
ldap-monitor audit all
```

### Audit Ciblé

Auditer uniquement les utilisateurs :

```bash
ldap-monitor audit users
```

### Générer un Rapport HTML

```bash
ldap-monitor audit all --format html --output audit-report.html
```

Ouvrir le rapport dans votre navigateur :

```bash
# macOS
open audit-report.html

# Linux
xdg-open audit-report.html
```

## 📈 Exporter des Données

### Liste des Utilisateurs

```bash
ldap-monitor export users --format csv --output users.csv
```

### Liste des Groupes

```bash
ldap-monitor export groups --format json --output groups.json
```

## 🔍 Recherche d'Informations

### Chercher un utilisateur

```bash
ldap-monitor search --type user --query "john.doe"
```

### Chercher un groupe

```bash
ldap-monitor search --type group --query "developers"
```

## 💾 Backup Rapide

Faire un backup de votre annuaire :

```bash
ldap-monitor backup create --output backup-$(date +%Y%m%d).ldif
```

## 📊 Monitoring Continu

### Démarrer le daemon de monitoring

```bash
ldap-monitor monitor start --interval 300
```

Le monitoring va :
- ✅ Collecter les métriques toutes les 5 minutes
- ✅ Détecter les anomalies
- ✅ Envoyer des alertes si configurées
- ✅ Exposer les métriques Prometheus sur http://localhost:9090

### Vérifier le statut

```bash
ldap-monitor monitor status
```

### Arrêter le daemon

```bash
ldap-monitor monitor stop
```

## 🔔 Configuration des Alertes (Optionnel)

Pour recevoir des alertes sur Slack, ajouter dans `config.yaml` :

```yaml
alerts:
  enabled: true
  channels:
    - type: slack
      webhook_url: "${SLACK_WEBHOOK_URL}"
      enabled: true
```

Ajouter dans `.env` :
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

## 🛠️ Commandes Utiles

| Commande | Description |
|----------|-------------|
| `ldap-monitor --help` | Aide générale |
| `ldap-monitor health` | Vérifier la santé du serveur |
| `ldap-monitor audit all` | Audit complet |
| `ldap-monitor audit users` | Audit utilisateurs uniquement |
| `ldap-monitor audit groups` | Audit groupes uniquement |
| `ldap-monitor export users` | Exporter les utilisateurs |
| `ldap-monitor backup create` | Créer un backup |
| `ldap-monitor monitor start` | Démarrer le monitoring |
| `ldap-monitor search` | Rechercher dans l'annuaire |

## 🎯 Prochaines Étapes

Maintenant que vous avez fait vos premiers pas, vous pouvez :

1. **Personnaliser la configuration** : [Configuration Avancée](../configuration/Config-File-Structure.md)
2. **Automatiser les audits** : [Scripts d'Automatisation](../guides/Cron-Automation.md)
3. **Configurer les alertes** : [Système d'Alertes](../features/monitoring/Alerts-System.md)
4. **Mettre en production** : [Monitoring en Production](../guides/Production-Monitoring.md)

## 🆘 Besoin d'Aide ?

- Consultez la [FAQ](../troubleshooting/FAQ.md)
- Vérifiez les [Problèmes de Connexion](../troubleshooting/Connection-Issues.md)
- Consultez les [Erreurs Courantes](../troubleshooting/Common-Errors.md)

## 💡 Exemples Pratiques

### Workflow Quotidien Recommandé

```bash
# 1. Vérifier la santé
ldap-monitor health

# 2. Audit rapide
ldap-monitor audit users --severity critical

# 3. Backup hebdomadaire (le lundi)
if [ $(date +%u) -eq 1 ]; then
  ldap-monitor backup create --compress
fi

# 4. Export mensuel (le 1er du mois)
if [ $(date +%d) -eq 01 ]; then
  ldap-monitor export users --format csv
  ldap-monitor export groups --format json
fi
```

### Audit avec Filtre de Sévérité

```bash
# Afficher uniquement les problèmes critiques
ldap-monitor audit all --severity critical

# Afficher warnings et critiques
ldap-monitor audit all --severity warning
```

### Export avec Attributs Personnalisés

```bash
# Exporter uniquement certains attributs
ldap-monitor export users \
  --attributes cn,mail,telephoneNumber \
  --format csv \
  --output contacts.csv
```

## 🎓 Ressources d'Apprentissage

- [Toutes les Commandes CLI](../reference/CLI-Commands.md)
- [Cas d'Usage Complets](../examples/Use-Cases.md)
- [Configuration LDAP Détaillée](../configuration/LDAP-Configuration.md)

---

**Prêt à aller plus loin ?** Consultez le [Guide de Configuration Initiale](Initial-Configuration.md) pour une configuration complète.
