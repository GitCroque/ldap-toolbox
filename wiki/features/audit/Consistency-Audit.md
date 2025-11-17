# Audit de cohérence des données LDAP

## Introduction

L'audit de cohérence garantit que les données de votre annuaire LDAP sont intègres, sans corruption, et que toutes les références entre entrées sont valides. C'est essentiel pour maintenir la fiabilité de votre infrastructure.

## Table des matières

1. [Vue d'ensemble](#vue-densemble)
2. [Intégrité référentielle](#intégrité-référentielle)
3. [Entrées en double](#entrées-en-double)
4. [Références brisées](#références-brisées)
5. [Cohérence des attributs](#cohérence-des-attributs)
6. [Validation du schéma](#validation-du-schéma)
7. [Cohérence de réplication](#cohérence-de-réplication)
8. [Détection de corruption](#détection-de-corruption)
9. [Exemples pratiques](#exemples-pratiques)
10. [Réparation des données](#réparation-des-données)
11. [Prévention](#prévention)
12. [Dépannage](#dépannage)

## Vue d'ensemble

### Qu'est-ce que l'audit de cohérence ?

L'audit de cohérence vérifie :
- **Intégrité référentielle** : Toutes les références DN pointent vers des entrées existantes
- **Unicité** : Pas d'entrées ou d'attributs en double inappropriés
- **Cohérence des données** : Les valeurs sont logiques et valides
- **Conformité au schéma** : Les entrées respectent les objectClass
- **Réplication** : Les serveurs sont synchronisés
- **Corruption** : Pas de données corrompues

### Types de problèmes détectés

| Problème | Gravité | Fréquence | Impact |
|----------|---------|-----------|--------|
| Références brisées | Élevée | Courant | Erreurs applicatives |
| Entrées en double | Moyenne | Rare | Ambiguïté |
| Violations de schéma | Élevée | Rare | Instabilité |
| Désynchronisation | Critique | Occasionnel | Incohérences |
| Corruption | Critique | Très rare | Perte de données |

### Architecture de l'audit

```
┌────────────────────┐
│ ConsistencyAuditor │
└──────────┬─────────┘
           │
    ┌──────▼────────────────────────────┐
    │ _check_referential_integrity()    │
    │ _check_duplicate_entries()        │
    │ _check_broken_references()        │
    │ _check_attribute_consistency()    │
    │ _validate_schema()                │
    │ _check_replication_consistency()  │
    └──────┬────────────────────────────┘
           │
    ┌──────▼─────────┐
    │ AuditIssue[]   │
    └────────────────┘
```

## Intégrité référentielle

### Qu'est-ce que l'intégrité référentielle ?

L'intégrité référentielle garantit que toutes les références DN pointent vers des entrées qui existent.

**Exemple de référence valide :**
```ldif
dn: cn=Developers,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: Developers
member: uid=alice,ou=Users,dc=example,dc=com  # ✓ Alice existe
member: uid=bob,ou=Users,dc=example,dc=com    # ✓ Bob existe
```

**Exemple de référence brisée :**
```ldif
dn: cn=Developers,ou=Groups,dc=example,dc=com
objectClass: groupOfNames
cn: Developers
member: uid=alice,ou=Users,dc=example,dc=com    # ✓ Alice existe
member: uid=deleted,ou=Users,dc=example,dc=com  # ✗ Utilisateur supprimé
```

### Vérification de l'intégrité référentielle

**Script complet :**
```bash
#!/bin/bash
# check-referential-integrity.sh

echo "=== Referential Integrity Check ==="
echo "Started: $(date)"
echo ""

ISSUES=0
CHECKED=0

# Attributs contenant des références DN
REF_ATTRIBUTES=(
  "member"
  "memberOf"
  "manager"
  "secretary"
  "seeAlso"
  "owner"
  "roleOccupant"
)

for ATTR in "${REF_ATTRIBUTES[@]}"; do
  echo "Checking attribute: $ATTR"

  # Récupérer toutes les entrées ayant cet attribut
  ldapsearch -x -b "dc=example,dc=com" \
    "($ATTR=*)" \
    dn $ATTR 2>/dev/null | \

  awk -v attr="$ATTR" '
    /^dn: / { current_dn = substr($0, 5) }
    /^'"$ATTR"': / {
      ref_dn = substr($0, length("'"$ATTR"': ") + 1)
      print current_dn "|" ref_dn
    }
  ' | \

  while IFS='|' read SOURCE_DN REF_DN; do
    CHECKED=$((CHECKED + 1))

    # Vérifier si la référence existe
    if ! ldapsearch -x -b "$REF_DN" -s base dn 2>/dev/null | grep -q "^dn:"; then
      echo "  ✗ BROKEN: $SOURCE_DN"
      echo "     References non-existent: $REF_DN"
      ISSUES=$((ISSUES + 1))
    fi

    # Afficher progression tous les 100
    if [ $((CHECKED % 100)) -eq 0 ]; then
      echo "  Progress: $CHECKED references checked, $ISSUES issues found"
    fi
  done

  echo "  $ATTR: Done"
  echo ""
done

echo "==================================="
echo "Total references checked: $CHECKED"
echo "Broken references found: $ISSUES"
echo "Completed: $(date)"
```

### Détection avancée

**Script Python avec détails :**
```python
#!/usr/bin/env python3
# check-referential-integrity.py

from ldap3 import Server, Connection, ALL
from collections import defaultdict

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

# Attributs à vérifier
reference_attributes = [
    'member', 'memberOf', 'manager', 'secretary',
    'seeAlso', 'owner', 'roleOccupant'
]

issues = defaultdict(list)
checked = 0

print("=== Referential Integrity Check ===\n")

for attr in reference_attributes:
    print(f"Checking attribute: {attr}")

    # Rechercher toutes les entrées ayant cet attribut
    conn.search(
        'dc=example,dc=com',
        f'({attr}=*)',
        attributes=[attr]
    )

    for entry in conn.entries:
        source_dn = str(entry.entry_dn)

        # Récupérer les valeurs de l'attribut
        if hasattr(entry, attr):
            values = getattr(entry, attr).values
            if not isinstance(values, list):
                values = [values]

            for ref_dn in values:
                checked += 1

                # Vérifier que la référence existe
                if not conn.search(str(ref_dn), '(objectClass=*)', search_scope='BASE'):
                    issues[attr].append({
                        'source': source_dn,
                        'broken_reference': str(ref_dn),
                        'attribute': attr
                    })

                # Afficher progression
                if checked % 100 == 0:
                    print(f"  Progress: {checked} references checked")

    print(f"  {attr}: {len(issues[attr])} issues found\n")

# Résumé
print("=" * 50)
print(f"Total references checked: {checked}")
print(f"Total issues found: {sum(len(v) for v in issues.values())}")
print()

# Détails des problèmes
if any(issues.values()):
    print("=== Issues Details ===\n")
    for attr, attr_issues in issues.items():
        if attr_issues:
            print(f"{attr}: {len(attr_issues)} broken references")
            for issue in attr_issues[:10]:  # Afficher les 10 premiers
                print(f"  Source: {issue['source']}")
                print(f"  Broken: {issue['broken_reference']}")
                print()

    # Export JSON
    import json
    with open('referential-integrity-issues.json', 'w') as f:
        json.dump(dict(issues), f, indent=2)
    print("Full report saved to: referential-integrity-issues.json")
else:
    print("✓ No referential integrity issues found!")

conn.unbind()
```

### Réparation automatique

**Script de nettoyage :**
```bash
#!/bin/bash
# fix-broken-references.sh

# ⚠️  Toujours faire un backup avant !

ISSUES_FILE="referential-integrity-issues.json"

if [ ! -f "$ISSUES_FILE" ]; then
  echo "Error: Run check-referential-integrity.py first"
  exit 1
fi

echo "=== Fixing Broken References ==="
echo "This will remove broken references from entries"
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Cancelled"
  exit 0
fi

# Parser le fichier JSON et corriger chaque problème
jq -r '.[] | .[] | "\(.source)|\(.attribute)|\(.broken_reference)"' "$ISSUES_FILE" | \
while IFS='|' read SOURCE_DN ATTR BROKEN_REF; do
  echo "Fixing: $SOURCE_DN"
  echo "  Removing broken reference to: $BROKEN_REF"

  ldapmodify << EOF
dn: $SOURCE_DN
changetype: modify
delete: $ATTR
$ATTR: $BROKEN_REF
EOF

  if [ $? -eq 0 ]; then
    echo "  ✓ Fixed"
  else
    echo "  ✗ Failed"
  fi
  echo ""
done

echo "=== Repair Complete ==="
```

## Entrées en double

### Types de doublons

**1. DN en double (impossible normalement)**
- Ne devrait jamais arriver
- Indique une corruption majeure

**2. Attributs uniques en double**
```bash
# Deux utilisateurs avec le même email
uid=alice,ou=Users,dc=example,dc=com → mail: alice@example.com
uid=alice2,ou=Users,dc=example,dc=com → mail: alice@example.com
```

**3. Entrées similaires**
```bash
# Même personne, deux comptes différents
uid=john.doe,ou=Users,dc=example,dc=com
uid=jdoe,ou=Users,dc=example,dc=com
```

### Détection des doublons

**Script de détection :**
```python
#!/usr/bin/env python3
# detect-duplicates.py

from ldap3 import Server, Connection, ALL
from collections import defaultdict

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

# Attributs qui doivent être uniques
unique_attributes = ['mail', 'employeeNumber', 'telephoneNumber']

print("=== Duplicate Detection ===\n")

for attr in unique_attributes:
    print(f"Checking for duplicate {attr}...")

    # Récupérer toutes les valeurs
    conn.search(
        'ou=Users,dc=example,dc=com',
        '(objectClass=person)',
        attributes=[attr, 'cn']
    )

    # Grouper par valeur d'attribut
    values_map = defaultdict(list)

    for entry in conn.entries:
        if hasattr(entry, attr):
            value = str(getattr(entry, attr))
            if value:  # Ignorer les valeurs vides
                cn = str(entry.cn) if hasattr(entry, 'cn') else 'Unknown'
                values_map[value.lower()].append({
                    'dn': str(entry.entry_dn),
                    'cn': cn
                })

    # Trouver les doublons
    duplicates = {k: v for k, v in values_map.items() if len(v) > 1}

    if duplicates:
        print(f"  Found {len(duplicates)} duplicate {attr} values:\n")
        for value, entries in duplicates.items():
            print(f"  {attr}: {value}")
            for entry in entries:
                print(f"    - {entry['cn']} ({entry['dn']})")
            print()
    else:
        print(f"  ✓ No duplicates found\n")

conn.unbind()
```

### Recherche de doublons phonétiques

**Utilisation de soundex/metaphone :**
```python
#!/usr/bin/env python3
# detect-phonetic-duplicates.py

from ldap3 import Server, Connection, ALL
import jellyfish  # pip install jellyfish

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

print("=== Phonetic Duplicate Detection ===\n")

# Récupérer tous les utilisateurs
conn.search(
    'ou=Users,dc=example,dc=com',
    '(objectClass=person)',
    attributes=['cn', 'givenName', 'sn']
)

# Grouper par soundex
soundex_map = {}

for entry in conn.entries:
    if hasattr(entry, 'cn'):
        cn = str(entry.cn)
        soundex = jellyfish.soundex(cn)

        if soundex not in soundex_map:
            soundex_map[soundex] = []

        soundex_map[soundex].append({
            'dn': str(entry.entry_dn),
            'cn': cn
        })

# Afficher les groupes de noms similaires
print("Potential phonetic duplicates:\n")
for soundex, entries in soundex_map.items():
    if len(entries) > 1:
        print(f"Soundex: {soundex}")
        for entry in entries:
            print(f"  - {entry['cn']}")
            print(f"    {entry['dn']}")
        print()

conn.unbind()
```

### Fusion de doublons

**Script interactif :**
```python
#!/usr/bin/env python3
# merge-duplicates.py

from ldap3 import Server, Connection, ALL

def merge_entries(conn, primary_dn, secondary_dn):
    """Fusionne deux entrées en gardant primary"""

    print(f"\nMerging:")
    print(f"  Primary (keep):   {primary_dn}")
    print(f"  Secondary (merge): {secondary_dn}")

    # Récupérer les deux entrées
    conn.search(primary_dn, '(objectClass=*)', search_scope='BASE', attributes='*')
    primary = conn.entries[0]

    conn.search(secondary_dn, '(objectClass=*)', search_scope='BASE', attributes='*')
    secondary = conn.entries[0]

    # Fusionner les attributs
    modifications = {}

    for attr in secondary.entry_attributes:
        if attr not in ['dn', 'objectClass']:
            primary_value = getattr(primary, attr, None)
            secondary_value = getattr(secondary, attr, None)

            # Si primary n'a pas cet attribut, le copier
            if not primary_value and secondary_value:
                modifications[attr] = [(MODIFY_ADD, [str(secondary_value)])]
                print(f"  Adding {attr}: {secondary_value}")

    # Appliquer les modifications
    if modifications:
        conn.modify(primary_dn, modifications)
        print("  ✓ Attributes merged")

    # Mettre à jour les références
    print("  Updating references...")
    update_references(conn, secondary_dn, primary_dn)

    # Supprimer l'entrée secondaire
    print("  Deleting secondary entry...")
    conn.delete(secondary_dn)
    print("  ✓ Merge complete")

def update_references(conn, old_dn, new_dn):
    """Met à jour toutes les références vers old_dn"""
    reference_attrs = ['member', 'memberOf', 'manager']

    for attr in reference_attrs:
        conn.search(
            'dc=example,dc=com',
            f'({attr}={old_dn})',
            attributes=[attr]
        )

        for entry in conn.entries:
            conn.modify(
                entry.entry_dn,
                {attr: [(MODIFY_DELETE, [old_dn]), (MODIFY_ADD, [new_dn])]}
            )

# Utilisation
server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

# Exemple de fusion
primary = "uid=alice,ou=Users,dc=example,dc=com"
secondary = "uid=alice2,ou=Users,dc=example,dc=com"

merge_entries(conn, primary, secondary)

conn.unbind()
```

## Références brisées

### Types de références brisées

**1. Références vers des entrées supprimées**
```ldif
# Groupe référençant un utilisateur supprimé
dn: cn=Team,ou=Groups,dc=example,dc=com
member: uid=deleted-user,ou=Users,dc=example,dc=com  # N'existe plus
```

**2. Références circulaires**
```ldif
# A référence B, B référence A
dn: uid=alice,ou=Users,dc=example,dc=com
manager: uid=bob,ou=Users,dc=example,dc=com

dn: uid=bob,ou=Users,dc=example,dc=com
manager: uid=alice,ou=Users,dc=example,dc=com  # Circulaire !
```

**3. Références vers des OUs inexistantes**
```ldif
dn: uid=alice,ou=NonExistent,dc=example,dc=com  # OU n'existe pas
```

### Détection de références circulaires

```python
#!/usr/bin/env python3
# detect-circular-references.py

from ldap3 import Server, Connection, ALL

def find_circular_references(conn, start_dn, attr, visited=None):
    """Détecte les références circulaires"""
    if visited is None:
        visited = set()

    if start_dn in visited:
        return [start_dn]  # Cycle détecté

    visited.add(start_dn)

    # Récupérer l'attribut de référence
    conn.search(start_dn, '(objectClass=*)', search_scope='BASE', attributes=[attr])

    if not conn.entries:
        return None

    entry = conn.entries[0]

    if hasattr(entry, attr):
        ref_dn = str(getattr(entry, attr))

        # Continuer la recherche
        cycle = find_circular_references(conn, ref_dn, attr, visited.copy())
        if cycle:
            return [start_dn] + cycle

    return None

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

print("=== Circular Reference Detection ===\n")

# Vérifier tous les attributs 'manager'
conn.search('ou=Users,dc=example,dc=com', '(manager=*)', attributes=['manager'])

for entry in conn.entries:
    cycle = find_circular_references(conn, str(entry.entry_dn), 'manager')
    if cycle:
        print("Circular reference detected:")
        for dn in cycle:
            print(f"  → {dn}")
        print()

conn.unbind()
```

## Cohérence des attributs

### Validation des attributs obligatoires

**Vérification :**
```python
#!/usr/bin/env python3
# validate-required-attributes.py

from ldap3 import Server, Connection, ALL

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

# Définir les attributs obligatoires par objectClass
required_attributes = {
    'inetOrgPerson': ['cn', 'sn', 'mail', 'givenName'],
    'groupOfNames': ['cn', 'member'],
    'organizationalUnit': ['ou'],
}

print("=== Required Attributes Validation ===\n")

for object_class, required in required_attributes.items():
    print(f"Checking {object_class}...")

    conn.search(
        'dc=example,dc=com',
        f'(objectClass={object_class})',
        attributes=['*']
    )

    issues = []

    for entry in conn.entries:
        missing = []
        for attr in required:
            if not hasattr(entry, attr) or not getattr(entry, attr):
                missing.append(attr)

        if missing:
            issues.append({
                'dn': str(entry.entry_dn),
                'missing': missing
            })

    if issues:
        print(f"  Found {len(issues)} entries with missing required attributes:\n")
        for issue in issues[:10]:  # Afficher les 10 premiers
            print(f"    {issue['dn']}")
            print(f"      Missing: {', '.join(issue['missing'])}")
    else:
        print(f"  ✓ All entries valid\n")

conn.unbind()
```

### Validation du format des attributs

**Script de validation :**
```python
#!/usr/bin/env python3
# validate-attribute-formats.py

import re
from ldap3 import Server, Connection, ALL

# Patterns de validation
validators = {
    'mail': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
    'telephoneNumber': r'^\+?[0-9\s\-\(\)]+$',
    'postalCode': r'^[0-9]{5}$',
    'employeeNumber': r'^[0-9]+$',
}

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

print("=== Attribute Format Validation ===\n")

for attr, pattern in validators.items():
    print(f"Validating {attr}...")

    conn.search(
        'ou=Users,dc=example,dc=com',
        f'({attr}=*)',
        attributes=[attr]
    )

    invalid = []

    for entry in conn.entries:
        if hasattr(entry, attr):
            value = str(getattr(entry, attr))
            if not re.match(pattern, value):
                invalid.append({
                    'dn': str(entry.entry_dn),
                    'value': value
                })

    if invalid:
        print(f"  Found {len(invalid)} invalid values:\n")
        for item in invalid[:10]:
            print(f"    {item['dn']}")
            print(f"      Invalid value: {item['value']}")
    else:
        print(f"  ✓ All values valid\n")

conn.unbind()
```

### Validation de cohérence logique

**Exemple: vérifier cohérence des dates :**
```python
#!/usr/bin/env python3
# validate-date-consistency.py

from ldap3 import Server, Connection, ALL
from datetime import datetime

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

print("=== Date Consistency Validation ===\n")

# Vérifier que createTimestamp < modifyTimestamp
conn.search(
    'dc=example,dc=com',
    '(&(createTimestamp=*)(modifyTimestamp=*))',
    attributes=['createTimestamp', 'modifyTimestamp']
)

inconsistent = []

for entry in conn.entries:
    create = str(entry.createTimestamp)
    modify = str(entry.modifyTimestamp)

    # Convertir en datetime
    create_dt = datetime.strptime(create, '%Y%m%d%H%M%S.%fZ')
    modify_dt = datetime.strptime(modify, '%Y%m%d%H%M%S.%fZ')

    if modify_dt < create_dt:
        inconsistent.append({
            'dn': str(entry.entry_dn),
            'create': create,
            'modify': modify
        })

if inconsistent:
    print(f"Found {len(inconsistent)} entries with inconsistent timestamps:\n")
    for item in inconsistent:
        print(f"  {item['dn']}")
        print(f"    Created:  {item['create']}")
        print(f"    Modified: {item['modify']}")
        print()
else:
    print("✓ All timestamps consistent")

conn.unbind()
```

## Validation du schéma

### Vérification de la conformité

**Script de validation :**
```bash
#!/bin/bash
# validate-schema.sh

echo "=== Schema Validation ==="

# Vérifier chaque entrée
ldapsearch -x -b "dc=example,dc=com" "(objectClass=*)" \* + | \
awk '
BEGIN { dn = ""; oc = "" }
/^dn: / {
  if (dn != "" && oc != "") {
    print dn "|" oc
  }
  dn = $0; oc = ""
}
/^objectClass: / {
  if (oc == "") oc = substr($0, 14)
  else oc = oc "," substr($0, 14)
}
END {
  if (dn != "" && oc != "") {
    print dn "|" oc
  }
}
' | \
while IFS='|' read DN OC; do
  # Valider avec slapschema (OpenLDAP)
  # Note: nécessite accès au fichier de données
  echo "Validating: $DN"
  # ... validation ...
done
```

### Détection d'objectClass manquants

```python
#!/usr/bin/env python3
# check-objectclass.py

from ldap3 import Server, Connection, ALL

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

# Attributs requis par objectClass
objectclass_requirements = {
    'person': ['cn', 'sn'],
    'organizationalPerson': ['cn', 'sn'],
    'inetOrgPerson': ['cn', 'sn'],
    'groupOfNames': ['cn', 'member'],
}

print("=== ObjectClass Validation ===\n")

conn.search('dc=example,dc=com', '(objectClass=*)', attributes=['*', '+'])

issues = []

for entry in conn.entries:
    if not hasattr(entry, 'objectClass'):
        issues.append({
            'dn': str(entry.entry_dn),
            'issue': 'No objectClass attribute'
        })
        continue

    object_classes = [str(oc) for oc in entry.objectClass]

    # Vérifier les attributs requis
    for oc in object_classes:
        if oc in objectclass_requirements:
            required = objectclass_requirements[oc]
            missing = [attr for attr in required if not hasattr(entry, attr)]

            if missing:
                issues.append({
                    'dn': str(entry.entry_dn),
                    'objectClass': oc,
                    'missing': missing
                })

if issues:
    print(f"Found {len(issues)} schema violations:\n")
    for issue in issues[:20]:
        print(f"  {issue['dn']}")
        if 'missing' in issue:
            print(f"    ObjectClass: {issue['objectClass']}")
            print(f"    Missing: {', '.join(issue['missing'])}")
        else:
            print(f"    Issue: {issue['issue']}")
        print()
else:
    print("✓ All entries comply with schema")

conn.unbind()
```

## Cohérence de réplication

### Vérification de synchronisation

**Script multi-serveurs :**
```bash
#!/bin/bash
# check-replication-consistency.sh

# Serveurs à comparer
SERVERS=(
  "ldap1.example.com"
  "ldap2.example.com"
  "ldap3.example.com"
)

BIND_DN="cn=admin,dc=example,dc=com"
PASSWORD="password"
BASE_DN="dc=example,dc=com"

echo "=== Replication Consistency Check ==="
echo "Servers: ${SERVERS[@]}"
echo ""

# Récupérer le contextCSN de chaque serveur
echo "=== Context CSN ==="
for SERVER in "${SERVERS[@]}"; do
  echo -n "$SERVER: "
  ldapsearch -x -H "ldap://$SERVER" -D "$BIND_DN" -w "$PASSWORD" \
    -b "$BASE_DN" -s base contextCSN | \
    grep "^contextCSN:" | cut -d' ' -f2-
done
echo ""

# Compter les entrées sur chaque serveur
echo "=== Entry Count ==="
for SERVER in "${SERVERS[@]}"; do
  COUNT=$(ldapsearch -x -H "ldap://$SERVER" -D "$BIND_DN" -w "$PASSWORD" \
    -b "$BASE_DN" "(objectClass=*)" dn | grep -c "^dn:")
  echo "$SERVER: $COUNT entries"
done
echo ""

# Comparer les checksums
echo "=== Data Checksums ==="
for SERVER in "${SERVERS[@]}"; do
  CHECKSUM=$(ldapsearch -x -H "ldap://$SERVER" -D "$BIND_DN" -w "$PASSWORD" \
    -b "$BASE_DN" "(objectClass=*)" \* | md5sum | cut -d' ' -f1)
  echo "$SERVER: $CHECKSUM"
done
```

### Détection de divergences

```python
#!/usr/bin/env python3
# detect-replication-divergence.py

from ldap3 import Server, Connection, ALL
import hashlib

servers = [
    'ldap1.example.com',
    'ldap2.example.com',
    'ldap3.example.com',
]

bind_dn = 'cn=admin,dc=example,dc=com'
password = 'password'

print("=== Replication Divergence Detection ===\n")

# Récupérer les données de chaque serveur
server_data = {}

for server_name in servers:
    print(f"Fetching data from {server_name}...")

    server = Server(f'ldap://{server_name}', get_info=ALL)
    conn = Connection(server, bind_dn, password, auto_bind=True)

    conn.search('dc=example,dc=com', '(objectClass=*)', attributes='*')

    # Créer un dictionnaire {dn: hash_of_attributes}
    data = {}
    for entry in conn.entries:
        # Créer un hash des attributs
        attrs_str = str(sorted(entry.entry_attributes_as_dict.items()))
        attrs_hash = hashlib.sha256(attrs_str.encode()).hexdigest()
        data[str(entry.entry_dn)] = attrs_hash

    server_data[server_name] = data
    conn.unbind()

# Comparer les données
print("\n=== Comparison ===\n")

# Trouver toutes les DNs
all_dns = set()
for data in server_data.values():
    all_dns.update(data.keys())

divergent = []

for dn in all_dns:
    hashes = [server_data[s].get(dn) for s in servers]

    # Vérifier si tous les hashes sont identiques
    if len(set(h for h in hashes if h)) > 1:
        divergent.append({
            'dn': dn,
            'servers': {s: server_data[s].get(dn, 'MISSING') for s in servers}
        })

if divergent:
    print(f"Found {len(divergent)} divergent entries:\n")
    for item in divergent[:10]:
        print(f"  {item['dn']}")
        for server, hash_val in item['servers'].items():
            print(f"    {server}: {hash_val}")
        print()
else:
    print("✓ All servers are synchronized")
```

## Détection de corruption

### Vérification de base de données

**OpenLDAP (mdb_stat) :**
```bash
#!/bin/bash
# check-database-health.sh

echo "=== Database Health Check ==="

DB_PATH="/var/lib/ldap"

# Arrêter le service
systemctl stop slapd

# Vérifier l'intégrité
echo "Running mdb_stat..."
mdb_stat -e "$DB_PATH"

# Vérifier et réparer si nécessaire
echo "Running slapindex..."
slapindex -v

# Redémarrer
systemctl start slapd

# Vérifier les logs pour erreurs
echo "Checking for errors..."
journalctl -u slapd --since "1 hour ago" | grep -i error
```

### Détection de caractères invalides

```python
#!/usr/bin/env python3
# detect-invalid-characters.py

from ldap3 import Server, Connection, ALL
import re

server = Server('ldap://ldap.example.com', get_info=ALL)
conn = Connection(server, 'cn=admin,dc=example,dc=com', 'password', auto_bind=True)

print("=== Invalid Character Detection ===\n")

# Pattern pour caractères invalides (caractères de contrôle, etc.)
invalid_pattern = re.compile(r'[\x00-\x1F\x7F-\x9F]')

conn.search('dc=example,dc=com', '(objectClass=*)', attributes='*')

issues = []

for entry in conn.entries:
    for attr in entry.entry_attributes:
        value = str(getattr(entry, attr))

        if invalid_pattern.search(value):
            issues.append({
                'dn': str(entry.entry_dn),
                'attribute': attr,
                'value': repr(value)  # repr pour montrer les caractères spéciaux
            })

if issues:
    print(f"Found {len(issues)} attributes with invalid characters:\n")
    for issue in issues[:20]:
        print(f"  {issue['dn']}")
        print(f"    Attribute: {issue['attribute']}")
        print(f"    Value: {issue['value']}")
        print()
else:
    print("✓ No invalid characters found")

conn.unbind()
```

## Exemples pratiques

### Exemple 1 : Audit complet de cohérence

```bash
#!/bin/bash
# full-consistency-audit.sh

REPORT_DIR="/var/reports/ldap/consistency/$(date +%Y-%m-%d)"
mkdir -p "$REPORT_DIR"

echo "=== Full Consistency Audit - $(date) ==="

# 1. Intégrité référentielle
echo "1. Checking referential integrity..."
python3 check-referential-integrity.py > "$REPORT_DIR/referential-integrity.txt"

# 2. Doublons
echo "2. Detecting duplicates..."
python3 detect-duplicates.py > "$REPORT_DIR/duplicates.txt"

# 3. Validation du schéma
echo "3. Validating schema..."
python3 check-objectclass.py > "$REPORT_DIR/schema.txt"

# 4. Format des attributs
echo "4. Validating attribute formats..."
python3 validate-attribute-formats.py > "$REPORT_DIR/formats.txt"

# 5. Cohérence de réplication
echo "5. Checking replication..."
bash check-replication-consistency.sh > "$REPORT_DIR/replication.txt"

# 6. Détection de corruption
echo "6. Checking for corruption..."
python3 detect-invalid-characters.py > "$REPORT_DIR/corruption.txt"

# Générer rapport HTML
python3 generate-consistency-report.py "$REPORT_DIR"

echo "Report generated in: $REPORT_DIR"
```

## Réparation des données

### Workflow de réparation

```
1. BACKUP
   ↓
2. IDENTIFY ISSUES
   ↓
3. PLAN REPAIRS
   ↓
4. TEST ON COPY
   ↓
5. APPLY REPAIRS
   ↓
6. VERIFY
   ↓
7. MONITOR
```

### Script de réparation

```bash
#!/bin/bash
# repair-consistency-issues.sh

set -e

echo "=== Consistency Repair ==="

# 1. Backup obligatoire
echo "1. Creating backup..."
ldap-health-monitor backup full --output "/backup/pre-repair-$(date +%Y%m%d%H%M%S).ldif"

# 2. Confirmation
echo "This will repair consistency issues"
echo "Issues to repair:"
cat consistency-issues-summary.txt
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
  echo "Cancelled"
  exit 0
fi

# 3. Réparations
echo "3. Repairing broken references..."
bash fix-broken-references.sh

echo "4. Removing duplicate entries..."
# Requires manual review
echo "  Skipping - requires manual review"

echo "5. Fixing schema violations..."
# Add missing required attributes
# ...

echo "=== Repair Complete ==="
echo "Verification recommended"
```

## Prévention

### Contraintes d'intégrité

**OpenLDAP refint overlay :**
```ldif
dn: olcOverlay=refint,olcDatabase={1}mdb,cn=config
objectClass: olcOverlayConfig
objectClass: olcRefintConfig
olcOverlay: refint
olcRefintAttribute: member
olcRefintAttribute: memberOf
olcRefintNothing: cn=placeholder,dc=example,dc=com
```

### Validation côté application

```python
# Exemple de validation avant insertion
def add_group_member(conn, group_dn, member_dn):
    """Ajoute un membre avec validation"""

    # 1. Vérifier que le membre existe
    if not conn.search(member_dn, '(objectClass=*)', search_scope='BASE'):
        raise ValueError(f"Member does not exist: {member_dn}")

    # 2. Vérifier que le groupe existe
    if not conn.search(group_dn, '(objectClass=*)', search_scope='BASE'):
        raise ValueError(f"Group does not exist: {group_dn}")

    # 3. Vérifier que pas déjà membre
    conn.search(group_dn, '(objectClass=*)', attributes=['member'])
    if conn.entries and hasattr(conn.entries[0], 'member'):
        if member_dn in conn.entries[0].member.values:
            print("Already a member")
            return

    # 4. Ajouter
    conn.modify(group_dn, {'member': [(MODIFY_ADD, [member_dn])]})
```

## Dépannage

### Audit bloqué/lent

**Problème :** L'audit prend trop de temps

**Solutions :**
```bash
# Limiter la portée
BASE_DN="ou=Users,dc=example,dc=com"  # Au lieu de dc=example,dc=com

# Paralléliser
for OU in Users Groups; do
  python3 check-referential-integrity.py --base "ou=$OU,dc=example,dc=com" &
done
wait

# Augmenter les timeouts
ldap:
  timeout: 300
```

## Conclusion

L'audit de cohérence est essentiel pour garantir la fiabilité de votre annuaire LDAP. En automatisant les vérifications et en corrigeant rapidement les problèmes, vous évitez les erreurs en cascade.

**Points clés :**
- Audit hebdomadaire recommandé
- Backup avant toute réparation
- Validation systématique des données
- Monitoring de la réplication
- Prévention via contraintes

Pour aller plus loin :
- [Génération de rapports](./Audit-Reports.md)
- [Vue d'ensemble](./Overview.md)
