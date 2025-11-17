# Guide Multi-Serveurs

Guide complet pour configurer LDAP Health Monitor avec plusieurs serveurs LDAP, agrégation, et fédération.

## 🎯 Vue d'Ensemble

Ce guide couvre :

- Configuration multi-serveurs
- Failover et haute disponibilité
- Agrégation de données
- Fédération LDAP
- Synchronisation et réplication
- Load balancing
- Monitoring distribué

## 🏗️ Architectures Multi-Serveurs

### Architecture Master-Replica

```
┌─────────────────────────────────────────┐
│         LDAP Health Monitor             │
│         (Instance Centrale)             │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│Master│◄─►│Replica│
│LDAP  │  │LDAP  │
└──────┘  └──────┘
```

### Architecture Multi-Master

```
┌─────────────────────────────────────────┐
│         LDAP Health Monitor             │
│         avec Load Balancer              │
└────────┬────────────────────────────────┘
         │
    ┌────┴────┬────────┐
    │         │        │
┌───▼──┐  ┌──▼───┐ ┌──▼───┐
│Master│◄─►│Master│◄►│Master│
│ LDAP │  │ LDAP │ │ LDAP │
└──────┘  └──────┘ └──────┘
```

### Architecture Fédérée

```
┌─────────────────────────────────────────┐
│    LDAP Health Monitor (Agrégateur)     │
└─┬──────────┬──────────┬─────────────────┘
  │          │          │
┌─▼───────┐┌─▼───────┐┌─▼───────┐
│ Domain A││ Domain B││ Domain C│
│  LDAP   ││  LDAP   ││  LDAP   │
│ (Paris) ││(Londres)││(New York│
└─────────┘└─────────┘└─────────┘
```

## ⚙️ Configuration Multi-Serveurs

### Configuration Basique

```yaml
# config/multi-server-basic.yaml

# Plusieurs serveurs LDAP
ldap:
  # Liste de serveurs avec priorités
  servers:
    - uri: ldaps://ldap01.example.com:636
      priority: 1
      location: paris
      tags: [production, master]

    - uri: ldaps://ldap02.example.com:636
      priority: 2
      location: paris
      tags: [production, replica]

    - uri: ldaps://ldap03.example.com:636
      priority: 3
      location: london
      tags: [production, replica, dr]

  # Stratégie de failover
  failover:
    enabled: true
    strategy: priority  # priority, roundrobin, random
    retry_count: 3
    retry_delay: 2
    health_check: true
    health_check_interval: 60

  # Authentification commune
  bind_dn: cn=monitor,dc=example,dc=com
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=example,dc=com

  # Options communes
  timeout: 10
  use_ssl: true
  verify_ssl: true
```

### Configuration Avancée Multi-Domaines

```yaml
# config/multi-domain.yaml

# Configuration pour plusieurs domaines LDAP
domains:
  # Domain 1: Production principale
  - name: production
    enabled: true

    ldap:
      servers:
        - uri: ldaps://ldap-prod-01.example.com:636
          priority: 1
        - uri: ldaps://ldap-prod-02.example.com:636
          priority: 2

      bind_dn: cn=monitor,dc=prod,dc=example,dc=com
      bind_password: ${LDAP_PROD_PASSWORD}
      base_dn: dc=prod,dc=example,dc=com

      users_ou: ou=users,dc=prod,dc=example,dc=com
      groups_ou: ou=groups,dc=prod,dc=example,dc=com

    monitoring:
      enabled: true
      interval: 300
      priority: high

  # Domain 2: Développement
  - name: development
    enabled: true

    ldap:
      servers:
        - uri: ldaps://ldap-dev.example.com:636
          priority: 1

      bind_dn: cn=monitor,dc=dev,dc=example,dc=com
      bind_password: ${LDAP_DEV_PASSWORD}
      base_dn: dc=dev,dc=example,dc=com

    monitoring:
      enabled: true
      interval: 600
      priority: normal

  # Domain 3: Partenaires (externe)
  - name: partners
    enabled: true

    ldap:
      servers:
        - uri: ldaps://ldap.partner.com:636
          priority: 1

      bind_dn: cn=external-monitor,dc=partner,dc=com
      bind_password: ${LDAP_PARTNER_PASSWORD}
      base_dn: dc=partner,dc=com

    monitoring:
      enabled: true
      interval: 1800
      priority: low

# Agrégation des données
aggregation:
  enabled: true

  # Mode d'agrégation
  mode: merge  # merge, separate, federated

  # Mapping des attributs entre domaines
  attribute_mapping:
    production:
      uid: uid
      mail: mail
      cn: cn
    development:
      uid: uid
      mail: email
      cn: displayName
    partners:
      uid: username
      mail: emailAddress
      cn: fullName

  # Résolution des conflits
  conflict_resolution:
    strategy: priority  # priority, newest, oldest, manual
    priority_order: [production, development, partners]

# Monitoring global
monitoring:
  enabled: true

  # Métriques agrégées
  aggregate_metrics: true

  # Alertes cross-domain
  cross_domain_alerts:
    - name: replication_lag
      type: replication
      threshold: 300
      domains: [production]

    - name: total_users_anomaly
      type: count_anomaly
      threshold: 10  # % changement
      aggregate: true
```

