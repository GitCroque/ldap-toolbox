# Audit de structure LDAP

## Introduction

L'audit de structure examine l'organisation hiérarchique de votre annuaire LDAP. Une structure bien organisée est essentielle pour la maintenabilité, les performances et la compréhension de votre infrastructure.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Concepts fondamentaux](#concepts-fondamentaux)
3. [Utilisation de base](#utilisation-de-base)
4. [Unités organisationnelles vides](#unités-organisationnelles-vides)
5. [Hiérarchie et profondeur](#hiérarchie-et-profondeur)
6. [Conventions de nommage](#conventions-de-nommage)
7. [Organisation logique](#organisation-logique)
8. [Analyse de la structure](#analyse-de-la-structure)
9. [Réorganisation](#réorganisation)
10. [Exemples pratiques](#exemples-pratiques)
11. [Bonnes pratiques](#bonnes-pratiques)
12. [Dépannage](#dépannage)

## Vue d'ensemble

### Qu'est-ce que l'audit de structure ?

L'audit de structure analyse :
- **Organisation hiérarchique** : Comment les entrées sont organisées
- **Unités organisationnelles (OUs)** : Conteneurs logiques
- **Conventions de nommage** : Cohérence des noms
- **Profondeur de hiérarchie** : Complexité de l'arbre
- **Distribution des entrées** : Équilibre de la structure

### Pourquoi c'est important ?

**Impact sur les performances :**
```
Structure plate (mauvais) :
ou=Users avec 10000 entrées → Recherches lentes

Structure organisée (bon) :
ou=Users
  ├── ou=Paris (2000 entrées)
  ├── ou=London (3000 entrées)
  └── ou=NewYork (5000 entrées)
→ Recherches ciblées plus rapides
```

**Impact sur la maintenance :**
- Structure claire = Gestion facile
- Structure confuse = Erreurs fréquentes
- Conventions cohérentes = Automatisation possible

### Architecture de l'audit

```
┌──────────────────┐
│ StructureAuditor │
└────────┬─────────┘
         │
    ┌────▼────────────────────────┐
    │ _check_empty_ous()          │
    │ _check_naming_conventions() │
    │ _check_hierarchy_depth()    │
    │ _analyze_distribution()     │
    └────┬────────────────────────┘
         │
    ┌────▼─────────┐
    │ AuditIssue[] │
    └──────────────┘
```

## Concepts fondamentaux

### Distinguished Name (DN)

Le DN est l'adresse complète d'une entrée LDAP :

```
dn: uid=alice,ou=Developers,ou=IT,ou=Paris,dc=example,dc=com
    └─────┬──────┘ └──────────┬──────────┘ └────────┬────────┘
         RDN          Path (OUs)            Base DN
```

**Composants :**
- **RDN** : Relative Distinguished Name (identifiant unique dans le parent)
- **Path** : Chemin des OUs parentes
- **Base DN** : Racine de l'annuaire

### Unité Organisationnelle (OU)

Conteneur logique pour organiser les entrées :

```ldif
dn: ou=IT,dc=example,dc=com
objectClass: organizationalUnit
objectClass: top
ou: IT
description: Information Technology Department
```

**Utilisations courantes :**
- Par département : ou=Sales, ou=Marketing, ou=IT
- Par localisation : ou=Paris, ou=London, ou=Tokyo
- Par type : ou=Users, ou=Groups, ou=Computers
- Par fonction : ou=Employees, ou=Contractors, ou=Guests

### Hiérarchie LDAP

Structure en arbre inversé :

```
dc=example,dc=com (racine)
│
├── ou=Users
│   ├── ou=Employees
│   │   ├── ou=IT
│   │   │   ├── uid=alice
│   │   │   └── uid=bob
│   │   └── ou=Sales
│   │       └── uid=charlie
│   └── ou=Contractors
│       └── uid=temp1
│
├── ou=Groups
│   ├── cn=Developers
│   └── cn=Admins
│
└── ou=Applications
    └── ou=ServiceAccounts
```

### Profondeur de hiérarchie

**Mesure de complexité :**
```
Profondeur = Nombre de niveaux du root au leaf

Exemple :
dc=example,dc=com → 0 (root)
ou=Users,dc=example,dc=com → 1
ou=IT,ou=Users,dc=example,dc=com → 2
uid=alice,ou=IT,ou=Users,dc=example,dc=com → 3
```

**Recommandations :**
- **Optimal** : 2-4 niveaux
- **Acceptable** : 5-6 niveaux
- **Problématique** : > 7 niveaux

## Utilisation de base

### Commande simple

```bash
ldap-health-monitor audit structure
```

**Sortie exemple :**
```
Found 1 issue

INFO: 5 empty organizational units
  Found 5 OUs with no children
  💡 Consider removing unused OUs

Details:
  - ou=OldDept,dc=example,dc=com
  - ou=Archive2022,ou=Users,dc=example,dc=com
  - ou=Temp,ou=Groups,dc=example,dc=com
  - ou=Test,dc=example,dc=com
  - ou=Deprecated,ou=Applications,dc=example,dc=com
```

### Avec export JSON

```bash
ldap-health-monitor audit structure --format json --output structure-audit.json
```

**Sortie JSON :**
```json
{
  "timestamp": "2025-11-17T10:30:45",
  "issues": [
    {
      "level": "info",
      "category": "structure",
      "title": "5 empty organizational units",
      "description": "Found 5 OUs with no children",
      "recommendation": "Consider removing unused OUs",
      "details": {
        "ous": [
          "ou=OldDept,dc=example,dc=com",
          "ou=Archive2022,ou=Users,dc=example,dc=com",
          "ou=Temp,ou=Groups,dc=example,dc=com",
          "ou=Test,dc=example,dc=com",
          "ou=Deprecated,ou=Applications,dc=example,dc=com"
        ]
      }
    }
  ]
}
```

### Analyse complète

```bash
# Audit avec toutes les vérifications
ldap-health-monitor audit structure --verbose
```

## Unités organisationnelles vides

### Définition

Une OU vide est une unité organisationnelle sans enfant (pas d'entrées directes).

**Détection :**
```python
for ou in ous:
    children = connector.search(
        search_base=ou["dn"],
        search_filter="(objectClass=*)",
        attributes=["dn"]
    )
    if len(children) <= 1:  # Seulement l'OU elle-même
        empty_ous.append(ou["dn"])
```

### Exemple de résultat

```
INFO: 5 empty organizational units
  Found 5 OUs with no children
  💡 Consider removing unused OUs

Details:
  - ou=OldDept,dc=example,dc=com
    Created: 2020-03-15
    Last modified: 2020-03-15
    Description: "Former department, merged with IT"

  - ou=Archive2022,ou=Users,dc=example,dc=com
    Created: 2022-01-01
    Description: "Temporary archive container"

  - ou=Temp,ou=Groups,dc=example,dc=com
    Created: 2023-06-12
    Description: None
```

### Vérification manuelle

**Lister toutes les OUs :**
```bash
ldapsearch -x -b "dc=example,dc=com" \
  "(objectClass=organizationalUnit)" \
  dn ou description
```

**Vérifier si une OU est vide :**
```bash
#!/bin/bash
OU_DN="ou=Test,dc=example,dc=com"

COUNT=$(ldapsearch -x -b "$OU_DN" -s one "(objectClass=*)" dn | grep -c "^dn:")

if [ $COUNT -eq 0 ]; then
  echo "$OU_DN is empty"
else
  echo "$OU_DN has $COUNT children"
fi
```

**Liste détaillée des OUs vides :**
```bash
#!/bin/bash
# find-empty-ous.sh

ldapsearch -x -b "dc=example,dc=com" \
  "(objectClass=organizationalUnit)" dn | \
  grep "^dn:" | cut -d' ' -f2- | \
while read OU_DN; do
  COUNT=$(ldapsearch -x -b "$OU_DN" -s one "(objectClass=*)" dn 2>/dev/null | grep -c "^dn:")
  if [ $COUNT -eq 0 ]; then
    echo "Empty: $OU_DN"
  fi
done
```

### Causes communes

**Réorganisation incomplète :**
```bash
# Les entrées ont été déplacées mais l'ancienne OU reste
ldapmodrdn "uid=alice,ou=OldDept,dc=example,dc=com" "uid=alice" \
  -newsuperior "ou=IT,dc=example,dc=com"
# ou=OldDept est maintenant vide
```

**Projet abandonné :**
```bash
# OU créée pour un projet qui n'a jamais démarré
ldapadd << EOF
dn: ou=Project2024,ou=Applications,dc=example,dc=com
objectClass: organizationalUnit
ou: Project2024
description: New application project
EOF
# Projet annulé, OU jamais utilisée
```

**Archive temporaire :**
```bash
# OU créée pour une migration temporaire
ou=TempMigration,dc=example,dc=com
# Migration terminée, contenu déplacé, OU oubliée
```

### Nettoyage des OUs vides

**Vérification sécurisée avant suppression :**
```bash
#!/bin/bash
# safe-delete-empty-ou.sh

OU_DN="$1"

if [ -z "$OU_DN" ]; then
  echo "Usage: $0 <ou-dn>"
  exit 1
fi

# Vérifier que c'est bien une OU
if ! ldapsearch -x -b "$OU_DN" -s base "(objectClass=organizationalUnit)" dn 2>/dev/null | grep -q "^dn:"; then
  echo "Error: $OU_DN is not an organizationalUnit"
  exit 1
fi

# Compter les enfants
COUNT=$(ldapsearch -x -b "$OU_DN" -s one "(objectClass=*)" dn 2>/dev/null | grep -c "^dn:")

if [ $COUNT -gt 0 ]; then
  echo "Error: $OU_DN is not empty (has $COUNT children)"
  exit 1
fi

# Afficher les détails
echo "OU to delete:"
ldapsearch -x -b "$OU_DN" -s base

read -p "Confirm deletion? (yes/no): " CONFIRM

if [ "$CONFIRM" = "yes" ]; then
  ldapdelete "$OU_DN"
  echo "Deleted: $OU_DN"
else
  echo "Cancelled"
fi
```

**Suppression en masse :**
```bash
#!/bin/bash
# bulk-delete-empty-ous.sh

# Sauvegarder la liste
ldapsearch -x -b "dc=example,dc=com" \
  "(objectClass=organizationalUnit)" dn > /tmp/all-ous.ldif

# Trouver les OUs vides
EMPTY_OUS=$(
  ldapsearch -x -b "dc=example,dc=com" \
    "(objectClass=organizationalUnit)" dn | \
  grep "^dn:" | cut -d' ' -f2- | \
  while read OU_DN; do
    COUNT=$(ldapsearch -x -b "$OU_DN" -s one "(objectClass=*)" dn 2>/dev/null | grep -c "^dn:")
    if [ $COUNT -eq 0 ]; then
      echo "$OU_DN"
    fi
  done
)

# Afficher la liste
echo "Empty OUs found:"
echo "$EMPTY_OUS"
echo ""
echo "Total: $(echo "$EMPTY_OUS" | wc -l)"

read -p "Delete all empty OUs? (yes/no): " CONFIRM

if [ "$CONFIRM" = "yes" ]; then
  echo "$EMPTY_OUS" | while read OU_DN; do
    echo "Deleting: $OU_DN"
    ldapdelete "$OU_DN"
  done
  echo "Done!"
else
  echo "Cancelled"
fi
```

### Prévention

**Politique de création d'OU :**
```yaml
# Documentation des OUs
ou_policy:
  require_description: true
  require_owner: true
  require_approval: true
```

**Template de création :**
```bash
#!/bin/bash
# create-ou.sh

OU_NAME="$1"
PARENT_DN="$2"
OWNER="$3"
DESCRIPTION="$4"

if [ -z "$DESCRIPTION" ]; then
  echo "Error: Description is required"
  exit 1
fi

ldapadd << EOF
dn: ou=$OU_NAME,$PARENT_DN
objectClass: organizationalUnit
objectClass: top
ou: $OU_NAME
description: $DESCRIPTION
owner: $OWNER
createTimestamp: $(date -u +%Y%m%d%H%M%SZ)
EOF
```

**Audit périodique :**
```bash
# Cron mensuel
0 0 1 * * ldap-health-monitor audit structure --format json --output /var/reports/structure-$(date +%Y%m).json
```

## Hiérarchie et profondeur

### Analyse de la profondeur

**Script de calcul :**
```bash
#!/bin/bash
# analyze-depth.sh

echo "DN,Depth"

ldapsearch -x -b "dc=example,dc=com" "(objectClass=*)" dn | \
  grep "^dn:" | cut -d' ' -f2- | \
while read DN; do
  # Compter les virgules (approximation de la profondeur)
  DEPTH=$(echo "$DN" | tr -cd ',' | wc -c)
  echo "$DN,$DEPTH"
done | sort -t',' -k2 -n -r | head -20
```

**Sortie exemple :**
```
DN,Depth
uid=alice,ou=Developers,ou=IT,ou=Paris,ou=Employees,ou=Users,dc=example,dc=com,7
uid=bob,ou=Support,ou=IT,ou=London,ou=Employees,ou=Users,dc=example,dc=com,7
cn=App1,ou=Production,ou=WebApps,ou=Applications,dc=example,dc=com,5
...
```

### Visualisation de l'arbre

**Script de génération d'arbre :**
```bash
#!/bin/bash
# tree-view.sh

BASE_DN="dc=example,dc=com"

function print_tree() {
  local dn="$1"
  local prefix="$2"

  # Afficher l'entrée courante
  RDN=$(echo "$dn" | cut -d',' -f1)
  echo "$prefix$RDN"

  # Récupérer les enfants directs
  ldapsearch -x -b "$dn" -s one "(objectClass=*)" dn 2>/dev/null | \
    grep "^dn:" | cut -d' ' -f2- | \
  while read CHILD_DN; do
    print_tree "$CHILD_DN" "$prefix  "
  done
}

print_tree "$BASE_DN" ""
```

**Sortie exemple :**
```
dc=example,dc=com
  ou=Users
    ou=Employees
      ou=IT
        ou=Developers
          uid=alice
          uid=bob
        ou=Support
          uid=charlie
      ou=Sales
        uid=dave
    ou=Contractors
      uid=temp1
  ou=Groups
    cn=Developers
    cn=Admins
  ou=Applications
```

### Graphique avec Graphviz

**Génération de graphique DOT :**
```bash
#!/bin/bash
# generate-ldap-graph.sh

cat > ldap-tree.dot << 'HEADER'
digraph LDAP {
  rankdir=TB;
  node [shape=box, style=rounded];
HEADER

ldapsearch -x -b "dc=example,dc=com" "(objectClass=*)" dn | \
  grep "^dn:" | cut -d' ' -f2- | \
while read DN; do
  # Créer un ID unique (remplacer caractères spéciaux)
  ID=$(echo "$DN" | tr ',= ' '___')
  LABEL=$(echo "$DN" | cut -d',' -f1)

  echo "  \"$ID\" [label=\"$LABEL\"];"

  # Trouver le parent
  PARENT_DN=$(echo "$DN" | cut -d',' -f2-)
  if [ -n "$PARENT_DN" ]; then
    PARENT_ID=$(echo "$PARENT_DN" | tr ',= ' '___')
    echo "  \"$PARENT_ID\" -> \"$ID\";"
  fi
done >> ldap-tree.dot

echo "}" >> ldap-tree.dot

# Générer le graphique
dot -Tpng ldap-tree.dot -o ldap-tree.png
echo "Graph generated: ldap-tree.png"
```

### Optimisation de la profondeur

**Problème : Hiérarchie trop profonde**
```
Before (7 niveaux) :
uid=alice,ou=Developers,ou=IT,ou=Paris,ou=Employees,ou=Users,dc=example,dc=com

After (4 niveaux) :
uid=alice,ou=IT-Paris,ou=Users,dc=example,dc=com
```

**Script de réorganisation :**
```bash
#!/bin/bash
# flatten-hierarchy.sh

# Exemple : fusionner ou=Paris et ou=IT en ou=IT-Paris

# 1. Créer la nouvelle OU
ldapadd << EOF
dn: ou=IT-Paris,ou=Users,dc=example,dc=com
objectClass: organizationalUnit
ou: IT-Paris
description: IT department in Paris office
EOF

# 2. Déplacer les entrées
ldapsearch -x -b "ou=IT,ou=Paris,ou=Employees,ou=Users,dc=example,dc=com" \
  "(objectClass=person)" dn | \
  grep "^dn:" | cut -d' ' -f2- | \
while read OLD_DN; do
  RDN=$(echo "$OLD_DN" | cut -d',' -f1)
  NEW_DN="$RDN,ou=IT-Paris,ou=Users,dc=example,dc=com"

  echo "Moving: $OLD_DN -> $NEW_DN"

  ldapmodrdn "$OLD_DN" "$RDN" -newsuperior "ou=IT-Paris,ou=Users,dc=example,dc=com"
done

# 3. Supprimer les anciennes OUs vides
# (à faire manuellement après vérification)
```

## Conventions de nommage

### Analyse des conventions

**Script de vérification :**
```bash
#!/bin/bash
# check-naming-conventions.sh

echo "=== Naming Convention Analysis ==="
echo ""

# Vérifier les OUs
echo "Organizational Units:"
ldapsearch -x -b "dc=example,dc=com" "(objectClass=organizationalUnit)" ou | \
  grep "^ou:" | cut -d' ' -f2- | \
while read OU_NAME; do
  # Vérifier si suit les conventions
  if [[ "$OU_NAME" =~ ^[A-Z][a-zA-Z0-9-]+$ ]]; then
    echo "  ✓ $OU_NAME (valid)"
  else
    echo "  ✗ $OU_NAME (invalid format)"
  fi
done

echo ""
echo "Users:"
ldapsearch -x -b "ou=Users,dc=example,dc=com" "(objectClass=person)" uid | \
  grep "^uid:" | cut -d' ' -f2- | \
while read UID; do
  # Vérifier format lowercase letters
  if [[ "$UID" =~ ^[a-z][a-z0-9.]+$ ]]; then
    echo "  ✓ $UID (valid)"
  else
    echo "  ✗ $UID (invalid format)"
  fi
done
```

### Politiques de nommage courantes

**Pour les utilisateurs :**
```yaml
naming_policy:
  users:
    format: "firstname.lastname"
    examples:
      - "john.doe"
      - "alice.smith"
    rules:
      - lowercase_only
      - no_spaces
      - no_special_chars_except_dot
```

**Pour les groupes :**
```yaml
naming_policy:
  groups:
    format: "<prefix>-<name>[-<location>]"
    prefixes:
      SEC: Security groups
      APP: Application groups
      DL: Distribution lists
      PROJ: Project teams
    examples:
      - "SEC-Admins"
      - "APP-Developers-Paris"
      - "DL-Marketing"
      - "PROJ-WebRefresh"
```

**Pour les OUs :**
```yaml
naming_policy:
  ous:
    format: "PascalCase or kebab-case"
    examples:
      - "Users"
      - "ServiceAccounts"
      - "IT-Paris"
    rules:
      - descriptive
      - no_abbreviations_unless_standard
      - consistent_casing
```

### Détection des violations

**Script de détection :**
```python
#!/usr/bin/env python3
# check-naming-violations.py

import re
from ldap3 import Server, Connection, ALL

# Conventions
CONVENTIONS = {
    'user': r'^[a-z][a-z0-9.]+$',
    'group': r'^(SEC|APP|DL|PROJ)-[A-Za-z0-9-]+$',
    'ou': r'^[A-Z][A-Za-z0-9-]*$'
}

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

violations = []

# Vérifier les utilisateurs
conn.search('ou=Users,dc=example,dc=com', '(objectClass=person)', attributes=['uid'])
for entry in conn.entries:
    uid = str(entry.uid)
    if not re.match(CONVENTIONS['user'], uid):
        violations.append({
            'type': 'user',
            'dn': entry.entry_dn,
            'value': uid,
            'expected': 'lowercase alphanumeric with dots'
        })

# Vérifier les groupes
conn.search('ou=Groups,dc=example,dc=com', '(objectClass=groupOfNames)', attributes=['cn'])
for entry in conn.entries:
    cn = str(entry.cn)
    if not re.match(CONVENTIONS['group'], cn):
        violations.append({
            'type': 'group',
            'dn': entry.entry_dn,
            'value': cn,
            'expected': 'PREFIX-Name format'
        })

# Afficher les violations
print(f"Found {len(violations)} naming convention violations:")
for v in violations:
    print(f"  {v['type']}: {v['value']} (expected: {v['expected']})")
    print(f"    DN: {v['dn']}")

conn.unbind()
```

### Correction des violations

**Renommage sécurisé :**
```bash
#!/bin/bash
# rename-entry.sh

OLD_RDN="uid=JOHN.DOE"
NEW_RDN="uid=john.doe"
PARENT_DN="ou=Users,dc=example,dc=com"

OLD_DN="$OLD_RDN,$PARENT_DN"
NEW_DN="$NEW_RDN,$PARENT_DN"

echo "Renaming: $OLD_DN -> $NEW_DN"

# Vérifier que la nouvelle entrée n'existe pas déjà
if ldapsearch -x -b "$NEW_DN" -s base dn 2>/dev/null | grep -q "^dn:"; then
  echo "Error: Target DN already exists"
  exit 1
fi

# Effectuer le renommage
ldapmodrdn "$OLD_DN" "$NEW_RDN"

echo "Renamed successfully"

# Vérifier
ldapsearch -x -b "$NEW_DN" -s base dn
```

## Organisation logique

### Modèles d'organisation courants

**Par département :**
```
dc=example,dc=com
├── ou=Users
│   ├── ou=IT
│   ├── ou=Sales
│   ├── ou=Marketing
│   └── ou=HR
├── ou=Groups
│   ├── ou=IT-Groups
│   ├── ou=Sales-Groups
│   └── ou=Marketing-Groups
```

**Par localisation :**
```
dc=example,dc=com
├── ou=Paris
│   ├── ou=Users
│   └── ou=Groups
├── ou=London
│   ├── ou=Users
│   └── ou=Groups
└── ou=NewYork
    ├── ou=Users
    └── ou=Groups
```

**Par type d'objet :**
```
dc=example,dc=com
├── ou=People
│   ├── ou=Employees
│   ├── ou=Contractors
│   └── ou=Guests
├── ou=Groups
│   ├── ou=Security
│   ├── ou=Distribution
│   └── ou=Application
├── ou=Resources
│   ├── ou=Computers
│   ├── ou=Printers
│   └── ou=Rooms
└── ou=Services
    └── ou=ServiceAccounts
```

**Hybride (recommandé) :**
```
dc=example,dc=com
├── ou=Users
│   ├── ou=Employees
│   │   ├── ou=IT
│   │   ├── ou=Sales
│   │   └── ou=Marketing
│   ├── ou=Contractors
│   └── ou=ServiceAccounts
├── ou=Groups
│   ├── ou=Security
│   ├── ou=Distribution
│   └── ou=Application
└── ou=Resources
    ├── ou=Computers
    └── ou=SharedResources
```

### Évaluation de l'organisation

**Métriques de qualité :**
```python
#!/usr/bin/env python3
# evaluate-structure.py

def calculate_structure_score(conn):
    """Calcule un score de qualité de structure"""
    score = 100

    # Critère 1: Profondeur moyenne (optimal: 3-4)
    avg_depth = calculate_average_depth(conn)
    if avg_depth > 5:
        score -= 10
    elif avg_depth > 6:
        score -= 20

    # Critère 2: Distribution équilibrée
    distribution = check_distribution(conn)
    if distribution['max_in_ou'] > 1000:
        score -= 15

    # Critère 3: OUs vides
    empty_ous = count_empty_ous(conn)
    score -= min(empty_ous * 2, 20)

    # Critère 4: Conventions de nommage
    naming_violations = check_naming_conventions(conn)
    score -= min(len(naming_violations) * 1, 20)

    # Critère 5: Organisation logique
    logic_score = evaluate_logical_organization(conn)
    score = score * (logic_score / 100)

    return max(0, score)
```

## Analyse de la structure

### Rapport complet de structure

**Script de génération :**
```bash
#!/bin/bash
# structure-report.sh

OUTPUT="/var/reports/ldap-structure-$(date +%Y%m%d).txt"

{
  echo "==================================="
  echo "LDAP Structure Analysis Report"
  echo "Generated: $(date)"
  echo "==================================="
  echo ""

  # 1. Statistiques générales
  echo "=== General Statistics ==="
  TOTAL_ENTRIES=$(ldapsearch -x -b "dc=example,dc=com" "(objectClass=*)" dn | grep -c "^dn:")
  TOTAL_OUS=$(ldapsearch -x -b "dc=example,dc=com" "(objectClass=organizationalUnit)" dn | grep -c "^dn:")
  TOTAL_USERS=$(ldapsearch -x -b "dc=example,dc=com" "(objectClass=person)" dn | grep -c "^dn:")
  TOTAL_GROUPS=$(ldapsearch -x -b "dc=example,dc=com" "(objectClass=groupOfNames)" dn | grep -c "^dn:")

  echo "Total entries: $TOTAL_ENTRIES"
  echo "Organizational units: $TOTAL_OUS"
  echo "Users: $TOTAL_USERS"
  echo "Groups: $TOTAL_GROUPS"
  echo ""

  # 2. Top-level OUs
  echo "=== Top-Level OUs ==="
  ldapsearch -x -b "dc=example,dc=com" -s one "(objectClass=organizationalUnit)" dn | \
    grep "^dn:" | cut -d' ' -f2-
  echo ""

  # 3. Distribution par OU
  echo "=== Distribution by OU ==="
  ldapsearch -x -b "dc=example,dc=com" "(objectClass=organizationalUnit)" dn | \
    grep "^dn:" | cut -d' ' -f2- | \
  while read OU_DN; do
    COUNT=$(ldapsearch -x -b "$OU_DN" -s one "(objectClass=*)" dn 2>/dev/null | grep -c "^dn:")
    echo "$OU_DN: $COUNT entries"
  done | sort -t':' -k2 -n -r | head -20
  echo ""

  # 4. Profondeur maximale
  echo "=== Deepest Entries ==="
  ldapsearch -x -b "dc=example,dc=com" "(objectClass=*)" dn | \
    grep "^dn:" | cut -d' ' -f2- | \
  while read DN; do
    DEPTH=$(echo "$DN" | tr -cd ',' | wc -c)
    echo "$DEPTH,$DN"
  done | sort -t',' -k1 -n -r | head -10 | cut -d',' -f2-
  echo ""

  # 5. OUs vides
  echo "=== Empty OUs ==="
  ldapsearch -x -b "dc=example,dc=com" "(objectClass=organizationalUnit)" dn | \
    grep "^dn:" | cut -d' ' -f2- | \
  while read OU_DN; do
    COUNT=$(ldapsearch -x -b "$OU_DN" -s one "(objectClass=*)" dn 2>/dev/null | grep -c "^dn:")
    if [ $COUNT -eq 0 ]; then
      echo "$OU_DN"
    fi
  done
  echo ""

  echo "==================================="
  echo "End of Report"
  echo "==================================="
} > "$OUTPUT"

echo "Report generated: $OUTPUT"
cat "$OUTPUT"
```

### Visualisation avec D3.js

**Export JSON pour visualisation :**
```python
#!/usr/bin/env python3
# export-tree-json.py

import json
from ldap3 import Server, Connection, ALL

def build_tree(conn, base_dn):
    """Construit l'arbre LDAP en JSON"""
    conn.search(base_dn, '(objectClass=*)', search_scope='BASE', attributes=['*'])

    if not conn.entries:
        return None

    entry = conn.entries[0]
    node = {
        'name': str(entry.entry_dn).split(',')[0],
        'dn': str(entry.entry_dn),
        'objectClass': str(entry.objectClass) if hasattr(entry, 'objectClass') else 'unknown',
        'children': []
    }

    # Récupérer les enfants
    conn.search(base_dn, '(objectClass=*)', search_scope='LEVEL', attributes=['*'])

    for child in conn.entries:
        child_node = build_tree(conn, str(child.entry_dn))
        if child_node:
            node['children'].append(child_node)

    return node

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

tree = build_tree(conn, 'dc=example,dc=com')

with open('ldap-tree.json', 'w') as f:
    json.dump(tree, f, indent=2)

print("Tree exported to ldap-tree.json")
conn.unbind()
```

## Réorganisation

### Planification

**Étapes de réorganisation :**

1. **Analyse de l'existant**
```bash
ldap-health-monitor audit structure --format json --output current-structure.json
```

2. **Conception de la nouvelle structure**
```
Document: new-structure-design.md
- Objectifs
- Nouvelle hiérarchie
- Plan de migration
- Rollback plan
```

3. **Backup complet**
```bash
ldap-health-monitor backup full --output backup-before-reorg.ldif
```

4. **Migration par phases**
```
Phase 1: Créer nouvelles OUs
Phase 2: Déplacer utilisateurs de test
Phase 3: Validation
Phase 4: Migration complète
Phase 5: Nettoyage anciennes OUs
```

### Script de migration

```bash
#!/bin/bash
# migrate-structure.sh

set -e

echo "=== LDAP Structure Migration ==="
echo "Start: $(date)"

# Configuration
OLD_BASE="ou=OldStructure,dc=example,dc=com"
NEW_BASE="ou=NewStructure,dc=example,dc=com"
DRY_RUN=true

# Backup
echo "Creating backup..."
ldapsearch -x -b "dc=example,dc=com" > "/backup/pre-migration-$(date +%Y%m%d%H%M%S).ldif"

# Créer nouvelle structure
echo "Creating new OUs..."
while IFS= read -r LINE; do
  if [ "$DRY_RUN" = false ]; then
    echo "$LINE" | ldapadd
  else
    echo "Would create: $(echo "$LINE" | grep "^dn:")"
  fi
done < new-ous.ldif

# Migrer les entrées
echo "Migrating entries..."
ldapsearch -x -b "$OLD_BASE" "(objectClass=person)" dn | \
  grep "^dn:" | cut -d' ' -f2- | \
while read OLD_DN; do
  # Calculer nouveau DN
  RDN=$(echo "$OLD_DN" | cut -d',' -f1)
  NEW_DN="$RDN,$NEW_BASE"

  echo "Moving: $OLD_DN -> $NEW_DN"

  if [ "$DRY_RUN" = false ]; then
    ldapmodrdn "$OLD_DN" "$RDN" -newsuperior "$NEW_BASE"
  fi
done

echo "End: $(date)"
echo "=== Migration Complete ==="
```

## Exemples pratiques

### Exemple 1 : Audit mensuel automatisé

```bash
#!/bin/bash
# monthly-structure-audit.sh

DATE=$(date +%Y-%m)
REPORT_DIR="/var/reports/ldap/structure"

mkdir -p "$REPORT_DIR"

# Audit complet
ldap-health-monitor audit structure \
  --format json \
  --output "$REPORT_DIR/audit-$DATE.json"

# Générer rapport HTML
python3 << 'PYTHON'
import json
from datetime import datetime

with open(f'/var/reports/ldap/structure/audit-{DATE}.json') as f:
    data = json.load(f)

html = f"""
<!DOCTYPE html>
<html>
<head><title>Structure Audit {DATE}</title></head>
<body>
<h1>LDAP Structure Audit - {DATE}</h1>
<h2>Issues: {len(data.get('issues', []))}</h2>
<ul>
{"".join(f"<li>{issue['title']}</li>" for issue in data.get('issues', []))}
</ul>
</body>
</html>
"""

with open(f'/var/reports/ldap/structure/audit-{DATE}.html', 'w') as f:
    f.write(html)
PYTHON

# Notification si problèmes
ISSUES=$(jq -r '.issues | length' "$REPORT_DIR/audit-$DATE.json")
if [ "$ISSUES" -gt 0 ]; then
  echo "Structure audit found $ISSUES issues" | \
    mail -s "LDAP Structure Audit" -a "$REPORT_DIR/audit-$DATE.html" admin@example.com
fi
```

### Exemple 2 : Monitoring de croissance

```bash
#!/bin/bash
# monitor-growth.sh

while true; do
  TIMESTAMP=$(date +%s)

  # Compter par type
  USERS=$(ldapsearch -x -b "ou=Users,dc=example,dc=com" "(objectClass=person)" dn | grep -c "^dn:")
  GROUPS=$(ldapsearch -x -b "ou=Groups,dc=example,dc=com" "(objectClass=groupOfNames)" dn | grep -c "^dn:")
  OUS=$(ldapsearch -x -b "dc=example,dc=com" "(objectClass=organizationalUnit)" dn | grep -c "^dn:")

  # Logger
  echo "$TIMESTAMP,$USERS,$GROUPS,$OUS" >> /var/log/ldap-growth.csv

  sleep 3600  # Toutes les heures
done
```

## Bonnes pratiques

### Design de structure

1. **Gardez-la simple**
   - 3-4 niveaux maximum
   - Hiérarchie claire et compréhensible
   - Pas de sur-organisation

2. **Pensez aux performances**
   - Évitez les OUs avec > 1000 entrées directes
   - Utilisez des indexes appropriés
   - Subdivisez si nécessaire

3. **Documentez**
   - Chaque OU doit avoir une description
   - Maintenez un schéma à jour
   - Documentez les conventions

4. **Planifiez la croissance**
   - Structure évolutive
   - Espace pour nouveaux départements
   - Flexibilité pour réorganisation

### Maintenance

**Routine mensuelle :**
```bash
1. Audit de structure
2. Vérification OUs vides
3. Validation des conventions
4. Mise à jour de la documentation
5. Backup de référence
```

## Dépannage

### Structure corrompue

**Symptômes :**
- OUs orphelines
- Références circulaires
- Hiérarchie incohérente

**Diagnostic :**
```bash
# Vérifier l'intégrité
ldapsearch -x -b "dc=example,dc=com" "(objectClass=*)" dn | \
  grep "^dn:" | cut -d' ' -f2- | \
while read DN; do
  PARENT=$(echo "$DN" | cut -d',' -f2-)
  if ! ldapsearch -x -b "$PARENT" -s base dn 2>/dev/null | grep -q "^dn:"; then
    echo "Orphan: $DN (parent $PARENT does not exist)"
  fi
done
```

**Réparation :**
- Restaurer depuis backup
- Reconstruire les OUs manquantes
- Supprimer les entrées orphelines

## Conclusion

Une structure LDAP bien organisée est fondamentale pour la performance, la maintenabilité et la sécurité de votre annuaire. Un audit régulier permet de maintenir cette organisation dans le temps.

**Points clés :**
- Audit mensuel de la structure
- Suppression des OUs vides
- Respect des conventions de nommage
- Documentation à jour
- Profondeur de hiérarchie optimale

Pour aller plus loin :
- [Audit de sécurité](./Security-Audit.md)
- [Audit de cohérence](./Consistency-Audit.md)
- [Génération de rapports](./Audit-Reports.md)
