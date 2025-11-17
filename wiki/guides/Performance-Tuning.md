# Guide d'Optimisation des Performances

Guide complet pour optimiser les performances de LDAP Health Monitor et de votre infrastructure LDAP.

## 🎯 Vue d'Ensemble

Ce guide couvre :

- Optimisation de LDAP Health Monitor
- Optimisation du serveur LDAP
- Stratégies de cache
- Connection pooling
- Indexation et requêtes
- Scaling horizontal et vertical
- Benchmarking et profiling

## 🚀 Optimisation LDAP Health Monitor

### Configuration Performance

```yaml
# config/performance.yaml
ldap:
  # Connection pooling
  pool_enabled: true
  pool_size: 20              # Nombre de connexions dans le pool
  pool_timeout: 30           # Timeout acquisition connexion (s)
  pool_recycle: 3600         # Recycler connexions après (s)
  pool_pre_ping: true        # Vérifier connexion avant utilisation

  # Timeouts optimisés
  timeout: 10                # Timeout général (s)
  network_timeout: 5         # Timeout réseau (s)
  search_timeout: 15         # Timeout recherche (s)

  # Pagination optimale
  page_size: 1000            # Taille de page (max 1000 pour AD)
  simple_paged_results: true

  # Options réseau
  tcp_nodelay: true          # Désactiver Nagle algorithm
  keepalive: true            # Keep-alive TCP
  keepalive_interval: 60

# Cache
cache:
  enabled: true
  backend: redis             # redis ou memcached ou memory

  # Configuration Redis
  redis:
    host: localhost
    port: 6379
    db: 0
    password: ${REDIS_PASSWORD}
    max_connections: 50
    socket_timeout: 5
    socket_connect_timeout: 5

  # TTL par type
  ttl:
    users: 300               # 5 minutes
    groups: 600              # 10 minutes
    structure: 3600          # 1 heure
    health: 60               # 1 minute
    metrics: 120             # 2 minutes

  # Stratégie invalidation
  invalidation: lazy         # lazy ou eager
  max_size: 1000             # Taille max cache (entrées)

# Performance monitoring
performance:
  enabled: true

  # Profiling
  profiling:
    enabled: false           # Activer seulement pour debug
    output_dir: /var/log/ldap-monitor/profiling

  # Métriques performance
  metrics:
    track_query_time: true
    track_cache_hits: true
    track_connection_time: true
    slow_query_threshold: 1000  # ms

# Optimisation des workers
workers:
  # Threads pour opérations parallèles
  max_workers: 4
  thread_pool_size: 10

  # Queue pour tâches asynchrones
  async_enabled: true
  queue_size: 1000

# Batch operations
batch:
  enabled: true
  size: 100                  # Taille des batches
  parallel: true
  max_parallel: 4
```

### Connection Pooling

