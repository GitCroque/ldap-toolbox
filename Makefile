# Makefile for LDAP Health Monitor
# Compatible with macOS and Linux

.PHONY: help install install-dev test lint format clean audit backup monitor setup-cron docs

# Default config path
CONFIG ?= config.yaml

# Colors for output (works on macOS and Linux)
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m  # No Color

help:  ## Show this help message
	@echo "$(BLUE)LDAP Health Monitor - Make Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Environment variables:$(NC)"
	@echo "  CONFIG - Path to config file (default: config.yaml)"
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make install"
	@echo "  make test"
	@echo "  make audit CONFIG=myconfig.yaml"

install:  ## Install the package
	@echo "$(BLUE)Installing LDAP Health Monitor...$(NC)"
	pip install -e .
	@echo "$(GREEN)✓ Installation complete$(NC)"

install-dev:  ## Install with development dependencies
	@echo "$(BLUE)Installing with development dependencies...$(NC)"
	pip install -e ".[dev]"
	@echo "$(GREEN)✓ Development installation complete$(NC)"

test:  ## Run tests
	@echo "$(BLUE)Running tests...$(NC)"
	pytest tests/ -v
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-cov:  ## Run tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	pytest tests/ -v --cov=src --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report: htmlcov/index.html$(NC)"

lint:  ## Run linting checks
	@echo "$(BLUE)Running linters...$(NC)"
	@echo "Checking with ruff..."
	@ruff check src/ || true
	@echo "Checking with mypy..."
	@mypy src/ || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

format:  ## Format code with black
	@echo "$(BLUE)Formatting code with black...$(NC)"
	@black src/ tests/
	@echo "$(GREEN)✓ Code formatted$(NC)"

clean:  ## Clean up generated files
	@echo "$(BLUE)Cleaning up...$(NC)"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@rm -rf build/ dist/ .pytest_cache/ .mypy_cache/ .ruff_cache/ htmlcov/ .coverage
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

# LDAP Operations
config-init:  ## Initialize configuration file
	@echo "$(BLUE)Initializing configuration...$(NC)"
	@ldap-monitor config init
	@echo "$(GREEN)✓ Created config.yaml$(NC)"
	@echo "$(YELLOW)Please edit config.yaml with your LDAP settings$(NC)"

config-validate:  ## Validate configuration
	@echo "$(BLUE)Validating configuration...$(NC)"
	@ldap-monitor --config $(CONFIG) config validate
	@echo "$(GREEN)✓ Configuration is valid$(NC)"

test-connection:  ## Test LDAP connection
	@echo "$(BLUE)Testing LDAP connection...$(NC)"
	@ldap-monitor --config $(CONFIG) test connection

audit:  ## Run full LDAP audit
	@echo "$(BLUE)Running full LDAP audit...$(NC)"
	@ldap-monitor --config $(CONFIG) audit all --format html --output reports/audit-$$(date +%Y%m%d).html
	@echo "$(GREEN)✓ Audit complete: reports/audit-$$(date +%Y%m%d).html$(NC)"

audit-users:  ## Audit users only
	@echo "$(BLUE)Auditing users...$(NC)"
	@ldap-monitor --config $(CONFIG) audit users

audit-groups:  ## Audit groups only
	@echo "$(BLUE)Auditing groups...$(NC)"
	@ldap-monitor --config $(CONFIG) audit groups

audit-health:  ## Check LDAP server health
	@echo "$(BLUE)Checking LDAP health...$(NC)"
	@ldap-monitor --config $(CONFIG) audit health

backup:  ## Create full LDAP backup
	@echo "$(BLUE)Creating LDAP backup...$(NC)"
	@mkdir -p backups
	@ldap-monitor --config $(CONFIG) backup full --output backups/backup-$$(date +%Y%m%d_%H%M%S).ldif
	@echo "$(GREEN)✓ Backup created$(NC)"

backup-json:  ## Create JSON backup
	@echo "$(BLUE)Creating JSON backup...$(NC)"
	@mkdir -p backups
	@ldap-monitor --config $(CONFIG) backup full --output backups/backup-$$(date +%Y%m%d_%H%M%S).json --format json
	@echo "$(GREEN)✓ JSON backup created$(NC)"

export-users:  ## Export users to CSV
	@echo "$(BLUE)Exporting users to CSV...$(NC)"
	@mkdir -p exports
	@ldap-monitor --config $(CONFIG) export users --output exports/users-$$(date +%Y%m%d).csv --format csv
	@echo "$(GREEN)✓ Users exported$(NC)"

