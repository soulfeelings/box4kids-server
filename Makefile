.PHONY: menu dev-up dev-reset dev-build dev-deploy dev-stop db-up prod-up prod-stop migrate

# Ensure bash is used for interactive menu/read
SHELL := /bin/bash

# Docker commands
COMPOSE_CMD = docker compose

# Default target
menu:
	@echo "Select command to run:"
	@echo "1) dev-up        - Start development environment"
	@echo "2) dev-stop      - Stop all services"
	@echo "3) dev-reset     - Reset dev environment (remove volumes/images)"
	@echo "4) dev-build     - Build dev image (no cache)"
	@echo "5) dev-deploy    - Deploy dev containers (force recreate)"
	@echo "6) db-up         - Start database only"
	@echo "7) prod-up       - Start production environment"
	@echo "8) prod-stop     - Stop production environment"
	@echo "9) migrate       - Run database migrations"
	@read -p "Enter choice [1-9]: " choice; \
	case $$choice in \
		1) make dev-up ;; \
		2) make dev-stop ;; \
		3) make dev-reset ;; \
		4) make dev-build ;; \
		5) make dev-deploy ;; \
		6) make db-up ;; \
		7) make prod-up ;; \
		8) make prod-stop ;; \
		9) make migrate ;; \
		*) echo "Invalid choice!" ;; \
	esac

dev-up:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d

dev-reset:
	$(COMPOSE_CMD) -f docker-compose.dev.yml down -v --remove-orphans
	docker image prune -f --filter label=com.docker.compose.project=server
	docker volume prune -f --filter label=com.docker.compose.project=server

dev-build:
	$(COMPOSE_CMD) -f docker-compose.dev.yml build --no-cache --pull

dev-deploy:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d --force-recreate --remove-orphans

dev-stop:
	$(COMPOSE_CMD) -f docker-compose.dev.yml down

# Start database only
db-up:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d postgres

# Production commands
prod-up:
	@if [ -f docker-compose.prod.yml ]; then \
		$(COMPOSE_CMD) -f docker-compose.prod.yml up -d; \
	else \
		echo "docker-compose.prod.yml not found. Create it or use: make dev-up"; \
	fi

prod-stop:
	@if [ -f docker-compose.prod.yml ]; then \
		$(COMPOSE_CMD) -f docker-compose.prod.yml down; \
	else \
		echo "docker-compose.prod.yml not found. Nothing to stop."; \
	fi

# Database migrations
migrate:
	alembic upgrade head

# Generate new migration
migration:
	alembic revision --autogenerate -m "$(MESSAGE)"
 