```python
#!/usr/bin/env python3
# modules/connection_pool.py

import ldap
import queue
import threading
import time
from contextlib import contextmanager

class LDAPConnectionPool:
    """Pool de connexions LDAP réutilisables"""

    def __init__(self, uri, bind_dn, bind_pw, pool_size=10, timeout=30):
        self.uri = uri
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw
        self.pool_size = pool_size
        self.timeout = timeout

        # Queue pour stocker connexions disponibles
        self.pool = queue.Queue(maxsize=pool_size)

        # Statistiques
        self.stats = {
            'created': 0,
            'reused': 0,
            'closed': 0,
            'errors': 0
        }

        self.lock = threading.Lock()

        # Pré-créer connexions
        self._initialize_pool()

    def _initialize_pool(self):
        """Pré-créer connexions dans le pool"""
        for _ in range(self.pool_size):
            try:
                conn = self._create_connection()
                self.pool.put(conn, block=False)
            except queue.Full:
                break

    def _create_connection(self):
        """Créer nouvelle connexion LDAP"""
        conn = ldap.initialize(self.uri)

        # Options performance
        conn.set_option(ldap.OPT_REFERRALS, 0)
        conn.set_option(ldap.OPT_NETWORK_TIMEOUT, 5)
        conn.set_option(ldap.OPT_TIMEOUT, self.timeout)

        # Bind
        conn.simple_bind_s(self.bind_dn, self.bind_pw)

        with self.lock:
            self.stats['created'] += 1

        return conn

    def _validate_connection(self, conn):
        """Vérifier si connexion est valide"""
        try:
            # Whoami pour tester connexion
            conn.whoami_s()
            return True
        except ldap.LDAPError:
            return False

    @contextmanager
    def get_connection(self, timeout=None):
        """Obtenir connexion du pool (context manager)"""
        timeout = timeout or self.timeout
        conn = None

        try:
            # Essayer obtenir connexion existante
            conn = self.pool.get(block=True, timeout=timeout)

            # Vérifier validité
            if not self._validate_connection(conn):
                # Connexion invalide, en créer une nouvelle
                try:
                    conn.unbind_s()
                except:
                    pass

                conn = self._create_connection()
            else:
                with self.lock:
                    self.stats['reused'] += 1

            yield conn

        except queue.Empty:
            # Pool vide, créer nouvelle connexion temporaire
            conn = self._create_connection()
            yield conn

        except Exception as e:
            with self.lock:
                self.stats['errors'] += 1
            raise

        finally:
            # Remettre connexion dans pool
            if conn is not None:
                try:
                    # Essayer remettre dans pool
                    self.pool.put(conn, block=False)
                except queue.Full:
                    # Pool plein, fermer connexion
                    try:
                        conn.unbind_s()
                        with self.lock:
                            self.stats['closed'] += 1
                    except:
                        pass

    def close_all(self):
        """Fermer toutes les connexions"""
        while not self.pool.empty():
            try:
                conn = self.pool.get(block=False)
                conn.unbind_s()
                with self.lock:
                    self.stats['closed'] += 1
            except (queue.Empty, Exception):
                break

    def get_stats(self):
        """Obtenir statistiques du pool"""
        with self.lock:
            return {
                **self.stats,
                'pool_size': self.pool.qsize(),
                'max_size': self.pool_size
            }

# Usage
pool = LDAPConnectionPool(
    'ldaps://ldap.example.com',
    'cn=admin,dc=example,dc=com',
    'password',
    pool_size=20
)

# Utiliser connexion
with pool.get_connection() as conn:
    results = conn.search_s(
        'dc=example,dc=com',
        ldap.SCOPE_SUBTREE,
        '(objectClass=inetOrgPerson)'
    )

# Statistiques
print(pool.get_stats())
```

### Système de Cache

```python
#!/usr/bin/env python3
# modules/cache.py

import redis
import pickle
import hashlib
import time
from functools import wraps

class LDAPCache:
    """Cache intelligent pour requêtes LDAP"""

    def __init__(self, redis_host='localhost', redis_port=6379, default_ttl=300):
        self.redis = redis.Redis(
            host=redis_host,
            port=redis_port,
            decode_responses=False  # Binary pour pickle
        )
        self.default_ttl = default_ttl

        # Statistiques
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }

    def _make_key(self, prefix, *args, **kwargs):
        """Générer clé de cache"""
        # Combiner tous les arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"

        # Hash pour clé courte
        key_hash = hashlib.sha256(key_data.encode()).hexdigest()

        return f"ldap:cache:{prefix}:{key_hash}"

    def get(self, key):
        """Obtenir valeur du cache"""
        try:
            value = self.redis.get(key)
            if value is not None:
                self.stats['hits'] += 1
                return pickle.loads(value)
            else:
                self.stats['misses'] += 1
                return None
        except Exception as e:
            print(f"Cache get error: {e}")
            self.stats['misses'] += 1
            return None

    def set(self, key, value, ttl=None):
        """Mettre valeur dans cache"""
        try:
            ttl = ttl or self.default_ttl
            serialized = pickle.dumps(value)
            self.redis.setex(key, ttl, serialized)
            self.stats['sets'] += 1
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False

    def delete(self, key):
        """Supprimer du cache"""
        try:
            self.redis.delete(key)
            self.stats['deletes'] += 1
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False

    def clear_prefix(self, prefix):
        """Supprimer toutes les clés avec préfixe"""
        try:
            pattern = f"ldap:cache:{prefix}:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                self.stats['deletes'] += len(keys)
            return True
        except Exception as e:
            print(f"Cache clear error: {e}")
            return False

    def get_stats(self):
        """Obtenir statistiques cache"""
        total = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total * 100) if total > 0 else 0

        return {
            **self.stats,
            'total_requests': total,
            'hit_rate': hit_rate
        }

def cached(prefix, ttl=None):
    """Décorateur pour mettre en cache résultats de fonction"""

    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Générer clé
            cache_key = self.cache._make_key(prefix, *args, **kwargs)

            # Essayer obtenir du cache
            cached_value = self.cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Exécuter fonction
            result = func(self, *args, **kwargs)

            # Mettre en cache
            self.cache.set(cache_key, result, ttl)

            return result

        return wrapper

    return decorator

# Usage
class LDAPMonitor:

    def __init__(self):
        self.cache = LDAPCache()

    @cached('users', ttl=300)
    def get_all_users(self):
        """Obtenir tous les utilisateurs (avec cache)"""
        # Requête LDAP coûteuse
        # ...
        return users

    def invalidate_users_cache(self):
        """Invalider cache utilisateurs"""
        self.cache.clear_prefix('users')
```