### Configuration Géo-Distribuée

```yaml
# config/geo-distributed.yaml

# Serveurs géographiquement distribués
regions:
  # Europe
  - name: europe
    location: eu-west-1

    servers:
      - uri: ldaps://ldap-paris.example.com:636
        datacenter: paris
        priority: 1

      - uri: ldaps://ldap-london.example.com:636
        datacenter: london
        priority: 2

    bind_dn: cn=monitor,dc=europe,dc=example,dc=com
    bind_password: ${LDAP_EU_PASSWORD}
    base_dn: dc=europe,dc=example,dc=com

  # Amérique du Nord
  - name: north-america
    location: us-east-1

    servers:
      - uri: ldaps://ldap-newyork.example.com:636
        datacenter: newyork
        priority: 1

      - uri: ldaps://ldap-chicago.example.com:636
        datacenter: chicago
        priority: 2

    bind_dn: cn=monitor,dc=america,dc=example,dc=com
    bind_password: ${LDAP_US_PASSWORD}
    base_dn: dc=america,dc=example,dc=com

  # Asie-Pacifique
  - name: asia-pacific
    location: ap-southeast-1

    servers:
      - uri: ldaps://ldap-singapore.example.com:636
        datacenter: singapore
        priority: 1

    bind_dn: cn=monitor,dc=asia,dc=example,dc=com
    bind_password: ${LDAP_ASIA_PASSWORD}
    base_dn: dc=asia,dc=example,dc=com

# Routing intelligent
routing:
  # Préférer serveur local
  prefer_local: true

  # Géolocalisation
  geo_routing:
    enabled: true
    fallback_region: europe

  # Latence
  latency_based:
    enabled: true
    threshold_ms: 100
```

## 🔄 Failover et Haute Disponibilité

### Implémentation Failover

