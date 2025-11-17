# Intégration Email

Guide complet pour configurer les alertes email avec LDAP Health Monitor. Recevez des notifications par email sur l'état de votre infrastructure LDAP avec des rapports HTML détaillés.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Prérequis](#prérequis)
- [Configuration SMTP](#configuration-smtp)
- [Fournisseurs Email](#fournisseurs-email)
- [Configuration LDAP Monitor](#configuration-ldap-monitor)
- [Templates Email](#templates-email)
- [Types d'Alertes](#types-dalertes)
- [Rapports Automatiques](#rapports-automatiques)
- [Multi-destinataires](#multi-destinataires)
- [Sécurité](#sécurité)
- [Troubleshooting](#troubleshooting)

## 📊 Vue d'ensemble

### Fonctionnalités

- ✅ **Alertes temps réel** - Notifications instantanées par email
- ✅ **Rapports HTML** - Emails formatés avec graphiques et tableaux
- ✅ **Multi-destinataires** - Listes de distribution, groupes, individus
- ✅ **Templates personnalisables** - Design adapté à votre charte
- ✅ **Pièces jointes** - Rapports PDF, CSV, logs
- ✅ **Priorités email** - High priority pour alertes critiques
- ✅ **Support multi-providers** - Gmail, Office 365, SendGrid, SMTP custom

### Architecture

```
┌─────────────────────┐
│  LDAP Monitor       │
│  Alert Manager      │
└──────────┬──────────┘
           │ SMTP/API
           ↓
┌─────────────────────┐
│  SMTP Server        │
│  (Gmail, O365, etc) │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  Email Recipients   │
│  admin@example.com  │
└─────────────────────┘
```

## 🔧 Prérequis

### Accès SMTP

**Option 1 : Serveur SMTP interne**
- Accès à un serveur SMTP (port 25, 465, ou 587)
- Credentials d'authentification

**Option 2 : Service cloud**
- Compte Gmail, Office 365, SendGrid, Mailgun, etc.
- App password ou API key

### LDAP Health Monitor

- Version **1.0.0+**
- Module `alerts` activé
- Bibliothèque Python : `smtplib`, `email` (incluses)

## 📧 Configuration SMTP

### Configuration de base

Éditez `config.yaml` :

```yaml
alerts:
  # Activer les alertes
  enabled: true

  # Configuration Email
  email:
    enabled: true

    # Serveur SMTP
    smtp:
      host: "smtp.gmail.com"
      port: 587
      use_tls: true
      use_ssl: false
      timeout: 30

      # Authentification
      username: "ldap-monitor@example.com"
      password: ${SMTP_PASSWORD}  # Variable d'environnement

    # Expéditeur
    from:
      email: "ldap-monitor@example.com"
      name: "LDAP Health Monitor"

    # Destinataires par défaut
    to:
      - "admin@example.com"
      - "sysadmin@example.com"

    # CC (optionnel)
    cc:
      - "team-infra@example.com"

    # BCC (optionnel)
    bcc:
      - "logs@example.com"

    # Sévérités à notifier
    severities:
      - critical
      - warning
      - info

    # Types d'événements
    events:
      - server_down
      - high_response_time
      - audit_completed
      - backup_failed
      - user_locked

    # Format des emails
    format: "html"  # html, text, both
    include_logo: true
    include_timestamp: true
    include_server_info: true

    # Pièces jointes
    attachments:
      include_reports: true
      max_size_mb: 10
      compress: true
```

### Variables d'environnement

**`.env` :**

```bash
# SMTP Password
SMTP_PASSWORD=your-app-password

# Email destinataires (override config.yaml)
EMAIL_TO=admin@example.com,sysadmin@example.com
EMAIL_CC=team@example.com

# Email expéditeur
EMAIL_FROM=ldap-monitor@example.com
```

**Charger les variables :**

```bash
# Export manuel
export SMTP_PASSWORD="your-password"

# Ou charger depuis .env
export $(cat .env | xargs)

# Ou avec direnv
echo 'dotenv' > .envrc
direnv allow
```

## 📮 Fournisseurs Email

### Gmail

**Configuration :**

```yaml
alerts:
  email:
    smtp:
      host: "smtp.gmail.com"
      port: 587
      use_tls: true
      username: "your-email@gmail.com"
      password: ${GMAIL_APP_PASSWORD}
```

**Générer un App Password :**

1. Accédez à [Google Account Security](https://myaccount.google.com/security)
2. Activez **2-Step Verification**
3. Allez dans **App passwords**
4. Générez un nouveau mot de passe pour "Mail"
5. Utilisez ce mot de passe dans `SMTP_PASSWORD`

**Limites Gmail :**
- **500 emails/jour** (compte gratuit)
- **2000 emails/jour** (Google Workspace)

### Office 365 / Outlook

**Configuration :**

```yaml
alerts:
  email:
    smtp:
      host: "smtp.office365.com"
      port: 587
      use_tls: true
      username: "your-email@company.com"
      password: ${SMTP_PASSWORD}
```

**Authentication moderne :**

Pour utiliser OAuth2 avec Office 365 (plus sécurisé) :

```yaml
alerts:
  email:
    smtp:
      host: "smtp.office365.com"
      port: 587
      use_tls: true
      auth_method: "oauth2"
      oauth2:
        client_id: ${AZURE_CLIENT_ID}
        client_secret: ${AZURE_CLIENT_SECRET}
        tenant_id: ${AZURE_TENANT_ID}
```

**Limites Office 365 :**
- **10,000 emails/jour**
- **30 messages/minute**

### SendGrid

**Configuration :**

```yaml
alerts:
  email:
    provider: "sendgrid"
    sendgrid:
      api_key: ${SENDGRID_API_KEY}
      from_email: "ldap-monitor@example.com"
      from_name: "LDAP Health Monitor"
```

**Obtenir API Key :**

1. Créez un compte sur [SendGrid](https://sendgrid.com)
2. Settings → API Keys → Create API Key
3. Permissions : "Mail Send" (Full Access)

**Limites SendGrid :**
- **100 emails/jour** (Free tier)
- **Illimité** (plans payants)

### Amazon SES

**Configuration :**

```yaml
alerts:
  email:
    provider: "ses"
    ses:
      region: "eu-west-1"
      access_key_id: ${AWS_ACCESS_KEY_ID}
      secret_access_key: ${AWS_SECRET_ACCESS_KEY}
      from_email: "ldap-monitor@example.com"
```

**Configuration AWS :**

```bash
# Installer AWS CLI
pip install boto3

# Configurer credentials
aws configure

# Vérifier l'email expéditeur (en sandbox)
aws ses verify-email-identity --email-address ldap-monitor@example.com
```

**Limites SES :**
- **Sandbox : 200 emails/jour**
- **Production : 50,000 emails/jour** (par défaut, augmentable)

### SMTP Custom / Serveur Interne

**Configuration :**

```yaml
alerts:
  email:
    smtp:
      host: "mail.company.local"
      port: 25
      use_tls: false
      use_ssl: false
      # Pas d'authentification si réseau interne
      require_auth: false
```

**Avec authentification :**

```yaml
alerts:
  email:
    smtp:
      host: "smtp.company.com"
      port: 465
      use_ssl: true
      username: "ldap-monitor"
      password: ${SMTP_PASSWORD}
```

## ⚙️ Configuration LDAP Monitor

### Configuration avancée

```yaml
alerts:
  email:
    enabled: true

    # Configuration SMTP
    smtp:
      host: "smtp.gmail.com"
      port: 587
      use_tls: true
      username: ${SMTP_USERNAME}
      password: ${SMTP_PASSWORD}

      # Retry et timeout
      timeout: 30
      retry_attempts: 3
      retry_delay: 5

    # Expéditeur
    from:
      email: "ldap-monitor@example.com"
      name: "LDAP Health Monitor"

    # Routage par sévérité
    routing:
      critical:
        to:
          - "oncall@example.com"
          - "manager@example.com"
        cc: []
        subject_prefix: "[CRITICAL]"
        priority: "high"

      warning:
        to:
          - "sysadmin@example.com"
        subject_prefix: "[WARNING]"
        priority: "normal"

      info:
        to:
          - "team-infra@example.com"
        subject_prefix: "[INFO]"
        priority: "low"

    # Templates
    templates:
      # Répertoire des templates
      directory: "/etc/ldap-monitor/email-templates"

      # Template par défaut
      default: "default.html"

      # Templates par type d'alerte
      server_down: "server-down.html"
      audit_completed: "audit-report.html"
      backup_completed: "backup-report.html"

    # Pièces jointes
    attachments:
      # Attacher les rapports
      include_reports: true

      # Types de fichiers autorisés
      allowed_types:
        - "pdf"
        - "html"
        - "csv"
        - "json"

      # Taille max par pièce jointe
      max_size_mb: 10

      # Compression automatique
      compress: true
      compression_format: "zip"

    # Throttling
    throttle:
      enabled: true
      max_emails_per_hour: 50
      group_similar_alerts: true
      grouping_window: 600  # 10 minutes

    # Digest
    digest:
      enabled: true
      schedule: "0 9 * * *"  # Tous les jours à 9h
      include_summary: true
      include_charts: true
```

## 📝 Templates Email

### Template HTML de base

**`templates/default.html` :**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }
        .header {
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 5px 5px 0 0;
        }
        .content {
            background: #f4f4f4;
            padding: 20px;
            border: 1px solid #ddd;
        }
        .alert-critical {
            background: #e74c3c;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .alert-warning {
            background: #f39c12;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        .alert-info {
            background: #3498db;
            color: white;
            padding: 15px;
            border-radius: 5px;
            margin: 10px 0;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
        }
        th, td {
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }
        th {
            background: #34495e;
            color: white;
        }
        .footer {
            background: #ecf0f1;
            padding: 15px;
            text-align: center;
            font-size: 12px;
            color: #7f8c8d;
            border-radius: 0 0 5px 5px;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background: #3498db;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin: 10px 0;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 LDAP Health Monitor</h1>
        <p>{{ alert_type }}</p>
    </div>

    <div class="content">
        <div class="alert-{{ severity }}">
            <h2>{{ alert_title }}</h2>
            <p>{{ alert_message }}</p>
        </div>

        <h3>📊 Détails</h3>
        <table>
            <tr>
                <th>Serveur</th>
                <td>{{ server_url }}</td>
            </tr>
            <tr>
                <th>Date/Heure</th>
                <td>{{ timestamp }}</td>
            </tr>
            <tr>
                <th>Sévérité</th>
                <td>{{ severity }}</td>
            </tr>
            <tr>
                <th>Durée</th>
                <td>{{ duration }}</td>
            </tr>
        </table>

        {% if metrics %}
        <h3>📈 Métriques</h3>
        <table>
            <tr>
                <th>Métrique</th>
                <th>Valeur</th>
            </tr>
            {% for metric in metrics %}
            <tr>
                <td>{{ metric.name }}</td>
                <td>{{ metric.value }}</td>
            </tr>
            {% endfor %}
        </table>
        {% endif %}

        {% if recommendations %}
        <h3>💡 Recommandations</h3>
        <ul>
            {% for rec in recommendations %}
            <li>{{ rec }}</li>
            {% endfor %}
        </ul>
        {% endif %}

        <div style="text-align: center; margin: 20px 0;">
            <a href="{{ dashboard_url }}" class="button">
                📊 Voir le Dashboard
            </a>
            <a href="{{ logs_url }}" class="button">
                📝 Consulter les Logs
            </a>
        </div>
    </div>

    <div class="footer">
        <p>LDAP Health Monitor v{{ version }}</p>
        <p>{{ timestamp }}</p>
        <p>
            <a href="{{ unsubscribe_url }}">Se désabonner</a> |
            <a href="{{ preferences_url }}">Préférences</a>
        </p>
    </div>
</body>
</html>
```

### Template pour Serveur Down

**`templates/server-down.html` :**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* Styles similaires au template de base */
    </style>
</head>
<body>
    <div class="header" style="background: #c0392b;">
        <h1>🔴 ALERTE CRITIQUE</h1>
        <h2>Serveur LDAP Inaccessible</h2>
    </div>

    <div class="content">
        <div class="alert-critical">
            <h2>⚠️ Le serveur LDAP est DOWN</h2>
            <p><strong>{{ server_url }}</strong> ne répond plus depuis <strong>{{ duration }}</strong></p>
        </div>

        <h3>🔍 Détails de l'Incident</h3>
        <table>
            <tr>
                <th>Serveur</th>
                <td>{{ server_url }}</td>
            </tr>
            <tr>
                <th>Port</th>
                <td>{{ port }}</td>
            </tr>
            <tr>
                <th>Détecté à</th>
                <td>{{ detection_time }}</td>
            </tr>
            <tr>
                <th>Dernière réponse</th>
                <td>{{ last_success }}</td>
            </tr>
            <tr>
                <th>Tentatives échouées</th>
                <td>{{ failed_attempts }}</td>
            </tr>
        </table>

        <h3>🚨 Impact</h3>
        <ul style="color: #c0392b; font-weight: bold;">
            <li>Authentification LDAP impossible</li>
            <li>Applications dépendantes affectées</li>
            <li>Intervention immédiate requise</li>
        </ul>

        <h3>🔧 Actions Recommandées</h3>
        <ol>
            <li>Vérifier le statut du serveur : <code>systemctl status slapd</code></li>
            <li>Consulter les logs : <code>/var/log/slapd.log</code></li>
            <li>Tester la connectivité : <code>telnet {{ server_host }} {{ port }}</code></li>
            <li>Redémarrer si nécessaire : <code>systemctl restart slapd</code></li>
            <li>Vérifier le monitoring : <a href="{{ dashboard_url }}">Grafana Dashboard</a></li>
        </ol>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{ dashboard_url }}" class="button" style="background: #c0392b;">
                🚨 Dashboard de Monitoring
            </a>
        </div>
    </div>

    <div class="footer">
        <p><strong>Notification automatique - LDAP Health Monitor</strong></p>
        <p>{{ timestamp }}</p>
    </div>
</body>
</html>
```

### Template Rapport d'Audit

**`templates/audit-report.html` :**

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        /* Styles similaires */
    </style>
</head>
<body>
    <div class="header" style="background: #27ae60;">
        <h1>✅ Rapport d'Audit LDAP</h1>
        <p>Audit terminé avec succès</p>
    </div>

    <div class="content">
        <h3>📊 Statistiques Générales</h3>
        <table>
            <tr>
                <th>Type d'Audit</th>
                <td>{{ audit_type }}</td>
            </tr>
            <tr>
                <th>Durée</th>
                <td>{{ duration }}</td>
            </tr>
            <tr>
                <th>Date</th>
                <td>{{ audit_date }}</td>
            </tr>
        </table>

        <h3>👥 Utilisateurs</h3>
        <table>
            <tr>
                <td><strong>Total</strong></td>
                <td>{{ total_users }}</td>
            </tr>
            <tr>
                <td>Actifs</td>
                <td style="color: #27ae60;">{{ active_users }}</td>
            </tr>
            <tr>
                <td>Inactifs (>90j)</td>
                <td style="color: #e67e22;">{{ inactive_users }}</td>
            </tr>
            <tr>
                <td>Verrouillés</td>
                <td style="color: #c0392b;">{{ locked_users }}</td>
            </tr>
            <tr>
                <td>Mot de passe expiré</td>
                <td style="color: #e74c3c;">{{ password_expired }}</td>
            </tr>
        </table>

        <h3>👥 Groupes</h3>
        <table>
            <tr>
                <td><strong>Total</strong></td>
                <td>{{ total_groups }}</td>
            </tr>
            <tr>
                <td>Groupes vides</td>
                <td>{{ empty_groups }}</td>
            </tr>
            <tr>
                <td>Groupes larges (>100)</td>
                <td>{{ large_groups }}</td>
            </tr>
            <tr>
                <td>Total membres</td>
                <td>{{ total_members }}</td>
            </tr>
        </table>

        {% if issues %}
        <h3>⚠️ Problèmes Détectés</h3>
        <ul>
            {% for issue in issues %}
            <li style="color: {{ issue.color }};">{{ issue.description }}</li>
            {% endfor %}
        </ul>
        {% endif %}

        <div style="text-align: center; margin: 20px 0;">
            <a href="{{ report_url }}" class="button">
                📄 Rapport Complet (HTML)
            </a>
        </div>
    </div>

    <div class="footer">
        <p>LDAP Health Monitor - Audit automatique</p>
        <p>{{ timestamp }}</p>
    </div>
</body>
</html>
```

## 🎯 Types d'Alertes

### 1. Alerte Serveur Down

**Déclencheur :** Serveur LDAP inaccessible

**Email envoyé :**
- **Sujet :** `[CRITICAL] Serveur LDAP Inaccessible - ldap.example.com`
- **Priorité :** Haute
- **Destinataires :** Équipe oncall
- **Template :** `server-down.html`

### 2. Alerte Temps de Réponse

**Déclencheur :** Latence élevée

**Email envoyé :**
- **Sujet :** `[WARNING] LDAP - Temps de réponse élevé (5.2s)`
- **Priorité :** Normale
- **Template :** `high-latency.html`

### 3. Rapport d'Audit Quotidien

**Déclencheur :** Cron quotidien

**Email envoyé :**
- **Sujet :** `[INFO] Rapport d'Audit LDAP Quotidien - 15/01/2024`
- **Priorité :** Basse
- **Pièces jointes :** Rapport HTML, CSV
- **Template :** `audit-report.html`

### 4. Alerte Backup Échoué

**Email envoyé :**
- **Sujet :** `[CRITICAL] Échec du Backup LDAP`
- **Détails :** Erreur, logs, espace disque

## 📊 Rapports Automatiques

### Configuration des rapports périodiques

```yaml
reports:
  email:
    # Rapport quotidien
    daily:
      enabled: true
      schedule: "0 9 * * *"  # 9h tous les jours
      recipients:
        - "admin@example.com"
      include:
        - server_health
        - user_statistics
        - group_statistics
        - recent_alerts
      format: "html"
      attach_csv: true

    # Rapport hebdomadaire
    weekly:
      enabled: true
      schedule: "0 9 * * 1"  # Lundi 9h
      recipients:
        - "manager@example.com"
        - "team@example.com"
      include:
        - executive_summary
        - trends
        - capacity_planning
        - security_summary
      format: "html"
      attach_pdf: true

    # Rapport mensuel
    monthly:
      enabled: true
      schedule: "0 9 1 * *"  # 1er du mois à 9h
      recipients:
        - "management@example.com"
      include:
        - monthly_summary
        - growth_metrics
        - compliance_report
        - recommendations
      format: "html"
      attach_pdf: true
```

### Envoi manuel de rapports

```bash
# Envoyer le rapport d'audit par email
ldap-monitor audit all \
  --email \
  --email-to "admin@example.com" \
  --email-subject "Rapport d'Audit LDAP"

# Avec pièce jointe
ldap-monitor audit all \
  --format html \
  --output /tmp/audit.html \
  --email \
  --email-attach /tmp/audit.html

# Rapport quotidien
ldap-monitor report daily --email
```

## 👥 Multi-destinataires

### Listes de distribution

```yaml
alerts:
  email:
    # Définir des groupes
    distribution_lists:
      oncall:
        - "oncall-primary@example.com"
        - "oncall-backup@example.com"
        - "manager@example.com"

      sysadmin:
        - "admin1@example.com"
        - "admin2@example.com"

      management:
        - "cto@example.com"
        - "it-manager@example.com"

    # Utiliser les groupes dans le routage
    routing:
      critical:
        to: "{{ distribution_lists.oncall }}"

      warning:
        to: "{{ distribution_lists.sysadmin }}"

      monthly_report:
        to: "{{ distribution_lists.management }}"
```

### Routage conditionnel

```yaml
alerts:
  email:
    routing_rules:
      # Serveur production
      - condition: "server == 'ldap-prod.example.com'"
        severity: "critical"
        to:
          - "oncall@example.com"
          - "manager@example.com"

      # Serveur test
      - condition: "server == 'ldap-test.example.com'"
        severity: "warning"
        to:
          - "dev-team@example.com"

      # Heures de bureau
      - condition: "time.hour >= 9 and time.hour <= 18"
        to:
          - "sysadmin@example.com"

      # En dehors des heures de bureau
      - condition: "time.hour < 9 or time.hour > 18"
        to:
          - "oncall@example.com"
        priority: "high"
```

## 🔒 Sécurité

### Meilleures pratiques

**1. Ne jamais stocker les mots de passe en clair :**

```yaml
# ❌ MAUVAIS
alerts:
  email:
    smtp:
      password: "my-password-in-clear"

# ✅ BON
alerts:
  email:
    smtp:
      password: ${SMTP_PASSWORD}
```

**2. Utiliser TLS/SSL :**

```yaml
alerts:
  email:
    smtp:
      use_tls: true  # STARTTLS (port 587)
      # Ou
      use_ssl: true  # SSL direct (port 465)
```

**3. Vérifier les certificats :**

```yaml
alerts:
  email:
    smtp:
      verify_cert: true
      cert_file: "/path/to/ca-bundle.crt"
```

**4. App Passwords au lieu de mots de passe compte :**

Pour Gmail, Office 365, utilisez toujours des App Passwords ou OAuth2.

**5. Limiter les informations sensibles :**

```yaml
alerts:
  email:
    # Ne pas inclure d'infos sensibles
    sanitize_content: true
    exclude_sensitive_fields:
      - "password"
      - "credentials"
      - "apiKey"
```

### Chiffrement des emails (S/MIME)

```yaml
alerts:
  email:
    encryption:
      enabled: true
      method: "smime"
      certificate: "/path/to/cert.pem"
      private_key: "/path/to/key.pem"
```

## 🐛 Troubleshooting

### Les emails ne sont pas envoyés

**Vérifier la configuration :**

```bash
# Valider le fichier config
ldap-monitor config validate

# Tester l'envoi d'email
ldap-monitor test email

# Vérifier les variables d'environnement
echo $SMTP_PASSWORD
```

**Logs détaillés :**

```bash
# Mode debug
ldap-monitor --debug monitor start --email

# Ou dans config.yaml
logging:
  level: DEBUG
  smtp_debug: true
```

### Erreur d'authentification SMTP

**Causes possibles :**
1. Mauvais username/password
2. App password requis (Gmail, O365)
3. 2FA activé sans app password
4. Compte bloqué

**Solution :**

```bash
# Tester avec telnet
telnet smtp.gmail.com 587

# Tester avec openssl
openssl s_client -connect smtp.gmail.com:587 -starttls smtp
```

### Emails marqués comme spam

**Solutions :**

1. **Configurer SPF, DKIM, DMARC :**

```dns
; SPF Record
example.com. IN TXT "v=spf1 include:_spf.google.com ~all"

; DKIM Record
default._domainkey.example.com. IN TXT "v=DKIM1; k=rsa; p=YOUR_PUBLIC_KEY"

; DMARC Record
_dmarc.example.com. IN TXT "v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com"
```

2. **Utiliser un service réputé :** SendGrid, AWS SES

3. **Éviter le spam :**
   - Pas de CAPS LOCK excessif
   - Texte et HTML équilibrés
   - Pas trop d'images
   - Lien de désinscription

### Timeout lors de l'envoi

```yaml
alerts:
  email:
    smtp:
      timeout: 60  # Augmenter le timeout
      retry_attempts: 3
      retry_delay: 10
```

### Pièces jointes trop volumineuses

```yaml
alerts:
  email:
    attachments:
      # Compresser automatiquement
      compress: true
      max_size_mb: 5

      # Ou héberger et envoyer lien
      use_links: true
      upload_to: "s3://bucket/reports/"
```

## 📚 Exemples de Scripts

### Script d'envoi personnalisé

```bash
#!/bin/bash
# send-ldap-report.sh

# Config
RECIPIENT="admin@example.com"
SMTP_HOST="smtp.gmail.com"
SMTP_PORT="587"
FROM="ldap-monitor@example.com"

# Générer le rapport
ldap-monitor audit all --format html --output /tmp/report.html

# Envoyer via mail command (si disponible)
mail -s "Rapport LDAP Quotidien" \
     -a /tmp/report.html \
     -r "$FROM" \
     "$RECIPIENT" << EOF
Bonjour,

Veuillez trouver ci-joint le rapport d'audit LDAP quotidien.

Cordialement,
LDAP Health Monitor
EOF

# Ou via Python
python3 << PYTHON
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

msg = MIMEMultipart()
msg['From'] = "$FROM"
msg['To'] = "$RECIPIENT"
msg['Subject'] = "Rapport LDAP Quotidien"

body = "Veuillez trouver ci-joint le rapport d'audit LDAP."
msg.attach(MIMEText(body, 'plain'))

# Pièce jointe
with open("/tmp/report.html", "rb") as f:
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename=report.html")
    msg.attach(part)

# Envoyer
server = smtplib.SMTP("$SMTP_HOST", $SMTP_PORT)
server.starttls()
server.login("$FROM", "$SMTP_PASSWORD")
server.send_message(msg)
server.quit()
PYTHON
```

## 📚 Ressources

- [SMTP RFC 5321](https://tools.ietf.org/html/rfc5321)
- [Email Templates Best Practices](https://sendgrid.com/blog/email-template-best-practices/)
- [Gmail SMTP Guide](https://support.google.com/mail/answer/7126229)
- [Office 365 SMTP](https://docs.microsoft.com/en-us/exchange/mail-flow-best-practices/how-to-set-up-a-multifunction-device-or-application-to-send-email-using-microsoft-365-or-office-365)

## 🔗 Liens Connexes

- [Configuration des Alertes](../configuration/Alerts-Configuration.md)
- [Slack Integration](Slack.md)
- [Webhooks](Webhooks.md)
- [Rapports d'Audit](../features/audit/Audit-Reports.md)