### Optimisation des Requêtes

```python
#!/usr/bin/env python3
# modules/optimized_queries.py

import ldap

class OptimizedLDAPQueries:
    """Requêtes LDAP optimisées"""

    def __init__(self, conn):
        self.conn = conn

    def search_paginated(self, base_dn, search_filter, attrs=None, page_size=1000):
        """Recherche paginée efficace"""

        # Control de pagination
        page_ctrl = ldap.controls.SimplePagedResultsControl(
            True,
            size=page_size,
            cookie=''
        )

        all_results = []

        while True:
            # Recherche avec pagination
            msgid = self.conn.search_ext(
                base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                attrlist=attrs,
                serverctrls=[page_ctrl]
            )

            # Récupérer résultats
            rtype, rdata, rmsgid, serverctrls = self.conn.result3(msgid)

            all_results.extend(rdata)

            # Trouver control de pagination dans réponse
            pctrls = [
                c for c in serverctrls
                if c.controlType == ldap.controls.SimplePagedResultsControl.controlType
            ]

            if not pctrls:
                break

            # Obtenir cookie pour page suivante
            cookie = pctrls[0].cookie
            if not cookie:
                break

            # Mettre à jour control pour page suivante
            page_ctrl.cookie = cookie

        return all_results

    def search_attributes_only(self, base_dn, search_filter, attrs):
        """Recherche avec seulement attributs demandés (pas de valeurs)"""

        return self.conn.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            search_filter,
            attrlist=attrs,
            attrsonly=1  # Attributs seulement, pas de valeurs
        )

    def count_entries(self, base_dn, search_filter):
        """Compter entrées efficacement sans récupérer données"""

        # Recherche avec attributs vides
        results = self.conn.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            search_filter,
            attrlist=['1.1']  # Attribute vide spécial
        )

        return len(results)

    def search_parallel(self, searches, max_workers=4):
        """Exécuter plusieurs recherches en parallèle"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results = {}

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Soumettre toutes les recherches
            futures = {
                executor.submit(
                    self.conn.search_s,
                    search['base_dn'],
                    search.get('scope', ldap.SCOPE_SUBTREE),
                    search['filter'],
                    search.get('attrs')
                ): search['name']
                for search in searches
            }

            # Collecter résultats
            for future in as_completed(futures):
                name = futures[future]
                try:
                    results[name] = future.result()
                except Exception as e:
                    print(f"Search '{name}' failed: {e}")
                    results[name] = []

        return results

    def search_with_filter_optimization(self, base_dn, filters):
        """Optimiser filtres LDAP complexes"""

        # Combiner filtres de manière efficace
        # Mettre filtres les plus sélectifs en premier

        # Exemple: au lieu de (&(objectClass=user)(mail=*))
        # Utiliser: (&(mail=*)(objectClass=user))
        # Car mail=* est plus sélectif

        optimized_filter = self._optimize_filter(filters)

        return self.conn.search_s(
            base_dn,
            ldap.SCOPE_SUBTREE,
            optimized_filter
        )

    def _optimize_filter(self, filters):
        """Optimiser ordre des filtres"""
        # Heuristique simple: filtres avec valeurs exactes en premier

        def filter_priority(f):
            if '=' in f and '*' not in f:
                return 0  # Haute priorité (égalité exacte)
            elif '=' in f:
                return 1  # Moyenne priorité (wildcard)
            else:
                return 2  # Basse priorité

        sorted_filters = sorted(filters, key=filter_priority)

        return '(&' + ''.join(sorted_filters) + ')'

# Usage
conn = ldap.initialize('ldaps://ldap.example.com')
conn.simple_bind_s('cn=admin,dc=example,dc=com', 'password')

queries = OptimizedLDAPQueries(conn)

# Pagination
users = queries.search_paginated(
    'dc=example,dc=com',
    '(objectClass=inetOrgPerson)',
    attrs=['uid', 'mail', 'cn'],
    page_size=1000
)

# Comptage rapide
user_count = queries.count_entries(
    'dc=example,dc=com',
    '(objectClass=inetOrgPerson)'
)

# Recherches parallèles
parallel_searches = [
    {
        'name': 'users',
        'base_dn': 'ou=users,dc=example,dc=com',
        'filter': '(objectClass=inetOrgPerson)',
        'attrs': ['uid']
    },
    {
        'name': 'groups',
        'base_dn': 'ou=groups,dc=example,dc=com',
        'filter': '(objectClass=groupOfNames)',
        'attrs': ['cn']
    }
]

results = queries.search_parallel(parallel_searches, max_workers=2)
```