```python
#!/usr/bin/env python3
# modules/multi_server.py

import ldap
import time
import logging
from typing import List, Dict, Optional

class LDAPServerPool:
    """Pool de serveurs LDAP avec failover automatique"""

    def __init__(self, servers: List[Dict], failover_config: Dict):
        self.servers = sorted(servers, key=lambda x: x.get('priority', 999))
        self.failover_config = failover_config

        # État des serveurs
        self.server_status = {
            server['uri']: {
                'available': True,
                'last_check': None,
                'failures': 0,
                'response_time': None
            }
            for server in self.servers
        }

        self.current_server = None
        self.logger = logging.getLogger(__name__)

    def _check_server_health(self, server_uri: str) -> bool:
        """Vérifier santé d'un serveur"""
        try:
            start = time.time()

            conn = ldap.initialize(server_uri)
            conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 5)

            # Test simple avec rootDSE
            conn.search_s('', ldap.SCOPE_BASE, '(objectClass=*)', [])

            response_time = (time.time() - start) * 1000

            # Mettre à jour status
            self.server_status[server_uri]['available'] = True
            self.server_status[server_uri]['last_check'] = time.time()
            self.server_status[server_uri]['failures'] = 0
            self.server_status[server_uri]['response_time'] = response_time

            conn.unbind_s()
            return True

        except Exception as e:
            self.logger.warning(f"Server {server_uri} health check failed: {e}")

            self.server_status[server_uri]['available'] = False
            self.server_status[server_uri]['last_check'] = time.time()
            self.server_status[server_uri]['failures'] += 1

            return False

    def get_available_server(self, strategy='priority') -> Optional[str]:
        """Obtenir serveur disponible selon stratégie"""

        # Vérifier santé si nécessaire
        if self.failover_config.get('health_check', True):
            interval = self.failover_config.get('health_check_interval', 60)

            for server in self.servers:
                uri = server['uri']
                last_check = self.server_status[uri]['last_check']

                if last_check is None or (time.time() - last_check) > interval:
                    self._check_server_health(uri)

        # Sélectionner serveur selon stratégie
        if strategy == 'priority':
            # Par ordre de priorité
            for server in self.servers:
                uri = server['uri']
                if self.server_status[uri]['available']:
                    return uri

        elif strategy == 'roundrobin':
            # Round-robin parmi serveurs disponibles
            available = [
                s['uri'] for s in self.servers
                if self.server_status[s['uri']]['available']
            ]

            if available:
                # Rotation
                if self.current_server in available:
                    idx = available.index(self.current_server)
                    next_idx = (idx + 1) % len(available)
                    return available[next_idx]
                else:
                    return available[0]

        elif strategy == 'latency':
            # Serveur avec meilleure latence
            available = [
                s for s in self.servers
                if self.server_status[s['uri']]['available']
                and self.server_status[s['uri']]['response_time'] is not None
            ]

            if available:
                best = min(
                    available,
                    key=lambda s: self.server_status[s['uri']]['response_time']
                )
                return best['uri']

        return None

    def connect_with_failover(self, bind_dn: str, bind_pw: str):
        """Se connecter avec failover automatique"""

        strategy = self.failover_config.get('strategy', 'priority')
        retry_count = self.failover_config.get('retry_count', 3)
        retry_delay = self.failover_config.get('retry_delay', 2)

        for attempt in range(retry_count):
            server_uri = self.get_available_server(strategy)

            if not server_uri:
                self.logger.error("No available LDAP servers")
                if attempt < retry_count - 1:
                    time.sleep(retry_delay)
                    continue
                else:
                    raise Exception("All LDAP servers unavailable")

            try:
                self.logger.info(f"Attempting connection to {server_uri}")

                conn = ldap.initialize(server_uri)
                conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 10)
                conn.simple_bind_s(bind_dn, bind_pw)

                self.current_server = server_uri
                self.logger.info(f"Connected to {server_uri}")

                return conn

            except Exception as e:
                self.logger.warning(
                    f"Connection failed to {server_uri}: {e}"
                )

                # Marquer serveur comme indisponible
                self.server_status[server_uri]['available'] = False
                self.server_status[server_uri]['failures'] += 1

                if attempt < retry_count - 1:
                    time.sleep(retry_delay)

        raise Exception(f"Failed to connect after {retry_count} attempts")

    def get_server_stats(self) -> Dict:
        """Obtenir statistiques des serveurs"""
        return {
            'servers': [
                {
                    'uri': server['uri'],
                    'priority': server.get('priority'),
                    'location': server.get('location'),
                    **self.server_status[server['uri']]
                }
                for server in self.servers
            ],
            'current_server': self.current_server
        }

# Usage
servers = [
    {'uri': 'ldaps://ldap01.example.com:636', 'priority': 1, 'location': 'paris'},
    {'uri': 'ldaps://ldap02.example.com:636', 'priority': 2, 'location': 'paris'},
    {'uri': 'ldaps://ldap03.example.com:636', 'priority': 3, 'location': 'london'}
]

failover_config = {
    'enabled': True,
    'strategy': 'priority',
    'retry_count': 3,
    'retry_delay': 2,
    'health_check': True,
    'health_check_interval': 60
}

pool = LDAPServerPool(servers, failover_config)
conn = pool.connect_with_failover('cn=monitor,dc=example,dc=com', 'password')

# Utiliser connexion
# ...

# Statistiques
stats = pool.get_server_stats()
print(stats)
```

## 📊 Agrégation de Données

### Agrégateur Multi-Domaines

