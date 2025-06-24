.PHONY: help test lint format clean docker-build docker-up docker-down

menu:
	@echo "Available commands:"; \
	select cmd in $$(make -qp | grep '^[a-z]' | cut -d: -f1 | sort); do \
		make $$cmd; \
		break; \
	done
# Default target
help:
	@echo "Available commands:"
	@echo "  dev          - Start development environment"
	@echo "  stop         - Stop all services"
	@echo "  logs         - Show API logs"
	@echo "  restart      - Restart API service"  
	@echo "  rebuild      - Rebuild and restart services"
	@echo "  test         - Run tests in Docker"
	@echo "  lint         - Run linting in Docker"
	@echo "  format       - Format code in Docker"
	@echo "  clean        - Clean cache files"
	@echo "  prod-up      - Start production environment"
	@echo "  prod-down    - Stop production environment"

# Development commands (aliases for Docker)
dev: docker-up

stop: docker-down

logs: docker-logs

restart: docker-restart

rebuild: docker-rebuild

# Run tests in Docker
test:
	$(COMPOSE_CMD) exec api pytest

# Run tests with coverage in Docker  
test-cov:
	$(COMPOSE_CMD) exec api pytest --cov=server --cov-report=html --cov-report=term

# Run linting in Docker
lint:
	$(COMPOSE_CMD) exec api flake8 server/
	$(COMPOSE_CMD) exec api mypy server/

# Format code in Docker
format:
	$(COMPOSE_CMD) exec api black server/
	$(COMPOSE_CMD) exec api isort server/

# Clean cache files
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# Docker commands
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null)
ifdef DOCKER_COMPOSE
    COMPOSE_CMD = docker-compose
else
    COMPOSE_CMD = docker compose
endif

docker-up:
	$(COMPOSE_CMD) up -d

docker-down:
	$(COMPOSE_CMD) down

docker-logs:
	$(COMPOSE_CMD) logs -f api

docker-restart:
	$(COMPOSE_CMD) restart api

docker-rebuild:
	$(COMPOSE_CMD) up -d --build

# Production Docker commands
prod-up: docker-prod-up

prod-down: docker-prod-down

docker-prod-up:
	$(COMPOSE_CMD) -f docker-compose.prod.yml up -d

docker-prod-down:
	$(COMPOSE_CMD) -f docker-compose.prod.yml down

docker-prod-rebuild:
	$(COMPOSE_CMD) -f docker-compose.prod.yml up -d --build 