## 🗄️ Optimisation Serveur LDAP

### Indexation OpenLDAP

```ldif
# Indices optimaux pour performance

dn: olcDatabase={1}mdb,cn=config
changetype: modify
add: olcDbIndex
olcDbIndex: objectClass eq
olcDbIndex: cn,sn,mail eq,pres,sub
olcDbIndex: uid eq,pres
olcDbIndex: uidNumber,gidNumber eq
olcDbIndex: memberUid eq,pres
olcDbIndex: member,memberOf eq
olcDbIndex: entryUUID eq
olcDbIndex: entryCSN eq

# Indices pour attributs couramment recherchés
olcDbIndex: displayName eq,pres,sub
olcDbIndex: department eq,pres
olcDbIndex: title eq,pres
```

```bash
# Vérifier utilisation indices
ldapsearch -Y EXTERNAL -H ldapi:/// \
    -b "cn=Monitor" \
    "(objectClass=*)" \
    olmDbStat

# Reconstruire indices
slapindex -v -f /etc/ldap/slapd.conf
```

### Configuration Backend MDB

```ldif
# Optimisations backend MDB

dn: olcDatabase={1}mdb,cn=config
changetype: modify
replace: olcDbMaxSize
# Taille max database (1 GB par défaut, augmenter si nécessaire)
olcDbMaxSize: 10737418240

add: olcDbMaxReaders
# Nombre max de lecteurs simultanés
olcDbMaxReaders: 126

add: olcDbEnvFlags
# Options environnement MDB
olcDbEnvFlags: writemap
olcDbEnvFlags: mapasync
```

### Tuning Active Directory

```
# Via PowerShell

# Augmenter limites recherche
Set-ADObject -Identity "CN=Default Query Policy,CN=Query-Policies,CN=Directory Service,CN=Windows NT,CN=Services,CN=Configuration,DC=example,DC=com" -Replace @{
    lDAPAdminLimits = "MaxValRange=5000"
    lDAPAdminLimits = "MaxPageSize=2000"
    lDAPAdminLimits = "MaxResultSetSize=10000"
}

# Optimiser réplication
repadmin /options +DISABLE_NTDSCONN_XLATE

# Indexation
# Vérifier indices via ADSI Edit
# Paths: CN=Schema,CN=Configuration,DC=example,DC=com
```

## 📊 Benchmarking

### Script de Benchmark