```python
#!/usr/bin/env python3
# modules/aggregator.py

import ldap
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict
import logging

class MultiDomainAggregator:
    """Agrégateur pour plusieurs domaines LDAP"""

    def __init__(self, domains: List[Dict]):
        self.domains = domains
        self.logger = logging.getLogger(__name__)

    def _connect_domain(self, domain: Dict):
        """Se connecter à un domaine"""
        try:
            server_uri = domain['ldap']['servers'][0]['uri']
            bind_dn = domain['ldap']['bind_dn']
            bind_pw = domain['ldap']['bind_password']

            conn = ldap.initialize(server_uri)
            conn.simple_bind_s(bind_dn, bind_pw)

            return conn

        except Exception as e:
            self.logger.error(f"Failed to connect to domain {domain['name']}: {e}")
            return None

    def _search_domain(self, domain: Dict, base_dn: str, search_filter: str, attrs: List[str]):
        """Rechercher dans un domaine"""
        conn = self._connect_domain(domain)

        if not conn:
            return {
                'domain': domain['name'],
                'success': False,
                'results': [],
                'error': 'Connection failed'
            }

        try:
            results = conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter, attrs)

            conn.unbind_s()

            return {
                'domain': domain['name'],
                'success': True,
                'results': results,
                'count': len(results)
            }

        except Exception as e:
            self.logger.error(f"Search failed in domain {domain['name']}: {e}")

            return {
                'domain': domain['name'],
                'success': False,
                'results': [],
                'error': str(e)
            }

    def aggregate_search(self, search_filter: str, attrs: List[str], parallel=True):
        """Recherche agrégée sur tous les domaines"""

        if parallel:
            return self._aggregate_search_parallel(search_filter, attrs)
        else:
            return self._aggregate_search_sequential(search_filter, attrs)

    def _aggregate_search_parallel(self, search_filter: str, attrs: List[str]):
        """Recherche parallèle"""
        results = {}

        with ThreadPoolExecutor(max_workers=len(self.domains)) as executor:
            # Soumettre recherches pour chaque domaine
            futures = {
                executor.submit(
                    self._search_domain,
                    domain,
                    domain['ldap']['base_dn'],
                    search_filter,
                    attrs
                ): domain['name']
                for domain in self.domains
                if domain.get('enabled', True)
            }

            # Collecter résultats
            for future in as_completed(futures):
                domain_name = futures[future]
                try:
                    result = future.result()
                    results[domain_name] = result
                except Exception as e:
                    self.logger.error(f"Exception for domain {domain_name}: {e}")
                    results[domain_name] = {
                        'domain': domain_name,
                        'success': False,
                        'results': [],
                        'error': str(e)
                    }

        return results

    def _aggregate_search_sequential(self, search_filter: str, attrs: List[str]):
        """Recherche séquentielle"""
        results = {}

        for domain in self.domains:
            if not domain.get('enabled', True):
                continue

            domain_name = domain['name']
            result = self._search_domain(
                domain,
                domain['ldap']['base_dn'],
                search_filter,
                attrs
            )

            results[domain_name] = result

        return results

    def merge_results(self, aggregated_results: Dict, attribute_mapping: Dict = None):
        """Fusionner résultats de plusieurs domaines"""

        merged = []

        for domain_name, domain_result in aggregated_results.items():
            if not domain_result['success']:
                continue

            # Mapping attributs si configuré
            mapping = attribute_mapping.get(domain_name, {}) if attribute_mapping else {}

            for dn, attrs in domain_result['results']:
                # Appliquer mapping
                if mapping:
                    mapped_attrs = {}
                    for key, value in attrs.items():
                        mapped_key = mapping.get(key, key)
                        mapped_attrs[mapped_key] = value
                else:
                    mapped_attrs = attrs

                # Ajouter métadonnées
                mapped_attrs['_source_domain'] = domain_name
                mapped_attrs['_original_dn'] = dn

                merged.append((dn, mapped_attrs))

        return merged

    def get_aggregate_stats(self):
        """Obtenir statistiques agrégées"""

        stats = {
            'total_domains': len(self.domains),
            'enabled_domains': len([d for d in self.domains if d.get('enabled', True)]),
            'domains': {}
        }

        # Collecter stats par domaine
        for domain in self.domains:
            if not domain.get('enabled', True):
                continue

            domain_name = domain['name']

            try:
                conn = self._connect_domain(domain)

                if conn:
                    # Compter utilisateurs
                    users_ou = domain['ldap'].get('users_ou', domain['ldap']['base_dn'])
                    user_results = conn.search_s(
                        users_ou,
                        ldap.SCOPE_SUBTREE,
                        '(objectClass=person)',
                        ['1.1']
                    )

                    # Compter groupes
                    groups_ou = domain['ldap'].get('groups_ou', domain['ldap']['base_dn'])
                    group_results = conn.search_s(
                        groups_ou,
                        ldap.SCOPE_SUBTREE,
                        '(objectClass=group*)',
                        ['1.1']
                    )

                    conn.unbind_s()

                    stats['domains'][domain_name] = {
                        'available': True,
                        'users': len(user_results),
                        'groups': len(group_results)
                    }

                else:
                    stats['domains'][domain_name] = {
                        'available': False
                    }

            except Exception as e:
                self.logger.error(f"Failed to get stats for {domain_name}: {e}")
                stats['domains'][domain_name] = {
                    'available': False,
                    'error': str(e)
                }

        # Totaux
        stats['total_users'] = sum(
            d.get('users', 0) for d in stats['domains'].values()
        )
        stats['total_groups'] = sum(
            d.get('groups', 0) for d in stats['domains'].values()
        )

        return stats

# Usage
domains = [
    {
        'name': 'production',
        'enabled': True,
        'ldap': {
            'servers': [{'uri': 'ldaps://ldap-prod.example.com:636'}],
            'bind_dn': 'cn=monitor,dc=prod,dc=example,dc=com',
            'bind_password': 'password',
            'base_dn': 'dc=prod,dc=example,dc=com'
        }
    },
    {
        'name': 'development',
        'enabled': True,
        'ldap': {
            'servers': [{'uri': 'ldaps://ldap-dev.example.com:636'}],
            'bind_dn': 'cn=monitor,dc=dev,dc=example,dc=com',
            'bind_password': 'password',
            'base_dn': 'dc=dev,dc=example,dc=com'
        }
    }
]

aggregator = MultiDomainAggregator(domains)

# Recherche agrégée
results = aggregator.aggregate_search(
    '(objectClass=inetOrgPerson)',
    ['uid', 'mail', 'cn']
)

# Fusionner résultats
merged = aggregator.merge_results(results)

# Statistiques
stats = aggregator.get_aggregate_stats()
print(f"Total users across all domains: {stats['total_users']}")
```

