# Audit des groupes LDAP

## Introduction

L'audit des groupes est crucial pour maintenir une structure de groupes propre et efficace dans votre annuaire LDAP. Les groupes mal gérés peuvent causer des problèmes de performance, de sécurité et de maintenance.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Types de problèmes détectés](#types-de-problèmes-détectés)
3. [Utilisation de base](#utilisation-de-base)
4. [Groupes vides](#groupes-vides)
5. [Groupes volumineux](#groupes-volumineux)
6. [Membres orphelins](#membres-orphelins)
7. [Membres en double](#membres-en-double)
8. [Groupes imbriqués](#groupes-imbriqués)
9. [Exemples pratiques](#exemples-pratiques)
10. [Nettoyage et maintenance](#nettoyage-et-maintenance)
11. [Bonnes pratiques](#bonnes-pratiques)
12. [Dépannage](#dépannage)

## Vue d'ensemble

### Pourquoi auditer les groupes ?

Les groupes LDAP sont utilisés pour :
- **Gestion des accès** : Contrôle des permissions
- **Distribution d'emails** : Listes de diffusion
- **Organisation** : Structuration logique des utilisateurs
- **Automatisation** : Provisioning de comptes

**Problèmes courants :**
- Groupes vides inutilisés
- Références vers des utilisateurs supprimés
- Doublons de membres
- Groupes trop volumineux affectant les performances
- Structure d'imbrication complexe

### Architecture de l'audit

```
┌─────────────────┐
│  GroupAuditor   │
└────────┬────────┘
         │
    ┌────▼────────────────────────┐
    │ _check_empty_groups()       │
    │ _check_large_groups()       │
    │ _check_orphaned_members()   │
    │ _check_duplicate_members()  │
    └────┬────────────────────────┘
         │
    ┌────▼─────────┐
    │ AuditIssue[] │
    └──────────────┘
```

### Statistiques collectées

L'audit collecte automatiquement :
```json
{
  "total": 156,
  "empty": 12,
  "total_members": 4523,
  "average_members": 29.0
}
```

## Types de problèmes détectés

### Résumé des détections

| Problème | Niveau | Impact | Fréquence |
|----------|--------|--------|-----------|
| Groupes vides | WARNING | Moyen | Très courant |
| Groupes volumineux | INFO | Faible | Courant |
| Membres orphelins | WARNING | Élevé | Rare |
| Membres en double | WARNING | Moyen | Rare |

### Impact sur les performances

```
Problème → Impact → Conséquence

Groupes vides → Pollution → Gestion difficile
Membres orphelins → Erreurs → Échecs de requêtes
Groupes volumineux → Lenteur → Timeout
Doublons → Incohérence → Comportement imprévisible
```

## Utilisation de base

### Commande simple

```bash
ldap-health-monitor audit groups
```

**Sortie exemple :**
```
Found 3 issues

WARNING: 12 empty groups
  Found 12 groups with no members
  💡 Remove unused empty groups

INFO: 5 large groups
  Found 5 groups with more than 100 members
  💡 Consider splitting large groups for better management

WARNING: 3 groups with orphaned members
  Found 8 group members that don't exist in 3 groups
  💡 Remove orphaned member references
```

### Avec options spécifiques

```bash
# Afficher seulement les groupes vides
ldap-health-monitor audit groups --empty

# Afficher seulement les groupes volumineux
ldap-health-monitor audit groups --large
```

### Export des résultats

```bash
# Export JSON
ldap-health-monitor audit groups --format json --output groups-audit.json

# Export CSV
ldap-health-monitor audit groups --format csv --output groups-audit.csv
```

### Avec configuration personnalisée

```bash
ldap-health-monitor --config /etc/ldap/custom.yaml audit groups
```

## Groupes vides

### Définition

Un groupe vide est un groupe sans aucun membre :
```ldif
dn: cn=OldProject,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: OldProject
# Aucun attribut member
```

### Détection

**Code de détection :**
```python
empty_groups = [g for g in groups if not g.members]
```

**Seuil configurable :**
```yaml
audit:
  thresholds:
    max_empty_groups: 5
```

Si le nombre de groupes vides dépasse ce seuil, une alerte est générée.

### Exemple de résultat

```
WARNING: 12 empty groups
  Found 12 groups with no members
  💡 Remove unused empty groups

Details:
  - cn=OldProject,ou=Groups,dc=example,dc=com
  - cn=TempTeam,ou=Groups,dc=example,dc=com
  - cn=Archived2023,ou=Groups,dc=example,dc=com
  - cn=TestGroup,ou=Groups,dc=example,dc=com
  - cn=SampleGroup,ou=Groups,dc=example,dc=com
  ... (7 more)
```

### Causes communes

**Nettoyage incomplet :**
```bash
# Suppression des membres sans supprimer le groupe
ldapdelete "uid=user1,ou=Users,dc=example,dc=com"
ldapmodify << EOF
dn: cn=SalesTeam,ou=Groups,dc=example,dc=com
changetype: modify
delete: member
member: uid=user1,ou=Users,dc=example,dc=com
EOF
# Dernier membre supprimé → groupe vide
```

**Préparation anticipée :**
```bash
# Création d'un groupe pour un futur projet
ldapadd << EOF
dn: cn=Project2026,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: Project2026
EOF
# Membres ajoutés plus tard
```

**Tests et développement :**
```bash
# Groupes de test créés et jamais nettoyés
cn=TestGroup1
cn=TestGroup2
cn=DevTest
```

### Vérification manuelle

```bash
# Lister tous les groupes vides
ldapsearch -x -b "ou=Groups,dc=example,dc=com" \
  "(&(objectClass=groupOfNames)(!(member=*)))" dn

# Compter les groupes vides
ldapsearch -x -b "ou=Groups,dc=example,dc=com" \
  "(&(objectClass=groupOfNames)(!(member=*)))" dn | grep -c "^dn:"
```

### Nettoyage

**Dry-run (simulation) :**
```bash
ldap-health-monitor cleanup empty-groups
# Affiche ce qui serait supprimé
```

**Nettoyage réel :**
```bash
ldap-health-monitor cleanup empty-groups --confirm
```

**Script manuel :**
```bash
#!/bin/bash
# cleanup-empty-groups.sh

ldapsearch -x -b "ou=Groups,dc=example,dc=com" \
  "(&(objectClass=groupOfNames)(!(member=*)))" dn | \
  grep "^dn:" | \
  cut -d' ' -f2- | \
  while read DN; do
    echo "Deleting: $DN"
    ldapdelete "$DN"
  done
```

### Prévention

**Politique de création :**
```yaml
# Configuration requérant au moins un membre
group:
  require_initial_member: true
  minimum_members: 1
```

**Audit régulier :**
```bash
# Cron hebdomadaire
0 8 * * 1 ldap-health-monitor audit groups --empty | mail -s "Empty Groups Report" admin@example.com
```

## Groupes volumineux

### Définition

Groupe contenant un très grand nombre de membres.

**Seuil par défaut :** 100 membres
```yaml
audit:
  thresholds:
    max_group_size: 100
```

### Impact sur les performances

**Problèmes potentiels :**

1. **Temps de réponse lent :**
```
Groupe de 500 membres = ~50ms de traitement supplémentaire
Groupe de 5000 membres = ~500ms
```

2. **Charge mémoire :**
```
Membre = ~200 bytes
1000 membres = ~200KB par requête
10000 membres = ~2MB par requête
```

3. **Limite de taille LDAP :**
```
OpenLDAP limit: sizelimit 500
Active Directory limit: MaxValRange 1500
```

### Exemple de résultat

```
INFO: 5 large groups
  Found 5 groups with more than 100 members
  💡 Consider splitting large groups for better management

Details:
  - cn=AllEmployees,ou=Groups,dc=example,dc=com (1234 members)
  - cn=Engineering,ou=Groups,dc=example,dc=com (456 members)
  - cn=CompanyWide,ou=Groups,dc=example,dc=com (892 members)
  - cn=Newsletter,ou=Groups,dc=example,dc=com (678 members)
  - cn=IT-Team,ou=Groups,dc=example,dc=com (123 members)
```

### Analyse d'un groupe volumineux

```bash
# Compter les membres
ldapsearch -x -b "cn=AllEmployees,ou=Groups,dc=example,dc=com" member | grep -c "^member:"

# Afficher les statistiques
ldap-health-monitor group show "cn=AllEmployees,ou=Groups,dc=example,dc=com"
```

**Résultat :**
```
DN: cn=AllEmployees,ou=Groups,dc=example,dc=com
CN: AllEmployees
Description: All company employees
Members: 1234
```

### Stratégies de division

**Par département :**
```
cn=AllEmployees (1234)
  ├── cn=Engineering (456)
  ├── cn=Sales (234)
  ├── cn=Marketing (156)
  └── cn=Support (388)
```

**Par localisation :**
```
cn=Global (1234)
  ├── cn=Paris (567)
  ├── cn=London (345)
  └── cn=NewYork (322)
```

**Par fonction :**
```
cn=ITTeam (456)
  ├── cn=IT-Developers (234)
  ├── cn=IT-SysAdmins (89)
  └── cn=IT-Support (133)
```

### Script de division

```bash
#!/bin/bash
# split-large-group.sh

SOURCE_GROUP="cn=AllEmployees,ou=Groups,dc=example,dc=com"
BASE_OU="ou=Groups,dc=example,dc=com"

# Récupérer tous les membres
MEMBERS=$(ldapsearch -x -b "$SOURCE_GROUP" member | grep "^member:" | cut -d' ' -f2-)

# Diviser par département (attribut departmentNumber)
for DEPT in Engineering Sales Marketing Support; do
  NEW_GROUP="cn=$DEPT,$BASE_OU"

  # Créer le nouveau groupe
  ldapadd << EOF
dn: $NEW_GROUP
objectClass: groupOfNames
cn: $DEPT
member: cn=placeholder
EOF

  # Ajouter les membres du département
  echo "$MEMBERS" | while read MEMBER; do
    USER_DEPT=$(ldapsearch -x -b "$MEMBER" departmentNumber | grep "^departmentNumber:" | cut -d' ' -f2)
    if [ "$USER_DEPT" = "$DEPT" ]; then
      ldapmodify << EOF
dn: $NEW_GROUP
changetype: modify
add: member
member: $MEMBER
EOF
    fi
  done

  # Supprimer le placeholder
  ldapmodify << EOF
dn: $NEW_GROUP
changetype: modify
delete: member
member: cn=placeholder
EOF
done
```

### Monitoring des groupes volumineux

```bash
#!/bin/bash
# monitor-group-sizes.sh

ldapsearch -x -b "ou=Groups,dc=example,dc=com" "(objectClass=groupOfNames)" dn member | \
  awk '/^dn:/ {if(dn!="") print dn, count; dn=$0; count=0} /^member:/ {count++} END {print dn, count}' | \
  sort -k2 -n -r | \
  head -20
```

**Sortie :**
```
dn: cn=AllEmployees,ou=Groups,dc=example,dc=com 1234
dn: cn=CompanyWide,ou=Groups,dc=example,dc=com 892
dn: cn=Newsletter,ou=Groups,dc=example,dc=com 678
dn: cn=Engineering,ou=Groups,dc=example,dc=com 456
...
```

## Membres orphelins

### Définition

Un membre orphelin est une référence dans un groupe vers une entrée LDAP qui n'existe plus.

**Exemple :**
```ldif
dn: cn=SalesTeam,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: SalesTeam
member: uid=john,ou=Users,dc=example,dc=com      # ✅ Existe
member: uid=alice,ou=Users,dc=example,dc=com     # ✅ Existe
member: uid=olduser,ou=Users,dc=example,dc=com   # ❌ N'existe plus (orphelin)
```

### Détection

**Algorithme :**
```python
for group in groups:
    orphans = []
    for member_dn in group.members:
        entry = connector.get_entry(member_dn, attributes=["dn"])
        if not entry:
            orphans.append(member_dn)
    if orphans:
        groups_with_orphans.append({"group": group.dn, "orphans": orphans})
```

### Exemple de résultat

```
WARNING: 8 orphaned group members
  Found 8 group members that don't exist in 3 groups
  💡 Remove orphaned member references

Details:
  Group: cn=SalesTeam,ou=Groups,dc=example,dc=com
    Orphaned members:
      - uid=olduser1,ou=Users,dc=example,dc=com
      - uid=deleted2,ou=Users,dc=example,dc=com

  Group: cn=Engineering,ou=Groups,dc=example,dc=com
    Orphaned members:
      - uid=former-employee,ou=Users,dc=example,dc=com
      - uid=temp123,ou=Users,dc=example,dc=com
      - uid=contractor1,ou=Users,dc=example,dc=com

  Group: cn=Project-X,ou=Groups,dc=example,dc=com
    Orphaned members:
      - uid=exuser1,ou=Users,dc=example,dc=com
      - uid=exuser2,ou=Users,dc=example,dc=com
      - uid=exuser3,ou=Users,dc=example,dc=com
```

### Causes

**Suppression d'utilisateur sans mise à jour des groupes :**
```bash
# ❌ Mauvaise pratique
ldapdelete "uid=john,ou=Users,dc=example,dc=com"
# Les groupes contenant john ont maintenant une référence orpheline
```

**Déplacement d'entrée :**
```bash
# Changement du DN
ldapmodrdn "uid=alice,ou=Temp,dc=example,dc=com" "uid=alice" \
  -newsuperior "ou=Users,dc=example,dc=com"
# Ancienne référence orpheline si non mise à jour
```

**Corruption de données :**
- Réplication échouée
- Restauration partielle de backup
- Modification manuelle incorrecte

### Impact

**Problèmes fonctionnels :**
- Erreurs dans les applications
- Permissions invalides
- Listes de diffusion cassées

**Problèmes de performance :**
- Requêtes qui échouent
- Timeout sur les recherches
- Logs remplis d'erreurs

### Nettoyage des orphelins

**Vérification manuelle :**
```bash
#!/bin/bash
# check-orphans.sh

GROUP_DN="cn=SalesTeam,ou=Groups,dc=example,dc=com"

ldapsearch -x -b "$GROUP_DN" member | grep "^member:" | cut -d' ' -f2- | while read MEMBER; do
  if ! ldapsearch -x -b "$MEMBER" -s base dn 2>/dev/null | grep -q "^dn:"; then
    echo "Orphan: $MEMBER"
  fi
done
```

**Nettoyage automatique :**
```bash
#!/bin/bash
# remove-orphans.sh

GROUP_DN="cn=SalesTeam,ou=Groups,dc=example,dc=com"

ldapsearch -x -b "$GROUP_DN" member | grep "^member:" | cut -d' ' -f2- | while read MEMBER; do
  if ! ldapsearch -x -b "$MEMBER" -s base dn 2>/dev/null | grep -q "^dn:"; then
    echo "Removing orphan: $MEMBER"
    ldapmodify << EOF
dn: $GROUP_DN
changetype: modify
delete: member
member: $MEMBER
EOF
  fi
done
```

**Avec Python :**
```python
#!/usr/bin/env python3
# cleanup_orphans.py

from ldap3 import Server, Connection, ALL

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

# Récupérer tous les groupes
conn.search('ou=Groups,dc=example,dc=com', '(objectClass=groupOfNames)', attributes=['member'])

for entry in conn.entries:
    group_dn = entry.entry_dn
    members = entry.member.values if hasattr(entry, 'member') else []

    for member in members:
        # Vérifier si le membre existe
        if not conn.search(member, '(objectClass=*)', search_scope='BASE'):
            print(f"Removing orphan {member} from {group_dn}")
            conn.modify(group_dn, {'member': [(MODIFY_DELETE, [member])]})

conn.unbind()
```

### Prévention

**Utiliser l'intégrité référentielle :**

**OpenLDAP (slapo-refint) :**
```ldif
dn: olcOverlay=refint,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcRefintConfig
olcOverlay: refint
olcRefintAttribute: member
olcRefintAttribute: memberOf
olcRefintNothing: cn=placeholder,ou=Groups,dc=example,dc=com
```

**Procédure de suppression sécurisée :**
```bash
#!/bin/bash
# safe-delete-user.sh

USER_DN="$1"

if [ -z "$USER_DN" ]; then
  echo "Usage: $0 <user-dn>"
  exit 1
fi

# 1. Trouver tous les groupes contenant l'utilisateur
echo "Finding groups containing $USER_DN..."
GROUPS=$(ldapsearch -x -b "ou=Groups,dc=example,dc=com" \
  "(&(objectClass=groupOfNames)(member=$USER_DN))" dn | \
  grep "^dn:" | cut -d' ' -f2-)

# 2. Retirer des groupes
echo "$GROUPS" | while read GROUP_DN; do
  if [ -n "$GROUP_DN" ]; then
    echo "Removing from: $GROUP_DN"
    ldapmodify << EOF
dn: $GROUP_DN
changetype: modify
delete: member
member: $USER_DN
EOF
  fi
done

# 3. Supprimer l'utilisateur
echo "Deleting user: $USER_DN"
ldapdelete "$USER_DN"

echo "Done!"
```

## Membres en double

### Définition

Un membre apparaît plusieurs fois dans le même groupe.

**Exemple :**
```ldif
dn: cn=DevTeam,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: DevTeam
member: uid=alice,ou=Users,dc=example,dc=com
member: uid=bob,ou=Users,dc=example,dc=com
member: uid=alice,ou=Users,dc=example,dc=com  # ❌ Doublon
```

### Détection

```python
for group in groups:
    seen = set()
    duplicates = []

    for member in group.members:
        if member in seen:
            duplicates.append(member)
        seen.add(member)

    if duplicates:
        groups_with_duplicates.append({
            "group": group.dn,
            "duplicates": list(set(duplicates))
        })
```

### Exemple de résultat

```
WARNING: 3 groups with duplicate members
  Found 3 groups containing duplicate member entries
  💡 Remove duplicate member entries

Details:
  Group: cn=DevTeam,ou=Groups,dc=example,dc=com
    Duplicates:
      - uid=alice,ou=Users,dc=example,dc=com (appears 2 times)

  Group: cn=Managers,ou=Groups,dc=example,dc=com
    Duplicates:
      - uid=john,ou=Users,dc=example,dc=com (appears 3 times)
      - uid=sarah,ou=Users,dc=example,dc=com (appears 2 times)

  Group: cn=QA,ou=Groups,dc=example,dc=com
    Duplicates:
      - uid=tester1,ou=Users,dc=example,dc=com (appears 2 times)
```

### Causes

**Ajouts multiples accidentels :**
```bash
# Script exécuté plusieurs fois
ldapmodify << EOF
dn: cn=DevTeam,ou=Groups,dc=example,dc=com
changetype: modify
add: member
member: uid=alice,ou=Users,dc=example,dc=com
EOF
```

**Scripts sans vérification :**
```bash
# ❌ Pas de vérification si déjà membre
add_to_group() {
  ldapmodify << EOF
dn: $1
changetype: modify
add: member
member: $2
EOF
}
```

**Synchronisation défaillante :**
- Réplication en conflit
- Import CSV avec doublons
- Migration mal gérée

### Vérification manuelle

```bash
#!/bin/bash
# find-duplicate-members.sh

GROUP_DN="cn=DevTeam,ou=Groups,dc=example,dc=com"

ldapsearch -x -b "$GROUP_DN" member | \
  grep "^member:" | \
  cut -d' ' -f2- | \
  sort | \
  uniq -d
```

### Nettoyage

**Méthode 1 : Supprimer toutes les occurrences puis rajouter une fois :**
```bash
#!/bin/bash
# clean-duplicates.sh

GROUP_DN="$1"
DUPLICATE="$2"

# Supprimer toutes les occurrences
ldapmodify << EOF
dn: $GROUP_DN
changetype: modify
delete: member
member: $DUPLICATE
EOF

# Rajouter une seule fois
ldapmodify << EOF
dn: $GROUP_DN
changetype: modify
add: member
member: $DUPLICATE
EOF
```

**Méthode 2 : Reconstruire le groupe :**
```bash
#!/bin/bash
# rebuild-group.sh

GROUP_DN="$1"

# Récupérer les membres uniques
UNIQUE_MEMBERS=$(ldapsearch -x -b "$GROUP_DN" member | \
  grep "^member:" | \
  cut -d' ' -f2- | \
  sort -u)

# Supprimer tous les membres
ldapmodify << EOF
dn: $GROUP_DN
changetype: modify
delete: member
EOF

# Rajouter les membres uniques
echo "$UNIQUE_MEMBERS" | while read MEMBER; do
  ldapmodify << EOF
dn: $GROUP_DN
changetype: modify
add: member
member: $MEMBER
EOF
done
```

### Prévention

**Script avec vérification :**
```bash
#!/bin/bash
# safe-add-member.sh

GROUP_DN="$1"
MEMBER_DN="$2"

# Vérifier si déjà membre
if ldapsearch -x -b "$GROUP_DN" member | grep -q "^member: $MEMBER_DN$"; then
  echo "Already a member: $MEMBER_DN"
  exit 0
fi

# Ajouter
ldapmodify << EOF
dn: $GROUP_DN
changetype: modify
add: member
member: $MEMBER_DN
EOF
```

**Code Python avec vérification :**
```python
def add_member_safe(conn, group_dn, member_dn):
    """Ajoute un membre uniquement s'il n'est pas déjà présent"""
    conn.search(group_dn, '(objectClass=*)', attributes=['member'])

    if conn.entries:
        current_members = conn.entries[0].member.values if hasattr(conn.entries[0], 'member') else []

        if member_dn in current_members:
            print(f"{member_dn} is already a member of {group_dn}")
            return False

    conn.modify(group_dn, {'member': [(MODIFY_ADD, [member_dn])]})
    return True
```

## Groupes imbriqués

### Définition

Un groupe contenant d'autres groupes comme membres.

**Exemple :**
```ldif
dn: cn=AllIT,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: AllIT
member: cn=Developers,ou=Groups,dc=example,dc=com
member: cn=SysAdmins,ou=Groups,dc=example,dc=com
member: cn=Support,ou=Groups,dc=example,dc=com

dn: cn=Developers,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: Developers
member: uid=alice,ou=Users,dc=example,dc=com
member: uid=bob,ou=Users,dc=example,dc=com
```

### Analyse des imbrications

```bash
#!/bin/bash
# analyze-nested-groups.sh

GROUP_DN="$1"

echo "Analyzing: $GROUP_DN"
echo "Direct members:"

ldapsearch -x -b "$GROUP_DN" member | grep "^member:" | cut -d' ' -f2- | while read MEMBER; do
  echo "  - $MEMBER"

  # Vérifier si c'est un groupe
  if ldapsearch -x -b "$MEMBER" -s base "(objectClass=groupOfNames)" dn 2>/dev/null | grep -q "^dn:"; then
    echo "    (GROUP - nested)"

    # Lister les membres du sous-groupe
    ldapsearch -x -b "$MEMBER" member | grep "^member:" | cut -d' ' -f2- | while read SUB_MEMBER; do
      echo "      -> $SUB_MEMBER"
    done
  fi
done
```

### Profondeur d'imbrication

**Script de calcul de profondeur :**
```python
#!/usr/bin/env python3
# check-nesting-depth.py

def get_nesting_depth(conn, group_dn, visited=None, depth=0):
    """Calcule la profondeur maximale d'imbrication"""
    if visited is None:
        visited = set()

    if group_dn in visited:
        return depth  # Éviter les cycles

    visited.add(group_dn)

    conn.search(group_dn, '(objectClass=*)', attributes=['member'])

    if not conn.entries:
        return depth

    members = conn.entries[0].member.values if hasattr(conn.entries[0], 'member') else []
    max_depth = depth

    for member in members:
        # Vérifier si c'est un groupe
        if conn.search(member, '(objectClass=groupOfNames)', search_scope='BASE'):
            member_depth = get_nesting_depth(conn, member, visited.copy(), depth + 1)
            max_depth = max(max_depth, member_depth)

    return max_depth

# Utilisation
depth = get_nesting_depth(conn, 'cn=AllIT,ou=Groups,dc=example,dc=com')
print(f"Maximum nesting depth: {depth}")
```

### Détection de cycles

**Cycle d'imbrication (à éviter) :**
```
cn=GroupA → member: cn=GroupB
cn=GroupB → member: cn=GroupC
cn=GroupC → member: cn=GroupA  # ❌ Cycle!
```

**Script de détection :**
```python
def detect_cycles(conn, group_dn, path=None):
    """Détecte les cycles dans les groupes imbriqués"""
    if path is None:
        path = []

    if group_dn in path:
        print(f"CYCLE DETECTED: {' -> '.join(path)} -> {group_dn}")
        return True

    path.append(group_dn)

    conn.search(group_dn, '(objectClass=*)', attributes=['member'])

    if conn.entries:
        members = conn.entries[0].member.values if hasattr(conn.entries[0], 'member') else []

        for member in members:
            if conn.search(member, '(objectClass=groupOfNames)', search_scope='BASE'):
                if detect_cycles(conn, member, path.copy()):
                    return True

    return False
```

### Résolution récursive de membres

**Obtenir tous les membres (y compris imbriqués) :**
```python
def get_all_members_recursive(conn, group_dn, visited=None):
    """Obtient tous les membres, incluant ceux des groupes imbriqués"""
    if visited is None:
        visited = set()

    if group_dn in visited:
        return set()  # Éviter boucles infinies

    visited.add(group_dn)
    all_members = set()

    conn.search(group_dn, '(objectClass=*)', attributes=['member'])

    if conn.entries:
        members = conn.entries[0].member.values if hasattr(conn.entries[0], 'member') else []

        for member in members:
            # Si c'est un groupe, récursion
            if conn.search(member, '(objectClass=groupOfNames)', search_scope='BASE'):
                all_members.update(get_all_members_recursive(conn, member, visited.copy()))
            else:
                # Sinon, c'est un utilisateur
                all_members.add(member)

    return all_members

# Utilisation
members = get_all_members_recursive(conn, 'cn=AllIT,ou=Groups,dc=example,dc=com')
print(f"Total members (including nested): {len(members)}")
for member in sorted(members):
    print(f"  - {member}")
```

## Exemples pratiques

### Exemple 1 : Audit hebdomadaire complet

```bash
#!/bin/bash
# weekly-groups-audit.sh

OUTPUT_DIR="/var/reports/ldap/groups"
DATE=$(date +%Y-%m-%d)

mkdir -p "$OUTPUT_DIR"

echo "=== Groups Audit - $DATE ===" | tee "$OUTPUT_DIR/audit-$DATE.txt"

# Audit complet
ldap-health-monitor audit groups \
  --format json \
  --output "$OUTPUT_DIR/audit-$DATE.json"

# Rapport console
ldap-health-monitor audit groups | tee -a "$OUTPUT_DIR/audit-$DATE.txt"

# Statistiques
ldap-health-monitor audit groups --format json | \
  jq '.statistics' > "$OUTPUT_DIR/stats-$DATE.json"

# Envoi email si problèmes
ISSUES=$(ldap-health-monitor audit groups --format json | jq -r '.issues | length')
if [ "$ISSUES" -gt 0 ]; then
  mail -s "⚠️ Groups Audit: $ISSUES issues found" admin@example.com < "$OUTPUT_DIR/audit-$DATE.txt"
fi
```

### Exemple 2 : Dashboard de monitoring

```bash
#!/bin/bash
# groups-dashboard.sh

cat > /var/www/html/ldap-groups.html << 'EOF'
<!DOCTYPE html>
<html>
<head>
    <title>LDAP Groups Dashboard</title>
    <meta http-equiv="refresh" content="300">
    <style>
        body { font-family: Arial; margin: 20px; }
        .stat { display: inline-block; margin: 10px; padding: 15px; background: #f0f0f0; border-radius: 5px; }
        .warning { background: #fff3cd; }
        .critical { background: #f8d7da; }
    </style>
</head>
<body>
    <h1>LDAP Groups Status</h1>
    <p>Last update: $(date)</p>
EOF

# Récupérer les données
DATA=$(ldap-health-monitor audit groups --format json)

# Statistiques
TOTAL=$(echo "$DATA" | jq -r '.statistics.total')
EMPTY=$(echo "$DATA" | jq -r '.statistics.empty')
AVG=$(echo "$DATA" | jq -r '.statistics.average_members')

cat >> /var/www/html/ldap-groups.html << EOF
    <div class="stat">
        <h3>$TOTAL</h3>
        <p>Total Groups</p>
    </div>
    <div class="stat warning">
        <h3>$EMPTY</h3>
        <p>Empty Groups</p>
    </div>
    <div class="stat">
        <h3>$AVG</h3>
        <p>Avg Members/Group</p>
    </div>

    <h2>Issues</h2>
EOF

echo "$DATA" | jq -r '.issues[] | "<div class=\"stat warning\"><p>" + .title + "</p></div>"' >> /var/www/html/ldap-groups.html

cat >> /var/www/html/ldap-groups.html << 'EOF'
</body>
</html>
EOF
```

## Nettoyage et maintenance

### Maintenance régulière

**Script de maintenance mensuel :**
```bash
#!/bin/bash
# monthly-groups-maintenance.sh

echo "=== Groups Maintenance - $(date) ==="

# 1. Backup avant maintenance
echo "Creating backup..."
ldap-health-monitor backup full --output /backups/ldap-$(date +%Y%m%d).ldif

# 2. Audit initial
echo "Initial audit..."
ldap-health-monitor audit groups --format json --output /tmp/before.json

# 3. Nettoyage des orphelins
echo "Cleaning orphaned members..."
# Script custom de nettoyage

# 4. Nettoyage des doublons
echo "Cleaning duplicate members..."
# Script custom de nettoyage

# 5. Suppression des groupes vides (avec confirmation)
echo "Empty groups found:"
ldap-health-monitor cleanup empty-groups

read -p "Remove empty groups? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
  ldap-health-monitor cleanup empty-groups --confirm
fi

# 6. Audit final
echo "Final audit..."
ldap-health-monitor audit groups --format json --output /tmp/after.json

# 7. Rapport
echo "Comparison:"
echo "Before: $(jq -r '.issues | length' /tmp/before.json) issues"
echo "After: $(jq -r '.issues | length' /tmp/after.json) issues"
```

## Bonnes pratiques

### Politique de groupes

1. **Conventions de nommage**
```
cn=<type>-<function>-<location>
Exemples:
  cn=SEC-Admins-Global
  cn=APP-Developers-Paris
  cn=DL-Marketing-All
```

2. **Documentation des groupes**
```ldif
dn: cn=DevTeam,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: DevTeam
description: Development team members - Contact: dev-lead@example.com
owner: uid=manager,ou=Users,dc=example,dc=com
```

3. **Révision régulière**
```bash
# Audit trimestriel avec révision manuelle
# Liste les groupes pour validation
```

### Automatisation

**Webhook pour nettoyage automatique :**
```python
# auto-cleanup-webhook.py
@app.route('/webhook/group-audit', methods=['POST'])
def group_audit_webhook():
    # Exécuter audit
    result = run_audit()

    # Auto-cleanup des problèmes simples
    if result['empty_groups'] and len(result['empty_groups']) < 10:
        cleanup_empty_groups(result['empty_groups'])

    # Notification des problèmes complexes
    if result['orphaned_members']:
        send_alert(result['orphaned_members'])

    return jsonify(result)
```

## Dépannage

### Audit lent

**Problème :** L'audit prend trop de temps

**Solutions :**
```yaml
# Augmenter les timeouts
ldap:
  timeout: 120

# Limiter la portée
ldap:
  groups_ou: "ou=ActiveGroups,ou=Groups,dc=example,dc=com"
```

### Faux positifs

**Problème :** Groupes signalés comme vides mais contenant des membres

**Diagnostic :**
```bash
# Vérifier l'attribut member
ldapsearch -x -b "cn=Group,ou=Groups,dc=example,dc=com" member

# Vérifier d'autres attributs (memberUid, uniqueMember)
ldapsearch -x -b "cn=Group,ou=Groups,dc=example,dc=com" memberUid uniqueMember
```

**Configuration :**
```yaml
ldap:
  group_member_attribute: memberUid  # Au lieu de member
```

## Conclusion

L'audit des groupes est essentiel pour maintenir un annuaire LDAP propre et performant. En intégrant ces audits dans votre routine de maintenance, vous prévenez les problèmes avant qu'ils n'impactent vos utilisateurs.

**Points clés :**
- Audit hebdomadaire recommandé
- Nettoyage mensuel des groupes vides
- Vérification régulière des orphelins
- Documentation de la structure des groupes
- Automatisation du monitoring

Pour aller plus loin :
- [Audit de structure](./Structure-Audit.md)
- [Audit de cohérence](./Consistency-Audit.md)
- [Génération de rapports](./Audit-Reports.md)
