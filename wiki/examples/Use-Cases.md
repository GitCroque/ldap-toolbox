# Cas d'Usage Complets - LDAP Health Monitor

Ce guide présente des scénarios d'utilisation réels de LDAP Health Monitor pour différents types d'organisations, de la startup à l'entreprise internationale.

## 📋 Table des Matières

- [Startup Tech (50-200 utilisateurs)](#startup-tech)
- [PME (200-1000 utilisateurs)](#pme-moyenne-entreprise)
- [Grande Entreprise (1000-10000+ utilisateurs)](#grande-entreprise)
- [Conformité et Audit](#conformité-et-audit)
- [Migration et Consolidation](#migration-et-consolidation)
- [Gestion Multi-Sites](#gestion-multi-sites)

---

## Startup Tech (50-200 utilisateurs)

### Contexte
Une startup en croissance rapide utilise OpenLDAP pour gérer l'authentification de ses employés. L'équipe IT est réduite (1-2 personnes) et a besoin d'automatisation.

### Objectifs
- Détecter rapidement les problèmes d'accès
- Automatiser le monitoring quotidien
- Minimiser le temps d'administration
- Maintenir la sécurité sans expertise LDAP approfondie

### Configuration Initiale

```yaml
# config-startup.yaml
ldap:
  server: ldap://ldap.startup.tech
  port: 389
  bind_dn: cn=admin,dc=startup,dc=tech
  bind_password: ${LDAP_PASSWORD}
  base_dn: dc=startup,dc=tech
  users_ou: ou=users,dc=startup,dc=tech
  groups_ou: ou=groups,dc=startup,dc=tech
  use_tls: true
  tls_verify: true

audit:
  users:
    required_attributes:
      - mail
      - givenName
      - sn
      - employeeNumber
    inactive_days: 90
    check_password_policy: true

  groups:
    max_size: 100
    warn_empty: true

  security:
    check_weak_passwords: false  # Géré par politique LDAP
    check_admin_accounts: true
    check_service_accounts: true

monitoring:
  enabled: true
  interval: 300  # 5 minutes
  metrics:
    - connection_time
    - user_count
    - group_count
    - failed_binds

  thresholds:
    connection_time_warning: 1000  # ms
    connection_time_critical: 3000
    user_count_change: 10  # Alerte si +/- 10 users en 5 min

alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channel: "#tech-alerts"
    mention_on_critical: "@channel"
    events:
      - critical_issue
      - service_down

  email:
    enabled: true
    smtp_host: smtp.gmail.com
    smtp_port: 587
    from: ldap-monitor@startup.tech
    to:
      - admin@startup.tech
      - cto@startup.tech
    events:
      - critical_issue
      - daily_summary

reports:
  daily_summary: true
  weekly_report: true
  formats:
    - json
    - html
  retention_days: 90
```

### Workflows Quotidiens

#### 1. Check Matinal Automatisé

```bash
#!/bin/bash
# /opt/scripts/ldap-morning-check.sh

export LDAP_PASSWORD="$(cat /etc/ldap-monitor/password)"
export SLACK_WEBHOOK="$(cat /etc/ldap-monitor/slack-webhook)"

# Audit de santé rapide
ldap-monitor -c /etc/ldap-monitor/config.yaml audit health \
  --format json \
  --output /var/log/ldap-monitor/health-$(date +%Y%m%d).json

# Vérifier les nouveaux utilisateurs de la veille
ldap-monitor -c /etc/ldap-monitor/config.yaml user list \
  | grep "created: $(date -d yesterday +%Y-%m-%d)" \
  > /tmp/new-users.txt

if [ -s /tmp/new-users.txt ]; then
  echo "Nouveaux utilisateurs détectés :" >> /tmp/morning-report.txt
  cat /tmp/new-users.txt >> /tmp/morning-report.txt
fi

# Audit de sécurité hebdomadaire (lundi uniquement)
if [ $(date +%u) -eq 1 ]; then
  ldap-monitor -c /etc/ldap-monitor/config.yaml audit all \
    --format html \
    --output /var/www/reports/weekly-audit-$(date +%Y-W%V).html
fi

# Envoyer le rapport par Slack
if [ -f /tmp/morning-report.txt ]; then
  curl -X POST ${SLACK_WEBHOOK} \
    -H 'Content-Type: application/json' \
    -d "{\"text\": \"📊 LDAP Morning Report\n$(cat /tmp/morning-report.txt)\"}"
fi
```

#### 2. Onboarding Automatique

```bash
#!/bin/bash
# /opt/scripts/ldap-onboard-user.sh

NEW_USER_EMAIL=$1
NEW_USER_NAME=$2
NEW_USER_DEPT=$3

# Vérifier que l'utilisateur n'existe pas déjà
EXISTING=$(ldap-monitor user search "${NEW_USER_EMAIL}" 2>/dev/null)

if [ -n "$EXISTING" ]; then
  echo "❌ L'utilisateur existe déjà : ${NEW_USER_EMAIL}"
  exit 1
fi

# Créer l'utilisateur (via script LDAP séparé)
/opt/scripts/create-ldap-user.sh "${NEW_USER_EMAIL}" "${NEW_USER_NAME}" "${NEW_USER_DEPT}"

# Attendre la propagation
sleep 2

# Vérifier la création
ldap-monitor user show "uid=${NEW_USER_EMAIL},ou=users,dc=startup,dc=tech"

# Ajouter aux groupes par défaut
case $NEW_USER_DEPT in
  "engineering")
    GROUPS=("developers" "all-staff" "vpn-users")
    ;;
  "sales")
    GROUPS=("sales-team" "all-staff" "crm-users")
    ;;
  *)
    GROUPS=("all-staff")
    ;;
esac

for GROUP in "${GROUPS[@]}"; do
  echo "Ajout à ${GROUP}..."
  # Commande d'ajout au groupe
done

# Audit final
ldap-monitor audit users --format json | jq ".[] | select(.email == \"${NEW_USER_EMAIL}\")"

echo "✅ Onboarding terminé pour ${NEW_USER_EMAIL}"
```

#### 3. Monitoring en Temps Réel

```bash
#!/bin/bash
# Lancer le daemon de monitoring

ldap-monitor -c /etc/ldap-monitor/config.yaml monitor start --daemon

# Exposer les métriques Prometheus
ldap-monitor -c /etc/ldap-monitor/config.yaml monitor prometheus --port 9091 &

# Vérifier le statut
sleep 5
curl http://localhost:9091/metrics | grep ldap_
```

### Tableau de Bord Grafana

```json
{
  "dashboard": {
    "title": "LDAP Health - Startup Dashboard",
    "panels": [
      {
        "title": "Utilisateurs Actifs",
        "targets": [
          {
            "expr": "ldap_user_count{status=\"active\"}"
          }
        ]
      },
      {
        "title": "Temps de Connexion",
        "targets": [
          {
            "expr": "ldap_connection_time_ms"
          }
        ]
      },
      {
        "title": "Échecs d'Authentification",
        "targets": [
          {
            "expr": "rate(ldap_failed_binds_total[5m])"
          }
        ]
      },
      {
        "title": "Croissance Utilisateurs",
        "targets": [
          {
            "expr": "ldap_user_count - ldap_user_count offset 1w"
          }
        ]
      }
    ]
  }
}
```

---

## PME - Moyenne Entreprise (200-1000 utilisateurs)

### Contexte
Une PME avec plusieurs départements utilise Active Directory pour gérer les accès. Nécessite une conformité SOC2 et des audits réguliers.

### Objectifs
- Conformité réglementaire continue
- Gestion multi-départements
- Audits de sécurité réguliers
- Reporting pour le management
- Intégration avec systèmes RH

### Configuration Avancée

```yaml
# config-pme.yaml
ldap:
  server: ldaps://ad.entreprise.local
  port: 636
  bind_dn: CN=ldap-monitor,OU=Service Accounts,DC=entreprise,DC=local
  bind_password: ${LDAP_PASSWORD}
  base_dn: DC=entreprise,DC=local

  # Configuration Active Directory
  schema: active_directory
  page_size: 1000

  # OUs multiples
  users_ou:
    - OU=Employees,DC=entreprise,DC=local
    - OU=Contractors,DC=entreprise,DC=local
  groups_ou: OU=Groups,DC=entreprise,DC=local

  use_tls: true
  tls_verify: true
  tls_ca_cert: /etc/ldap-monitor/certs/ca.crt

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

    # Règles métier
    custom_checks:
      - name: "email_matches_domain"
        description: "Email doit être @entreprise.com"
        pattern: "^[a-z.]+@entreprise\\.com$"

      - name: "employee_has_manager"
        description: "Tous les employés doivent avoir un manager"
        required_attribute: "manager"
        exceptions:
          - "CN=CEO,OU=Executives,DC=entreprise,DC=local"

  groups:
    max_size: 500
    warn_empty: true
    check_nested_groups: true
    max_nesting_level: 3

    # Groupes critiques à surveiller
    critical_groups:
      - CN=Domain Admins,CN=Users,DC=entreprise,DC=local
      - CN=Enterprise Admins,CN=Users,DC=entreprise,DC=local
      - CN=Finance-Access,OU=Groups,DC=entreprise,DC=local

  security:
    check_weak_passwords: true
    check_admin_accounts: true
    check_service_accounts: true
    check_password_age: true
    password_max_age_days: 90

    # Détection d'anomalies
    anomaly_detection:
      enabled: true
      baseline_days: 30
      threshold_stddev: 2.5

monitoring:
  enabled: true
  interval: 120  # 2 minutes

  metrics:
    - connection_time
    - user_count_by_ou
    - user_count_by_department
    - group_count
    - group_membership_changes
    - failed_binds
    - account_lockouts
    - password_expirations
    - disabled_accounts

  thresholds:
    connection_time_warning: 500
    connection_time_critical: 2000
    failed_binds_rate: 10  # par minute
    account_lockouts_rate: 5

alerts:
  slack:
    enabled: true
    webhook_url: ${SLACK_WEBHOOK}
    channels:
      default: "#ops-ldap"
      security: "#security-alerts"
      compliance: "#compliance"

    routing:
      - event: "critical_issue"
        channel: "#ops-ldap"
        mention: "@oncall"

      - event: "security_violation"
        channel: "#security-alerts"
        mention: "@security-team"

      - event: "compliance_issue"
        channel: "#compliance"
        mention: "@compliance-officer"

  email:
    enabled: true
    smtp_host: smtp.office365.com
    smtp_port: 587
    smtp_user: ldap-monitor@entreprise.com
    smtp_password: ${SMTP_PASSWORD}
    from: ldap-monitor@entreprise.com

    recipients:
      - role: "admin"
        emails: ["it-team@entreprise.com"]
        events: ["critical_issue", "service_down"]

      - role: "security"
        emails: ["security@entreprise.com"]
        events: ["security_violation", "unauthorized_access"]

      - role: "management"
        emails: ["cio@entreprise.com"]
        events: ["weekly_summary", "monthly_report"]

      - role: "compliance"
        emails: ["compliance@entreprise.com"]
        events: ["compliance_issue", "audit_report"]

  webhooks:
    enabled: true
    endpoints:
      - name: "ServiceNow"
        url: ${SERVICENOW_WEBHOOK}
        events: ["critical_issue"]
        method: POST
        headers:
          Authorization: "Bearer ${SERVICENOW_TOKEN}"

      - name: "Splunk"
        url: ${SPLUNK_HEC_URL}
        events: ["all"]
        method: POST
        headers:
          Authorization: "Splunk ${SPLUNK_HEC_TOKEN}"

integrations:
  prometheus:
    enabled: true
    port: 9090
    path: /metrics

  n8n:
    enabled: true
    webhook_url: ${N8N_WEBHOOK}
    events:
      - user_created
      - user_deleted
      - group_modified
      - security_violation

reports:
  daily_summary: true
  weekly_report: true
  monthly_report: true
  quarterly_audit: true

  formats:
    - json
    - html
    - csv

  destinations:
    - type: local
      path: /var/reports/ldap-monitor

    - type: s3
      bucket: entreprise-ldap-reports
      prefix: ldap-monitor/
      region: eu-west-1

    - type: sharepoint
      site: https://entreprise.sharepoint.com/sites/IT
      folder: "LDAP Reports"

  retention:
    daily: 90
    weekly: 365
    monthly: 1825  # 5 ans pour conformité

compliance:
  soc2:
    enabled: true
    controls:
      - CC6.1  # Logical Access Controls
      - CC6.2  # Authentication
      - CC6.3  # Authorization
      - CC7.2  # System Monitoring

  gdpr:
    enabled: true
    data_retention_days: 1825  # 5 ans
    anonymize_after_days: 90  # Pour anciens employés

  iso27001:
    enabled: true
    controls:
      - A.9.2.1  # User registration
      - A.9.2.2  # User access provisioning
      - A.9.2.5  # Review of user access rights
      - A.9.2.6  # Removal of access rights
```

### Processus de Conformité

#### Audit SOC2 Mensuel

```bash
#!/bin/bash
# /opt/scripts/soc2-monthly-audit.sh

REPORT_DATE=$(date +%Y-%m)
REPORT_DIR="/var/reports/compliance/soc2/${REPORT_DATE}"

mkdir -p "${REPORT_DIR}"

echo "🔍 Démarrage de l'audit SOC2 - ${REPORT_DATE}"

# CC6.1 - Contrôles d'accès logique
echo "Audit CC6.1 - Contrôles d'accès..."
ldap-monitor audit security \
  --format json \
  --output "${REPORT_DIR}/cc6.1-access-controls.json"

# CC6.2 - Authentification
echo "Audit CC6.2 - Authentification..."
ldap-monitor audit users \
  --check-password-policy \
  --check-mfa \
  --format json \
  --output "${REPORT_DIR}/cc6.2-authentication.json"

# CC6.3 - Autorisation
echo "Audit CC6.3 - Autorisation..."
ldap-monitor audit groups \
  --check-permissions \
  --check-critical-groups \
  --format json \
  --output "${REPORT_DIR}/cc6.3-authorization.json"

# CC7.2 - Monitoring
echo "Audit CC7.2 - Monitoring..."
ldap-monitor monitor metrics \
  --format json \
  --output "${REPORT_DIR}/cc7.2-monitoring-metrics.json"

# Générer le rapport consolidé
python3 /opt/scripts/generate-soc2-report.py \
  --input-dir "${REPORT_DIR}" \
  --output "${REPORT_DIR}/soc2-audit-report-${REPORT_DATE}.html"

# Envoyer au compliance officer
echo "📧 Envoi du rapport..."
mail -s "SOC2 Monthly Audit - ${REPORT_DATE}" \
  -a "${REPORT_DIR}/soc2-audit-report-${REPORT_DATE}.html" \
  compliance@entreprise.com < /dev/null

# Archiver dans S3
aws s3 cp "${REPORT_DIR}" \
  "s3://entreprise-compliance/soc2/${REPORT_DATE}/" \
  --recursive

echo "✅ Audit SOC2 terminé"
```

---

## Grande Entreprise (10000+ utilisateurs)

### Contexte
Entreprise internationale avec plusieurs domaines AD, sites géographiques multiples, et exigences de conformité strictes (SOX, GDPR, HIPAA).

### Configuration Multi-Domaines

```yaml
# config-enterprise.yaml
ldap:
  # Configuration multi-domaines
  domains:
    - name: "EMEA"
      server: ldaps://ad-emea.global.corp
      port: 636
      bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=emea,DC=global,DC=corp
      bind_password: ${LDAP_PASSWORD_EMEA}
      base_dn: DC=emea,DC=global,DC=corp
      region: "Europe"
      compliance: ["GDPR", "ISO27001"]

    - name: "AMER"
      server: ldaps://ad-amer.global.corp
      port: 636
      bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=amer,DC=global,DC=corp
      bind_password: ${LDAP_PASSWORD_AMER}
      base_dn: DC=amer,DC=global,DC=corp
      region: "Americas"
      compliance: ["SOX", "SOC2", "HIPAA"]

    - name: "APAC"
      server: ldaps://ad-apac.global.corp
      port: 636
      bind_dn: CN=ldap-monitor,OU=ServiceAccounts,DC=apac,DC=global,DC=corp
      bind_password: ${LDAP_PASSWORD_APAC}
      base_dn: DC=apac,DC=global,DC=corp
      region: "Asia Pacific"
      compliance: ["SOC2", "ISO27001"]

  # Paramètres globaux
  schema: active_directory
  page_size: 5000
  connection_pool_size: 10
  timeout: 30
  use_tls: true
  tls_verify: true

monitoring:
  enabled: true
  interval: 60  # 1 minute
  distributed: true

  # Métriques enterprise
  metrics:
    - connection_time_by_domain
    - user_count_by_domain
    - user_count_by_region
    - user_count_by_business_unit
    - privileged_account_usage
    - cross_domain_access
    - replication_status
    - dc_health_by_site

  # Collecteurs distribués
  collectors:
    - region: "EMEA"
      host: ldap-monitor-eu-1.global.corp
      domains: ["EMEA"]

    - region: "AMER"
      host: ldap-monitor-us-1.global.corp
      domains: ["AMER"]

    - region: "APAC"
      host: ldap-monitor-ap-1.global.corp
      domains: ["APAC"]

  # Agrégation centralisée
  aggregator:
    enabled: true
    host: ldap-monitor-central.global.corp
    port: 8080

compliance:
  sox:
    enabled: true
    controls:
      - IT-AC-01  # User Access Management
      - IT-AC-02  # Privileged Access
      - IT-AC-03  # Access Reviews
      - IT-CM-01  # Change Management
    quarterly_review: true
    annual_audit: true

  gdpr:
    enabled: true
    data_protection_officer: dpo@global.corp
    right_to_erasure: true
    data_portability: true
    breach_notification_hours: 72

  hipaa:
    enabled: true
    domains: ["AMER"]
    ou_scope:
      - "OU=Healthcare,DC=amer,DC=global,DC=corp"
    controls:
      - "164.308(a)(3)"  # Workforce Security
      - "164.308(a)(4)"  # Access Management
      - "164.312(a)(1)"  # Access Control
```

### Workflow Enterprise - Revue Trimestrielle des Accès

```bash
#!/bin/bash
# /opt/scripts/enterprise-access-review.sh

QUARTER=$(date +%Y-Q$(( ($(date +%-m)-1)/3+1 )))
REPORT_BASE="/enterprise/reports/access-review/${QUARTER}"

mkdir -p "${REPORT_BASE}"

echo "🏢 Démarrage de la revue d'accès trimestrielle - ${QUARTER}"

# Pour chaque domaine
for DOMAIN in EMEA AMER APAC; do
  echo "📊 Traitement du domaine ${DOMAIN}..."

  DOMAIN_DIR="${REPORT_BASE}/${DOMAIN}"
  mkdir -p "${DOMAIN_DIR}"

  # Extraire tous les utilisateurs
  ldap-monitor -c /etc/ldap-monitor/config-${DOMAIN,,}.yaml \
    user list \
    --format json \
    --output "${DOMAIN_DIR}/all-users.json"

  # Identifier les comptes privilégiés
  ldap-monitor -c /etc/ldap-monitor/config-${DOMAIN,,}.yaml \
    audit security \
    --check-privileged \
    --format json \
    --output "${DOMAIN_DIR}/privileged-accounts.json"

  # Comptes inactifs (> 90 jours)
  ldap-monitor -c /etc/ldap-monitor/config-${DOMAIN,,}.yaml \
    audit users \
    --inactive-days 90 \
    --format csv \
    --output "${DOMAIN_DIR}/inactive-accounts.csv"

  # Comptes sans manager
  jq -r '.[] | select(.manager == null or .manager == "") |
    [.employeeNumber, .cn, .mail, .department] | @csv' \
    "${DOMAIN_DIR}/all-users.json" \
    > "${DOMAIN_DIR}/no-manager.csv"

  # Groupes critiques et leurs membres
  for GROUP in "Domain Admins" "Enterprise Admins" "Finance Access"; do
    GROUP_SAFE=$(echo "${GROUP}" | tr ' ' '-')
    ldap-monitor -c /etc/ldap-monitor/config-${DOMAIN,,}.yaml \
      group show "CN=${GROUP},CN=Users,DC=${DOMAIN,,},DC=global,DC=corp" \
      --format json \
      > "${DOMAIN_DIR}/group-${GROUP_SAFE}.json"
  done

done

# Consolider les rapports
python3 /opt/scripts/consolidate-access-review.py \
  --input "${REPORT_BASE}" \
  --output "${REPORT_BASE}/consolidated-report.xlsx"

# Générer les workflows de validation
python3 /opt/scripts/generate-approval-workflows.py \
  --report "${REPORT_BASE}/consolidated-report.xlsx" \
  --output "${REPORT_BASE}/approval-workflows"

# Créer les tickets ServiceNow pour chaque manager
python3 /opt/scripts/create-servicenow-tickets.py \
  --workflows "${REPORT_BASE}/approval-workflows" \
  --assignment-group "Access Review ${QUARTER}"

echo "✅ Revue d'accès initiée - ${QUARTER}"
echo "📧 Notifications envoyées aux managers"
```

---

## Conformité et Audit

### Scénario : Préparation Audit Externe

```bash
#!/bin/bash
# /opt/scripts/prepare-external-audit.sh

AUDIT_DATE="2024-12"
AUDIT_DIR="/secure/audits/${AUDIT_DATE}"
AUDITOR_ACCESS_DIR="${AUDIT_DIR}/auditor-access"

mkdir -p "${AUDITOR_ACCESS_DIR}"

# 1. Snapshot complet de la configuration
echo "📸 Capture de la configuration LDAP..."
ldap-monitor backup full \
  --output "${AUDIT_DIR}/ldap-snapshot-${AUDIT_DATE}.ldif" \
  --format ldif

# 2. Rapports de conformité
echo "📋 Génération des rapports de conformité..."

# SOC2
ldap-monitor audit all \
  --compliance soc2 \
  --format html \
  --output "${AUDITOR_ACCESS_DIR}/soc2-compliance.html"

# ISO27001
ldap-monitor audit security \
  --compliance iso27001 \
  --controls A.9.2 \
  --format pdf \
  --output "${AUDITOR_ACCESS_DIR}/iso27001-a9.2.pdf"

# 3. Historique des modifications (6 derniers mois)
echo "📜 Extraction de l'historique..."
ldap-monitor reports history \
  --start-date $(date -d "6 months ago" +%Y-%m-%d) \
  --end-date $(date +%Y-%m-%d) \
  --events "user_created,user_deleted,group_modified,permission_changed" \
  --format csv \
  --output "${AUDITOR_ACCESS_DIR}/change-history.csv"

# 4. Liste des comptes privilégiés
ldap-monitor user list \
  --filter "(memberOf=CN=Domain Admins,*)" \
  --format excel \
  --output "${AUDITOR_ACCESS_DIR}/privileged-accounts.xlsx"

# 5. Politiques de mot de passe
ldap-monitor audit security \
  --check password-policy \
  --format json \
  --output "${AUDITOR_ACCESS_DIR}/password-policies.json"

# 6. Statistiques d'authentification
ldap-monitor monitor metrics \
  --metric failed_authentications \
  --period 6months \
  --format chart \
  --output "${AUDITOR_ACCESS_DIR}/auth-failures.png"

# 7. Anonymiser les données sensibles
python3 /opt/scripts/anonymize-audit-data.py \
  --input-dir "${AUDITOR_ACCESS_DIR}" \
  --config /etc/ldap-monitor/anonymization-rules.yaml

# 8. Créer un index
cat > "${AUDITOR_ACCESS_DIR}/README.md" << EOF
# Audit LDAP - ${AUDIT_DATE}

## Documents Fournis

1. **soc2-compliance.html** - Rapport de conformité SOC2
2. **iso27001-a9.2.pdf** - Conformité ISO27001 section 9.2
3. **change-history.csv** - Historique des modifications (6 mois)
4. **privileged-accounts.xlsx** - Liste des comptes privilégiés
5. **password-policies.json** - Politiques de mot de passe
6. **auth-failures.png** - Graphique des échecs d'authentification

## Période Couverte
- Du: $(date -d "6 months ago" +%Y-%m-%d)
- Au: $(date +%Y-%m-%d)

## Domaines Inclus
- EMEA
- AMER
- APAC

## Contact
- IT Security: security@global.corp
- Compliance Officer: compliance@global.corp
EOF

# 9. Chiffrer et signer
gpg --encrypt --recipient auditor@auditfirm.com \
  --output "${AUDIT_DIR}/audit-package-${AUDIT_DATE}.gpg" \
  --archive "${AUDITOR_ACCESS_DIR}"

echo "✅ Package d'audit préparé: ${AUDIT_DIR}/audit-package-${AUDIT_DATE}.gpg"
```

---

## Migration et Consolidation

### Scénario : Migration OpenLDAP vers Active Directory

```yaml
# config-migration.yaml
migration:
  source:
    type: openldap
    server: ldap://old-ldap.company.com
    bind_dn: cn=admin,dc=company,dc=com
    base_dn: dc=company,dc=com

  target:
    type: active_directory
    server: ldaps://new-ad.company.com
    bind_dn: CN=migration-service,OU=ServiceAccounts,DC=company,DC=com
    base_dn: DC=company,DC=com

  mapping:
    users:
      uid: sAMAccountName
      cn: cn
      mail: mail
      givenName: givenName
      sn: sn
      telephoneNumber: telephoneNumber

    groups:
      cn: cn
      description: description
      member: member

  validation:
    dry_run: true
    verify_after_migration: true
    rollback_on_error: true

  batch_size: 100
  delay_between_batches: 5  # secondes
```

### Script de Migration

```bash
#!/bin/bash
# /opt/scripts/migrate-to-ad.sh

MIGRATION_ID="mig-$(date +%Y%m%d-%H%M%S)"
MIGRATION_LOG="/var/log/migrations/${MIGRATION_ID}.log"

exec 1> >(tee -a "${MIGRATION_LOG}")
exec 2>&1

echo "🚀 Démarrage de la migration - ${MIGRATION_ID}"

# Phase 1: Validation pré-migration
echo "1️⃣ Phase 1: Validation..."
ldap-monitor migration validate \
  --config /etc/ldap-monitor/config-migration.yaml \
  --output "/tmp/${MIGRATION_ID}-validation.json"

# Vérifier les erreurs
if ! jq -e '.valid == true' "/tmp/${MIGRATION_ID}-validation.json" > /dev/null; then
  echo "❌ La validation a échoué. Consultez le rapport."
  exit 1
fi

# Phase 2: Dry run
echo "2️⃣ Phase 2: Dry run..."
ldap-monitor migration run \
  --config /etc/ldap-monitor/config-migration.yaml \
  --dry-run \
  --output "/tmp/${MIGRATION_ID}-dryrun.json"

echo "📊 Statistiques du dry run:"
jq -r '.statistics | to_entries[] | "\(.key): \(.value)"' \
  "/tmp/${MIGRATION_ID}-dryrun.json"

read -p "Continuer avec la migration réelle? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
  echo "❌ Migration annulée"
  exit 0
fi

# Phase 3: Backup
echo "3️⃣ Phase 3: Backup..."
ldap-monitor backup full \
  --source openldap \
  --output "/backups/${MIGRATION_ID}-source-backup.ldif"

ldap-monitor backup full \
  --source active_directory \
  --output "/backups/${MIGRATION_ID}-target-backup.ldif"

# Phase 4: Migration par batch
echo "4️⃣ Phase 4: Migration..."
ldap-monitor migration run \
  --config /etc/ldap-monitor/config-migration.yaml \
  --batch-size 100 \
  --output "/tmp/${MIGRATION_ID}-results.json" \
  --progress

# Phase 5: Validation post-migration
echo "5️⃣ Phase 5: Validation post-migration..."
ldap-monitor migration verify \
  --config /etc/ldap-monitor/config-migration.yaml \
  --output "/tmp/${MIGRATION_ID}-verification.json"

# Phase 6: Rapport
python3 /opt/scripts/generate-migration-report.py \
  --migration-id "${MIGRATION_ID}" \
  --output "/reports/migration-${MIGRATION_ID}.html"

echo "✅ Migration terminée - ${MIGRATION_ID}"
```

---

## Gestion Multi-Sites

### Configuration pour Organisation Géographiquement Distribuée

```yaml
# config-multi-site.yaml
topology:
  sites:
    - name: "Paris HQ"
      location: "Paris, France"
      ldap_servers:
        - ldaps://dc1-paris.corp.local
        - ldaps://dc2-paris.corp.local
      monitoring_server: mon-paris.corp.local
      timezone: "Europe/Paris"

    - name: "London Office"
      location: "London, UK"
      ldap_servers:
        - ldaps://dc1-london.corp.local
      monitoring_server: mon-london.corp.local
      timezone: "Europe/London"

    - name: "New York Office"
      location: "New York, USA"
      ldap_servers:
        - ldaps://dc1-ny.corp.local
        - ldaps://dc2-ny.corp.local
      monitoring_server: mon-ny.corp.local
      timezone: "America/New_York"

  replication:
    check_replication_lag: true
    max_lag_seconds: 300
    alert_on_lag: true

  failover:
    enabled: true
    automatic: true
    health_check_interval: 30

monitoring:
  distributed: true
  central_aggregator: mon-central.corp.local

  per_site_metrics:
    - site_connectivity
    - replication_status
    - local_user_count
    - local_auth_rate
    - cross_site_auth
```

### Dashboard Multi-Sites

```python
#!/usr/bin/env python3
# /opt/scripts/multi-site-dashboard.py

import requests
from datetime import datetime
import json

SITES = ["Paris HQ", "London Office", "New York Office"]

def get_site_status(site):
    """Récupère le statut d'un site"""
    config = load_site_config(site)

    status = {
        "site": site,
        "timestamp": datetime.now().isoformat(),
        "health": {},
        "metrics": {},
        "alerts": []
    }

    # Health check
    result = subprocess.run(
        ["ldap-monitor", "-c", config, "audit", "health", "--format", "json"],
        capture_output=True, text=True
    )
    status["health"] = json.loads(result.stdout)

    # Metrics
    result = subprocess.run(
        ["ldap-monitor", "-c", config, "monitor", "metrics", "--format", "json"],
        capture_output=True, text=True
    )
    status["metrics"] = json.loads(result.stdout)

    return status

def generate_dashboard():
    """Génère le dashboard multi-sites"""
    dashboard = {
        "generated_at": datetime.now().isoformat(),
        "sites": []
    }

    for site in SITES:
        print(f"Collecte des données pour {site}...")
        site_status = get_site_status(site)
        dashboard["sites"].append(site_status)

    # Générer HTML
    html = generate_html_dashboard(dashboard)

    with open("/var/www/html/ldap-dashboard.html", "w") as f:
        f.write(html)

    print("✅ Dashboard généré: /var/www/html/ldap-dashboard.html")

if __name__ == "__main__":
    generate_dashboard()
```

---

## Conclusion

Ces cas d'usage démontrent la flexibilité de LDAP Health Monitor pour s'adapter à différentes tailles et types d'organisations. La clé du succès réside dans:

1. **Configuration adaptée** - Ajuster les paramètres selon la taille et les besoins
2. **Automatisation** - Scripts et workflows adaptés au contexte
3. **Monitoring continu** - Alertes et métriques pertinentes
4. **Conformité** - Rapports et audits réguliers
5. **Documentation** - Traçabilité et audit trail complet

Pour des exemples d'automatisation avancée, consultez [Automation-Scripts.md](./Automation-Scripts.md).
