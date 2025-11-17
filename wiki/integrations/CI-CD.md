# Intégration CI/CD

Guide complet pour intégrer LDAP Health Monitor dans vos pipelines CI/CD. Automatisez les audits LDAP, validez les configurations, et assurez la conformité dans GitHub Actions, GitLab CI, Jenkins, et autres plateformes CI/CD.

## 📋 Table des Matières

- [Vue d'ensemble](#vue-densemble)
- [Cas d'Usage](#cas-dusage)
- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Jenkins](#jenkins)
- [CircleCI](#circleci)
- [Azure Pipelines](#azure-pipelines)
- [Bitbucket Pipelines](#bitbucket-pipelines)
- [Configuration Docker](#configuration-docker)
- [Exemples Avancés](#exemples-avancés)
- [Meilleures Pratiques](#meilleures-pratiques)

## 📊 Vue d'ensemble

### Pourquoi LDAP Monitor dans CI/CD ?

- ✅ **Validation automatique** - Vérifier la config avant déploiement
- ✅ **Tests d'intégration** - Valider les changements LDAP
- ✅ **Audits programmés** - Exécution régulière des audits
- ✅ **Compliance** - Vérifier la conformité aux standards
- ✅ **Détection précoce** - Identifier les problèmes avant production
- ✅ **Documentation** - Générer des rapports automatiques

### Architecture

```
┌─────────────────────┐
│  Git Push/PR        │
│  Code Changes       │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│  CI/CD Pipeline     │
│  (GitHub Actions,   │
│   GitLab CI, etc)   │
└──────────┬──────────┘
           │
           ├──→ Build
           ├──→ Test
           ├──→ LDAP Audit ←─ LDAP Health Monitor
           ├──→ Deploy
           └──→ Report
```

## 🎯 Cas d'Usage

### 1. Validation de Configuration

**Avant de déployer une nouvelle configuration LDAP :**

```yaml
- Valider la syntaxe du fichier config
- Tester la connexion au serveur
- Vérifier les permissions
- Valider le schéma LDAP
```

### 2. Audits Programmés

**Exécution régulière (quotidienne, hebdomadaire) :**

```yaml
- Audit complet de l'infrastructure LDAP
- Détection d'anomalies
- Génération de rapports
- Notifications d'alertes
```

### 3. Tests d'Intégration

**Après changements LDAP :**

```yaml
- Vérifier que les utilisateurs existent
- Valider les groupes et permissions
- Tester l'authentification
- Vérifier la cohérence des données
```

### 4. Conformité et Compliance

**Validation des politiques de sécurité :**

```yaml
- Vérifier les politiques de mots de passe
- Auditer les permissions
- Détecter les comptes inactifs
- Valider la structure organisationnelle
```

## 🔧 GitHub Actions

### Workflow de base

**`.github/workflows/ldap-audit.yml` :**

```yaml
name: LDAP Health Audit

on:
  # Déclenchement manuel
  workflow_dispatch:

  # Programmé (tous les jours à 9h UTC)
  schedule:
    - cron: '0 9 * * *'

  # Sur push vers main
  push:
    branches:
      - main
    paths:
      - 'ldap/**'
      - 'config/ldap/**'

  # Sur Pull Request
  pull_request:
    paths:
      - 'ldap/**'

jobs:
  ldap-audit:
    name: Audit LDAP Infrastructure
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install LDAP Health Monitor
        run: |
          pip install ldap-health-monitor

      - name: Configure LDAP Monitor
        run: |
          # Copier la configuration
          cp config/ldap-monitor.yml config.yaml

          # Créer le fichier .env avec les secrets
          cat > .env << EOF
          LDAP_PASSWORD=${{ secrets.LDAP_PASSWORD }}
          LDAP_BIND_DN=${{ secrets.LDAP_BIND_DN }}
          EOF

      - name: Test LDAP Connection
        run: |
          ldap-monitor test connection

      - name: Run LDAP Audit
        id: audit
        run: |
          ldap-monitor audit all \
            --format json \
            --output audit-results.json

      - name: Generate HTML Report
        run: |
          ldap-monitor audit all \
            --format html \
            --output audit-report.html

      - name: Upload Audit Report
        uses: actions/upload-artifact@v4
        with:
          name: ldap-audit-report
          path: |
            audit-report.html
            audit-results.json
          retention-days: 30

      - name: Check for Critical Issues
        run: |
          # Parser le JSON et vérifier les issues critiques
          critical_count=$(jq '.issues[] | select(.severity=="critical") | length' audit-results.json)

          if [ "$critical_count" -gt 0 ]; then
            echo "::error::$critical_count critical issues found in LDAP audit"
            exit 1
          fi

      - name: Send Slack Notification
        if: failure()
        uses: slackapi/slack-github-action@v1
        with:
          webhook-url: ${{ secrets.SLACK_WEBHOOK_URL }}
          payload: |
            {
              "text": "❌ LDAP Audit Failed in GitHub Actions",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*LDAP Audit Failed*\n\nRepository: ${{ github.repository }}\nBranch: ${{ github.ref }}\nWorkflow: ${{ github.workflow }}"
                  }
                }
              ]
            }

      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('audit-results.json', 'utf8'));

            const comment = `
            ## 🔍 LDAP Audit Results

            **Status:** ${results.status}
            **Duration:** ${results.duration}

            ### 📊 Statistics
            - **Users:** ${results.users.total} (${results.users.active} active)
            - **Groups:** ${results.groups.total}
            - **Issues:** ${results.issues.length}

            ### ⚠️ Issues Found
            ${results.issues.map(issue => `- [${issue.severity}] ${issue.description}`).join('\n')}

            [View Full Report](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: comment
            });
```

### Workflow avancé avec matrice

**Tests sur plusieurs environnements :**

```yaml
name: LDAP Multi-Environment Audit

on:
  schedule:
    - cron: '0 */6 * * *'  # Toutes les 6 heures

jobs:
  audit:
    name: Audit LDAP - ${{ matrix.environment }}
    runs-on: ubuntu-latest

    strategy:
      matrix:
        environment: [dev, staging, production]
        include:
          - environment: dev
            config: config/dev-ldap.yml
          - environment: staging
            config: config/staging-ldap.yml
          - environment: production
            config: config/prod-ldap.yml

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install ldap-health-monitor

      - name: Configure for ${{ matrix.environment }}
        run: |
          cp ${{ matrix.config }} config.yaml

          cat > .env << EOF
          LDAP_PASSWORD=${{ secrets[format('LDAP_PASSWORD_{0}', matrix.environment)] }}
          EOF

      - name: Run Audit
        run: |
          ldap-monitor audit all \
            --format json \
            --output audit-${{ matrix.environment }}.json

      - name: Upload Results
        uses: actions/upload-artifact@v4
        with:
          name: audit-${{ matrix.environment }}
          path: audit-${{ matrix.environment }}.json
```

### Action réutilisable

**`.github/actions/ldap-audit/action.yml` :**

```yaml
name: 'LDAP Audit Action'
description: 'Run LDAP Health Monitor audit'

inputs:
  ldap-password:
    description: 'LDAP bind password'
    required: true
  config-file:
    description: 'Path to config file'
    required: false
    default: 'config.yaml'
  audit-type:
    description: 'Type of audit (health, users, groups, all)'
    required: false
    default: 'all'

outputs:
  status:
    description: 'Audit status'
    value: ${{ steps.audit.outputs.status }}
  report-path:
    description: 'Path to audit report'
    value: ${{ steps.audit.outputs.report }}

runs:
  using: 'composite'
  steps:
    - name: Install LDAP Monitor
      shell: bash
      run: pip install ldap-health-monitor

    - name: Run Audit
      id: audit
      shell: bash
      env:
        LDAP_PASSWORD: ${{ inputs.ldap-password }}
      run: |
        ldap-monitor audit ${{ inputs.audit-type }} \
          --config ${{ inputs.config-file }} \
          --format json \
          --output audit-results.json

        echo "status=success" >> $GITHUB_OUTPUT
        echo "report=audit-results.json" >> $GITHUB_OUTPUT
```

**Utilisation :**

```yaml
jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: ./.github/actions/ldap-audit
        with:
          ldap-password: ${{ secrets.LDAP_PASSWORD }}
          audit-type: 'all'
```

## 🦊 GitLab CI

### Pipeline de base

**`.gitlab-ci.yml` :**

```yaml
stages:
  - validate
  - test
  - audit
  - report
  - deploy

variables:
  LDAP_MONITOR_VERSION: "1.0.0"

# Template pour les jobs LDAP
.ldap_template:
  image: python:3.11-slim
  before_script:
    - pip install ldap-health-monitor==$LDAP_MONITOR_VERSION
    - cp configs/$CI_ENVIRONMENT_NAME.yaml config.yaml
  cache:
    paths:
      - venv/

# Validation de configuration
validate_config:
  stage: validate
  extends: .ldap_template
  script:
    - ldap-monitor config validate
  only:
    - merge_requests
    - main

# Test de connexion
test_connection:
  stage: test
  extends: .ldap_template
  script:
    - ldap-monitor test connection
  variables:
    LDAP_PASSWORD: $LDAP_DEV_PASSWORD
  only:
    - merge_requests

# Audit complet
ldap_audit:
  stage: audit
  extends: .ldap_template
  script:
    - |
      ldap-monitor audit all \
        --format json \
        --output audit-results.json

    - |
      ldap-monitor audit all \
        --format html \
        --output audit-report.html

  artifacts:
    name: "ldap-audit-$CI_COMMIT_SHORT_SHA"
    paths:
      - audit-results.json
      - audit-report.html
    reports:
      junit: audit-results.json
    expire_in: 30 days

  variables:
    LDAP_PASSWORD: $LDAP_PASSWORD

  only:
    - schedules
    - main

# Audit de sécurité
security_audit:
  stage: audit
  extends: .ldap_template
  script:
    - ldap-monitor audit security --format json --output security.json

    # Vérifier les issues critiques
    - |
      critical=$(jq '[.issues[] | select(.severity=="critical")] | length' security.json)
      if [ "$critical" -gt 0 ]; then
        echo "Critical security issues found: $critical"
        exit 1
      fi

  artifacts:
    paths:
      - security.json
    expire_in: 90 days

  only:
    - schedules

# Génération de rapport
generate_report:
  stage: report
  extends: .ldap_template
  script:
    - ldap-monitor report daily --email --email-to $REPORT_EMAIL

  dependencies:
    - ldap_audit

  only:
    - schedules

  variables:
    SMTP_PASSWORD: $SMTP_PASSWORD
    REPORT_EMAIL: "admin@example.com"
```

### Pipeline multi-environnements

```yaml
# Audit Development
audit:dev:
  stage: audit
  extends: .ldap_template
  script:
    - ldap-monitor audit all --output dev-audit.json
  environment:
    name: development
  variables:
    LDAP_PASSWORD: $LDAP_DEV_PASSWORD
  only:
    - develop

# Audit Staging
audit:staging:
  stage: audit
  extends: .ldap_template
  script:
    - ldap-monitor audit all --output staging-audit.json
  environment:
    name: staging
  variables:
    LDAP_PASSWORD: $LDAP_STAGING_PASSWORD
  only:
    - staging

# Audit Production
audit:production:
  stage: audit
  extends: .ldap_template
  script:
    - ldap-monitor audit all --output prod-audit.json

    # Envoyer notification si problèmes
    - |
      if [ -s prod-audit.json ]; then
        ldap-monitor notify slack \
          --message "Production LDAP audit completed" \
          --attach prod-audit.json
      fi

  environment:
    name: production
  variables:
    LDAP_PASSWORD: $LDAP_PROD_PASSWORD
  only:
    - main
    - schedules

  when: manual
  allow_failure: false
```

### Scheduled Pipeline

**Via GitLab UI ou `.gitlab-ci.yml` :**

```yaml
# Créer dans Settings > CI/CD > Schedules

# Description: Daily LDAP Audit
# Interval: 0 9 * * * (tous les jours à 9h)
# Target Branch: main
# Variables:
#   - AUDIT_TYPE: full
#   - NOTIFY: "true"

daily_audit:
  stage: audit
  extends: .ldap_template
  script:
    - ldap-monitor audit $AUDIT_TYPE

    - |
      if [ "$NOTIFY" = "true" ]; then
        ldap-monitor notify email --to admin@example.com
      fi

  only:
    - schedules
```

## 🔨 Jenkins

### Jenkinsfile déclaratif

**`Jenkinsfile` :**

```groovy
pipeline {
    agent {
        docker {
            image 'python:3.11-slim'
        }
    }

    triggers {
        // Exécution quotidienne à 9h
        cron('0 9 * * *')
    }

    environment {
        LDAP_PASSWORD = credentials('ldap-password')
        SLACK_WEBHOOK = credentials('slack-webhook-url')
    }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    pip install --upgrade pip
                    pip install ldap-health-monitor
                '''
            }
        }

        stage('Validate Config') {
            steps {
                sh 'ldap-monitor config validate'
            }
        }

        stage('Test Connection') {
            steps {
                sh 'ldap-monitor test connection'
            }
        }

        stage('LDAP Audit') {
            steps {
                script {
                    sh '''
                        ldap-monitor audit all \
                            --format json \
                            --output audit-results.json

                        ldap-monitor audit all \
                            --format html \
                            --output audit-report.html
                    '''
                }
            }
        }

        stage('Analyze Results') {
            steps {
                script {
                    def results = readJSON file: 'audit-results.json'

                    // Vérifier les issues critiques
                    def criticalIssues = results.issues.findAll {
                        it.severity == 'critical'
                    }

                    if (criticalIssues.size() > 0) {
                        echo "WARNING: ${criticalIssues.size()} critical issues found"
                        currentBuild.result = 'UNSTABLE'

                        // Envoyer notification
                        sh """
                            curl -X POST ${SLACK_WEBHOOK} \
                                -H 'Content-Type: application/json' \
                                -d '{
                                    "text": "⚠️ LDAP Audit: ${criticalIssues.size()} critical issues",
                                    "attachments": [{
                                        "color": "danger",
                                        "text": "Build: ${env.BUILD_URL}"
                                    }]
                                }'
                        """
                    }

                    // Publier les métriques
                    echo "Total users: ${results.users.total}"
                    echo "Active users: ${results.users.active}"
                    echo "Groups: ${results.groups.total}"
                }
            }
        }

        stage('Archive Reports') {
            steps {
                archiveArtifacts artifacts: 'audit-*.json,audit-*.html',
                                 fingerprint: true

                publishHTML([
                    reportDir: '.',
                    reportFiles: 'audit-report.html',
                    reportName: 'LDAP Audit Report'
                ])
            }
        }

        stage('Cleanup') {
            steps {
                sh 'ldap-monitor cleanup dry-run'
            }
        }
    }

    post {
        always {
            // Toujours archiver les résultats
            archiveArtifacts artifacts: '**/audit-*.json', allowEmptyArchive: true
        }

        success {
            echo 'LDAP Audit completed successfully'
        }

        failure {
            // Notification en cas d'échec
            sh """
                curl -X POST ${SLACK_WEBHOOK} \
                    -H 'Content-Type: application/json' \
                    -d '{
                        "text": "❌ LDAP Audit Pipeline FAILED",
                        "attachments": [{
                            "color": "danger",
                            "fields": [
                                {"title": "Job", "value": "${env.JOB_NAME}"},
                                {"title": "Build", "value": "${env.BUILD_NUMBER}"}
                            ]
                        }]
                    }'
            """
        }
    }
}
```

### Pipeline multi-branches

```groovy
pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['dev', 'staging', 'production'],
            description: 'Target environment'
        )
        choice(
            name: 'AUDIT_TYPE',
            choices: ['health', 'users', 'groups', 'security', 'all'],
            description: 'Type of audit to run'
        )
    }

    stages {
        stage('Audit') {
            steps {
                script {
                    withCredentials([
                        string(credentialsId: "ldap-${params.ENVIRONMENT}-password", variable: 'LDAP_PWD')
                    ]) {
                        sh """
                            export LDAP_PASSWORD=\$LDAP_PWD
                            ldap-monitor audit ${params.AUDIT_TYPE} \
                                --config config/${params.ENVIRONMENT}.yaml \
                                --output audit-${params.ENVIRONMENT}.json
                        """
                    }
                }
            }
        }
    }
}
```

## ⭕ CircleCI

**`.circleci/config.yml` :**

```yaml
version: 2.1

executors:
  python-executor:
    docker:
      - image: cimg/python:3.11
    working_directory: ~/project

jobs:
  ldap-audit:
    executor: python-executor

    steps:
      - checkout

      - restore_cache:
          keys:
            - deps-{{ checksum "requirements.txt" }}

      - run:
          name: Install LDAP Monitor
          command: |
            pip install ldap-health-monitor

      - save_cache:
          key: deps-{{ checksum "requirements.txt" }}
          paths:
            - ~/.cache/pip

      - run:
          name: Configure
          command: |
            cp config/ldap-monitor.yml config.yaml
            echo "LDAP_PASSWORD=$LDAP_PASSWORD" > .env

      - run:
          name: Test Connection
          command: ldap-monitor test connection

      - run:
          name: Run Audit
          command: |
            ldap-monitor audit all \
              --format json \
              --output /tmp/audit-results.json

      - run:
          name: Generate Report
          command: |
            ldap-monitor audit all \
              --format html \
              --output /tmp/audit-report.html

      - store_artifacts:
          path: /tmp/audit-results.json
          destination: audit-results

      - store_artifacts:
          path: /tmp/audit-report.html
          destination: audit-report

      - store_test_results:
          path: /tmp/audit-results.json

workflows:
  version: 2

  # Workflow quotidien
  daily-audit:
    triggers:
      - schedule:
          cron: "0 9 * * *"
          filters:
            branches:
              only: main

    jobs:
      - ldap-audit:
          context: ldap-credentials

  # Workflow sur commit
  commit-audit:
    jobs:
      - ldap-audit:
          context: ldap-credentials
          filters:
            branches:
              only:
                - main
                - develop
```

## 🔵 Azure Pipelines

**`azure-pipelines.yml` :**

```yaml
trigger:
  branches:
    include:
      - main
      - develop
  paths:
    include:
      - ldap/**
      - config/**

schedules:
  - cron: "0 9 * * *"
    displayName: Daily LDAP Audit
    branches:
      include:
        - main
    always: true

pool:
  vmImage: 'ubuntu-latest'

variables:
  - group: ldap-credentials
  - name: pythonVersion
    value: '3.11'

stages:
  - stage: Validate
    displayName: 'Validate Configuration'
    jobs:
      - job: ValidateConfig
        displayName: 'Validate LDAP Config'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - script: |
              pip install ldap-health-monitor
            displayName: 'Install LDAP Monitor'

          - script: |
              ldap-monitor config validate
            displayName: 'Validate Configuration'

  - stage: Audit
    displayName: 'LDAP Audit'
    dependsOn: Validate
    jobs:
      - job: RunAudit
        displayName: 'Run LDAP Audit'
        steps:
          - task: UsePythonVersion@0
            inputs:
              versionSpec: '$(pythonVersion)'

          - script: |
              pip install ldap-health-monitor
            displayName: 'Install Dependencies'

          - task: Bash@3
            displayName: 'Configure LDAP Monitor'
            env:
              LDAP_PASSWORD: $(ldap-password)
            inputs:
              targetType: 'inline'
              script: |
                cp config/ldap-monitor.yml config.yaml
                echo "LDAP_PASSWORD=$LDAP_PASSWORD" > .env

          - script: |
              ldap-monitor test connection
            displayName: 'Test LDAP Connection'

          - script: |
              ldap-monitor audit all \
                --format json \
                --output $(Build.ArtifactStagingDirectory)/audit-results.json
            displayName: 'Run LDAP Audit'

          - script: |
              ldap-monitor audit all \
                --format html \
                --output $(Build.ArtifactStagingDirectory)/audit-report.html
            displayName: 'Generate HTML Report'

          - task: PublishBuildArtifacts@1
            inputs:
              pathToPublish: '$(Build.ArtifactStagingDirectory)'
              artifactName: 'ldap-audit-reports'

          - task: PublishTestResults@2
            inputs:
              testResultsFormat: 'JUnit'
              testResultsFiles: '**/audit-results.json'

  - stage: Notify
    displayName: 'Send Notifications'
    dependsOn: Audit
    condition: always()
    jobs:
      - job: SendNotifications
        displayName: 'Send Audit Notifications'
        steps:
          - task: Bash@3
            displayName: 'Send Slack Notification'
            env:
              SLACK_WEBHOOK: $(slack-webhook-url)
            inputs:
              targetType: 'inline'
              script: |
                curl -X POST $SLACK_WEBHOOK \
                  -H 'Content-Type: application/json' \
                  -d '{
                    "text": "LDAP Audit completed",
                    "attachments": [{
                      "color": "good",
                      "text": "Build: $(Build.BuildNumber)"
                    }]
                  }'
```

## 🔷 Bitbucket Pipelines

**`bitbucket-pipelines.yml` :**

```yaml
image: python:3.11

definitions:
  caches:
    pip: ~/.cache/pip

  steps:
    - step: &ldap-audit
        name: LDAP Audit
        caches:
          - pip
        script:
          - pip install ldap-health-monitor
          - cp config/ldap-monitor.yml config.yaml
          - echo "LDAP_PASSWORD=$LDAP_PASSWORD" > .env
          - ldap-monitor test connection
          - ldap-monitor audit all --format json --output audit-results.json
          - ldap-monitor audit all --format html --output audit-report.html
        artifacts:
          - audit-results.json
          - audit-report.html

pipelines:
  default:
    - step: *ldap-audit

  branches:
    main:
      - step: *ldap-audit

  pull-requests:
    '**':
      - step:
          name: Validate Configuration
          script:
            - pip install ldap-health-monitor
            - ldap-monitor config validate

  custom:
    production-audit:
      - step:
          name: Production LDAP Audit
          deployment: production
          script:
            - pip install ldap-health-monitor
            - export LDAP_PASSWORD=$LDAP_PROD_PASSWORD
            - ldap-monitor audit all --notify

  schedules:
    daily-audit:
      - cron: '0 9 * * *'
      - step: *ldap-audit
```

## 🐳 Configuration Docker

### Dockerfile pour CI/CD

**`Dockerfile.ci` :**

```dockerfile
FROM python:3.11-slim

# Métadonnées
LABEL maintainer="admin@example.com"
LABEL description="LDAP Health Monitor for CI/CD"

# Variables d'environnement
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Dépendances système
RUN apt-get update && apt-get install -y \
    build-essential \
    libldap2-dev \
    libsasl2-dev \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Installer LDAP Monitor
RUN pip install --upgrade pip
RUN pip install ldap-health-monitor

# Répertoire de travail
WORKDIR /workspace

# Point d'entrée
ENTRYPOINT ["ldap-monitor"]
CMD ["--help"]
```

**Utilisation dans CI/CD :**

```yaml
# GitHub Actions
- name: Run audit in Docker
  run: |
    docker run --rm \
      -v $(pwd)/config.yaml:/workspace/config.yaml \
      -e LDAP_PASSWORD=${{ secrets.LDAP_PASSWORD }} \
      ldap-monitor:ci \
      audit all --format json

# GitLab CI
audit:
  image: ldap-monitor:ci
  script:
    - ldap-monitor audit all
```

## 💡 Exemples Avancés

### Validation Pre-commit

**`.pre-commit-config.yaml` :**

```yaml
repos:
  - repo: local
    hooks:
      - id: validate-ldap-config
        name: Validate LDAP Configuration
        entry: ldap-monitor config validate
        language: system
        pass_filenames: false
        files: ^config/.*\.ya?ml$

      - id: test-ldap-connection
        name: Test LDAP Connection
        entry: bash -c 'ldap-monitor test connection || echo "LDAP server unreachable"'
        language: system
        pass_filenames: false
        files: ^config/.*\.ya?ml$
```

### Matrix Testing

**GitHub Actions avec matrix :**

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
        ldap-server: ['openldap', 'active-directory']

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Test with ${{ matrix.ldap-server }}
        run: |
          pip install ldap-health-monitor
          ldap-monitor audit health \
            --config config/${{ matrix.ldap-server }}.yml
```

## ✅ Meilleures Pratiques

### 1. Sécurité des Secrets

```yaml
# ✅ BON - Utiliser les secrets de la plateforme
env:
  LDAP_PASSWORD: ${{ secrets.LDAP_PASSWORD }}

# ❌ MAUVAIS - Jamais en dur dans le code
env:
  LDAP_PASSWORD: "my-password"
```

### 2. Caching des Dépendances

```yaml
# GitHub Actions
- uses: actions/cache@v3
  with:
    path: ~/.cache/pip
    key: ${{ runner.os }}-pip-${{ hashFiles('**/requirements.txt') }}

# GitLab CI
cache:
  paths:
    - .pip-cache/
```

### 3. Artifacts et Rapports

```yaml
# Toujours sauvegarder les rapports
- uses: actions/upload-artifact@v4
  with:
    name: audit-report
    path: audit-report.html
    retention-days: 30
```

### 4. Notifications Conditionnelles

```yaml
# Notifier seulement en cas de problème
- name: Notify on failure
  if: failure()
  run: ldap-monitor notify slack
```

### 5. Tests Non-bloquants

```yaml
# Permettre l'échec sans bloquer le pipeline
- name: Security Audit
  continue-on-error: true
  run: ldap-monitor audit security
```

## 📚 Ressources

- [GitHub Actions Docs](https://docs.github.com/actions)
- [GitLab CI/CD](https://docs.gitlab.com/ee/ci/)
- [Jenkins Pipeline](https://www.jenkins.io/doc/book/pipeline/)
- [CircleCI Docs](https://circleci.com/docs/)

## 🔗 Liens Connexes

- [Configuration LDAP](../configuration/LDAP-Configuration.md)
- [Webhooks Integration](Webhooks.md)
- [Docker Deployment](../guides/Docker-Deployment.md)
- [Audit Features](../features/audit/Overview.md)
