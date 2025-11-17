# Installation Complète

Ce guide détaille toutes les méthodes d'installation de LDAP Health Monitor.

## 📋 Prérequis

### Système d'Exploitation

LDAP Health Monitor est compatible avec :
- ✅ **macOS** 10.14+ (priorité)
- ✅ **Linux** (Ubuntu 20.04+, Debian 10+, CentOS 8+, RHEL 8+)
- ✅ **Windows** 10/11 (via WSL2 recommandé)

### Python

**Version requise** : Python 3.10 ou supérieur

Vérifiez votre version :
```bash
python3 --version
```

Si Python n'est pas installé :

**macOS :**
```bash
# Avec Homebrew (recommandé)
brew install python@3.11

# Ou télécharger depuis python.org
```

**Linux (Ubuntu/Debian) :**
```bash
sudo apt update
sudo apt install python3.11 python3.11-venv python3-pip
```

**Linux (RHEL/CentOS) :**
```bash
sudo dnf install python3.11 python3-pip
```

### Dépendances Système

**macOS :**
```bash
# OpenSSL pour connexions sécurisées
brew install openssl

# Optionnel mais recommandé
brew install git
```

**Linux (Ubuntu/Debian) :**
```bash
sudo apt install -y \
    build-essential \
    libssl-dev \
    libsasl2-dev \
    python3-dev \
    libldap2-dev
```

**Linux (RHEL/CentOS) :**
```bash
sudo dnf install -y \
    gcc \
    openssl-devel \
    python3-devel \
    openldap-devel
```

## 🚀 Méthodes d'Installation

### Méthode 1 : Via pip (Recommandé pour Développement)

**Avantages :**
- ✅ Installation rapide
- ✅ Mise à jour facile
- ✅ Gestion des dépendances automatique

**Installation :**
```bash
# Installation globale (nécessite sudo sur certains systèmes)
pip install ldap-health-monitor

# Ou pour l'utilisateur courant
pip install --user ldap-health-monitor
```

**Mise à jour :**
```bash
pip install --upgrade ldap-health-monitor
```

**Vérification :**
```bash
ldap-monitor --version
ldap-monitor --help
```

### Méthode 2 : Via pipx (Recommandé pour Utilisateurs)

**Avantages :**
- ✅ Installation isolée (pas de conflit de dépendances)
- ✅ Commande disponible globalement
- ✅ Facile à désinstaller

**Installation de pipx :**

**macOS :**
```bash
brew install pipx
pipx ensurepath
```

**Linux :**
```bash
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

**Installation de ldap-monitor :**
```bash
pipx install ldap-health-monitor
```

**Mise à jour :**
```bash
pipx upgrade ldap-health-monitor
```

**Désinstallation :**
```bash
pipx uninstall ldap-health-monitor
```

### Méthode 3 : Depuis les Sources (Développement)

**Avantages :**
- ✅ Version latest
- ✅ Modifications du code possibles
- ✅ Contribution au projet

**Clonage du dépôt :**
```bash
git clone https://github.com/yourusername/ldap-health-monitor.git
cd ldap-health-monitor
```

**Création d'un environnement virtuel :**
```bash
# Créer l'environnement
python3 -m venv venv

# Activer l'environnement
# macOS/Linux :
source venv/bin/activate

# Windows (WSL) :
source venv/bin/activate
```

**Installation en mode développement :**
```bash
# Installation des dépendances de base
pip install -e .

# Ou avec les dépendances de développement
pip install -e ".[dev]"
```

**Vérification :**
```bash
ldap-monitor --version
```

### Méthode 4 : Via Docker (Expérimental)

**Avantages :**
- ✅ Environnement isolé
- ✅ Pas de dépendances système
- ✅ Reproductible

**Dockerfile (à créer) :**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libldap2-dev \
    libsasl2-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install -e .

ENTRYPOINT ["ldap-monitor"]
```

**Build et utilisation :**
```bash
# Build
docker build -t ldap-monitor .

# Utilisation
docker run -v $(pwd)/config.yaml:/app/config.yaml ldap-monitor audit health
```

## 🔧 Configuration Post-Installation

