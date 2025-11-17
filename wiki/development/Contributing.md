# Guide de Contribution

## Bienvenue!

Merci de votre intérêt pour contribuer au LDAP Health Monitor! Ce guide vous aidera à démarrer et à comprendre notre processus de contribution.

## Table des Matières

1. [Code de Conduite](#code-de-conduite)
2. [Comment Contribuer](#comment-contribuer)
3. [Configuration de l'Environnement](#configuration-de-lenvironnement)
4. [Workflow Git](#workflow-git)
5. [Standards de Code](#standards-de-code)
6. [Processus de Review](#processus-de-review)
7. [Types de Contributions](#types-de-contributions)

## Code de Conduite

### Nos Engagements

- Respecter tous les contributeurs
- Accueillir les nouvelles idées
- Fournir des feedbacks constructifs
- Favoriser un environnement inclusif et bienveillant

### Comportements Attendus

**Faire:**
- Utiliser un langage accueillant et inclusif
- Respecter les points de vue différents
- Accepter les critiques constructives
- Montrer de l'empathie envers les autres

**Ne pas faire:**
- Utiliser un langage sexualisé ou des images inappropriées
- Troller, insulter ou faire des commentaires désobligeants
- Harceler publiquement ou en privé
- Publier des informations privées sans permission

## Comment Contribuer

### 1. Trouver une Tâche

**Issues Existantes:**
- Parcourir les [issues GitHub](https://github.com/your-repo/issues)
- Chercher les labels `good-first-issue` ou `help-wanted`
- Commenter l'issue pour indiquer que vous y travaillez

**Nouvelles Fonctionnalités:**
- Créer une issue décrivant la fonctionnalité
- Attendre feedback avant de commencer
- Discuter de l'approche avec les mainteneurs

**Bugs:**
- Créer une issue avec reproduction détaillée
- Inclure logs, configuration, environnement
- Proposer un fix si possible

### 2. Types de Contributions Bienvenues

#### Code

- Nouvelles fonctionnalités
- Corrections de bugs
- Optimisations de performance
- Amélioration de tests
- Refactoring

#### Documentation

- Corrections de typos
- Clarification de guides
- Nouveaux exemples
- Traductions
- Améliorations de README

#### Tests

- Nouveaux tests unitaires
- Tests d'intégration
- Amélioration de la couverture
- Tests de performance

#### Design

- Amélioration de l'UI/UX
- Graphiques et visualisations
- Rapports plus lisibles

## Configuration de l'Environnement

### Prérequis

- Python 3.9 ou supérieur
- Git
- Un éditeur de code (VS Code, PyCharm recommandés)

### Installation

```bash
# 1. Fork le repository sur GitHub

# 2. Cloner votre fork
git clone https://github.com/YOUR-USERNAME/ldap-toolbox.git
cd ldap-toolbox

# 3. Ajouter le repository upstream
git remote add upstream https://github.com/original-owner/ldap-toolbox.git

# 4. Créer un environnement virtuel
python -m venv venv

# Activer l'environnement
# Sur Linux/Mac:
source venv/bin/activate
# Sur Windows:
venv\Scripts\activate

# 5. Installer les dépendances de développement
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 6. Installer en mode développement
pip install -e .

# 7. Installer les hooks pre-commit
pre-commit install
```

### Vérifier l'Installation

```bash
# Exécuter les tests
pytest

# Vérifier le linting
black --check src/
flake8 src/
mypy src/

# Tester la CLI
ldap-monitor --help
```

## Workflow Git

### Branches

**Structure des branches:**
- `main` - Production, stable
- `develop` - Développement actif
- `feature/*` - Nouvelles fonctionnalités
- `bugfix/*` - Corrections de bugs
- `hotfix/*` - Corrections urgentes
- `docs/*` - Documentation

### Workflow Standard

#### 1. Créer une Branche

```bash
# Mettre à jour main
git checkout main
git pull upstream main

# Créer une branche depuis main
git checkout -b feature/add-permission-audit

# Ou pour un bugfix
git checkout -b bugfix/fix-connection-timeout
```

**Nommage des branches:**
- `feature/description-courte` - Nouvelles fonctionnalités
- `bugfix/description-bug` - Corrections de bugs
- `docs/sujet` - Documentation
- `refactor/module-name` - Refactoring
- `test/what-to-test` - Tests

#### 2. Développer

```bash
# Faire vos modifications
# ...

# Ajouter les fichiers modifiés
git add src/audit/permissions.py
git add tests/unit/test_permissions.py

# Commit avec message descriptif
git commit -m "feat: Add permissions audit module

- Implement PermissionsAuditor class
- Add ACL checking
- Add admin rights verification
- Add comprehensive tests
- Update documentation

Closes #123"
```

#### 3. Garder la Branche à Jour

```bash
# Récupérer les dernières modifications
git fetch upstream

# Rebaser sur main
git rebase upstream/main

# Résoudre les conflits si nécessaire
# Puis:
git rebase --continue
```

#### 4. Pousser les Modifications

```bash
# Première fois
git push -u origin feature/add-permission-audit

# Pushs suivants
git push

# Après un rebase (force push)
git push --force-with-lease
```

### Messages de Commit

#### Format des Commits (Conventional Commits)

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: Nouvelle fonctionnalité
- `fix`: Correction de bug
- `docs`: Documentation
- `style`: Formatage, missing semicolons, etc.
- `refactor`: Refactoring de code
- `test`: Ajout ou modification de tests
- `chore`: Maintenance (dependencies, config, etc.)
- `perf`: Amélioration de performance

**Exemples:**

```bash
# Feature
git commit -m "feat(audit): add permissions auditor

Implement comprehensive permissions and ACL auditing.
Includes checks for:
- Overly permissive ACLs
- Admin account monitoring
- Write permissions verification

Closes #123"

# Bugfix
git commit -m "fix(connector): handle connection timeout correctly

Previously, connection timeouts were not properly caught,
causing the application to crash.

Now timeouts are caught and converted to AuditIssue with
appropriate error message.

Fixes #456"

# Documentation
git commit -m "docs: add permissions audit guide

Add comprehensive guide for creating new audit modules
using the permissions auditor as example.

Includes:
- Step-by-step implementation
- Testing strategies
- Integration with CLI"

# Refactoring
git commit -m "refactor(reporters): extract common PDF styles

Move common PDF styling code into reusable methods
to reduce duplication and improve maintainability."
```

## Processus de Pull Request

### 1. Avant de Créer une PR

**Checklist:**
- [ ] Code suit les standards (voir Code Style)
- [ ] Tests ajoutés et passent tous
- [ ] Documentation mise à jour
- [ ] Pas de conflits avec main
- [ ] Commit messages sont clairs
- [ ] Coverage ne diminue pas

```bash
# Vérifier que tout est OK
pytest
black --check src/
flake8 src/
mypy src/

# Vérifier coverage
pytest --cov=src --cov-report=term
```

### 2. Créer la Pull Request

**Sur GitHub:**

1. Aller sur votre fork
2. Cliquer "Pull Request"
3. Base: `main` ← Compare: `votre-branche`
4. Remplir le template

**Template de PR:**

```markdown
## Description

Brève description des changements.

## Type de Changement

- [ ] Bug fix (non-breaking change qui corrige un bug)
- [ ] Nouvelle fonctionnalité (non-breaking change qui ajoute une fonctionnalité)
- [ ] Breaking change (fix ou feature qui causerait un changement de comportement)
- [ ] Documentation
- [ ] Refactoring

## Motivation et Contexte

Pourquoi ce changement est nécessaire? Quel problème résout-il?

Closes #(issue number)

## Comment a-t-il été testé?

Décrivez les tests effectués.

- [ ] Tests unitaires
- [ ] Tests d'intégration
- [ ] Tests manuels

## Captures d'écran (si applicable)

## Checklist

- [ ] Mon code suit le style de ce projet
- [ ] J'ai effectué une auto-review de mon code
- [ ] J'ai commenté mon code, particulièrement dans les zones complexes
- [ ] J'ai mis à jour la documentation
- [ ] Mes changements ne génèrent pas de nouveaux warnings
- [ ] J'ai ajouté des tests qui prouvent que mon fix/feature fonctionne
- [ ] Les tests unitaires passent localement
- [ ] La coverage n'a pas diminué
```

### 3. Review Process

**Ce qui se passe ensuite:**

1. **Automated Checks** - CI/CD exécute:
   - Tests unitaires
   - Tests d'intégration
   - Linting (black, flake8)
   - Type checking (mypy)
   - Coverage check

2. **Code Review** - Les mainteneurs:
   - Examinent le code
   - Testent les changements
   - Fournissent des feedbacks
   - Approuvent ou demandent des modifications

3. **Modifications** - Si demandées:
   ```bash
   # Faire les modifications
   git add .
   git commit -m "fix: address review comments"
   git push
   # La PR se met à jour automatiquement
   ```

4. **Merge** - Une fois approuvée:
   - Le mainteneur merge la PR
   - La branche peut être supprimée

### 4. Après le Merge

```bash
# Mettre à jour votre fork
git checkout main
git pull upstream main
git push origin main

# Supprimer la branche locale
git branch -d feature/add-permission-audit

# Supprimer la branche remote
git push origin --delete feature/add-permission-audit
```

## Standards de Code

### Voir: Code-Style.md

Référez-vous au guide [Code-Style.md](./Code-Style.md) pour:
- Conventions de nommage
- Style de code
- Documentation
- Type hints
- Best practices

### Quick Reference

```python
# Bon
class PermissionsAuditor:
    """Auditeur pour les permissions LDAP."""

    def __init__(self, connector: LDAPConnector, config: Config) -> None:
        """Initialise l'auditeur.

        Args:
            connector: Connecteur LDAP
            config: Configuration de l'application
        """
        self.connector = connector
        self.config = config

    def audit_permissions(self) -> List[AuditIssue]:
        """Effectue l'audit des permissions.

        Returns:
            Liste des problèmes découverts
        """
        issues: List[AuditIssue] = []
        # Implementation...
        return issues
```

## Processus de Review

### Pour les Reviewers

**Que vérifier:**

1. **Fonctionnalité**
   - Le code fait-il ce qu'il prétend faire?
   - Y a-t-il des edge cases non gérés?
   - Les erreurs sont-elles gérées correctement?

2. **Tests**
   - Les tests couvrent-ils les cas importants?
   - Les tests sont-ils clairs et maintenables?
   - La couverture est-elle suffisante?

3. **Code Quality**
   - Le code est-il lisible?
   - Y a-t-il de la duplication?
   - Les noms sont-ils descriptifs?
   - Les fonctions sont-elles trop longues/complexes?

4. **Documentation**
   - Les docstrings sont-elles complètes?
   - La documentation utilisateur est-elle à jour?
   - Les exemples sont-ils clairs?

5. **Performance**
   - Y a-t-il des problèmes de performance évidents?
   - Les requêtes LDAP sont-elles optimisées?

6. **Sécurité**
   - Les inputs sont-ils validés?
   - Les credentials sont-ils gérés correctement?
   - Y a-t-il des vulnérabilités évidentes?

### Comment Faire une Review

**Commenter:**

```markdown
# Bon feedback
Le code fonctionne bien mais je suggère d'extraire cette logique
dans une méthode séparée pour améliorer la lisibilité:

```python
def _validate_acl(self, acl: str) -> bool:
    # Logique de validation
    pass
```

Qu'en pensez-vous?
```

```markdown
# Moins bon
Ce code est mauvais. Refaire.
```

**Approuver:**

```markdown
LGTM! (Looks Good To Me)

Excellent travail sur:
- Tests complets
- Documentation claire
- Gestion d'erreurs robuste

Juste une petite suggestion: considérer d'ajouter un log debug
à la ligne 45 pour faciliter le debugging.
```

**Demander des Modifications:**

```markdown
Merci pour cette contribution! Avant de merger, pourriez-vous:

1. Ajouter un test pour le cas où l'OU n'existe pas
2. Mettre à jour la documentation dans README.md
3. Extraire la validation dans une méthode privée

Sinon le code est de très bonne qualité!
```

## Résolution de Conflits

### Conflits Git

```bash
# Mettre à jour main
git fetch upstream
git checkout main
git merge upstream/main

# Retourner sur votre branche
git checkout feature/your-feature

# Rebaser
git rebase main

# Si conflits:
# 1. Résoudre dans les fichiers
# 2. Marquer comme résolu
git add <fichier-resolu>

# 3. Continuer le rebase
git rebase --continue

# Si ça devient trop compliqué:
git rebase --abort
# Et demander de l'aide!
```

### Conflits de Design

Si vous n'êtes pas d'accord avec un feedback:

1. **Comprendre le point de vue**
   - Demander des clarifications
   - Considérer l'expérience du reviewer

2. **Expliquer votre approche**
   - Donner vos raisons
   - Fournir des exemples
   - Proposer des alternatives

3. **Chercher un consensus**
   - Être ouvert au compromis
   - Impliquer d'autres contributeurs si nécessaire
   - Documenter la décision

## FAQ Contributeurs

### Q: Comment puis-je commencer?

**R:** Regardez les issues avec le label `good-first-issue`. Ces issues sont parfaites pour les nouveaux contributeurs.

### Q: J'ai trouvé un bug mais je ne sais pas comment le corriger

**R:** Créez une issue avec:
- Description du bug
- Steps pour reproduire
- Comportement attendu vs actuel
- Logs et configuration

Quelqu'un d'autre pourra peut-être le corriger!

### Q: Ma PR est ouverte depuis longtemps sans review

**R:** Les mainteneurs sont bénévoles. Vous pouvez:
- Commenter poliment sur la PR
- Mentionner dans Discord/Slack
- Vérifier que la PR est prête (tests passent, etc.)

### Q: Puis-je travailler sur plusieurs issues en même temps?

**R:** Oui, mais:
- Utilisez des branches séparées
- Finissez une PR avant d'en ouvrir beaucoup d'autres
- Communiquez si vous prenez une grande issue

### Q: Comment puis-je devenir mainteneur?

**R:** Les mainteneurs sont choisis parmi les contributeurs réguliers qui:
- Font des contributions de qualité
- Aident sur les reviews
- Sont actifs dans la communauté
- Montrent une bonne compréhension du projet

### Q: Où puis-je poser des questions?

**R:**
- GitHub Discussions pour questions générales
- Issue pour bugs spécifiques
- Discord/Slack pour discussions rapides

## Ressources

### Documentation

- [Architecture](./Architecture.md)
- [Code Style](./Code-Style.md)
- [Testing](./Testing.md)
- [Adding Audit Module](./Adding-Audit-Module.md)

### Outils

- [Black](https://black.readthedocs.io/) - Formatage
- [Flake8](https://flake8.pycqa.org/) - Linting
- [MyPy](https://mypy.readthedocs.io/) - Type checking
- [Pytest](https://docs.pytest.org/) - Testing
- [Pre-commit](https://pre-commit.com/) - Git hooks

### Communauté

- GitHub Discussions
- Discord Server
- Twitter: @ldap-monitor
- Email: maintainers@ldap-monitor.dev

## Remerciements

Merci à tous nos contributeurs! Votre temps et expertise sont grandement appréciés.

### Hall of Fame

Les contributeurs avec le plus d'impact:
- Nom Contributeur (@github) - X contributions
- Autre Contributeur (@github) - Y contributions

## Licence

En contribuant, vous acceptez que vos contributions soient sous la même licence que le projet (MIT License).

---

**Merci de contribuer à LDAP Health Monitor!** 🎉

Si vous avez des questions, n'hésitez pas à les poser dans les GitHub Discussions.