monitor-start:  ## Start monitoring daemon
	@echo "$(BLUE)Starting monitoring daemon...$(NC)"
	@./examples/scripts/monitor-daemon.sh start $(CONFIG)

monitor-stop:  ## Stop monitoring daemon
	@echo "$(BLUE)Stopping monitoring daemon...$(NC)"
	@./examples/scripts/monitor-daemon.sh stop

monitor-status:  ## Show monitoring daemon status
	@./examples/scripts/monitor-daemon.sh status

monitor-metrics:  ## Show current metrics
	@echo "$(BLUE)Current LDAP metrics:$(NC)"
	@ldap-monitor --config $(CONFIG) monitor metrics

cleanup-dry-run:  ## Run cleanup in dry-run mode
	@echo "$(BLUE)Running cleanup analysis (dry-run)...$(NC)"
	@ldap-monitor --config $(CONFIG) cleanup dry-run

cleanup:  ## Run cleanup (with confirmation)
	@echo "$(YELLOW)⚠️  This will modify your LDAP directory$(NC)"
	@echo "Backup will be created automatically"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		echo "$(BLUE)Running cleanup...$(NC)"; \
		ldap-monitor --config $(CONFIG) cleanup empty-groups --confirm; \
	fi

# Automation Setup
setup-cron:  ## Setup automated tasks (cron/launchd)
	@echo "$(BLUE)Setting up automated tasks...$(NC)"
	@chmod +x examples/scripts/*.sh
	@./examples/scripts/setup-cron.sh install
	@echo "$(GREEN)✓ Automated tasks configured$(NC)"

remove-cron:  ## Remove automated tasks
	@echo "$(BLUE)Removing automated tasks...$(NC)"
	@./examples/scripts/setup-cron.sh uninstall
	@echo "$(GREEN)✓ Automated tasks removed$(NC)"

# Development
dev-setup:  ## Setup development environment
	@echo "$(BLUE)Setting up development environment...$(NC)"
	@make install-dev
	@pre-commit install || echo "$(YELLOW)pre-commit not available$(NC)"
	@mkdir -p logs backups reports exports
	@echo "$(GREEN)✓ Development environment ready$(NC)"

run-daily-audit:  ## Run daily audit script
	@echo "$(BLUE)Running daily audit script...$(NC)"
	@./examples/scripts/daily-audit.sh $(CONFIG)

run-backup:  ## Run backup script
	@echo "$(BLUE)Running backup script...$(NC)"
	@./examples/scripts/auto-backup.sh $(CONFIG)

run-cleanup:  ## Run cleanup script (dry-run)
	@echo "$(BLUE)Running cleanup script (dry-run)...$(NC)"
	@DRY_RUN=true ./examples/scripts/auto-cleanup.sh $(CONFIG)

# Documentation
docs:  ## Open documentation
	@echo "$(BLUE)Opening documentation...$(NC)"
	@if command -v open > /dev/null; then \
		open README.md; \
	elif command -v xdg-open > /dev/null; then \
		xdg-open README.md; \
	else \
		echo "$(YELLOW)Please open README.md manually$(NC)"; \
	fi

wiki:  ## Open wiki documentation
	@echo "$(BLUE)Opening wiki...$(NC)"
	@if command -v open > /dev/null; then \
		open wiki/Home.md; \
	elif command -v xdg-open > /dev/null; then \
		xdg-open wiki/Home.md; \
	else \
		echo "$(YELLOW)Please open wiki/Home.md manually$(NC)"; \
	fi

# Docker (optional)
docker-build:  ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	@docker build -t ldap-health-monitor .
	@echo "$(GREEN)✓ Docker image built$(NC)"

docker-run:  ## Run in Docker
	@echo "$(BLUE)Running in Docker...$(NC)"
	@docker run -v $$(pwd)/$(CONFIG):/app/config.yaml ldap-health-monitor audit health

# Distribution
build:  ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	@python -m build
	@echo "$(GREEN)✓ Packages built in dist/$(NC)"

publish-test:  ## Publish to TestPyPI
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	@python -m twine upload --repository testpypi dist/*

publish:  ## Publish to PyPI
	@echo "$(YELLOW)⚠️  Publishing to PyPI$(NC)"
	@read -p "Continue? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python -m twine upload dist/*; \
	fi

# Quick commands
quick-audit: test-connection audit-health audit-users audit-groups  ## Quick comprehensive audit

quick-check: config-validate test-connection  ## Quick configuration check

.DEFAULT_GOAL := help
