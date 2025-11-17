# Mode Daemon - Service de Surveillance

## Introduction

Le mode daemon permet d'exécuter LDAP Health Monitor en tant que service système en arrière-plan, assurant une surveillance continue de votre infrastructure LDAP 24/7. Ce guide couvre l'installation, la configuration et la gestion du daemon sur différentes plateformes.

## Table des Matières

- [Introduction](#introduction)
- [Qu'est-ce qu'un Daemon ?](#quest-ce-quun-daemon)
- [Architecture du Daemon](#architecture-du-daemon)
- [Installation et Configuration](#installation-et-configuration)
- [Systemd (Linux)](#systemd-linux)
- [Launchd (macOS)](#launchd-macos)
- [Windows Service](#windows-service)
- [Docker Container](#docker-container)
- [Gestion du Daemon](#gestion-du-daemon)
- [Logs et Monitoring](#logs-et-monitoring)
- [Haute Disponibilité](#haute-disponibilité)
- [Troubleshooting](#troubleshooting)
- [Bonnes Pratiques](#bonnes-pratiques)

---

## Qu'est-ce qu'un Daemon ?

Un **daemon** (ou service) est un processus qui s'exécute en arrière-plan de manière continue, sans interaction directe avec l'utilisateur. Pour LDAP Health Monitor, le daemon :

- **Collecte** les métriques à intervalles réguliers
- **Surveille** l'état du serveur LDAP en continu
- **Envoie** des alertes en cas de problème
- **Expose** les métriques pour Prometheus
- **S'exécute** automatiquement au démarrage du système
- **Redémarre** automatiquement en cas d'erreur

### Avantages du Mode Daemon

| Avantage | Description |
|----------|-------------|
| **Surveillance continue** | Monitoring 24/7 sans intervention manuelle |
| **Démarrage automatique** | Lance automatiquement au boot du serveur |
| **Auto-recovery** | Redémarrage automatique en cas d'erreur |
| **Gestion centralisée** | Contrôle via systemctl/launchctl |
| **Logs structurés** | Journalisation via syslog/journald |
| **Resource limits** | Limitations CPU/mémoire configurables |

---

## Architecture du Daemon

### Composants du Daemon

```
┌─────────────────────────────────────────────────────────────┐
│                 LDAP Monitor Daemon                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐   │
│  │           Main Process                             │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  • Signal handling (SIGTERM, SIGINT, SIGHUP)       │   │
│  │  • Graceful shutdown                               │   │
│  │  • Health checks                                   │   │
│  └────────────────┬───────────────────────────────────┘   │
│                   │                                         │
│  ┌────────────────▼───────────────────────────────────┐   │
│  │         Scheduler (schedule library)               │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  • Collecte périodique (ex: toutes les 5 min)     │   │
│  │  • Gestion des jobs                                │   │
│  │  • Retry logic                                     │   │
│  └────────────────┬───────────────────────────────────┘   │
│                   │                                         │
│  ┌────────────────▼───────────────────────────────────┐   │
│  │    Worker Threads / Async Tasks                    │   │
│  ├────────────────────────────────────────────────────┤   │
│  │  • Metrics Collector                               │   │
│  │  • Alert Manager                                   │   │
│  │  • Prometheus Exporter                             │   │
│  └────────────────────────────────────────────────────┘   │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Cycle de Vie du Daemon

```
┌───────────────────────────────────────────────────────────┐
│                  Cycle de Vie                              │
└───────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   START      │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │ Initialization│
    │ - Load config │
    │ - Connect LDAP│
    │ - Setup sched │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │   RUNNING    │◄────────────┐
    │ - Collect    │             │
    │ - Alert      │             │
    │ - Export     │             │
    └──────┬───────┘             │
           │                     │
           │ Error?              │
           ├─────────Yes────►┌───┴────┐
           │                 │ Retry  │
           │                 │ Sleep  │
           │                 └────────┘
           │ No
           │
           │ Signal SIGTERM/SIGINT?
           │
    ┌──────▼───────┐
    │  STOPPING    │
    │ - Finish jobs│
    │ - Close conns│
    │ - Cleanup    │
    └──────┬───────┘
           │
    ┌──────▼───────┐
    │   STOPPED    │
    └──────────────┘
```

---

## Installation et Configuration

### Prérequis

```bash
# Vérifier l'installation de Python
python3 --version

# Vérifier l'installation de pip
pip3 --version

# Installer LDAP Health Monitor
pip3 install ldap-health-monitor

# Ou depuis le source
cd ldap-health-monitor
pip3 install -e .
```

### Structure des Fichiers

```bash
# Structure recommandée
/opt/ldap-monitor/               # Installation
├── bin/
│   └── ldap-monitor            # Exécutable
├── config/
│   ├── config.yaml             # Configuration principale
│   └── .env                    # Variables d'environnement
├── logs/
│   └── monitor.log             # Logs
├── data/
│   └── metrics.db              # Base de données (si SQLite)
└── backups/
    └── ...                      # Backups

/etc/systemd/system/             # systemd (Linux)
└── ldap-monitor.service

/Library/LaunchDaemons/          # launchd (macOS)
└── com.company.ldap-monitor.plist

/var/log/ldap-monitor/           # Logs système
└── monitor.log
```

### Création du Répertoire

```bash
# Créer la structure
sudo mkdir -p /opt/ldap-monitor/{bin,config,logs,data,backups}
sudo mkdir -p /var/log/ldap-monitor

# Créer un utilisateur dédié (sécurité)
sudo useradd -r -s /bin/false -d /opt/ldap-monitor ldap-monitor

# Permissions
sudo chown -R ldap-monitor:ldap-monitor /opt/ldap-monitor
sudo chown -R ldap-monitor:ldap-monitor /var/log/ldap-monitor
sudo chmod 750 /opt/ldap-monitor
sudo chmod 640 /opt/ldap-monitor/config/config.yaml
```

---

## Systemd (Linux)

### Service Unit File

Créer `/etc/systemd/system/ldap-monitor.service` :

```ini
[Unit]
Description=LDAP Health Monitor Daemon
Documentation=https://github.com/ldap-health-monitor/wiki
After=network.target network-online.target
Wants=network-online.target

[Service]
Type=simple
User=ldap-monitor
Group=ldap-monitor
WorkingDirectory=/opt/ldap-monitor

# Commande principale
ExecStart=/usr/local/bin/ldap-monitor monitor start --daemon --config /opt/ldap-monitor/config/config.yaml

# Reload configuration on SIGHUP
ExecReload=/bin/kill -HUP $MAINPID

# Arrêt gracieux
KillMode=mixed
KillSignal=SIGTERM
TimeoutStopSec=30s

# Restart automatique
Restart=always
RestartSec=10s

# Limites de ressources
MemoryLimit=512M
CPUQuota=50%
TasksMax=50

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/ldap-monitor /var/log/ldap-monitor

# Variables d'environnement
EnvironmentFile=/opt/ldap-monitor/config/.env

# Logs
StandardOutput=journal
StandardError=journal
SyslogIdentifier=ldap-monitor

[Install]
WantedBy=multi-user.target
```

### Installation du Service

```bash
# Copier le fichier de service
sudo cp ldap-monitor.service /etc/systemd/system/

# Recharger systemd
sudo systemctl daemon-reload

# Activer le service (démarrage automatique)
sudo systemctl enable ldap-monitor

# Démarrer le service
sudo systemctl start ldap-monitor

# Vérifier le statut
sudo systemctl status ldap-monitor

# Sortie attendue
● ldap-monitor.service - LDAP Health Monitor Daemon
     Loaded: loaded (/etc/systemd/system/ldap-monitor.service; enabled; vendor preset: enabled)
     Active: active (running) since Sun 2025-11-17 14:30:00 CET; 5min ago
   Main PID: 12345 (ldap-monitor)
      Tasks: 8 (limit: 50)
     Memory: 145.2M (limit: 512.0M)
        CPU: 2.5s
     CGroup: /system.slice/ldap-monitor.service
             └─12345 /usr/local/bin/ldap-monitor monitor start --daemon
```

### Gestion du Service Systemd

```bash
# Démarrer
sudo systemctl start ldap-monitor

# Arrêter
sudo systemctl stop ldap-monitor

# Redémarrer
sudo systemctl restart ldap-monitor

# Recharger la config (SIGHUP)
sudo systemctl reload ldap-monitor

# Voir les logs
sudo journalctl -u ldap-monitor -f

# Voir les logs avec filtres
sudo journalctl -u ldap-monitor --since "1 hour ago"
sudo journalctl -u ldap-monitor -p err  # Seulement les erreurs
sudo journalctl -u ldap-monitor -n 100  # Dernières 100 lignes

# Voir le statut détaillé
sudo systemctl status ldap-monitor -l

# Activer (démarrage auto)
sudo systemctl enable ldap-monitor

# Désactiver (pas de démarrage auto)
sudo systemctl disable ldap-monitor
```

### Configuration Avancée Systemd

#### Avec Timer (alternative à l'intervalle interne)

```ini
# /etc/systemd/system/ldap-monitor.timer
[Unit]
Description=LDAP Health Monitor Timer
Documentation=https://github.com/ldap-health-monitor/wiki

[Timer]
# Démarrage 5 minutes après le boot
OnBootSec=5min

# Exécution toutes les 5 minutes
OnUnitActiveSec=5min

# Randomiser +/- 30 secondes (éviter pic de charge)
RandomizedDelaySec=30s

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/ldap-monitor.service (modifié)
[Unit]
Description=LDAP Health Monitor Collection
Documentation=https://github.com/ldap-health-monitor/wiki

[Service]
Type=oneshot
User=ldap-monitor
Group=ldap-monitor
ExecStart=/usr/local/bin/ldap-monitor metrics collect
```

```bash
# Activer le timer
sudo systemctl enable ldap-monitor.timer
sudo systemctl start ldap-monitor.timer

# Vérifier
sudo systemctl list-timers ldap-monitor.timer
```

#### Avec Socket Activation

```ini
# /etc/systemd/system/ldap-monitor.socket
[Unit]
Description=LDAP Monitor Prometheus Socket
Documentation=https://github.com/ldap-health-monitor/wiki

[Socket]
ListenStream=9090
Accept=false

[Install]
WantedBy=sockets.target
```

---

## Launchd (macOS)

### Property List File

Créer `/Library/LaunchDaemons/com.company.ldap-monitor.plist` :

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- Identifiant unique -->
    <key>Label</key>
    <string>com.company.ldap-monitor</string>

    <!-- Programme à exécuter -->
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/ldap-monitor</string>
        <string>monitor</string>
        <string>start</string>
        <string>--daemon</string>
        <string>--config</string>
        <string>/opt/ldap-monitor/config/config.yaml</string>
    </array>

    <!-- Répertoire de travail -->
    <key>WorkingDirectory</key>
    <string>/opt/ldap-monitor</string>

    <!-- Utilisateur -->
    <key>UserName</key>
    <string>_ldap-monitor</string>
    <key>GroupName</key>
    <string>_ldap-monitor</string>

    <!-- Démarrage automatique -->
    <key>RunAtLoad</key>
    <true/>

    <!-- Keep alive (redémarrer si crash) -->
    <key>KeepAlive</key>
    <dict>
        <key>SuccessfulExit</key>
        <false/>
        <key>Crashed</key>
        <true/>
    </dict>

    <!-- Logs -->
    <key>StandardOutPath</key>
    <string>/var/log/ldap-monitor/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/var/log/ldap-monitor/stderr.log</string>

    <!-- Variables d'environnement -->
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>/usr/local/bin:/usr/bin:/bin</string>
    </dict>

    <!-- Limites de ressources -->
    <key>SoftResourceLimits</key>
    <dict>
        <key>NumberOfFiles</key>
        <integer>1024</integer>
    </dict>

    <!-- Délai avant redémarrage -->
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
```

### Installation du Service Launchd

```bash
# Copier le plist
sudo cp com.company.ldap-monitor.plist /Library/LaunchDaemons/

# Permissions
sudo chown root:wheel /Library/LaunchDaemons/com.company.ldap-monitor.plist
sudo chmod 644 /Library/LaunchDaemons/com.company.ldap-monitor.plist

# Charger le service
sudo launchctl load /Library/LaunchDaemons/com.company.ldap-monitor.plist

# Démarrer
sudo launchctl start com.company.ldap-monitor

# Vérifier
sudo launchctl list | grep ldap-monitor

# Sortie
12345   0       com.company.ldap-monitor
```

### Gestion du Service Launchd

```bash
# Charger
sudo launchctl load /Library/LaunchDaemons/com.company.ldap-monitor.plist

# Décharger (arrêter et désactiver)
sudo launchctl unload /Library/LaunchDaemons/com.company.ldap-monitor.plist

# Démarrer
sudo launchctl start com.company.ldap-monitor

# Arrêter
sudo launchctl stop com.company.ldap-monitor

# Lister les services
sudo launchctl list | grep ldap

# Voir les logs
tail -f /var/log/ldap-monitor/stdout.log
tail -f /var/log/ldap-monitor/stderr.log
```

---

## Windows Service

### Installation avec NSSM (Non-Sucking Service Manager)

```powershell
# Télécharger NSSM
# https://nssm.cc/download

# Installer le service
nssm install ldap-monitor "C:\Python39\Scripts\ldap-monitor.exe" "monitor start --daemon --config C:\ldap-monitor\config.yaml"

# Configurer le service
nssm set ldap-monitor AppDirectory C:\ldap-monitor
nssm set ldap-monitor DisplayName "LDAP Health Monitor"
nssm set ldap-monitor Description "Monitoring service for LDAP infrastructure"
nssm set ldap-monitor Start SERVICE_AUTO_START
nssm set ldap-monitor AppStdout C:\ldap-monitor\logs\stdout.log
nssm set ldap-monitor AppStderr C:\ldap-monitor\logs\stderr.log
nssm set ldap-monitor AppRotateFiles 1
nssm set ldap-monitor AppRotateSeconds 86400
nssm set ldap-monitor AppRotateBytes 10485760

# Démarrer
nssm start ldap-monitor

# Status
nssm status ldap-monitor

# Arrêter
nssm stop ldap-monitor

# Désinstaller
nssm remove ldap-monitor confirm
```

### Gestion via Services Windows

```powershell
# PowerShell

# Démarrer
Start-Service ldap-monitor

# Arrêter
Stop-Service ldap-monitor

# Redémarrer
Restart-Service ldap-monitor

# Status
Get-Service ldap-monitor

# Sortie
Status   Name               DisplayName
------   ----               -----------
Running  ldap-monitor       LDAP Health Monitor
```

---

## Docker Container

### Dockerfile

```dockerfile
# Dockerfile

FROM python:3.11-slim

# Métadonnées
LABEL maintainer="your-email@company.com"
LABEL description="LDAP Health Monitor"
LABEL version="1.0.0"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV LDAP_MONITOR_CONFIG=/config/config.yaml

# Installer les dépendances système
RUN apt-get update && apt-get install -y \
    libldap2-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

# Créer un utilisateur non-root
RUN useradd -r -u 1000 -m ldap-monitor

# Répertoire de travail
WORKDIR /app

# Copier les fichiers
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir -e .

# Créer les répertoires nécessaires
RUN mkdir -p /config /data /logs && \
    chown -R ldap-monitor:ldap-monitor /app /config /data /logs

# Utiliser l'utilisateur non-root
USER ldap-monitor

# Volumes
VOLUME ["/config", "/data", "/logs"]

# Exposer le port Prometheus
EXPOSE 9090

# Health check
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD ldap-monitor health || exit 1

# Commande par défaut
CMD ["ldap-monitor", "monitor", "start", "--daemon", "--config", "/config/config.yaml"]
```

### Docker Compose

```yaml
# docker-compose.yml

version: '3.8'

services:
  ldap-monitor:
    build: .
    image: ldap-monitor:latest
    container_name: ldap-monitor
    restart: unless-stopped

    # Variables d'environnement
    environment:
      - LDAP_PASSWORD=${LDAP_PASSWORD}
      - SLACK_WEBHOOK=${SLACK_WEBHOOK}
      - SMTP_USER=${SMTP_USER}
      - SMTP_PASSWORD=${SMTP_PASSWORD}

    # Fichier d'environnement
    env_file:
      - .env

    # Volumes
    volumes:
      - ./config:/config:ro
      - ldap-monitor-data:/data
      - ldap-monitor-logs:/logs

    # Ports
    ports:
      - "9090:9090"  # Prometheus metrics

    # Réseau
    networks:
      - monitoring

    # Health check
    healthcheck:
      test: ["CMD", "ldap-monitor", "health"]
      interval: 60s
      timeout: 10s
      retries: 3
      start_period: 30s

    # Limites de ressources
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 128M

    # Logging
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"

volumes:
  ldap-monitor-data:
  ldap-monitor-logs:

networks:
  monitoring:
    external: true
```

### Déploiement Docker

```bash
# Build
docker build -t ldap-monitor:latest .

# Run simple
docker run -d \
  --name ldap-monitor \
  --restart unless-stopped \
  -v $(pwd)/config:/config:ro \
  -v ldap-monitor-data:/data \
  -v ldap-monitor-logs:/logs \
  -p 9090:9090 \
  -e LDAP_PASSWORD=${LDAP_PASSWORD} \
  ldap-monitor:latest

# Avec docker-compose
docker-compose up -d

# Logs
docker logs -f ldap-monitor

# Status
docker ps | grep ldap-monitor

# Arrêter
docker-compose down

# Mise à jour
docker-compose pull
docker-compose up -d
```

---

## Gestion du Daemon

### Commandes CLI

```bash
# Démarrer le daemon
ldap-monitor monitor start --daemon

# Démarrer en foreground (debug)
ldap-monitor monitor start

# Arrêter le daemon
ldap-monitor monitor stop

# Redémarrer
ldap-monitor monitor restart

# Recharger la configuration (sans arrêter)
ldap-monitor monitor reload

# Status
ldap-monitor monitor status

# Sortie
✅ LDAP Monitor Daemon Status
────────────────────────────────────
Status:     Running
PID:        12345
Uptime:     2 days, 5 hours, 23 minutes
Config:     /opt/ldap-monitor/config/config.yaml

Metrics:
  Collections:    1,234
  Last collection: 2025-11-17 14:30:00 (30s ago)
  Alerts sent:    12 (5 critical, 7 warning)

Health:
  LDAP connection: ✅ OK
  Prometheus:      ✅ Running (port 9090)
  Memory usage:    145 MB / 512 MB (28%)
  CPU usage:       2.5%
```

### Signals Unix

```bash
# Arrêt gracieux
kill -TERM <PID>
# ou
kill -INT <PID>

# Rechargement config
kill -HUP <PID>

# Arrêt forcé (à éviter)
kill -KILL <PID>
```

### PID File

```python
# Le daemon crée un PID file
/var/run/ldap-monitor.pid

# Contenu: le PID du processus
12345
```

```bash
# Lire le PID
cat /var/run/ldap-monitor.pid

# Vérifier si le processus tourne
kill -0 $(cat /var/run/ldap-monitor.pid) && echo "Running" || echo "Stopped"

# Arrêter proprement
kill -TERM $(cat /var/run/ldap-monitor.pid)
```

---

## Logs et Monitoring

### Configuration des Logs

```yaml
# config.yaml

logging:
  level: INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

  # Fichier de log
  file: /var/log/ldap-monitor/monitor.log
  max_bytes: 10485760  # 10 MB
  backup_count: 5

  # Console (stdout)
  console: true

  # Format
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  datefmt: "%Y-%m-%d %H:%M:%S"

  # Logs structurés (JSON)
  json: false

  # Syslog (optionnel)
  syslog:
    enabled: false
    address: /dev/log
    facility: daemon
```

### Rotation des Logs

#### Logrotate (Linux)

```bash
# /etc/logrotate.d/ldap-monitor

/var/log/ldap-monitor/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0640 ldap-monitor ldap-monitor
    sharedscripts
    postrotate
        systemctl reload ldap-monitor > /dev/null 2>&1 || true
    endscript
}
```

### Surveillance du Daemon Lui-même

#### Healthcheck Endpoint

```bash
# Le daemon expose un endpoint de santé
curl http://localhost:9090/health

# Réponse
{
  "status": "healthy",
  "uptime": 172800,
  "last_collection": "2025-11-17T14:30:00Z",
  "ldap_connection": "ok",
  "prometheus_server": "running"
}
```

#### Monitoring avec Monit

```bash
# /etc/monit/conf.d/ldap-monitor

check process ldap-monitor with pidfile /var/run/ldap-monitor.pid
    start program = "/bin/systemctl start ldap-monitor"
    stop program  = "/bin/systemctl stop ldap-monitor"

    # Vérifier que le processus tourne
    if failed host localhost port 9090 protocol http
        request "/health"
        with timeout 10 seconds
        for 3 cycles
    then restart

    # Vérifier l'usage mémoire
    if memory > 512 MB then alert
    if memory > 768 MB then restart

    # Vérifier l'usage CPU
    if cpu > 80% for 5 cycles then alert
    if cpu > 95% for 10 cycles then restart

    # Vérifier le PID file
    if not exist then restart
    if failed pid then restart
```

---

## Haute Disponibilité

### Mode Master-Standby

```yaml
# config.yaml (sur le master)

monitoring:
  ha:
    enabled: true
    mode: master

    # Lock distribué (Redis/etcd)
    lock:
      backend: redis
      redis_url: redis://localhost:6379/0
      key: ldap-monitor:master-lock
      ttl: 30  # secondes

    # Heartbeat
    heartbeat:
      interval: 10  # secondes
      timeout: 30   # considéré mort après 30s
```

```yaml
# config.yaml (sur le standby)

monitoring:
  ha:
    enabled: true
    mode: standby

    # Même configuration de lock
    lock:
      backend: redis
      redis_url: redis://localhost:6379/0
      key: ldap-monitor:master-lock
      ttl: 30

    # Promotion automatique
    auto_promote: true
    promotion_delay: 30  # attendre 30s avant promotion
```

### Load Balancing (Multiple Instances)

```yaml
# Plusieurs instances avec partitionnement

# Instance 1 - Métriques de contenu
monitoring:
  instance_id: collector-1
  metrics:
    - users_count
    - groups_count

# Instance 2 - Métriques de performance
monitoring:
  instance_id: collector-2
  metrics:
    - response_time
    - operations

# Instance 3 - Métriques de sécurité
monitoring:
  instance_id: collector-3
  metrics:
    - auth_failures
    - ssl_cert_expiry
```

---

## Troubleshooting

### Problème 1 : Le Daemon Ne Démarre Pas

**Diagnostic** :
```bash
# Vérifier les logs systemd
sudo journalctl -u ldap-monitor -n 50

# Tester en foreground
sudo -u ldap-monitor ldap-monitor monitor start

# Vérifier la config
ldap-monitor config validate

# Vérifier les permissions
ls -la /opt/ldap-monitor/config/
```

**Solutions communes** :
1. Vérifier les permissions sur config.yaml
2. Vérifier que l'utilisateur ldap-monitor existe
3. Vérifier les dépendances Python
4. Vérifier la connectivité LDAP

### Problème 2 : Le Daemon S'Arrête de Manière Inattendue

**Diagnostic** :
```bash
# Voir pourquoi il s'est arrêté
sudo journalctl -u ldap-monitor -p err

# Vérifier l'OOM killer
dmesg | grep -i "out of memory"
sudo journalctl -k | grep -i "killed process"

# Vérifier l'usage ressources
systemctl status ldap-monitor -l
```

**Solutions** :
```ini
# Augmenter les limites dans le service
[Service]
MemoryLimit=1G
Restart=always
RestartSec=10s
```

### Problème 3 : Métriques Non Collectées

**Diagnostic** :
```bash
# Vérifier que le daemon tourne
ldap-monitor monitor status

# Vérifier les logs
tail -f /var/log/ldap-monitor/monitor.log

# Collecte manuelle pour tester
ldap-monitor metrics collect --verbose
```

---

## Bonnes Pratiques

### 1. Sécurité

```bash
# ✅ Utilisateur dédié (pas root)
User=ldap-monitor

# ✅ Permissions strictes sur config
chmod 600 /opt/ldap-monitor/config/config.yaml

# ✅ SELinux/AppArmor
# Créer un profil de sécurité

# ✅ Limites de ressources
MemoryLimit=512M
CPUQuota=50%
```

### 2. Fiabilité

```ini
# ✅ Restart automatique
Restart=always
RestartSec=10s

# ✅ Timeout approprié
TimeoutStopSec=30s

# ✅ Graceful shutdown
KillMode=mixed
KillSignal=SIGTERM
```

### 3. Monitoring

```bash
# ✅ Surveiller le daemon lui-même
# Utiliser Monit, Supervisor, ou Prometheus

# ✅ Logs structurés
logging:
  json: true

# ✅ Alertes si le daemon s'arrête
# Via Monit, Systemd OnFailure, etc.
```

### 4. Maintenance

```bash
# ✅ Rotation des logs configurée
# ✅ Backups réguliers de la config
# ✅ Documentation des procédures
# ✅ Tests réguliers du failover (si HA)
```

---

## Conclusion

Le mode daemon assure une surveillance continue et fiable de votre infrastructure LDAP. Les points clés :

1. **Utiliser systemd/launchd** pour gestion système native
2. **Configurer le restart automatique** pour la résilience
3. **Limiter les ressources** pour éviter la surcharge
4. **Surveiller le daemon** lui-même
5. **Implémenter la HA** pour les environnements critiques

### Prochaines Étapes

- **[Prometheus Metrics](./Prometheus-Metrics.md)** - Intégration avec Prometheus
- **[History & Trends](./History-Trends.md)** - Analyse historique
- **[Metrics Collection](./Metrics-Collection.md)** - Détails sur la collecte

---

**Dernière mise à jour** : 2025-11-17
**Version** : 1.0.0
