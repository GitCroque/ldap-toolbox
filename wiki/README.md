# 📚 LDAP Health Monitor - Documentation Wiki

Documentation complète et détaillée de LDAP Health Monitor.

## 🎯 À propos de ce Wiki

Ce wiki contient la documentation technique complète, des guides pratiques détaillés, et des exemples d'utilisation pour tous les aspects de LDAP Health Monitor.

**Pour un aperçu rapide**, consultez le [README principal](../README.md).

**Pour la documentation détaillée**, commencez par le [Wiki Home](Home.md).

## 📖 Structure de la Documentation

### 🚀 [Getting Started](getting-started/)
Guides de démarrage pour les nouveaux utilisateurs
- Installation détaillée (tous les OS)
- Configuration initiale pas-à-pas
- Premiers tests et validations

### ⚙️ [Configuration](configuration/)
Tous les aspects de la configuration
- Structure des fichiers de config
- Configuration LDAP (OpenLDAP, AD, FreeIPA)
- Personnalisation du schéma
- Variables d'environnement
- Sécurité et best practices

### 🔍 [Features - Audit](features/audit/)
Documentation complète des fonctionnalités d'audit
- Audit de santé
- Audit des utilisateurs (détails, exemples, troubleshooting)
- Audit des groupes
- Audit de structure
- Audit de sécurité
- Génération de rapports

### 📊 [Features - Monitoring](features/monitoring/)
Monitoring et surveillance en continu
- Collecte de métriques
- Système d'alertes (Slack, Email, Webhooks)
- Mode daemon
- Export Prometheus
- Historique et tendances

### 🛠️ [Features - Management](features/management/)
Gestion et opérations sur LDAP
- Gestion des utilisateurs
- Gestion des groupes
- Opérations de nettoyage
- Backup et restauration
- Exports de données
- Opérations en masse

### 🔌 [Integrations](integrations/)
Guides d'intégration avec d'autres outils
- Prometheus & Grafana
- Slack notifications
- Email alerting
- n8n automation
- Webhooks génériques
- CI/CD integration

### 👨‍💻 [Development](development/)
Documentation pour les contributeurs
- Architecture du code
- Structure des modules
- Ajouter des fonctionnalités
- Tests et couverture
- Style de code
- Guide de contribution

### 📖 [Guides Pratiques](guides/)
Guides spécifiques par cas d'usage
- **Active Directory** (configuration détaillée, spécificités AD)
- **OpenLDAP** (configuration, exemples)
- **FreeIPA** (intégration)
- Migration depuis d'autres outils
- Monitoring en production
- Déploiement Docker
- Performance tuning
- Multi-server setup
- Stratégies de backup

### 🐛 [Troubleshooting](troubleshooting/)
Résolution de problèmes
- **FAQ** (questions fréquentes avec réponses détaillées)
- Problèmes de connexion
- Problèmes de performance
- Erreurs courantes
- Guide de debugging

## 🗺️ Guides par Niveau

### Débutant
1. [Installation](getting-started/Installation.md) ⭐
2. [Configuration LDAP](configuration/LDAP-Configuration.md) ⭐
3. [FAQ](troubleshooting/FAQ.md) ⭐
4. Premier audit (coming soon)

### Intermédiaire
1. [Audit des Utilisateurs](features/audit/Users-Audit.md) ⭐
2. [Configuration avancée](configuration/Config-File-Structure.md)
3. [Monitoring](features/monitoring/Overview.md)
4. [Intégrations](integrations/Prometheus-Grafana.md)

### Avancé
1. [Active Directory Guide](guides/Active-Directory.md) ⭐
2. [Architecture](development/Architecture.md)
3. [Performance Tuning](guides/Performance-Tuning.md)
4. [Contribution](development/Contributing.md)

## 🌟 Pages Importantes

### Les Plus Consultées
- ⭐ [Installation Complète](getting-started/Installation.md)
- ⭐ [Configuration LDAP](configuration/LDAP-Configuration.md)
- ⭐ [Audit des Utilisateurs](features/audit/Users-Audit.md)
- ⭐ [Guide Active Directory](guides/Active-Directory.md)
- ⭐ [FAQ](troubleshooting/FAQ.md)

### Guides Spécifiques
- 🏢 [Active Directory](guides/Active-Directory.md) - Configuration et spécificités AD
- 🐧 [OpenLDAP](guides/OpenLDAP.md) - Configuration OpenLDAP
- 🔒 [Security Best Practices](configuration/Security-Best-Practices.md) - Sécurité
- 🚀 [Production Monitoring](guides/Production-Monitoring.md) - Déploiement prod

## 📝 Convention de Documentation

Dans ce wiki :
- **📘 Tutoriel** : Guide pas-à-pas pour débutants
- **🔧 Reference** : Documentation technique détaillée
- **💡 Example** : Code et configurations prêts à l'emploi
- **⚠️ Important** : Points cruciaux à ne pas manquer
- **🔒 Security** : Considérations de sécurité
- **⭐ Essentiel** : Pages les plus importantes

## 🔍 Navigation Rapide

**Par Type de Serveur :**
- [Active Directory](guides/Active-Directory.md)
- [OpenLDAP](guides/OpenLDAP.md)
- [FreeIPA](guides/FreeIPA.md)

**Par Fonctionnalité :**
- [Audit](features/audit/Overview.md)
- [Monitoring](features/monitoring/Overview.md)
- [Management](features/management/User-Management.md)

**Par Besoin :**
- "Je veux installer" → [Installation](getting-started/Installation.md)
- "Je veux configurer AD" → [Active Directory](guides/Active-Directory.md)
- "Je veux auditer mes users" → [Users Audit](features/audit/Users-Audit.md)
- "J'ai un problème" → [FAQ](troubleshooting/FAQ.md)
- "Je veux contribuer" → [Contributing](development/Contributing.md)

## 🆕 Dernières Mises à Jour

**Version 1.0.0** (Janvier 2025)
- ✅ Documentation complète
- ✅ Guide Active Directory détaillé
- ✅ Guide Audit des Utilisateurs
- ✅ FAQ complète
- ✅ Installation multi-OS
- 🔜 Guide OpenLDAP (en cours)
- 🔜 Guide FreeIPA (en cours)
- 🔜 Exemples d'automatisation (en cours)

## 💬 Contribuer à la Documentation

La documentation peut toujours être améliorée ! Voir [Contributing](development/Contributing.md).

**Comment contribuer :**
1. Fork le projet
2. Modifier/Ajouter des fichiers dans `wiki/`
3. Soumettre une Pull Request

**Ce dont on a besoin :**
- Plus d'exemples pratiques
- Guides pour d'autres serveurs LDAP
- Screenshots et diagrammes
- Corrections et clarifications
- Traductions

## 🔗 Liens Utiles

- [README Principal](../README.md) - Aperçu rapide
- [GitHub Repository](https://github.com/yourusername/ldap-health-monitor)
- [Report Issues](https://github.com/yourusername/ldap-health-monitor/issues)
- [Discussions](https://github.com/yourusername/ldap-health-monitor/discussions)

## 📧 Support

Besoin d'aide ?
- 📖 Consultez la [FAQ](troubleshooting/FAQ.md)
- 🐛 [Ouvrez une issue](https://github.com/yourusername/ldap-health-monitor/issues)
- 💬 [Posez une question](https://github.com/yourusername/ldap-health-monitor/discussions)

---

**Commencez maintenant :** [Wiki Home](Home.md) | [Installation](getting-started/Installation.md) | [Quick Start](getting-started/Quick-Start.md)
