# Makefile for i9 Smart Campaigns API
# Author: Lee Chardes
# Date: 2025-01-22

.PHONY: help venv install install-dev clean clean-cache test test-cov run dev migrate db-up db-down docker-up docker-down lint format security docs
.PHONY: gen-images setup-ssh deploy-homolog deploy-production deploy-status deploy-logs deploy-restart deploy-shell deploy-ssh deploy-info deploy-clean

# Colors for output
CYAN=\033[0;36m
GREEN=\033[0;32m
YELLOW=\033[1;33m
RED=\033[0;31m
NC=\033[0m # No Color

# Python and environment
PYTHON = python3
VENV = .venv
VENV_ACTIVATE = . $(VENV)/bin/activate
PIP = $(VENV)/bin/pip
PYTHON_VENV = $(VENV)/bin/python
UVICORN = $(VENV)/bin/uvicorn
PYTEST = $(VENV)/bin/pytest
ALEMBIC = $(VENV)/bin/alembic
BLACK = $(VENV)/bin/black
FLAKE8 = $(VENV)/bin/flake8
MYPY = $(VENV)/bin/mypy
PIP_COMPILE = $(VENV)/bin/pip-compile
SAFETY = $(VENV)/bin/safety

# Application
APP_MODULE = app.main:app
HOST = 0.0.0.0
PORT = 8000

help: ## Show this help message
	@echo "$(CYAN)Available commands:$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(YELLOW)Examples:$(NC)"
	@echo "  make install        # Setup complete environment"
	@echo "  make dev            # Run development server"
	@echo "  make test           # Run all tests"
	@echo "  make docker-up      # Start all services with Docker"

# Environment setup
venv: ## Create virtual environment
	@echo "$(CYAN)Creating virtual environment...$(NC)"
	@$(PYTHON) -m venv $(VENV)
	@echo "$(GREEN)✓ Virtual environment created$(NC)"

install: venv ## Install production dependencies
	@echo "$(CYAN)Installing dependencies...$(NC)"
	@$(PIP) install --upgrade pip setuptools wheel
	@if [ -f requirements.txt ]; then \
		$(PIP) install -r requirements.txt; \
	elif [ -f requirements.in ]; then \
		$(PIP) install pip-tools && \
		$(PIP_COMPILE) requirements.in && \
		$(PIP) install -r requirements.txt; \
	else \
		echo "$(RED)No requirements file found!$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(CYAN)Installing development dependencies...$(NC)"
	@if [ -f requirements-dev.txt ]; then \
		$(PIP) install -r requirements-dev.txt; \
	else \
		$(PIP) install pytest pytest-cov pytest-asyncio black flake8 mypy safety bandit; \
	fi
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"

requirements: ## Compile requirements from requirements.in
	@echo "$(CYAN)Compiling requirements...$(NC)"
	@$(VENV_ACTIVATE) && pip-compile requirements.in
	@echo "$(GREEN)✓ Requirements compiled$(NC)"

# Cleaning
clean: ## Remove Python cache files
	@echo "$(CYAN)Cleaning Python cache...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cache cleaned$(NC)"

clean-all: clean ## Remove venv and all generated files
	@echo "$(CYAN)Removing virtual environment...$(NC)"
	@rm -rf $(VENV)
	@rm -rf htmlcov/
	@rm -rf logs/
	@rm -rf static/uploads/
	@echo "$(GREEN)✓ All cleaned$(NC)"

# Development
run: ## Run production server
	@echo "$(CYAN)Starting production server...$(NC)"
	@$(UVICORN) $(APP_MODULE) --host $(HOST) --port $(PORT)

dev: ## Run development server with reload
	@echo "$(CYAN)Starting development server...$(NC)"
	@$(UVICORN) $(APP_MODULE) --reload --host $(HOST) --port $(PORT)

shell: ## Start Python shell with app context
	@echo "$(CYAN)Starting Python shell...$(NC)"
	@$(PYTHON_VENV) -i -c "from app.main import app; from app.config.settings import settings; print('App and settings loaded')"

# Database
migrate: ## Run database migrations
	@echo "$(CYAN)Running migrations...$(NC)"
	@$(ALEMBIC) upgrade head
	@echo "$(GREEN)✓ Migrations completed$(NC)"

migrate-create: ## Create new migration (usage: make migrate-create name="add_users_table")
	@echo "$(CYAN)Creating migration...$(NC)"
	@$(ALEMBIC) revision --autogenerate -m "$(name)"
	@echo "$(GREEN)✓ Migration created$(NC)"

migrate-rollback: ## Rollback last migration
	@echo "$(CYAN)Rolling back migration...$(NC)"
	@$(ALEMBIC) downgrade -1
	@echo "$(GREEN)✓ Rollback completed$(NC)"

db-reset: ## Reset database (drop and recreate)
	@echo "$(YELLOW)⚠ This will delete all data! Press Ctrl+C to cancel...$(NC)"
	@sleep 3
	@echo "$(CYAN)Resetting database...$(NC)"
	@$(ALEMBIC) downgrade base
	@$(ALEMBIC) upgrade head
	@echo "$(GREEN)✓ Database reset$(NC)"

# Docker
docker-up: ## Start all services with Docker Compose
	@echo "$(CYAN)Starting Docker services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)✓ Services started$(NC)"
	@echo "$(CYAN)Services:$(NC)"
	@echo "  - API: http://localhost:$(PORT)"
	@echo "  - Docs: http://localhost:$(PORT)/docs"
	@echo "  - MinIO: http://localhost:9001"

docker-down: ## Stop all Docker services
	@echo "$(CYAN)Stopping Docker services...$(NC)"
	@docker-compose down
	@echo "$(GREEN)✓ Services stopped$(NC)"

docker-logs: ## Show Docker logs
	@docker-compose logs -f

docker-build: ## Build Docker image
	@echo "$(CYAN)Building Docker image...$(NC)"
	@docker build -t i9-campaigns-api .
	@echo "$(GREEN)✓ Image built$(NC)"

# Testing
test: ## Run all tests
	@echo "$(CYAN)Running tests...$(NC)"
	@$(PYTEST) -v
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-cov: ## Run tests with coverage
	@echo "$(CYAN)Running tests with coverage...$(NC)"
	@$(PYTEST) --cov=app --cov-report=html --cov-report=term
	@echo "$(GREEN)✓ Coverage report generated$(NC)"
	@echo "$(CYAN)View report: open htmlcov/index.html$(NC)"

test-unit: ## Run unit tests only
	@echo "$(CYAN)Running unit tests...$(NC)"
	@$(PYTEST) tests/unit -v

test-integration: ## Run integration tests only
	@echo "$(CYAN)Running integration tests...$(NC)"
	@$(PYTEST) tests/integration -v

test-watch: ## Run tests in watch mode
	@echo "$(CYAN)Running tests in watch mode...$(NC)"
	@$(PYTEST) -v --watch

# Code quality
lint: ## Run linting checks
	@echo "$(CYAN)Running linting...$(NC)"
	@$(FLAKE8) app/ tests/ --max-line-length=120 --exclude=migrations
	@echo "$(GREEN)✓ Linting passed$(NC)"

format: ## Format code with black
	@echo "$(CYAN)Formatting code...$(NC)"
	@$(BLACK) app/ tests/ scripts/
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting
	@echo "$(CYAN)Checking code format...$(NC)"
	@$(BLACK) --check app/ tests/ scripts/
	@echo "$(GREEN)✓ Code format OK$(NC)"

type-check: ## Run type checking with mypy

gen-images: ## Generate baseline JPEGs in repo/ (usage: make gen-images count=3 width=1080 height=1076 prefix=campanha)
	@echo "$(CYAN)Generating test images in repo/...$(NC)"
	@$(PYTHON_VENV) scripts/gen_repo_images.py --count $${count:-3} --width $${width:-1080} --height $${height:-1076} --prefix $${prefix:-campanha_teste}
	@echo "$(GREEN)✓ Images generated in repo/$(NC)"
	@echo "$(CYAN)Running type checking...$(NC)"
	@$(MYPY) app/ --ignore-missing-imports
	@echo "$(GREEN)✓ Type checking passed$(NC)"

security: ## Run security checks
	@echo "$(CYAN)Running security checks...$(NC)"
	@$(SAFETY) check
	@$(VENV)/bin/bandit -r app/ -ll
	@echo "$(GREEN)✓ Security checks passed$(NC)"

quality: lint format-check type-check security ## Run all code quality checks

# Documentation
docs: ## Generate API documentation
	@echo "$(CYAN)Generating documentation...$(NC)"
	@echo "$(GREEN)✓ Docs available at:$(NC)"
	@echo "  - Swagger: http://localhost:$(PORT)/docs"
	@echo "  - ReDoc: http://localhost:$(PORT)/redoc"

# Utility
env-copy: ## Copy .env.example to .env
	@echo "$(CYAN)Creating .env file...$(NC)"
	@cp -n .env.example .env 2>/dev/null || echo "$(YELLOW).env already exists$(NC)"
	@echo "$(GREEN)✓ Edit .env with your settings$(NC)"

logs: ## Tail application logs
	@echo "$(CYAN)Showing logs...$(NC)"
	@tail -f logs/*.log 2>/dev/null || echo "$(YELLOW)No logs found$(NC)"

ps: ## Show running processes
	@echo "$(CYAN)Running processes:$(NC)"
	@ps aux | grep -E "(uvicorn|fastapi)" | grep -v grep || echo "$(YELLOW)No processes found$(NC)"

kill: ## Kill all FastAPI/Uvicorn processes
	@echo "$(CYAN)Killing processes...$(NC)"
	@pkill -f uvicorn || echo "$(YELLOW)No processes to kill$(NC)"
	@echo "$(GREEN)✓ Processes killed$(NC)"

# Git helpers
commit: ## Quick commit with message (usage: make commit m="your message")
	@git add -A
	@git commit -m "$(m)"
	@echo "$(GREEN)✓ Committed$(NC)"

push: ## Push to origin
	@git push origin $$(git rev-parse --abbrev-ref HEAD)
	@echo "$(GREEN)✓ Pushed$(NC)"

# Quick commands
setup: install env-copy docker-up migrate ## Complete project setup
	@echo "$(GREEN)✓ Project setup complete!$(NC)"
	@echo ""
	@echo "$(CYAN)Next steps:$(NC)"
	@echo "  1. Edit .env with your settings"
	@echo "  2. Run 'make dev' to start development server"
	@echo "  3. Visit http://localhost:$(PORT)/docs"

all: clean install test lint ## Clean, install, test and lint
	@echo "$(GREEN)✓ All tasks completed$(NC)"

# ================================================
# DEPLOY COMMANDS
# ================================================

setup-ssh: ## Configure SSH authentication for deploy (run once)
	@echo "$(CYAN)Configurando autenticação SSH...$(NC)"
	@chmod +x scripts/setup-ssh.sh
	@./scripts/setup-ssh.sh
	@echo "$(GREEN)✓ SSH configurado$(NC)"

deploy-development: ## Inicia servidor de desenvolvimento local
	@bash scripts/deploy.sh development

deploy-homolog: ## Deploy to homologation environment
	@echo "$(CYAN)Deploying to homologation...$(NC)"
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh homolog
	
deploy-production: ## Deploy to production environment
	@echo "$(RED)⚠ Deploying to PRODUCTION!$(NC)"
	@echo "$(YELLOW)Press Ctrl+C to cancel...$(NC)"
	@sleep 3
	@chmod +x scripts/deploy.sh
	@./scripts/deploy.sh production

deploy-status: ## Check deployment status
	@echo "$(CYAN)Checking deployment status...$(NC)"
	@if [ -f .env.deploy.homolog ]; then \
		. .env.deploy.homolog && \
		ssh -i "$$SSH_KEY" $$SSH_USER@$$SSH_HOST "docker ps --filter name=i9-feed --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"; \
	else \
		echo "$(RED)Run 'make setup-ssh' first$(NC)"; \
	fi

deploy-logs: ## Show deployment logs
	@echo "$(CYAN)Showing deployment logs...$(NC)"
	@if [ -f .env.deploy.homolog ]; then \
		. .env.deploy.homolog && \
		ssh -i "$$SSH_KEY" $$SSH_USER@$$SSH_HOST "docker logs -f --tail 100 i9-feed-api"; \
	else \
		echo "$(RED)Run 'make setup-ssh' first$(NC)"; \
	fi

deploy-restart: ## Restart deployed containers
	@echo "$(CYAN)Restarting containers...$(NC)"
	@if [ -f .env.deploy.homolog ]; then \
		. .env.deploy.homolog && \
		ssh -i "$$SSH_KEY" $$SSH_USER@$$SSH_HOST "docker restart i9-feed-api i9-feed-redis" && \
		echo "$(GREEN)✓ Containers restarted$(NC)"; \
	else \
		echo "$(RED)Run 'make setup-ssh' first$(NC)"; \
	fi

deploy-shell: ## Access deployed container shell
	@echo "$(CYAN)Accessing container shell...$(NC)"
	@if [ -f .env.deploy.homolog ]; then \
		. .env.deploy.homolog && \
		ssh -i "$$SSH_KEY" $$SSH_USER@$$SSH_HOST "docker exec -it i9-feed-api /bin/bash"; \
	else \
		echo "$(RED)Run 'make setup-ssh' first$(NC)"; \
	fi

deploy-ssh: ## SSH to deployment server
	@echo "$(CYAN)Connecting to deployment server...$(NC)"
	@if [ -f .env.deploy.homolog ]; then \
		. .env.deploy.homolog && \
		ssh -i "$$SSH_KEY" $$SSH_USER@$$SSH_HOST; \
	else \
		echo "$(RED)Run 'make setup-ssh' first$(NC)"; \
	fi

deploy-info: ## Show deployment configuration
	@echo "$(CYAN)Deployment Configuration:$(NC)"
	@if [ -f .env.deploy.homolog ]; then \
		. .env.deploy.homolog && \
		echo "  Server: $$SSH_HOST" && \
		echo "  User: $$SSH_USER" && \
		echo "  Key: $$SSH_KEY" && \
		echo "  Remote Dir: $$REMOTE_DIR" && \
		echo "" && \
		echo "$(CYAN)URLs:$(NC)" && \
		echo "  Homolog API: http://$$SSH_HOST:8001" && \
		echo "  Homolog Docs: http://$$SSH_HOST:8001/docs" && \
		echo "  Production API: http://172.16.2.90:8000" && \
		echo "  Production Docs: http://172.16.2.90:8000/docs"; \
	else \
		echo "$(RED)Run 'make setup-ssh' first$(NC)"; \
	fi

deploy-clean: ## Clean deployment artifacts
	@echo "$(CYAN)Cleaning deployment artifacts...$(NC)"
	@if [ -f .env.deploy.homolog ]; then \
		. .env.deploy.homolog && \
		ssh -i "$$SSH_KEY" $$SSH_USER@$$SSH_HOST "docker image prune -f && docker volume prune -f" && \
		echo "$(GREEN)✓ Cleanup completed$(NC)"; \
	else \
		echo "$(RED)Run 'make setup-ssh' first$(NC)"; \
	fi

.DEFAULT_GOAL := help

import-images: ## Import images from repo/ directory via API
	@$(PYTHON_VENV) scripts/bulk_import_repo_images.py