### 1. Vérifier l'installation

```bash
# Version
ldap-monitor --version

# Aide
ldap-monitor --help

# Liste des commandes
ldap-monitor config --help
ldap-monitor audit --help
```

### 2. Créer les répertoires de travail

```bash
# Créer la structure
mkdir -p ~/.config/ldap-monitor
mkdir -p ~/ldap-monitor/{backups,reports,logs}

# Ou laisser l'outil les créer automatiquement
```

### 3. Initialiser la configuration

```bash
# Créer config.yaml
ldap-monitor config init

# Ou spécifier un chemin
ldap-monitor config init --output ~/.config/ldap-monitor/config.yaml
```

### 4. Copier l'exemple d'environnement

```bash
# Si installé depuis les sources
cp .env.example .env

# Sinon, créer .env manuellement
cat > .env << EOF
LDAP_PASSWORD=your-password
SLACK_WEBHOOK=
SMTP_PASSWORD=
EOF
```

## 🧪 Test de l'Installation

### Test rapide

```bash
# Tester la connexion (nécessite config.yaml configuré)
ldap-monitor test connection

# Si pas encore configuré, tester juste la commande
ldap-monitor --version
```

### Test complet

```bash
# 1. Vérifier toutes les dépendances
python3 -c "import ldap3, click, rich, pydantic; print('✅ All imports OK')"

# 2. Valider la configuration
ldap-monitor config validate

# 3. Tester la connexion LDAP
ldap-monitor test connection

# 4. Faire un audit simple
ldap-monitor audit health
```

## ❌ Désinstallation

### Via pip

```bash
pip uninstall ldap-health-monitor
```

### Via pipx

```bash
pipx uninstall ldap-health-monitor
```

### Installation depuis sources

```bash
# Si installé avec pip install -e .
pip uninstall ldap-health-monitor

# Supprimer le dossier
rm -rf ldap-health-monitor/
```

### Nettoyage complet

```bash
# Supprimer les fichiers de configuration
rm -rf ~/.config/ldap-monitor/

# Supprimer les données
rm -rf ~/ldap-monitor/
```

## 🐛 Problèmes Courants d'Installation

### Erreur : "command not found: ldap-monitor"

**Solution :**
```bash
# Vérifier que le PATH est correct
echo $PATH

# Ajouter au PATH (bash)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc

# Ajouter au PATH (zsh - macOS)
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Erreur : "ModuleNotFoundError: No module named 'ldap3'"

**Solution :**
```bash
# Réinstaller les dépendances
pip install -r requirements.txt

# Ou réinstaller le package
pip install --force-reinstall ldap-health-monitor
```

### Erreur de compilation (macOS) : "fatal error: 'sasl/sasl.h' file not found"

**Solution :**
```bash
# Installer les dépendances système
brew install openssl libsasl2

# Définir les flags de compilation
export LDFLAGS="-L$(brew --prefix openssl)/lib"
export CPPFLAGS="-I$(brew --prefix openssl)/include"

# Réinstaller
pip install --no-cache-dir ldap-health-monitor
```

### Erreur (Linux) : "error: command 'gcc' failed"

**Solution :**
```bash
# Ubuntu/Debian
sudo apt install build-essential python3-dev libldap2-dev libsasl2-dev

# RHEL/CentOS
sudo dnf install gcc python3-devel openldap-devel
```

### Permission denied

**Solution :**
```bash
# Installer pour l'utilisateur courant
pip install --user ldap-health-monitor

# Ou utiliser pipx (recommandé)
pipx install ldap-health-monitor
```

## 📚 Prochaines Étapes

Après l'installation :

1. 📖 [Configuration Initiale](Initial-Configuration.md)
2. 🚀 [Quick Start Guide](Quick-Start.md)
3. 🔍 [Test de Connexion](Testing-Connection.md)

## 🆘 Besoin d'Aide ?

- 📖 [FAQ](../troubleshooting/FAQ.md)
- 🐛 [Troubleshooting](../troubleshooting/Common-Errors.md)
- 💬 [GitHub Issues](https://github.com/yourusername/ldap-health-monitor/issues)
