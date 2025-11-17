# LDAP Health Monitor - Wiki Complet

Bienvenue dans la documentation complète de LDAP Health Monitor, l'outil CLI open-source pour auditer, monitorer et gérer vos serveurs LDAP et Active Directory.

## 📚 Table des Matières

### 🚀 Getting Started
- [Installation Complète](getting-started/Installation.md)
- [Premier Lancement](getting-started/Quick-Start.md)
- [Configuration Initiale](getting-started/Initial-Configuration.md)
- [Test de Connexion](getting-started/Testing-Connection.md)

### ⚙️ Configuration
- [Structure du Fichier Config](configuration/Config-File-Structure.md)
- [Variables d'Environnement](configuration/Environment-Variables.md)
- [Configuration LDAP](configuration/LDAP-Configuration.md)
- [Configuration des Audits](configuration/Audit-Configuration.md)
- [Configuration du Monitoring](configuration/Monitoring-Configuration.md)
- [Configuration des Alertes](configuration/Alerts-Configuration.md)
- [Configuration de la Gestion](configuration/Management-Configuration.md)
- [Personnalisation du Schéma](configuration/Schema-Customization.md)

### 🔍 Fonctionnalités - Audit
- [Vue d'Ensemble des Audits](features/audit/Overview.md)
- [Audit de Santé](features/audit/Health-Check.md)
- [Audit des Utilisateurs](features/audit/Users-Audit.md)
- [Audit des Groupes](features/audit/Groups-Audit.md)
- [Audit de Structure](features/audit/Structure-Audit.md)
- [Audit de Sécurité](features/audit/Security-Audit.md)
- [Audit de Cohérence](features/audit/Consistency-Audit.md)
- [Rapports d'Audit](features/audit/Audit-Reports.md)

### 📊 Fonctionnalités - Monitoring
- [Vue d'Ensemble du Monitoring](features/monitoring/Overview.md)
- [Collecte de Métriques](features/monitoring/Metrics-Collection.md)
- [Système d'Alertes](features/monitoring/Alerts-System.md)
- [Mode Daemon](features/monitoring/Daemon-Mode.md)
- [Métriques Prometheus](features/monitoring/Prometheus-Metrics.md)
- [Historique et Tendances](features/monitoring/History-Trends.md)

### 🛠️ Fonctionnalités - Gestion
- [Gestion des Utilisateurs](features/management/User-Management.md)
- [Gestion des Groupes](features/management/Group-Management.md)
- [Opérations de Nettoyage](features/management/Cleanup-Operations.md)
- [Backup et Restauration](features/management/Backup-Restore.md)
- [Exports de Données](features/management/Data-Exports.md)
- [Opérations en Masse](features/management/Bulk-Operations.md)

### 🔌 Intégrations
- [Prometheus & Grafana](integrations/Prometheus-Grafana.md)
- [Slack Notifications](integrations/Slack.md)
- [Email Alerting](integrations/Email.md)
- [n8n Automation](integrations/n8n.md)
- [Webhooks Génériques](integrations/Webhooks.md)
- [CI/CD Integration](integrations/CI-CD.md)

### 👨‍💻 Développement
- [Architecture du Code](development/Architecture.md)
- [Structure des Modules](development/Module-Structure.md)
- [Modèles de Données](development/Data-Models.md)
- [Ajouter un Module d'Audit](development/Adding-Audit-Module.md)
- [Ajouter un Reporter](development/Adding-Reporter.md)
- [Tests et Couverture](development/Testing.md)
- [Contribution](development/Contributing.md)
- [Style de Code](development/Code-Style.md)

### 📖 Guides Pratiques
- [Migrer depuis un autre outil](guides/Migration.md)
- [Automatisation avec Cron](guides/Cron-Automation.md)
- [Monitoring en Production](guides/Production-Monitoring.md)
- [Déploiement Docker](guides/Docker-Deployment.md)
- [Active Directory Specifics](guides/Active-Directory.md)
- [OpenLDAP Specifics](guides/OpenLDAP.md)
- [FreeIPA Integration](guides/FreeIPA.md)
- [Performance Tuning](guides/Performance-Tuning.md)
- [Multi-Server Setup](guides/Multi-Server.md)
- [Backup Strategy](guides/Backup-Strategy.md)

### 🔒 Sécurité
- [Best Practices](configuration/Security-Best-Practices.md)
- [Credential Management](configuration/Credential-Management.md)
- [Access Control](configuration/Access-Control.md)
- [Audit Logs](configuration/Audit-Logs.md)
- [Compliance](configuration/Compliance.md)

### 🐛 Troubleshooting
- [FAQ](troubleshooting/FAQ.md)
- [Problèmes de Connexion](troubleshooting/Connection-Issues.md)
- [Problèmes de Performance](troubleshooting/Performance-Issues.md)
- [Erreurs Courantes](troubleshooting/Common-Errors.md)
- [Debugging](troubleshooting/Debugging.md)

### 📚 Référence CLI
- [Toutes les Commandes](reference/CLI-Commands.md)
- [Options Globales](reference/Global-Options.md)
- [Formats d'Export](reference/Export-Formats.md)
- [Codes de Retour](reference/Exit-Codes.md)

### 🌟 Exemples
- [Cas d'Usage Complets](examples/Use-Cases.md)
- [Scripts d'Automatisation](examples/Automation-Scripts.md)
- [Configurations Avancées](examples/Advanced-Configs.md)
- [Intégrations Personnalisées](examples/Custom-Integrations.md)

## 🎯 Par où commencer ?

### Utilisateur Débutant
1. [Installation](getting-started/Installation.md)
2. [Quick Start](getting-started/Quick-Start.md)
3. [Configuration de base](configuration/LDAP-Configuration.md)
4. [Premier audit](features/audit/Health-Check.md)

### Administrateur Système
1. [Configuration avancée](configuration/Config-File-Structure.md)
2. [Monitoring en production](guides/Production-Monitoring.md)
3. [Alertes et notifications](features/monitoring/Alerts-System.md)
4. [Backup strategy](guides/Backup-Strategy.md)

### Développeur
1. [Architecture](development/Architecture.md)
2. [Contribution](development/Contributing.md)
3. [Ajouter des fonctionnalités](development/Adding-Audit-Module.md)
4. [Tests](development/Testing.md)

## 📝 Conventions

- 📘 **Tutoriel** : Guide pas-à-pas pour débutants
- 🔧 **Guide technique** : Documentation détaillée
- 💡 **Exemple** : Code et configurations prêts à l'emploi
- ⚠️ **Attention** : Points importants à ne pas manquer
- 🔒 **Sécurité** : Considérations de sécurité

## 🔗 Liens Utiles

- [GitHub Repository](https://github.com/yourusername/ldap-health-monitor)
- [Report Issues](https://github.com/yourusername/ldap-health-monitor/issues)
- [Discussions](https://github.com/yourusername/ldap-health-monitor/discussions)

## 📖 Dernières Mises à Jour

- **v1.0.0** - Documentation initiale complète
- Ajout guides Active Directory et OpenLDAP
- Exemples d'intégration Prometheus/Grafana
- Guide de migration

---

💡 **Astuce** : Utilisez la recherche (Ctrl+F) pour trouver rapidement ce que vous cherchez !
