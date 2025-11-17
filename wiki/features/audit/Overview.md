# Vue d'ensemble des fonctionnalités d'audit

## Introduction

Le module d'audit LDAP Health Monitor fournit un ensemble complet d'outils pour analyser, évaluer et surveiller la santé de votre annuaire LDAP. Cette documentation présente une vue d'ensemble de toutes les fonctionnalités d'audit disponibles.

## Table des matières

1. [Types d'audits disponibles](#types-daudits-disponibles)
2. [Comment fonctionnent les audits](#comment-fonctionnent-les-audits)
3. [Formats de sortie](#formats-de-sortie)
4. [Niveaux d'alerte](#niveaux-dalerte)
5. [Scoring et évaluation](#scoring-et-évaluation)
6. [Exemples d'utilisation](#exemples-dutilisation)
7. [Architecture des audits](#architecture-des-audits)
8. [Bonnes pratiques](#bonnes-pratiques)

## Types d'audits disponibles

### 1. Audit de santé (Health Check)

Vérifie l'état général du serveur LDAP :
- Connectivité au serveur
- Temps de réponse
- Validité des certificats SSL/TLS
- Statistiques générales de l'annuaire

**Commande CLI :**
```bash
ldap-health-monitor audit health
```

**Cas d'usage :**
- Vérification quotidienne de la disponibilité
- Monitoring des performances
- Validation des certificats avant expiration
- Diagnostic rapide en cas d'incident

### 2. Audit des utilisateurs (Users Audit)

Analyse les comptes utilisateurs pour détecter :
- Comptes inactifs depuis longtemps
- Attributs obligatoires manquants
- Adresses email en double
- UIDs en double
- Comptes désactivés non nettoyés

**Commande CLI :**
```bash
ldap-health-monitor audit users
ldap-health-monitor audit users --inactive
ldap-health-monitor audit users --missing-attributes
```

**Cas d'usage :**
- Nettoyage des comptes obsolètes
- Conformité RGPD
- Validation de l'intégrité des données
- Préparation des audits de sécurité

### 3. Audit des groupes (Groups Audit)

Examine la structure et le contenu des groupes :
- Groupes vides sans membres
- Groupes trop volumineux
- Membres orphelins (références vers des entrées inexistantes)
- Membres en double dans un même groupe
- Groupes imbriqués

**Commande CLI :**
```bash
ldap-health-monitor audit groups
ldap-health-monitor audit groups --empty
ldap-health-monitor audit groups --large
```

**Cas d'usage :**
- Optimisation de la structure des groupes
- Nettoyage des références obsolètes
- Amélioration des performances
- Maintenance préventive

### 4. Audit de structure (Structure Audit)

Analyse l'organisation hiérarchique de l'annuaire :
- Unités organisationnelles vides
- Conventions de nommage
- Profondeur de la hiérarchie
- Organisation logique des entrées

**Commande CLI :**
```bash
ldap-health-monitor audit structure
```

**Cas d'usage :**
- Réorganisation de l'annuaire
- Standardisation de la structure
- Planification de la migration
- Documentation de l'architecture

### 5. Audit de sécurité (Security Audit)

Évalue les aspects de sécurité :
- Politiques de mots de passe
- Comptes privilégiés
- Configuration SSL/TLS
- Permissions et ACLs
- Politiques de verrouillage de compte

**Commande CLI :**
```bash
ldap-health-monitor audit security
```

**Cas d'usage :**
- Audits de sécurité réglementaires
- Renforcement de la sécurité
- Conformité aux politiques internes
- Détection des vulnérabilités

### 6. Audit de cohérence (Consistency Audit)

Vérifie l'intégrité et la cohérence des données :
- Entrées en double
- Références manquantes ou brisées
- Intégrité référentielle
- Cohérence des attributs multi-valués

**Commande CLI :**
```bash
ldap-health-monitor audit consistency
```

**Cas d'usage :**
- Validation après migration
- Nettoyage périodique
- Détection de corruptions
- Assurance qualité des données

### 7. Audit complet (Full Audit)

Execute tous les audits en une seule commande :
```bash
ldap-health-monitor audit all
```

## Comment fonctionnent les audits

### Processus d'audit

1. **Connexion au serveur LDAP**
   ```
   Configuration → Connexion → Authentification
   ```

2. **Collecte des données**
   ```
   Lecture des entrées → Extraction des attributs → Mise en cache
   ```

3. **Analyse et détection**
   ```
   Application des règles → Détection des anomalies → Scoring
   ```

4. **Génération du rapport**
   ```
   Agrégation des résultats → Formatage → Export
   ```

### Architecture technique

```
┌─────────────────────┐
│   CLI Interface     │
└──────────┬──────────┘
           │
┌──────────▼──────────┐
│  Audit Orchestrator │
└──────────┬──────────┘
           │
     ┌─────┴─────┐
     │           │
┌────▼────┐ ┌───▼─────┐
│ Auditors│ │Reporters│
└─────────┘ └─────────┘
```

### Configuration des audits

Les audits utilisent le fichier de configuration pour définir :
- Les seuils d'alerte
- Les attributs obligatoires
- Les règles de validation
- Les politiques de sécurité

**Exemple de configuration :**
```yaml
audit:
  # Attributs obligatoires pour les utilisateurs
  required_user_attributes:
    - mail
    - givenName
    - sn
    - telephoneNumber

  # Seuils d'alerte
  thresholds:
    # Temps de réponse
    response_time_warning_ms: 500
    response_time_critical_ms: 2000

    # Certificats SSL
    ssl_cert_expiry_warning_days: 30

    # Utilisateurs inactifs
    inactive_days: 90

    # Groupes
    max_empty_groups: 5
    max_group_size: 100

  # Configuration de sécurité
  security:
    check_privileged_accounts: true
    privileged_groups:
      - "cn=Domain Admins,ou=Groups,dc=example,dc=com"
      - "cn=Enterprise Admins,ou=Groups,dc=example,dc=com"
```

## Formats de sortie

### Console (par défaut)

Affichage formaté dans le terminal avec couleurs et icônes :

```bash
ldap-health-monitor audit health
```

**Sortie :**
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

### JSON

Export structuré pour traitement automatisé :

```bash
ldap-health-monitor audit all --format json --output rapport.json
```

**Exemple de sortie :**
```json
{
  "timestamp": "2025-11-17T10:30:45.123456",
  "score": 85,
  "health": {
    "status": "healthy",
    "response_time": 127.5,
    "message": "LDAP server is healthy",
    "details": {
      "response_time_ms": 127.5,
      "server_info": {
        "vendor": "OpenLDAP",
        "version": "2.4.57"
      },
      "statistics": {
        "users_total": 1234,
        "groups_total": 156,
        "ous_total": 23
      }
    }
  },
  "issues": [
    {
      "level": "warning",
      "category": "groups",
      "title": "12 empty groups",
      "description": "Found 12 groups with no members",
      "recommendation": "Remove unused empty groups",
      "details": {
        "count": 12,
        "sample": [
          "cn=OldProject,ou=Groups,dc=example,dc=com",
          "cn=Temp,ou=Groups,dc=example,dc=com"
        ]
      }
    }
  ],
  "recommendations": [
    "Remove unused empty groups",
    "Review and clean up disabled accounts",
    "Consider setting up regular health monitoring"
  ]
}
```

### HTML

Rapport visuel pour documentation et présentation :

```bash
ldap-health-monitor audit all --format html --output rapport.html
```

Le rapport HTML inclut :
- En-tête avec métadonnées
- Score global coloré
- Tableau des problèmes avec code couleur
- Statistiques visuelles
- Liste des recommandations
- CSS embarqué pour mise en forme

### CSV

Export tabulaire pour analyse dans Excel/LibreOffice :

```bash
ldap-health-monitor audit users --format csv --output users.csv
```

**Exemple :**
```csv
level,category,title,description,recommendation
warning,users,45 users missing required attributes,Found 45 users with missing attributes,Complete user profiles
critical,users,3 duplicate email addresses,Found 3 emails used by multiple users,Ensure email addresses are unique
```

## Niveaux d'alerte

Les audits classifient les problèmes en trois niveaux :

### INFO (ℹ️)

**Gravité :** Faible
**Action :** Informative, pas d'action urgente requise
**Exemples :**
- Groupes volumineux (> 100 membres)
- Nombre de comptes désactivés
- Statistiques générales

**Exemple de message :**
```
ℹ️  156 large groups
   Found 156 groups with more than 100 members
   💡 Consider splitting large groups for better management
```

### WARNING (⚠️)

**Gravité :** Moyenne
**Action :** Correction recommandée à court terme
**Exemples :**
- Groupes vides
- Certificat SSL expirant bientôt
- Temps de réponse élevé
- Attributs manquants
- Membres orphelins

**Exemple de message :**
```
⚠️  High response time
   Server response time is 1523ms (warning threshold: 500ms)
   💡 Monitor server performance
```

### CRITICAL (🔴)

**Gravité :** Élevée
**Action :** Correction immédiate requise
**Exemples :**
- Serveur inaccessible
- Certificat SSL expiré
- Temps de réponse critique
- Emails en double
- UIDs en double

**Exemple de message :**
```
🔴 SSL certificate expired
   Certificate expired 5 days ago
   💡 Renew SSL certificate immediately
```

## Scoring et évaluation

### Calcul du score

Le score global est calculé sur 100 points :

```
Score = 100 - (nombre_problèmes × poids)
```

**Poids par niveau :**
- INFO : -1 point
- WARNING : -5 points
- CRITICAL : -10 points

**Exemple :**
```
Problèmes détectés :
- 3 × INFO = -3 points
- 5 × WARNING = -25 points
- 1 × CRITICAL = -10 points

Score final = 100 - 38 = 62/100
```

### Interprétation du score

| Score | Statut | Signification |
|-------|--------|---------------|
| 90-100 | Excellent | Annuaire en très bon état |
| 75-89 | Bon | Quelques améliorations possibles |
| 60-74 | Moyen | Nécessite attention et corrections |
| 40-59 | Faible | Problèmes importants à résoudre |
| 0-39 | Critique | Action immédiate requise |

**Exemple de rapport avec score :**
```bash
📊 Audit Report - 2025-11-17 10:30:45
Score: 62/100

⚠️ Status: Moyen - Nécessite attention
```

## Exemples d'utilisation

### Audit quotidien rapide

Vérification de la santé du serveur :

```bash
# Test simple de connectivité
ldap-health-monitor test connection

# Audit de santé complet
ldap-health-monitor audit health

# Avec export JSON pour historique
ldap-health-monitor audit health --format json --output "health-$(date +%Y%m%d).json"
```

### Audit hebdomadaire complet

```bash
# Exécution de tous les audits
ldap-health-monitor audit all --format html --output rapport-hebdo.html

# Génération de rapports multiples
ldap-health-monitor audit all --format json --output rapport.json
ldap-health-monitor audit all --format html --output rapport.html
```

### Audit spécifique avant maintenance

```bash
# Avant nettoyage des groupes
ldap-health-monitor audit groups --empty

# Avant suppression des comptes inactifs
ldap-health-monitor audit users --inactive

# Vérification de la structure avant réorganisation
ldap-health-monitor audit structure
```

### Audit de sécurité mensuel

```bash
# Audit de sécurité complet
ldap-health-monitor audit security

# Vérification des certificats
ldap-health-monitor audit health | grep -i ssl

# Audit des comptes privilégiés
ldap-health-monitor group members "cn=Domain Admins,ou=Groups,dc=example,dc=com"
```

### Automatisation avec cron

**Script d'audit quotidien :**
```bash
#!/bin/bash
# /usr/local/bin/ldap-daily-audit.sh

DATE=$(date +%Y%m%d)
OUTPUT_DIR="/var/log/ldap-audits"
CONFIG="/etc/ldap-health-monitor/config.yaml"

mkdir -p "$OUTPUT_DIR"

# Audit de santé
ldap-health-monitor -c "$CONFIG" audit health \
  --format json \
  --output "$OUTPUT_DIR/health-$DATE.json"

# Audit complet hebdomadaire (lundi)
if [ $(date +%u) -eq 1 ]; then
  ldap-health-monitor -c "$CONFIG" audit all \
    --format html \
    --output "$OUTPUT_DIR/full-audit-$DATE.html"
fi

# Notification si score < 70
SCORE=$(jq -r '.score' "$OUTPUT_DIR/health-$DATE.json")
if [ "$SCORE" -lt 70 ]; then
  echo "LDAP Audit Score: $SCORE" | mail -s "LDAP Health Alert" admin@example.com
fi
```

**Configuration crontab :**
```cron
# Audit quotidien à 6h du matin
0 6 * * * /usr/local/bin/ldap-daily-audit.sh

# Audit de sécurité le 1er de chaque mois
0 8 1 * * ldap-health-monitor -c /etc/config.yaml audit security --format html --output /var/reports/security-$(date +%Y%m).html
```

## Architecture des audits

### Composants principaux

#### 1. Auditeurs (Auditors)

Chaque auditeur est responsable d'un type d'analyse :

```python
# Structure d'un auditeur
class ExampleAuditor:
    def __init__(self, connector, config):
        self.connector = connector
        self.config = config

    def audit(self) -> List[AuditIssue]:
        issues = []
        # Logique d'audit
        return issues
```

**Auditeurs disponibles :**
- `HealthChecker` - Santé du serveur
- `UserAuditor` - Audit des utilisateurs
- `GroupAuditor` - Audit des groupes
- `StructureAuditor` - Audit de la structure
- `SecurityAuditor` - Audit de sécurité
- `ConsistencyAuditor` - Audit de cohérence

#### 2. Connecteur LDAP

Gère la communication avec le serveur :

```python
connector = LDAPConnector(config.ldap)
# Recherche
entries = connector.search(search_base, search_filter)
# Récupération d'entrée
entry = connector.get_entry(dn)
# Test de connexion
success, time, error = connector.test_connection()
```

#### 3. Reporters

Formatent et exportent les résultats :

```python
# Console
ConsoleReporter().report_audit(report)

# JSON
JSONReporter().export_audit(report, "output.json")

# HTML
HTMLReporter().export_audit(report, "output.html")

# CSV
CSVReporter().export_data(data, "output.csv")
```

### Flux de données

```
┌──────────┐
│  Config  │
└────┬─────┘
     │
     ▼
┌──────────────┐      ┌──────────────┐
│  Connector   │─────▶│ LDAP Server  │
└──────┬───────┘      └──────────────┘
       │
       ▼
┌──────────────┐
│   Auditor    │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ AuditIssue[] │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ AuditReport  │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Reporter   │
└──────┬───────┘
       │
       ▼
┌──────────────┐
│   Output     │
└──────────────┘
```

## Bonnes pratiques

### Fréquence des audits

**Quotidien :**
- Audit de santé (health)
- Monitoring des performances

**Hebdomadaire :**
- Audit des utilisateurs
- Audit des groupes
- Audit complet

**Mensuel :**
- Audit de sécurité
- Audit de structure
- Audit de cohérence
- Révision complète

**Trimestriel :**
- Audit approfondi avec analyse détaillée
- Optimisation de la configuration
- Planification des améliorations

### Conservation des rapports

```bash
# Structure recommandée
/var/log/ldap-audits/
├── daily/
│   ├── 2025-11-17-health.json
│   ├── 2025-11-18-health.json
│   └── ...
├── weekly/
│   ├── 2025-W47-full.html
│   └── ...
├── monthly/
│   ├── 2025-11-security.html
│   └── ...
└── archive/
    └── 2024/
```

### Interprétation des résultats

1. **Prioriser par niveau**
   - Traiter d'abord les CRITICAL
   - Planifier les WARNING
   - Noter les INFO pour amélioration continue

2. **Analyser les tendances**
   - Comparer les scores dans le temps
   - Identifier les problèmes récurrents
   - Mesurer l'impact des corrections

3. **Contextualiser**
   - Certains problèmes peuvent être normaux
   - Adapter les seuils à votre environnement
   - Documenter les exceptions connues

### Personnalisation des seuils

Ajustez les seuils selon votre environnement :

```yaml
audit:
  thresholds:
    # Pour un réseau local rapide
    response_time_warning_ms: 100
    response_time_critical_ms: 500

    # Pour grande organisation
    max_group_size: 500
    max_empty_groups: 20

    # Pour conformité stricte
    inactive_days: 30
    ssl_cert_expiry_warning_days: 60
```

### Intégration avec monitoring

```bash
# Export Prometheus
ldap-health-monitor monitor prometheus --port 9090

# Métriques disponibles :
# - ldap_health_status
# - ldap_response_time_ms
# - ldap_users_total
# - ldap_groups_total
# - ldap_audit_issues_total
```

### Documentation des exceptions

Créez un fichier de suivi :

```yaml
# exceptions.yaml
known_issues:
  - type: empty_group
    dn: "cn=FutureProject,ou=Groups,dc=example,dc=com"
    reason: "Groupe créé pour projet Q1 2026"
    expires: "2026-01-01"

  - type: large_group
    dn: "cn=AllEmployees,ou=Groups,dc=example,dc=com"
    reason: "Groupe global intentionnellement large"
    permanent: true
```

## Dépannage

### Problèmes courants

**Connexion échouée :**
```bash
# Tester la connectivité
ldap-health-monitor test connection

# Vérifier la configuration
ldap-health-monitor config validate
```

**Performance lente :**
```bash
# Limiter la portée
ldap-health-monitor audit users --limit 100

# Ajuster les timeouts dans config.yaml
ldap:
  timeout: 60
```

**Erreurs de certificats :**
```bash
# Désactiver temporairement la vérification SSL (dev uniquement)
ldap:
  use_ssl: true
  verify_cert: false
```

## Ressources supplémentaires

- [Health Check](./Health-Check.md) - Documentation détaillée de l'audit de santé
- [Groups Audit](./Groups-Audit.md) - Audit approfondi des groupes
- [Security Audit](./Security-Audit.md) - Audit de sécurité complet
- [Audit Reports](./Audit-Reports.md) - Guide des rapports et exports

## Conclusion

Les fonctionnalités d'audit LDAP Health Monitor fournissent une suite complète d'outils pour maintenir un annuaire LDAP sain, performant et sécurisé. En combinant des audits réguliers avec une analyse attentive des résultats, vous pouvez prévenir les problèmes avant qu'ils n'impactent vos utilisateurs et maintenir un haut niveau de qualité de service.
