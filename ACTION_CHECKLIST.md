# ✅ Checklist d'Actions - LDAP Toolbox

**Basé sur l'audit du 17 novembre 2025**

Cette checklist fournit des actions concrètes et priorisées pour améliorer le projet LDAP Toolbox.

---

## 🔴 CRITIQUE - À faire immédiatement

### 1. Corriger la validation TLS ⚠️

**Priorité** : CRITIQUE  
**Effort** : 1-2 heures  
**Impact** : Sécurité majeure

- [ ] Ajouter le paramètre `tls_validate` dans `LDAPConfig`
- [ ] Ajouter le paramètre `ca_bundle_path` dans `LDAPConfig`
- [ ] Modifier `src/core/connector.py` ligne 40
- [ ] Mettre à jour `config.example.yaml`
- [ ] Ajouter documentation sur la validation TLS
- [ ] Tester avec certificats valides et invalides

**Code à modifier** :

```python
# src/core/models.py
class LDAPConfig(BaseModel):
    # ... existing fields ...
    tls_validate: bool = True
    ca_bundle_path: Optional[str] = None
```

```python
# src/core/connector.py
if self.config.use_tls:
    tls_config = Tls(
        validate=ssl.CERT_REQUIRED if self.config.tls_validate else ssl.CERT_NONE,
        ca_certs_file=self.config.ca_bundle_path if self.config.ca_bundle_path else None
    )
```

---

## 🟠 HAUTE PRIORITÉ - Dans les 2 semaines

### 2. Tests du connecteur LDAP

**Priorité** : HAUTE  
**Effort** : 3-5 jours  
**Impact** : Fiabilité critique

- [ ] Créer `tests/unit/test_connector.py`
- [ ] Test de connexion réussie
- [ ] Test de connexion échouée
- [ ] Test du retry logic (3 tentatives)
- [ ] Test de recherche simple
- [ ] Test de recherche paginée
- [ ] Test de récupération d'entrée unique
- [ ] Test d'ajout d'entrée
- [ ] Test de modification d'entrée
- [ ] Test de suppression d'entrée
- [ ] Test du context manager
- [ ] Test de test_connection()
- [ ] Test de get_server_info()
- [ ] Vérifier coverage > 80% pour connector.py

### 3. Tests des auditors

**Priorité** : HAUTE  
**Effort** : 1 semaine  
**Impact** : Qualité des audits

#### HealthChecker
- [ ] Créer `tests/unit/test_health.py`
- [ ] Test de check_health() avec serveur sain
- [ ] Test avec temps de réponse élevé
- [ ] Test avec serveur inaccessible
- [ ] Test de vérification certificat SSL
- [ ] Test de récupération des statistiques

#### UserAuditor
- [ ] Créer `tests/unit/test_users.py`
- [ ] Test de détection d'attributs manquants
- [ ] Test de détection de doublons email
- [ ] Test de détection de doublons UID
- [ ] Test de détection de comptes inactifs
- [ ] Test de détection de comptes désactivés

#### GroupAuditor
- [ ] Créer `tests/unit/test_groups.py`
- [ ] Test de détection de groupes vides
- [ ] Test de détection de groupes trop grands
- [ ] Test de validation des membres

### 4. Tests de backup

**Priorité** : HAUTE  
**Effort** : 2-3 jours  
**Impact** : Intégrité des données

- [ ] Créer `tests/unit/test_backup.py`
- [ ] Test de backup_full() format LDIF
- [ ] Test de backup_full() format JSON
- [ ] Test de backup_full() format YAML
- [ ] Test de compression
- [ ] Test d'export_users() format CSV
- [ ] Test d'export_users() format JSON
- [ ] Test de gestion des erreurs

### 5. Configuration CI/CD

**Priorité** : HAUTE  
**Effort** : 1 jour  
**Impact** : Automatisation

- [ ] Créer `.github/workflows/test.yml`
- [ ] Tests automatiques sur push
- [ ] Tests sur multiple versions Python (3.10, 3.11, 3.12)
- [ ] Génération du rapport de coverage
- [ ] Upload du coverage sur Codecov
- [ ] Créer `.github/workflows/lint.yml`
- [ ] Linting automatique (black, ruff, mypy)
- [ ] Créer badge de status dans README

**Fichier à créer** :

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest --cov=src --cov-report=xml
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## 🟡 MOYENNE PRIORITÉ - Dans le mois

### 6. Compléter la documentation technique

**Priorité** : MOYENNE  
**Effort** : 1-2 jours  
**Impact** : Adoption utilisateur