## 🔧 Load Balancing

### Configuration HAProxy

```
# /etc/haproxy/haproxy.cfg

global
    log /dev/log local0
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

defaults
    log     global
    mode    tcp
    option  tcplog
    option  dontlognull
    timeout connect 5000
    timeout client  50000
    timeout server  50000

# LDAP Frontend (non-SSL)
frontend ldap_frontend
    bind *:389
    mode tcp
    default_backend ldap_backend

# LDAPS Frontend (SSL)
frontend ldaps_frontend
    bind *:636
    mode tcp
    default_backend ldap_backend

# LDAP Backend
backend ldap_backend
    mode tcp
    balance roundrobin
    option tcp-check

    # Health checks
    tcp-check connect
    tcp-check send-binary 300c0201 # LDAP bind request
    tcp-check expect binary 0a0100 # Success response

    server ldap1 10.0.1.10:636 check inter 10s fall 3 rise 2
    server ldap2 10.0.1.11:636 check inter 10s fall 3 rise 2
    server ldap3 10.0.1.12:636 check inter 10s fall 3 rise 2 backup

# Stats interface
listen stats
    bind *:8404
    stats enable
    stats uri /
    stats refresh 10s
    stats admin if TRUE
```

## 📊 Monitoring Distribué

### Configuration Monitoring Multi-Serveurs

```bash
# Monitoring avec LDAP Health Monitor

# Audit tous les domaines
ldap-monitor audit all --all-domains

# Statistiques agrégées
ldap-monitor stats aggregate

# Santé de tous les serveurs
ldap-monitor health check --all-servers

# Rapport multi-domaines
ldap-monitor report generate \
    --all-domains \
    --format html \
    --output /var/reports/multi-domain-report.html
```

## 📖 Voir Aussi

- [Performance Tuning](Performance-Tuning.md)
- [Production Monitoring](Production-Monitoring.md)
- [High Availability](../configuration/High-Availability.md)
- [Backup Strategy](Backup-Strategy.md)
