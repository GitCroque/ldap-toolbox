# Configurations Avancées - LDAP Health Monitor

Guide complet des configurations avancées pour LDAP Health Monitor : multi-environnement, haute disponibilité, configurations complexes.

## 📋 Table des Matières

- [Multi-Environnement](#multi-environnement)
- [Haute Disponibilité](#haute-disponibilité)
- [Active Directory Multi-Domaines](#active-directory-multi-domaines)
- [Configuration Hybride Cloud](#configuration-hybride-cloud)
- [Schémas LDAP Personnalisés](#schémas-ldap-personnalisés)
- [Sécurité Avancée](#sécurité-avancée)
- [Performance et Optimisation](#performance-et-optimisation)

---

## Multi-Environnement

### Architecture Multi-Environnement

```yaml
# config-multi-env.yaml
---
# Configuration partagée entre environnements
_shared: &shared_config
  audit:
    users:
      required_attributes: &required_attrs
        - mail
        - givenName
        - sn
        - employeeNumber

    groups:
      max_size: 1000
      warn_empty: true

  monitoring:
    enabled: true
    metrics:
      - connection_time
      - user_count
      - group_count
      - failed_binds

  reports:
    formats:
      - json
      - html
    retention_days: 90

# ============================================================================
# DÉVELOPPEMENT
# ============================================================================
development:
  <<: *shared_config

  ldap:
    server: ldap://ldap-dev.internal.company.com
    port: 389
    bind_dn: cn=ldap-monitor-dev,ou=services,dc=dev,dc=company,dc=com
    bind_password: ${LDAP_PASSWORD_DEV}
    base_dn: dc=dev,dc=company,dc=com
    users_ou: ou=users,dc=dev,dc=company,dc=com
    groups_ou: ou=groups,dc=dev,dc=company,dc=com

    # Dev: Pas de TLS requis
    use_tls: false
    connection_timeout: 10
    page_size: 100

  audit:
    users:
      required_attributes: *required_attrs
      inactive_days: 180  # Plus permissif en dev
      check_password_policy: false

  monitoring:
    interval: 600  # 10 minutes - moins fréquent
    thresholds:
      connection_time_warning: 2000
      connection_time_critical: 5000

  alerts:
    slack:
      enabled: true
      webhook_url: ${SLACK_WEBHOOK_DEV}
      channel: "#dev-ldap"
      events:
        - critical_issue

    email:
      enabled: false

  management:
    dry_run_default: true  # Toujours dry-run en dev
    require_confirmation: false
    auto_backup: false

# ============================================================================
# STAGING / PRÉ-PRODUCTION
# ============================================================================
staging:
  <<: *shared_config

  ldap:
    server: ldaps://ldap-staging.company.com
    port: 636
    bind_dn: cn=ldap-monitor-staging,ou=services,dc=staging,dc=company,dc=com
    bind_password: ${LDAP_PASSWORD_STAGING}
    base_dn: dc=staging,dc=company,dc=com
    users_ou: ou=users,dc=staging,dc=company,dc=com
    groups_ou: ou=groups,dc=staging,dc=company,dc=com

    # Staging: TLS requis
    use_tls: true
    tls_verify: true
    tls_ca_cert: /etc/ssl/certs/company-ca-staging.crt
    connection_timeout: 15
    page_size: 500

  audit:
    users:
      required_attributes: *required_attrs
      inactive_days: 90
      check_password_policy: true
      check_account_expiry: true

    security:
      check_weak_passwords: true
      check_admin_accounts: true
      check_service_accounts: true

  monitoring:
    interval: 300  # 5 minutes
    thresholds:
      connection_time_warning: 1000
      connection_time_critical: 3000
      failed_binds_rate: 10

  alerts:
    slack:
      enabled: true
      webhook_url: ${SLACK_WEBHOOK_STAGING}
      channel: "#staging-alerts"
      events:
        - critical_issue
        - security_violation

    email:
      enabled: true
      smtp_host: smtp.company.com
      smtp_port: 587
      from: ldap-monitor-staging@company.com
      to:
        - qa-team@company.com

  management:
    dry_run_default: true
    require_confirmation: true
    auto_backup: true
    backup_dir: /backups/ldap-staging

# ============================================================================
# PRODUCTION
# ============================================================================
production:
  <<: *shared_config

  ldap:
    # Multiples serveurs pour HA
    servers:
      - server: ldaps://ldap-prod-1.company.com
        port: 636
        priority: 1
        datacenter: dc1

      - server: ldaps://ldap-prod-2.company.com
        port: 636
        priority: 1
        datacenter: dc2

      - server: ldaps://ldap-prod-3.company.com
        port: 636
        priority: 2  # Backup
        datacenter: dc3

    # Configuration commune
    bind_dn: cn=ldap-monitor,ou=services,dc=company,dc=com
    bind_password: ${LDAP_PASSWORD_PROD}
    base_dn: dc=company,dc=com

    # OUs multiples
    users_ou:
      - ou=employees,dc=company,dc=com
      - ou=contractors,dc=company,dc=com
      - ou=service-accounts,dc=company,dc=com
    groups_ou: ou=groups,dc=company,dc=com

    # Sécurité maximale
    use_tls: true
    tls_verify: true
    tls_ca_cert: /etc/ssl/certs/company-ca-prod.crt
    tls_client_cert: /etc/ssl/certs/ldap-monitor-client.crt
    tls_client_key: /etc/ssl/private/ldap-monitor-client.key

    # Performance
    connection_timeout: 10
    page_size: 1000
    connection_pool_size: 10
    retry_max: 3
    retry_delay: 5

  audit:
    users:
      required_attributes:
        - mail
        - givenName
        - sn
        - employeeNumber
        - department
        - manager
        - telephoneNumber

      inactive_days: 60
      check_password_policy: true
      check_account_expiry: true
      check_disabled_accounts: true
      check_locked_accounts: true

      # Règles métier strictes
      custom_checks:
        - name: valid_email_domain
          description: Email must be @company.com
          pattern: "^[a-z0-9._%+-]+@company\\.com$"
          severity: critical

        - name: employee_has_manager
          description: All employees must have a manager
          required_attribute: manager
          exceptions:
            - cn=CEO,ou=executives,dc=company,dc=com

        - name: valid_department
          description: Department must be from approved list
          attribute: department
          allowed_values:
            - Engineering
            - Sales
            - Marketing
            - Finance
            - HR
            - Operations

    groups:
      max_size: 500
      warn_empty: true
      check_nested_groups: true
      max_nesting_level: 3

      critical_groups:
        - cn=Domain Admins,cn=Users,dc=company,dc=com
        - cn=Enterprise Admins,cn=Users,dc=company,dc=com
        - cn=Schema Admins,cn=Users,dc=company,dc=com
        - cn=Finance-Access,ou=groups,dc=company,dc=com

    security:
      check_weak_passwords: true
      check_admin_accounts: true
      check_service_accounts: true
      check_password_age: true
      password_max_age_days: 90

      anomaly_detection:
        enabled: true
        baseline_days: 30
        threshold_stddev: 2.5

  monitoring:
    enabled: true
    interval: 60  # 1 minute

    metrics:
      - connection_time_by_server
      - user_count_by_ou
      - user_count_by_department
      - group_count
      - group_membership_changes
      - failed_binds
      - account_lockouts
      - password_expirations
      - disabled_accounts
      - privileged_account_usage

    thresholds:
      connection_time_warning: 500
      connection_time_critical: 2000
      failed_binds_rate: 5
      account_lockouts_rate: 3
      user_count_change_percent: 5

  alerts:
    slack:
      enabled: true
      webhook_url: ${SLACK_WEBHOOK_PROD}
      channels:
        default: "#prod-ldap-alerts"
        security: "#security-incidents"
        compliance: "#compliance-alerts"

      routing:
        - event: critical_issue
          channel: "#prod-ldap-alerts"
          mention: "@oncall"
          severity: critical

        - event: security_violation
          channel: "#security-incidents"
          mention: "@security-oncall"
          severity: critical

        - event: compliance_issue
          channel: "#compliance-alerts"
          mention: "@compliance-team"
          severity: high

    email:
      enabled: true
      smtp_host: smtp.office365.com
      smtp_port: 587
      smtp_use_tls: true
      smtp_user: ldap-monitor@company.com
      smtp_password: ${SMTP_PASSWORD}
      from: ldap-monitor@company.com

      recipients:
        - role: admin
          emails:
            - ldap-admins@company.com
            - oncall@company.com
          events:
            - critical_issue
            - service_down

        - role: security
          emails:
            - security@company.com
          events:
            - security_violation
            - unauthorized_access
            - privilege_escalation

        - role: compliance
          emails:
            - compliance@company.com
          events:
            - compliance_issue
            - audit_failure

        - role: management
          emails:
            - cio@company.com
          events:
            - weekly_summary
            - monthly_report

    pagerduty:
      enabled: true
      integration_key: ${PAGERDUTY_KEY}
      events:
        - critical_issue
        - service_down
      severity_mapping:
        critical: critical
        high: error
        medium: warning

    webhooks:
      enabled: true
      endpoints:
        - name: ServiceNow
          url: ${SERVICENOW_WEBHOOK}
          events:
            - critical_issue
            - security_violation
          headers:
            Authorization: "Bearer ${SERVICENOW_TOKEN}"
            Content-Type: "application/json"

        - name: Splunk
          url: ${SPLUNK_HEC_URL}
          events: ["*"]  # Tous les événements
          headers:
            Authorization: "Splunk ${SPLUNK_TOKEN}"

        - name: DataDog
          url: ${DATADOG_WEBHOOK}
          events:
            - critical_issue
            - performance_degradation

  integrations:
    prometheus:
      enabled: true
      port: 9090
      path: /metrics
      basic_auth:
        username: prometheus
        password: ${PROMETHEUS_PASSWORD}

    grafana:
      enabled: true
      api_url: https://grafana.company.com
      api_key: ${GRAFANA_API_KEY}
      dashboard_id: ldap-health-monitor

  reports:
    daily_summary: true
    weekly_report: true
    monthly_report: true
    quarterly_audit: true

    formats:
      - json
      - html
      - pdf
      - csv

    destinations:
      - type: local
        path: /var/reports/ldap-monitor
        retention_days: 90

      - type: s3
        bucket: company-ldap-reports
        prefix: production/ldap-monitor/
        region: us-east-1
        encryption: AES256
        retention_days: 1825  # 5 ans

      - type: sharepoint
        site: https://company.sharepoint.com/sites/IT
        folder: LDAP Reports/Production
        retention_days: 365

  compliance:
    soc2:
      enabled: true
      controls:
        - CC6.1
        - CC6.2
        - CC6.3
        - CC7.2
      quarterly_review: true
      annual_audit: true

    gdpr:
      enabled: true
      data_retention_days: 1825
      anonymize_after_days: 90
      right_to_erasure: true

    sox:
      enabled: true
      controls:
        - ITGC-01
        - ITGC-02
        - ITGC-03
      quarterly_review: true

  management:
    dry_run_default: false
    require_confirmation: true
    auto_backup: true
    backup_dir: /backups/ldap-production
    backup_retention_days: 90

    safety_limits:
      max_bulk_operations: 100
      max_delete_batch: 10
      require_manager_approval: true
```

### Script de Sélection d'Environnement

```bash
#!/bin/bash
# /opt/ldap-monitor/bin/ldap-monitor-env

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONFIG_DIR="/etc/ldap-monitor"

# Détecter l'environnement
detect_environment() {
    if [ -f "$CONFIG_DIR/environment" ]; then
        cat "$CONFIG_DIR/environment"
    elif [ -n "$LDAP_MONITOR_ENV" ]; then
        echo "$LDAP_MONITOR_ENV"
    else
        # Détecter par hostname
        HOSTNAME=$(hostname)
        case "$HOSTNAME" in
            *-dev-*|*-development-*)
                echo "development"
                ;;
            *-staging-*|*-stg-*)
                echo "staging"
                ;;
            *-prod-*|*-production-*)
                echo "production"
                ;;
            *)
                echo "development"  # Default
                ;;
        esac
    fi
}

# Charger la configuration de l'environnement
load_environment() {
    local ENV=$1
    local CONFIG_FILE="$CONFIG_DIR/config-multi-env.yaml"

    # Extraire la section de l'environnement
    yq eval ".${ENV}" "$CONFIG_FILE" > "/tmp/ldap-monitor-${ENV}-$$.yaml"

    echo "/tmp/ldap-monitor-${ENV}-$$.yaml"
}

# Charger les credentials de l'environnement
load_credentials() {
    local ENV=$1

    case "$ENV" in
        development)
            source "$CONFIG_DIR/credentials-dev.env"
            ;;
        staging)
            source "$CONFIG_DIR/credentials-staging.env"
            ;;
        production)
            source "$CONFIG_DIR/credentials-prod.env"
            ;;
    esac
}

# Main
ENV=$(detect_environment)
CONFIG=$(load_environment "$ENV")
load_credentials "$ENV"

echo "🌍 Environment: $ENV"
echo "📄 Config: $CONFIG"

# Exécuter ldap-monitor avec la config appropriée
ldap-monitor -c "$CONFIG" "$@"

# Cleanup
rm -f "$CONFIG"
```

---

## Haute Disponibilité

### Configuration HA avec Failover Automatique

```yaml
# config-high-availability.yaml
high_availability:
  enabled: true
  mode: active-active  # ou active-passive

  # Cluster de serveurs LDAP
  ldap_cluster:
    load_balancing:
      strategy: round-robin  # ou least-connections, weighted
      health_check_interval: 30
      health_check_timeout: 5
      max_failures: 3
      failure_timeout: 300  # Temps avant retry

    nodes:
      - id: ldap-dc1
        server: ldaps://ldap-dc1.company.com
        port: 636
        weight: 100
        datacenter: dc1
        region: us-east-1
        priority: 1
        max_connections: 100

      - id: ldap-dc2
        server: ldaps://ldap-dc2.company.com
        port: 636
        weight: 100
        datacenter: dc2
        region: us-west-1
        priority: 1
        max_connections: 100

      - id: ldap-dc3
        server: ldaps://ldap-dc3.company.com
        port: 636
        weight: 50
        datacenter: dc3
        region: eu-west-1
        priority: 2
        max_connections: 50

    # Connexion partagée
    bind_dn: cn=ldap-monitor,ou=services,dc=company,dc=com
    bind_password: ${LDAP_PASSWORD}
    base_dn: dc=company,dc=com

    # Pool de connexions
    connection_pool:
      min_size: 5
      max_size: 50
      idle_timeout: 300
      max_lifetime: 1800

  # Monitoring distribué
  monitoring_cluster:
    nodes:
      - id: monitor-dc1
        host: monitor-dc1.company.com
        port: 8080
        datacenter: dc1
        primary: true

      - id: monitor-dc2
        host: monitor-dc2.company.com
        port: 8080
        datacenter: dc2
        primary: false

      - id: monitor-dc3
        host: monitor-dc3.company.com
        port: 8080
        datacenter: dc3
        primary: false

    # Synchronisation d'état
    state_sync:
      enabled: true
      method: redis  # ou etcd, consul
      redis:
        host: redis-cluster.company.com
        port: 6379
        password: ${REDIS_PASSWORD}
        db: 0
        cluster_mode: true

    # Leader election
    leader_election:
      enabled: true
      method: raft  # ou etcd
      election_timeout: 10
      heartbeat_interval: 2

  # Réplication et cohérence
  replication:
    check_enabled: true
    max_lag_seconds: 300
    check_interval: 60

    # Monitoring de la réplication AD
    active_directory:
      check_replication: true
      check_fsmo_roles: true
      check_trusts: true

  # Failover automatique
  failover:
    enabled: true
    automatic: true
    health_check_interval: 30
    failure_threshold: 3
    recovery_time: 60

    notifications:
      slack:
        enabled: true
        events:
          - node_down
          - node_up
          - failover_triggered
          - primary_changed

      email:
        enabled: true
        to:
          - oncall@company.com

  # Backup distribué
  backup:
    strategy: distributed
    replication_factor: 3  # Copies dans 3 datacenters

    destinations:
      - datacenter: dc1
        path: /backups/ldap/dc1
        type: local

      - datacenter: dc2
        path: /backups/ldap/dc2
        type: nfs
        nfs_server: nfs-dc2.company.com

      - datacenter: dc3
        type: s3
        bucket: company-ldap-backups-dc3
        region: eu-west-1

monitoring:
  # Métriques HA spécifiques
  ha_metrics:
    - cluster_health
    - node_status_by_dc
    - replication_lag
    - failover_count
    - active_connections_by_node
    - request_distribution
    - response_time_by_datacenter

  # Alertes HA
  ha_alerts:
    - name: node_down
      condition: "node_health == 0"
      severity: critical
      action: trigger_failover

    - name: replication_lag_high
      condition: "replication_lag_seconds > 300"
      severity: warning

    - name: split_brain
      condition: "active_primaries > 1"
      severity: critical
      action: emergency_lockdown
```

### Script de Gestion de Cluster

```bash
#!/bin/bash
# /opt/ldap-monitor/bin/cluster-manager.sh

REDIS_HOST="redis-cluster.company.com"
REDIS_PORT=6379

# Vérifier le statut du cluster
check_cluster_status() {
    echo "🔍 Vérification du statut du cluster..."

    # Vérifier chaque noeud LDAP
    for NODE in ldap-dc1 ldap-dc2 ldap-dc3; do
        echo "Checking $NODE..."

        HEALTH=$(ldap-monitor -c /etc/ldap-monitor/config-ha.yaml \
            test connection \
            --server "${NODE}.company.com" \
            --format json | jq -r '.success')

        # Enregistrer dans Redis
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
            HSET "ldap:cluster:nodes:${NODE}" \
            "health" "$HEALTH" \
            "last_check" "$(date -Iseconds)"

        if [ "$HEALTH" = "true" ]; then
            echo "  ✅ $NODE: Healthy"
        else
            echo "  ❌ $NODE: Unhealthy"
            trigger_alert "$NODE"
        fi
    done
}

# Détecter le noeud primaire
detect_primary() {
    PRIMARY=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
        GET "ldap:cluster:primary")

    if [ -z "$PRIMARY" ]; then
        echo "⚠️  Aucun primaire détecté. Élection en cours..."
        elect_primary
    else
        echo "👑 Primaire actuel: $PRIMARY"
    fi
}

# Élire un nouveau primaire
elect_primary() {
    # Trouver le noeud le plus sain
    BEST_NODE=""
    BEST_SCORE=0

    for NODE in ldap-dc1 ldap-dc2 ldap-dc3; do
        HEALTH=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
            HGET "ldap:cluster:nodes:${NODE}" health)

        if [ "$HEALTH" = "true" ]; then
            # Calculer le score basé sur latence et charge
            SCORE=100  # Logic simplified
            if [ "$SCORE" -gt "$BEST_SCORE" ]; then
                BEST_SCORE=$SCORE
                BEST_NODE=$NODE
            fi
        fi
    done

    if [ -n "$BEST_NODE" ]; then
        echo "🎯 Élection de $BEST_NODE comme primaire"
        redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
            SET "ldap:cluster:primary" "$BEST_NODE"

        # Notifier
        notify_slack "Nouveau primaire LDAP: $BEST_NODE"
    else
        echo "❌ Aucun noeud sain disponible!"
        notify_slack "🚨 LDAP Cluster: Aucun noeud sain disponible!"
    fi
}

# Déclencher un failover
trigger_failover() {
    local FAILED_NODE=$1

    echo "🔄 Déclenchement du failover pour $FAILED_NODE..."

    # Marquer le noeud comme down
    redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
        HSET "ldap:cluster:nodes:${FAILED_NODE}" \
        "status" "down" \
        "failed_at" "$(date -Iseconds)"

    # Si c'était le primaire, réélire
    CURRENT_PRIMARY=$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" \
        GET "ldap:cluster:primary")

    if [ "$CURRENT_PRIMARY" = "$FAILED_NODE" ]; then
        echo "⚠️  Le primaire est down. Réélection nécessaire."
        elect_primary
    fi

    # Rediriger le trafic
    redistribute_traffic

    # Notification
    notify_slack "🔄 Failover déclenché: $FAILED_NODE est down"
}

# Redistribuer le trafic
redistribute_traffic() {
    echo "🔀 Redistribution du trafic..."

    # Mettre à jour HAProxy ou load balancer
    # (exemple simplifié)
}

# Envoyer une alerte
notify_slack() {
    local MESSAGE=$1

    if [ -n "$SLACK_WEBHOOK" ]; then
        curl -X POST "$SLACK_WEBHOOK" \
            -H 'Content-Type: application/json' \
            -d "{\"text\": \"$MESSAGE\"}"
    fi
}

# Main loop
main() {
    while true; do
        check_cluster_status
        detect_primary

        sleep 30
    done
}

# Si exécuté directement
if [ "${BASH_SOURCE[0]}" -eq "${0}" ]; then
    source /etc/ldap-monitor/credentials.env
    main
fi
```

---

## Active Directory Multi-Domaines

### Configuration Forêt AD Complexe

```yaml
# config-ad-forest.yaml
active_directory:
  forest:
    name: COMPANY.COM
    functional_level: Windows2016

    # Domaines de la forêt
    domains:
      - name: COMPANY.COM
        netbios: COMPANY
        type: root
        dns_servers:
          - 10.0.1.10
          - 10.0.1.11

        domain_controllers:
          - hostname: DC1-HQ
            fqdn: dc1-hq.company.com
            ip: 10.0.1.10
            site: HQ-Site
            roles:
              - PDC
              - RID Master
              - Infrastructure Master

          - hostname: DC2-HQ
            fqdn: dc2-hq.company.com
            ip: 10.0.1.11
            site: HQ-Site
            roles: []

        ldap_config:
          server: ldaps://company.com
          port: 636
          bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=company,DC=com
          bind_password: ${LDAP_PASSWORD_ROOT}
          base_dn: DC=company,DC=com

      - name: EMEA.COMPANY.COM
        netbios: EMEA
        type: child
        parent: COMPANY.COM
        dns_servers:
          - 10.1.1.10
          - 10.1.1.11

        domain_controllers:
          - hostname: DC1-EMEA
            fqdn: dc1-emea.emea.company.com
            ip: 10.1.1.10
            site: London-Site
            roles: []

          - hostname: DC2-EMEA
            fqdn: dc2-emea.emea.company.com
            ip: 10.1.1.11
            site: Paris-Site
            roles: []

        ldap_config:
          server: ldaps://emea.company.com
          port: 636
          bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=emea,DC=company,DC=com
          bind_password: ${LDAP_PASSWORD_EMEA}
          base_dn: DC=emea,DC=company,DC=com

      - name: APAC.COMPANY.COM
        netbios: APAC
        type: child
        parent: COMPANY.COM
        dns_servers:
          - 10.2.1.10
          - 10.2.1.11

        domain_controllers:
          - hostname: DC1-APAC
            fqdn: dc1-apac.apac.company.com
            ip: 10.2.1.10
            site: Singapore-Site
            roles: []

        ldap_config:
          server: ldaps://apac.company.com
          port: 636
          bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=apac,DC=company,DC=com
          bind_password: ${LDAP_PASSWORD_APAC}
          base_dn: DC=apac,DC=company,DC=com

    # Sites et réplication
    sites:
      - name: HQ-Site
        location: "New York, USA"
        subnets:
          - 10.0.0.0/16
        domain_controllers:
          - DC1-HQ
          - DC2-HQ

      - name: London-Site
        location: "London, UK"
        subnets:
          - 10.1.0.0/16
        domain_controllers:
          - DC1-EMEA

      - name: Paris-Site
        location: "Paris, France"
        subnets:
          - 10.1.100.0/24
        domain_controllers:
          - DC2-EMEA

      - name: Singapore-Site
        location: "Singapore"
        subnets:
          - 10.2.0.0/16
        domain_controllers:
          - DC1-APAC

    # Liens de réplication
    site_links:
      - name: HQ-London
        sites:
          - HQ-Site
          - London-Site
        cost: 100
        replication_interval: 180  # minutes

      - name: HQ-Singapore
        sites:
          - HQ-Site
          - Singapore-Site
        cost: 200
        replication_interval: 360

      - name: London-Paris
        sites:
          - London-Site
          - Paris-Site
        cost: 50
        replication_interval: 60

    # Trusts inter-domaines
    trusts:
      - source: COMPANY.COM
        target: EMEA.COMPANY.COM
        type: parent-child
        direction: bidirectional
        transitive: true

      - source: COMPANY.COM
        target: APAC.COMPANY.COM
        type: parent-child
        direction: bidirectional
        transitive: true

      # Trust externe (exemple avec partenaire)
      - source: COMPANY.COM
        target: PARTNER.COM
        type: external
        direction: bidirectional
        transitive: false

  # Monitoring spécifique AD
  monitoring:
    check_replication: true
    replication_max_lag: 900  # 15 minutes

    check_fsmo_roles: true
    check_gc_servers: true
    check_dns_integration: true

    check_trusts: true
    trust_verification_interval: 3600

    metrics:
      - replication_lag_by_site
      - dc_health_by_site
      - fsmo_role_holders
      - global_catalog_status
      - trust_status

  # Audit spécifique AD
  audit:
    check_admin_count: true
    check_sid_history: true
    check_group_policy: true
    check_service_principals: true

    # Groupes protégés AD
    protected_groups:
      - Domain Admins
      - Enterprise Admins
      - Schema Admins
      - Administrators
      - Account Operators
      - Server Operators
      - Backup Operators
      - Print Operators

    # Comptes de service critiques
    critical_service_accounts:
      - krbtgt
      - MSOL_*
      - AAD_*
```

---

## Configuration Hybride Cloud

### Azure AD + On-Premises AD

```yaml
# config-hybrid-cloud.yaml
hybrid_configuration:
  # Active Directory On-Premises
  on_premises:
    ldap:
      server: ldaps://ad.company.local
      port: 636
      bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=company,DC=local
      bind_password: ${LDAP_PASSWORD_ONPREM}
      base_dn: DC=company,DC=local

  # Azure Active Directory
  azure_ad:
    enabled: true
    tenant_id: ${AZURE_TENANT_ID}
    client_id: ${AZURE_CLIENT_ID}
    client_secret: ${AZURE_CLIENT_SECRET}

    # Graph API configuration
    graph_api:
      endpoint: https://graph.microsoft.com/v1.0
      scopes:
        - User.Read.All
        - Group.Read.All
        - Directory.Read.All

  # Azure AD Connect (Sync)
  aad_connect:
    enabled: true
    server: aadconnect.company.local
    sync_interval: 30  # minutes

    monitoring:
      check_sync_status: true
      check_sync_errors: true
      max_sync_lag_minutes: 60

    # Objets synchronisés
    sync_scope:
      users:
        source_ou: OU=Employees,DC=company,DC=local
        filter: "(!(userAccountControl:1.2.840.113556.1.4.803:=2))"  # Enabled only

      groups:
        source_ou: OU=Groups,DC=company,DC=local
        types:
          - security
          - distribution

  # Comparaison On-Prem vs Cloud
  synchronization_audit:
    enabled: true
    interval: 3600  # 1 hour

    checks:
      - user_count_match
      - group_count_match
      - attribute_consistency
      - orphaned_cloud_objects
      - orphaned_onprem_objects

    # Attributs à vérifier
    sync_attributes:
      - userPrincipalName
      - mail
      - displayName
      - givenName
      - sn
      - department
      - title

  # Multi-cloud
  multi_cloud:
    - provider: aws
      directory_service:
        type: microsoft_ad
        directory_id: d-1234567890
        region: us-east-1
        dns_addresses:
          - 10.100.1.10
          - 10.100.1.11

      credentials:
        access_key: ${AWS_ACCESS_KEY}
        secret_key: ${AWS_SECRET_KEY}

    - provider: gcp
      managed_ad:
        project: company-project
        region: us-central1
        domain: company.gcp.local

      credentials:
        service_account: ${GCP_SERVICE_ACCOUNT}

monitoring:
  hybrid_metrics:
    - onprem_user_count
    - azure_ad_user_count
    - sync_status
    - sync_lag_minutes
    - sync_errors_count
    - cloud_only_users
    - synced_users
    - licensing_status
```

---

## Schémas LDAP Personnalisés

### Extension de Schéma Personnalisé

```yaml
# config-custom-schema.yaml
ldap:
  server: ldap://ldap.company.com
  schema: custom  # ou openldap, active_directory

  # Définition de schéma personnalisé
  custom_schema:
    # Classes d'objets personnalisées
    object_classes:
      - name: companyEmployee
        oid: 1.3.6.1.4.1.99999.1.1.1
        description: "Extended employee object class"
        sup: inetOrgPerson
        structural: true
        must:
          - uid
          - mail
          - employeeNumber
        may:
          - costCenter
          - businessUnit
          - hireDate
          - terminationDate

      - name: companyContractor
        oid: 1.3.6.1.4.1.99999.1.1.2
        description: "Contractor object class"
        sup: inetOrgPerson
        structural: true
        must:
          - uid
          - mail
          - contractId
        may:
          - contractStart
          - contractEnd
          - vendorName

    # Attributs personnalisés
    attributes:
      - name: employeeNumber
        oid: 1.3.6.1.4.1.99999.2.1.1
        description: "Unique employee identifier"
        syntax: 1.3.6.1.4.1.1466.115.121.1.15  # Directory String
        single_value: true
        equality: caseIgnoreMatch

      - name: costCenter
        oid: 1.3.6.1.4.1.99999.2.1.2
        description: "Employee cost center"
        syntax: 1.3.6.1.4.1.1466.115.121.1.15
        single_value: true

      - name: businessUnit
        oid: 1.3.6.1.4.1.99999.2.1.3
        description: "Business unit"
        syntax: 1.3.6.1.4.1.1466.115.121.1.15
        single_value: true

      - name: hireDate
        oid: 1.3.6.1.4.1.99999.2.1.4
        description: "Employee hire date"
        syntax: 1.3.6.1.4.1.1466.115.121.1.24  # Generalized Time
        single_value: true

      - name: terminationDate
        oid: 1.3.6.1.4.1.99999.2.1.5
        description: "Employee termination date"
        syntax: 1.3.6.1.4.1.1466.115.121.1.24
        single_value: true

      - name: contractId
        oid: 1.3.6.1.4.1.99999.2.1.10
        description: "Contractor contract ID"
        syntax: 1.3.6.1.4.1.1466.115.121.1.15
        single_value: true

      - name: contractStart
        oid: 1.3.6.1.4.1.99999.2.1.11
        description: "Contract start date"
        syntax: 1.3.6.1.4.1.1466.115.121.1.24
        single_value: true

      - name: contractEnd
        oid: 1.3.6.1.4.1.99999.2.1.12
        description: "Contract end date"
        syntax: 1.3.6.1.4.1.1466.115.121.1.24
        single_value: true

  # Mapping des attributs
  attribute_mapping:
    # Standard → Custom
    standard_to_custom:
      uid: employeeNumber
      department: businessUnit

    # Custom → Standard
    custom_to_standard:
      employeeNumber: uid
      businessUnit: department

# Audit avec schéma personnalisé
audit:
  users:
    # Attributs requis du schéma custom
    required_attributes:
      - employeeNumber
      - costCenter
      - businessUnit
      - hireDate
      - mail

    # Validation personnalisée
    custom_validations:
      - attribute: employeeNumber
        pattern: "^EMP[0-9]{6}$"
        error_message: "Employee number must be EMP followed by 6 digits"

      - attribute: costCenter
        pattern: "^CC[0-9]{4}$"
        error_message: "Cost center must be CC followed by 4 digits"

      - attribute: businessUnit
        allowed_values:
          - Engineering
          - Sales
          - Marketing
          - Finance
          - HR
          - Operations
        error_message: "Invalid business unit"

      - attribute: hireDate
        format: "YYYYMMDD"
        error_message: "Hire date must be in YYYYMMDD format"

  contractors:
    object_class: companyContractor
    required_attributes:
      - contractId
      - contractStart
      - contractEnd
      - vendorName

    custom_validations:
      - attribute: contractId
        pattern: "^CTR[0-9]{8}$"

      - name: contract_dates_valid
        check: contractEnd > contractStart
        error_message: "Contract end date must be after start date"
```

---

## Sécurité Avancée

### Configuration Sécurité Renforcée

```yaml
# config-security-hardened.yaml
security:
  # Authentification
  authentication:
    # Certificats clients
    client_certificates:
      enabled: true
      ca_cert: /etc/ssl/certs/company-ca.crt
      client_cert: /etc/ssl/certs/ldap-monitor.crt
      client_key: /etc/ssl/private/ldap-monitor.key
      verify_peer: true
      verify_hostname: true

    # Rotation des credentials
    credential_rotation:
      enabled: true
      interval_days: 90
      warning_days: 14
      vault_integration: true

  # Chiffrement
  encryption:
    # TLS/SSL
    tls:
      enabled: true
      min_version: "1.2"
      cipher_suites:
        - TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384
        - TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256
        - TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256
      prefer_server_ciphers: true

    # Chiffrement des données au repos
    at_rest:
      enabled: true
      algorithm: AES-256-GCM
      key_management: vault  # ou kms, local

  # Gestion des secrets
  secrets_management:
    provider: hashicorp_vault  # ou aws_secrets, azure_keyvault

    vault:
      address: https://vault.company.com
      token: ${VAULT_TOKEN}
      namespace: ldap-monitor
      mount_point: secret

      # Paths des secrets
      secrets:
        ldap_password: secret/data/ldap/monitor/password
        slack_webhook: secret/data/integrations/slack/webhook
        smtp_password: secret/data/integrations/smtp/password

      # Auto-renewal
      auto_renew: true
      renew_before_expiry: 3600  # 1 hour

  # Audit de sécurité
  audit_logging:
    enabled: true
    log_level: detailed  # minimal, standard, detailed

    # Événements à logger
    events:
      - authentication_success
      - authentication_failure
      - authorization_denied
      - configuration_change
      - user_access
      - group_modification
      - privileged_operation
      - security_violation

    # Destinations des logs
    destinations:
      - type: file
        path: /var/log/ldap-monitor/security-audit.log
        rotation:
          max_size: 100MB
          max_files: 10
          compress: true

      - type: syslog
        server: syslog.company.com
        port: 514
        protocol: tcp
        facility: local0

      - type: splunk
        hec_url: ${SPLUNK_HEC_URL}
        hec_token: ${SPLUNK_HEC_TOKEN}
        index: security_audits

  # Contrôle d'accès
  access_control:
    # RBAC
    rbac:
      enabled: true

      roles:
        - name: admin
          permissions:
            - "*"

        - name: auditor
          permissions:
            - audit:read
            - report:read
            - user:read
            - group:read

        - name: operator
          permissions:
            - audit:*
            - monitor:*
            - user:read
            - group:read
            - backup:create

      # Assignation des rôles
      role_assignments:
        - user: "cn=admin,ou=admins,dc=company,dc=com"
          role: admin

        - user: "cn=auditor,ou=auditors,dc=company,dc=com"
          role: auditor

        - group: "cn=ldap-operators,ou=groups,dc=company,dc=com"
          role: operator

    # IP allowlist
    ip_allowlist:
      enabled: true
      addresses:
        - 10.0.0.0/8
        - 172.16.0.0/12
        - 192.168.0.0/16

  # Détection d'anomalies
  anomaly_detection:
    enabled: true

    # Machine Learning baseline
    baseline:
      enabled: true
      learning_period_days: 30
      update_interval_hours: 24

    # Règles de détection
    rules:
      - name: unusual_authentication_time
        description: "Login outside normal hours"
        threshold: 3_stddev
        action: alert

      - name: unusual_authentication_location
        description: "Login from unusual IP"
        threshold: 2_stddev
        action: alert_and_block

      - name: rapid_failed_logins
        description: "Multiple failed logins"
        threshold: 5_in_5min
        action: block

      - name: privilege_escalation
        description: "User added to privileged group"
        threshold: immediate
        action: alert_and_audit

  # Conformité
  compliance:
    # SOC2
    soc2:
      enabled: true
      controls:
        CC6.1:
          description: "Logical and Physical Access Controls"
          checks:
            - authentication_enforced
            - mfa_required
            - session_timeout

        CC6.6:
          description: "Logical and Physical Access Controls - Removal"
          checks:
            - termination_process
            - access_review

    # GDPR
    gdpr:
      enabled: true
      controls:
        - data_encryption
        - access_logging
        - right_to_erasure
        - data_portability

    # HIPAA
    hipaa:
      enabled: true
      controls:
        - access_control
        - audit_controls
        - integrity_controls
        - transmission_security
```

---

## Performance et Optimisation

### Configuration Optimisée pour Grande Échelle

```yaml
# config-performance-optimized.yaml
performance:
  # Connection pooling
  connection_pool:
    enabled: true
    min_connections: 10
    max_connections: 100
    connection_timeout: 10
    idle_timeout: 300
    max_lifetime: 3600

    # Pool par serveur
    per_server_pools: true

  # Caching
  caching:
    enabled: true

    # Cache de métadonnées
    metadata:
      enabled: true
      ttl: 3600  # 1 hour
      max_size: 10000

    # Cache de requêtes
    queries:
      enabled: true
      ttl: 300  # 5 minutes
      max_size: 5000

    # Backend de cache
    backend: redis
    redis:
      host: redis.company.com
      port: 6379
      db: 1
      password: ${REDIS_PASSWORD}

  # Pagination
  pagination:
    enabled: true
    page_size: 1000
    max_page_size: 5000

  # Batch operations
  batch:
    enabled: true
    size: 100
    delay_ms: 100  # Délai entre batches

  # Compression
  compression:
    enabled: true
    algorithm: gzip
    level: 6

  # Parallélisation
  parallelization:
    enabled: true
    max_workers: 10
    max_concurrent_queries: 50

  # Optimisation des requêtes
  query_optimization:
    # Indexation
    indexes:
      - uid
      - mail
      - memberOf
      - employeeNumber

    # Limites
    limits:
      max_search_results: 10000
      search_timeout: 30

    # Filtres optimisés
    optimized_filters:
      active_users: "(!(userAccountControl:1.2.840.113556.1.4.803:=2))"
      enabled_accounts: "(&(objectClass=user)(!(userAccountControl:1.2.840.113556.1.4.803:=2)))"

monitoring:
  performance_metrics:
    - query_response_time
    - connection_pool_usage
    - cache_hit_ratio
    - batch_processing_time
    - concurrent_operations
    - memory_usage
    - cpu_usage

  # Profiling
  profiling:
    enabled: true
    slow_query_threshold: 1000  # ms
    log_slow_queries: true

  # Resource limits
  resource_limits:
    max_memory_mb: 2048
    max_cpu_percent: 80
```

Ce guide couvre les configurations avancées les plus courantes. Pour des exemples d'intégrations personnalisées, consultez [Custom-Integrations.md](./Custom-Integrations.md).