- [ ] Créer `docs/security.md`
  - Bonnes pratiques de sécurité
  - Configuration TLS/SSL
  - Gestion des credentials
  - Permissions LDAP recommandées
  - Audit trail

- [ ] Créer `docs/audit-guide.md`
  - Types d'audits disponibles
  - Interprétation des résultats
  - Exemples concrets
  - Résolution des problèmes courants

- [ ] Créer `docs/monitoring-guide.md`
  - Configuration du monitoring
  - Métriques disponibles
  - Configuration des alertes
  - Intégration Prometheus/Grafana

- [ ] Créer `docs/management-guide.md`
  - Gestion des utilisateurs
  - Gestion des groupes
  - Opérations en masse
  - Backup et restore

### 7. Mettre à jour les URLs

**Priorité** : MOYENNE  
**Effort** : 30 minutes  
**Impact** : Professionnalisme

- [ ] Remplacer `yourusername` dans README.md
- [ ] Remplacer `yourusername` dans pyproject.toml
- [ ] Remplacer `yourusername` dans docs/*.md
- [ ] Vérifier tous les liens
- [ ] Tester les liens

### 8. Publier sur PyPI

**Priorité** : MOYENNE  
**Effort** : 4 heures  
**Impact** : Distribution

- [ ] Créer compte PyPI
- [ ] Configurer token API PyPI
- [ ] Tester build local : `python -m build`
- [ ] Tester installation locale
- [ ] Publier test version sur TestPyPI
- [ ] Vérifier installation depuis TestPyPI
- [ ] Publier version finale sur PyPI
- [ ] Mettre à jour README avec instructions pip
- [ ] Créer badge PyPI dans README

### 9. Créer Dockerfile

**Priorité** : MOYENNE  
**Effort** : 4 heures  
**Impact** : Déploiement

- [ ] Créer `Dockerfile`
- [ ] Utiliser image Python slim
- [ ] Optimiser les layers
- [ ] Créer `.dockerignore`
- [ ] Tester build local
- [ ] Tester exécution
- [ ] Créer docker-compose.example.yml
- [ ] Documenter utilisation Docker
- [ ] Publier sur Docker Hub (optionnel)

**Fichier à créer** :

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .
RUN pip install --no-cache-dir .

# Create directories
RUN mkdir -p /app/logs /app/backups /app/reports

# Set entrypoint
ENTRYPOINT ["ldap-monitor"]
CMD ["--help"]
```

### 10. Créer Makefile

**Priorité** : MOYENNE  
**Effort** : 2 heures  
**Impact** : Productivité développeur

- [ ] Créer `Makefile`
- [ ] Target `install` - Installation dev
- [ ] Target `test` - Lancer tests
- [ ] Target `coverage` - Rapport coverage HTML
- [ ] Target `lint` - Linting (ruff, mypy)
- [ ] Target `format` - Formatage (black)
- [ ] Target `clean` - Nettoyage
- [ ] Target `build` - Build package
- [ ] Target `docker-build` - Build Docker
- [ ] Target `docker-test` - Tests dans Docker
- [ ] Documenter dans README

**Fichier à créer** :

```makefile
.PHONY: help install test coverage lint format clean build

help:
	@echo "Commandes disponibles:"
	@echo "  make install    - Installer les dépendances"
	@echo "  make test       - Lancer les tests"
	@echo "  make coverage   - Rapport de coverage"
	@echo "  make lint       - Linting"
	@echo "  make format     - Formatage du code"
	@echo "  make clean      - Nettoyage"
	@echo "  make build      - Build du package"

install:
	pip install -e ".[dev]"
	pre-commit install

test:
	pytest --cov=src --cov-report=term-missing

coverage:
	pytest --cov=src --cov-report=html
	open htmlcov/index.html

lint:
	ruff check src/ tests/
	mypy src/

format:
	black src/ tests/
	ruff check --fix src/ tests/

clean:
	rm -rf build/ dist/ *.egg-info
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

build:
	python -m build
```

---

## 🟢 BASSE PRIORITÉ - Quand possible

### 11. Ajouter diagrammes d'architecture

**Priorité** : BASSE  
**Effort** : 1-2 jours  
**Impact** : Compréhension

- [ ] Installer mermaid-cli ou autre
- [ ] Créer diagramme architecture globale
- [ ] Créer diagramme flux d'audit
- [ ] Créer diagramme flux de monitoring
- [ ] Créer diagramme flux de backup
- [ ] Intégrer dans README.md
- [ ] Intégrer dans docs/

### 12. Mettre à jour Ruff

**Priorité** : BASSE  
**Effort** : 30 minutes  
**Impact** : Outils modernes

- [ ] Mettre à jour dans requirements.txt : `ruff>=0.8.0`
- [ ] Mettre à jour dans pyproject.toml : `ruff>=0.8.0`
- [ ] Tester linting
- [ ] Corriger éventuelles nouvelles erreurs
- [ ] Commit

### 13. Activer rate limiting par défaut

**Priorité** : BASSE  
**Effort** : 15 minutes  
**Impact** : Sécurité légère

- [ ] Modifier `config.example.yaml` : `rate_limit_enabled: true`
- [ ] Documenter le rate limiting
- [ ] Tester le rate limiting

### 14. Remplir le dossier utils/

**Priorité** : BASSE  
**Effort** : Variable  
**Impact** : Organisation

- [ ] Identifier fonctions utilitaires communes
- [ ] Créer modules appropriés (ex: formatters.py, validators.py)
- [ ] Déplacer code dupliqué
- [ ] Documenter les utilitaires

### 15. Tests d'intégration

**Priorité** : BASSE (après tests unitaires)  
**Effort** : 1 semaine  
**Impact** : Qualité globale

- [ ] Créer `tests/integration/`
- [ ] Utiliser docker-compose pour serveur LDAP de test
- [ ] Test end-to-end audit complet
- [ ] Test end-to-end backup/restore
- [ ] Test end-to-end monitoring
- [ ] Script de setup pour CI

### 16. Configuration Dependabot

**Priorité** : BASSE  
**Effort** : 1 heure  
**Impact** : Maintenance

- [ ] Créer `.github/dependabot.yml`
- [ ] Activer mises à jour pip
- [ ] Activer mises à jour GitHub Actions
- [ ] Configurer fréquence hebdomadaire
- [ ] Tester première PR Dependabot

### 17. Pre-commit hooks

**Priorité** : BASSE  
**Effort** : 2 heures  
**Impact** : Qualité

- [ ] Créer `.pre-commit-config.yaml`
- [ ] Hook black
- [ ] Hook ruff
- [ ] Hook mypy
- [ ] Hook trailing-whitespace
- [ ] Hook end-of-file-fixer
- [ ] Hook check-yaml
- [ ] Documenter dans CONTRIBUTING.md

---

## 📊 Progression globale

**Calculer le pourcentage d'actions complétées** :

```
Total tâches : ___
Complétées : ___
Progression : ____%
```

### Par priorité

- 🔴 Critique : ___ / 6 (___%)
- 🟠 Haute : ___ / 52 (___%)
- 🟡 Moyenne : ___ / 36 (___%)
- 🟢 Basse : ___ / 51 (___%)

---

## 🎯 Milestones suggérés

### Milestone 1 : Sécurité ✅
**Deadline** : J+7  
**Tâches critiques complétées**

- [x] TLS validé
- [x] Rate limiting activé
- [x] Documentation sécurité

### Milestone 2 : Tests unitaires ✅
**Deadline** : J+21  
**60% de coverage atteint**

- [x] Tests connecteur
- [x] Tests auditors
- [x] Tests backup
- [x] CI/CD configuré

### Milestone 3 : Documentation ✅
**Deadline** : J+28  
**Documentation complète**

- [x] Tous les guides créés
- [x] URLs mises à jour
- [x] Diagrammes ajoutés

### Milestone 4 : Publication ✅
**Deadline** : J+35  
**Package disponible publiquement**

- [x] PyPI publié
- [x] Dockerfile créé
- [x] Makefile créé

### Milestone 5 : Production Ready ✅
**Deadline** : J+42  
**Version 1.1 stable**

- [x] Tous les critiques corrigés
- [x] 80% coverage atteint
- [x] Documentation complète
- [x] CI/CD opérationnel

---

## 📝 Notes

### Estimation totale

**Temps de développement** : 5-6 semaines à temps plein

**Répartition** :
- Sécurité : 1 semaine
- Tests : 2-3 semaines
- Documentation : 1 semaine
- Publication : 1 semaine

### Ressources nécessaires

- 1 développeur Python expérimenté
- Accès à un serveur LDAP de test
- Compte PyPI
- Compte Docker Hub (optionnel)

### Risques

- ⚠️ Tests d'intégration peuvent révéler bugs cachés
- ⚠️ Compatibilité avec différents serveurs LDAP
- ⚠️ Performance avec grandes bases LDAP

---

**Dernière mise à jour** : 17 novembre 2025  
**Version** : 1.0

*Checklist basée sur AUDIT_REPORT.md*