```python
#!/usr/bin/env python3
# scripts/benchmark-ldap.py

import ldap
import time
import statistics
from concurrent.futures import ThreadPoolExecutor

class LDAPBenchmark:

    def __init__(self, uri, bind_dn, bind_pw):
        self.uri = uri
        self.bind_dn = bind_dn
        self.bind_pw = bind_pw

    def benchmark_connection(self, iterations=100):
        """Benchmark temps de connexion"""
        times = []

        for _ in range(iterations):
            start = time.time()

            conn = ldap.initialize(self.uri)
            conn.simple_bind_s(self.bind_dn, self.bind_pw)
            conn.unbind_s()

            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)

        return {
            'operation': 'connection',
            'iterations': iterations,
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }

    def benchmark_search(self, base_dn, search_filter, iterations=100):
        """Benchmark recherche"""
        conn = ldap.initialize(self.uri)
        conn.simple_bind_s(self.bind_dn, self.bind_pw)

        times = []

        for _ in range(iterations):
            start = time.time()

            conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)

            elapsed = (time.time() - start) * 1000  # ms
            times.append(elapsed)

        conn.unbind_s()

        return {
            'operation': 'search',
            'filter': search_filter,
            'iterations': iterations,
            'mean': statistics.mean(times),
            'median': statistics.median(times),
            'min': min(times),
            'max': max(times),
            'stdev': statistics.stdev(times) if len(times) > 1 else 0
        }

    def benchmark_concurrent(self, base_dn, search_filter, num_threads=10, iterations_per_thread=10):
        """Benchmark recherches concurrentes"""

        def worker():
            conn = ldap.initialize(self.uri)
            conn.simple_bind_s(self.bind_dn, self.bind_pw)

            times = []
            for _ in range(iterations_per_thread):
                start = time.time()
                conn.search_s(base_dn, ldap.SCOPE_SUBTREE, search_filter)
                elapsed = (time.time() - start) * 1000
                times.append(elapsed)

            conn.unbind_s()
            return times

        start_total = time.time()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker) for _ in range(num_threads)]
            all_times = [t for future in futures for t in future.result()]

        total_time = (time.time() - start_total) * 1000

        return {
            'operation': 'concurrent_search',
            'threads': num_threads,
            'iterations_per_thread': iterations_per_thread,
            'total_queries': len(all_times),
            'total_time_ms': total_time,
            'queries_per_second': len(all_times) / (total_time / 1000),
            'mean': statistics.mean(all_times),
            'median': statistics.median(all_times),
            'min': min(all_times),
            'max': max(all_times),
            'stdev': statistics.stdev(all_times)
        }

    def run_full_benchmark(self):
        """Exécuter benchmark complet"""
        print("=== LDAP Performance Benchmark ===\n")

        # Connection
        print("Benchmarking connections...")
        conn_result = self.benchmark_connection(100)
        print(f"  Mean: {conn_result['mean']:.2f} ms")
        print(f"  Median: {conn_result['median']:.2f} ms")
        print(f"  StdDev: {conn_result['stdev']:.2f} ms\n")

        # Simple search
        print("Benchmarking simple search...")
        search_result = self.benchmark_search(
            'dc=example,dc=com',
            '(objectClass=inetOrgPerson)',
            100
        )
        print(f"  Mean: {search_result['mean']:.2f} ms")
        print(f"  Median: {search_result['median']:.2f} ms")
        print(f"  StdDev: {search_result['stdev']:.2f} ms\n")

        # Concurrent
        print("Benchmarking concurrent searches...")
        concurrent_result = self.benchmark_concurrent(
            'dc=example,dc=com',
            '(objectClass=inetOrgPerson)',
            num_threads=10,
            iterations_per_thread=10
        )
        print(f"  Queries/sec: {concurrent_result['queries_per_second']:.2f}")
        print(f"  Mean: {concurrent_result['mean']:.2f} ms")
        print(f"  Max: {concurrent_result['max']:.2f} ms\n")

        return {
            'connection': conn_result,
            'search': search_result,
            'concurrent': concurrent_result
        }

# Usage
benchmark = LDAPBenchmark(
    'ldaps://ldap.example.com',
    'cn=admin,dc=example,dc=com',
    'password'
)

results = benchmark.run_full_benchmark()
```

## 📈 Scaling

### Scaling Vertical

```yaml
# Augmenter ressources serveur

# CPU
# - Augmenter nombre de cores
# - OpenLDAP: configurer threads
olcThreads: 16

# Mémoire
# - Augmenter RAM serveur
# - Augmenter cache BDB/MDB
olcDbCacheSize: 10000

# Disque
# - Utiliser SSD/NVMe
# - RAID 10 pour performance
# - Séparer données/logs
```

### Scaling Horizontal

```
# Load balancer (HAProxy)

frontend ldap_front
    bind *:389
    mode tcp
    default_backend ldap_back

backend ldap_back
    mode tcp
    balance roundrobin
    option tcp-check
    server ldap1 10.0.1.10:389 check
    server ldap2 10.0.1.11:389 check
    server ldap3 10.0.1.12:389 check
```

## 📖 Voir Aussi

- [Production Monitoring](Production-Monitoring.md)
- [Multi-Server Setup](Multi-Server.md)
- [Docker Deployment](Docker-Deployment.md)
- [OpenLDAP Guide](OpenLDAP.md)
