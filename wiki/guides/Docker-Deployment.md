# Guide de Déploiement Docker

Guide complet pour déployer LDAP Health Monitor avec Docker, docker-compose, et orchestration.

## 🎯 Vue d'Ensemble

Ce guide couvre :

- Déploiement avec Docker
- Configuration docker-compose
- Gestion des volumes et données persistantes
- Variables d'environnement
- Networking et sécurité
- Orchestration (Docker Swarm, Kubernetes)
- Mise à jour et maintenance

## 🐳 Image Docker

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim-bullseye AS builder

# Metadata
LABEL maintainer="ops@example.com"
LABEL description="LDAP Health Monitor"
LABEL version="1.0.0"

# Build arguments
ARG DEBIAN_FRONTEND=noninteractive
ARG BUILD_DATE
ARG VCS_REF
ARG VERSION

# Labels
LABEL org.opencontainers.image.created=$BUILD_DATE
LABEL org.opencontainers.image.revision=$VCS_REF
LABEL org.opencontainers.image.version=$VERSION

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libldap2-dev \
    libsasl2-dev \
    libssl-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11-slim-bullseye

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libldap-2.4-2 \
    libsasl2-2 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r -g 1000 ldapmon && \
    useradd -r -u 1000 -g ldapmon -d /app -s /sbin/nologin ldapmon

# Create directories
RUN mkdir -p /app /etc/ldap-monitor /var/lib/ldap-monitor /var/log/ldap-monitor && \
    chown -R ldapmon:ldapmon /app /etc/ldap-monitor /var/lib/ldap-monitor /var/log/ldap-monitor

WORKDIR /app

# Copy Python packages from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application
COPY --chown=ldapmon:ldapmon . .

# Install application
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER ldapmon

# Volumes
VOLUME ["/etc/ldap-monitor", "/var/lib/ldap-monitor", "/var/log/ldap-monitor"]

# Expose ports
EXPOSE 8080 9090

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ldap-monitor test connection || exit 1

# Default command
ENTRYPOINT ["ldap-monitor"]
CMD ["monitor", "start", "--daemon"]
```

### Build de l'Image

```bash
#!/bin/bash
# scripts/docker-build.sh

set -euo pipefail

# Variables
IMAGE_NAME="ldap-health-monitor"
REGISTRY="docker.io/yourorg"
VERSION=$(git describe --tags --always --dirty)
BUILD_DATE=$(date -u +'%Y-%m-%dT%H:%M:%SZ')
VCS_REF=$(git rev-parse --short HEAD)

# Build
docker build \
    --build-arg BUILD_DATE="$BUILD_DATE" \
    --build-arg VCS_REF="$VCS_REF" \
    --build-arg VERSION="$VERSION" \
    -t "$REGISTRY/$IMAGE_NAME:$VERSION" \
    -t "$REGISTRY/$IMAGE_NAME:latest" \
    .

# Test
docker run --rm "$REGISTRY/$IMAGE_NAME:$VERSION" --version

# Push (optionnel)
if [ "${PUSH:-false}" = "true" ]; then
    docker push "$REGISTRY/$IMAGE_NAME:$VERSION"
    docker push "$REGISTRY/$IMAGE_NAME:latest"
fi

echo "✓ Image built: $REGISTRY/$IMAGE_NAME:$VERSION"
```

## 🚀 Docker Compose

### Configuration Basique

```yaml
# docker-compose.yml
version: '3.8'

services:
  ldap-monitor:
    image: yourorg/ldap-health-monitor:latest
    container_name: ldap-monitor
    restart: unless-stopped

    # Configuration
    environment:
      - LDAP_SERVER=ldaps://ldap.example.com
      - LDAP_PORT=636
      - LDAP_BIND_DN=cn=monitor,dc=example,dc=com
      - LDAP_BIND_PASSWORD=${LDAP_PASSWORD}
      - LDAP_BASE_DN=dc=example,dc=com
      - LOG_LEVEL=INFO

    # Volumes
    volumes:
      - ./config:/etc/ldap-monitor:ro
      - ldap-monitor-data:/var/lib/ldap-monitor
      - ldap-monitor-logs:/var/log/ldap-monitor

    # Network
    networks:
      - ldap-network

    # Ports
    ports:
      - "8080:8080"  # API
      - "9090:9090"  # Metrics

    # Health check
    healthcheck:
      test: ["CMD", "ldap-monitor", "test", "connection"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

    # Ressources
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

volumes:
  ldap-monitor-data:
    driver: local
  ldap-monitor-logs:
    driver: local

networks:
  ldap-network:
    driver: bridge
```

### Configuration Avancée avec Stack Complète

```yaml
# docker-compose.full.yml
version: '3.8'

services:
  # LDAP Server (pour tests)
  openldap:
    image: osixia/openldap:latest
    container_name: openldap
    restart: unless-stopped
    environment:
      - LDAP_ORGANISATION=Example Inc
      - LDAP_DOMAIN=example.com
      - LDAP_ADMIN_PASSWORD=${LDAP_ADMIN_PASSWORD}
      - LDAP_CONFIG_PASSWORD=${LDAP_CONFIG_PASSWORD}
      - LDAP_TLS_VERIFY_CLIENT=try
    volumes:
      - openldap-data:/var/lib/ldap
      - openldap-config:/etc/ldap/slapd.d
      - ./certs:/container/service/slapd/assets/certs:ro
    networks:
      - ldap-network
    ports:
      - "389:389"
      - "636:636"

  # LDAP Monitor
  ldap-monitor:
    image: yourorg/ldap-health-monitor:latest
    container_name: ldap-monitor
    restart: unless-stopped
    depends_on:
      - openldap
      - postgres
      - redis

    environment:
      # LDAP Config
      - LDAP_SERVER=ldaps://openldap
      - LDAP_PORT=636
      - LDAP_BIND_DN=cn=admin,dc=example,dc=com
      - LDAP_BIND_PASSWORD=${LDAP_ADMIN_PASSWORD}
      - LDAP_BASE_DN=dc=example,dc=com
      - LDAP_USE_SSL=true
      - LDAP_VERIFY_SSL=false

      # Database
      - DB_TYPE=postgresql
      - DB_HOST=postgres
      - DB_PORT=5432
      - DB_NAME=ldap_monitor
      - DB_USER=ldapmon
      - DB_PASSWORD=${DB_PASSWORD}

      # Cache
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - CACHE_ENABLED=true

      # Monitoring
      - MONITORING_ENABLED=true
      - MONITORING_INTERVAL=300
      - METRICS_ENABLED=true

      # Alerting
      - ALERTS_ENABLED=true
      - SMTP_SERVER=${SMTP_SERVER}
      - SMTP_PORT=${SMTP_PORT}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
      - ALERT_EMAIL=${ALERT_EMAIL}
      - SLACK_WEBHOOK=${SLACK_WEBHOOK}

      # Security
      - API_ENABLED=true
      - API_KEY=${API_KEY}

    volumes:
      - ./config:/etc/ldap-monitor:ro
      - ldap-monitor-data:/var/lib/ldap-monitor
      - ldap-monitor-logs:/var/log/ldap-monitor

    networks:
      - ldap-network

    ports:
      - "8080:8080"
      - "9090:9090"

    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # PostgreSQL (pour métriques historiques)
  postgres:
    image: postgres:15-alpine
    container_name: ldap-monitor-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=ldap_monitor
      - POSTGRES_USER=ldapmon
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
      - ./init-db.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - ldap-network

  # Redis (pour cache)
  redis:
    image: redis:7-alpine
    container_name: ldap-monitor-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - ldap-network

  # Prometheus (pour métriques)
  prometheus:
    image: prom/prometheus:latest
    container_name: ldap-monitor-prometheus
    restart: unless-stopped
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus-data:/prometheus
    networks:
      - ldap-network
    ports:
      - "9091:9090"

  # Grafana (pour dashboards)
  grafana:
    image: grafana/grafana:latest
    container_name: ldap-monitor-grafana
    restart: unless-stopped
    depends_on:
      - prometheus
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
    volumes:
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
      - ./grafana/dashboards:/var/lib/grafana/dashboards:ro
      - grafana-data:/var/lib/grafana
    networks:
      - ldap-network
    ports:
      - "3000:3000"

  # Nginx (reverse proxy)
  nginx:
    image: nginx:alpine
    container_name: ldap-monitor-nginx
    restart: unless-stopped
    depends_on:
      - ldap-monitor
      - grafana
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
    networks:
      - ldap-network
    ports:
      - "80:80"
      - "443:443"

volumes:
  openldap-data:
  openldap-config:
  ldap-monitor-data:
  ldap-monitor-logs:
  postgres-data:
  redis-data:
  prometheus-data:
  grafana-data:

networks:
  ldap-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Fichier d'Environnement

```bash
# .env
# LDAP Configuration
LDAP_ADMIN_PASSWORD=SecureAdminPassword123!
LDAP_CONFIG_PASSWORD=SecureConfigPassword123!
LDAP_PASSWORD=SecureMonitorPassword123!

# Database
DB_PASSWORD=SecureDBPassword123!

# Redis
REDIS_PASSWORD=SecureRedisPassword123!

# Email/SMTP
SMTP_SERVER=smtp.example.com
SMTP_PORT=587
SMTP_USER=ldap-monitor@example.com
SMTP_PASSWORD=SecureSMTPPassword123!
ALERT_EMAIL=admin@example.com

# Slack
SLACK_WEBHOOK=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# API
API_KEY=SecureAPIKey123!

# Grafana
GRAFANA_PASSWORD=SecureGrafanaPassword123!
```

## 📦 Gestion des Volumes

### Volume Drivers

```yaml
# Volumes avec driver personnalisé
volumes:
  ldap-monitor-data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /mnt/data/ldap-monitor

  # Volume NFS
  ldap-monitor-shared:
    driver: local
    driver_opts:
      type: nfs
      o: addr=nfs-server.example.com,rw
      device: ":/exports/ldap-monitor"

  # Volume avec encryption
  ldap-monitor-encrypted:
    driver: local
    driver_opts:
      type: tmpfs
      device: tmpfs
      o: size=1G,uid=1000
```

### Backup des Volumes

```bash
#!/bin/bash
# scripts/backup-volumes.sh

set -euo pipefail

BACKUP_DIR="/backups/docker-volumes"
DATE=$(date +%Y%m%d-%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup volume data
docker run --rm \
    -v ldap-monitor-data:/data:ro \
    -v "$BACKUP_DIR":/backup \
    alpine \
    tar czf "/backup/ldap-monitor-data-$DATE.tar.gz" -C /data .

# Backup volume logs
docker run --rm \
    -v ldap-monitor-logs:/logs:ro \
    -v "$BACKUP_DIR":/backup \
    alpine \
    tar czf "/backup/ldap-monitor-logs-$DATE.tar.gz" -C /logs .

echo "✓ Backups created in $BACKUP_DIR"

# Nettoyage anciens backups (>30 jours)
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +30 -delete
```

### Restore des Volumes

```bash
#!/bin/bash
# scripts/restore-volumes.sh

set -euo pipefail

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Stop containers
docker-compose down

# Restore
docker run --rm \
    -v ldap-monitor-data:/data \
    -v "$(dirname "$BACKUP_FILE")":/backup \
    alpine \
    tar xzf "/backup/$(basename "$BACKUP_FILE")" -C /data

# Start containers
docker-compose up -d

echo "✓ Volume restored from $BACKUP_FILE"
```

## 🌐 Configuration Réseau

### Network Nginx

```nginx
# nginx/nginx.conf
user nginx;
worker_processes auto;
error_log /var/log/nginx/error.log warn;
pid /var/run/nginx.pid;

events {
    worker_connections 1024;
}

http {
    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                    '$status $body_bytes_sent "$http_referer" '
                    '"$http_user_agent" "$http_x_forwarded_for"';

    access_log /var/log/nginx/access.log main;

    sendfile on;
    tcp_nopush on;
    keepalive_timeout 65;
    gzip on;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # Upstream LDAP Monitor
    upstream ldap_monitor {
        server ldap-monitor:8080;
    }

    # Upstream Grafana
    upstream grafana {
        server grafana:3000;
    }

    # HTTP -> HTTPS redirect
    server {
        listen 80;
        server_name ldap-monitor.example.com;
        return 301 https://$server_name$request_uri;
    }

    # HTTPS
    server {
        listen 443 ssl http2;
        server_name ldap-monitor.example.com;

        # SSL
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers HIGH:!aNULL:!MD5;
        ssl_prefer_server_ciphers on;

        # Security headers
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-XSS-Protection "1; mode=block" always;

        # API
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;

            proxy_pass http://ldap_monitor/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Metrics
        location /metrics {
            proxy_pass http://ldap_monitor/metrics;
            allow 10.0.0.0/8;
            deny all;
        }

        # Grafana
        location /grafana/ {
            proxy_pass http://grafana/;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
        }

        # Health check
        location /health {
            proxy_pass http://ldap_monitor/health;
            access_log off;
        }
    }
}
```

### Network Isolation

```yaml
# docker-compose.network.yml
version: '3.8'

services:
  ldap-monitor:
    networks:
      - frontend
      - backend
      - ldap

  postgres:
    networks:
      - backend

  redis:
    networks:
      - backend

  nginx:
    networks:
      - frontend

networks:
  frontend:
    driver: bridge
    internal: false  # Accessible depuis l'extérieur

  backend:
    driver: bridge
    internal: true  # Isolé

  ldap:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/24
```

## 🔄 Orchestration

### Docker Swarm

```yaml
# docker-stack.yml
version: '3.8'

services:
  ldap-monitor:
    image: yourorg/ldap-health-monitor:latest
    deploy:
      mode: replicated
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        failure_action: rollback
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
      placement:
        constraints:
          - node.role == worker
          - node.labels.type == monitoring

    environment:
      - LDAP_SERVER=ldaps://ldap.example.com
      - LDAP_BIND_DN=cn=monitor,dc=example,dc=com
      - LDAP_BIND_PASSWORD_FILE=/run/secrets/ldap_password

    secrets:
      - ldap_password
      - api_key

    networks:
      - overlay-network

    ports:
      - target: 8080
        published: 8080
        protocol: tcp
        mode: ingress

    volumes:
      - ldap-monitor-data:/var/lib/ldap-monitor

    healthcheck:
      test: ["CMD", "ldap-monitor", "test", "connection"]
      interval: 30s
      timeout: 10s
      retries: 3

secrets:
  ldap_password:
    external: true
  api_key:
    external: true

volumes:
  ldap-monitor-data:
    driver: local

networks:
  overlay-network:
    driver: overlay
    attachable: true
```

```bash
# Déployer stack Swarm
docker stack deploy -c docker-stack.yml ldap-monitor

# Scaler
docker service scale ldap-monitor_ldap-monitor=5

# Update
docker service update \
    --image yourorg/ldap-health-monitor:v2.0 \
    ldap-monitor_ldap-monitor

# Logs
docker service logs -f ldap-monitor_ldap-monitor
```

### Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ldap-monitor
  namespace: monitoring
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ldap-monitor
  template:
    metadata:
      labels:
        app: ldap-monitor
    spec:
      containers:
      - name: ldap-monitor
        image: yourorg/ldap-health-monitor:latest
        ports:
        - containerPort: 8080
          name: api
        - containerPort: 9090
          name: metrics

        env:
        - name: LDAP_SERVER
          value: "ldaps://ldap.example.com"
        - name: LDAP_BIND_DN
          value: "cn=monitor,dc=example,dc=com"
        - name: LDAP_BIND_PASSWORD
          valueFrom:
            secretKeyRef:
              name: ldap-credentials
              key: password

        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "2Gi"
            cpu: "2000m"

        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10

        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5

        volumeMounts:
        - name: config
          mountPath: /etc/ldap-monitor
          readOnly: true
        - name: data
          mountPath: /var/lib/ldap-monitor

      volumes:
      - name: config
        configMap:
          name: ldap-monitor-config
      - name: data
        persistentVolumeClaim:
          claimName: ldap-monitor-data
---
apiVersion: v1
kind: Service
metadata:
  name: ldap-monitor
  namespace: monitoring
spec:
  selector:
    app: ldap-monitor
  ports:
  - name: api
    port: 8080
    targetPort: 8080
  - name: metrics
    port: 9090
    targetPort: 9090
  type: ClusterIP
```

## 📖 Voir Aussi

- [Production Monitoring](Production-Monitoring.md)
- [Performance Tuning](Performance-Tuning.md)
- [Multi-Server Setup](Multi-Server.md)
- [Backup Strategy](Backup-Strategy.md)
