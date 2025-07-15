.PHONY: menu help test lint format clean dev stop logs restart rebuild prod-up prod-down prod-rebuild

# Docker commands
DOCKER_COMPOSE := $(shell command -v docker-compose 2> /dev/null)
ifdef DOCKER_COMPOSE
    COMPOSE_CMD = docker-compose
else
    COMPOSE_CMD = docker compose
endif

# Default target
menu:
	@echo "Select command to run:"
	@echo "1) dev           - Start development environment"
	@echo "2) stop          - Stop all services"
	@echo "3) logs          - Show API logs"
	@echo "4) restart       - Restart API service"
	@echo "5) rebuild       - Rebuild and restart services"
	@echo "6) test          - Run tests"
	@echo "7) test-cov      - Run tests with coverage"
	@echo "8) lint          - Run linting"
	@echo "9) format        - Format code"
	@echo "10) check        - Format + lint"
	@echo "11) lint-local   - Run linting locally"
	@echo "12) format-local - Format code locally"
	@echo "13) clean        - Clean cache files"
	@echo "14) db-up        - Start database only"
	@echo "15) install-deps - Install dependencies in container"
	@echo "16) prod-up      - Start production environment"
	@echo "17) prod-down    - Stop production environment"
	@echo "18) prod-rebuild - Rebuild production environment"
	@read -p "Enter choice [1-18]: " choice; \
	case $$choice in \
		1) make dev ;; \
		2) make stop ;; \
		3) make logs ;; \
		4) make restart ;; \
		5) make rebuild ;; \
		6) make test ;; \
		7) make test-cov ;; \
		8) make lint ;; \
		9) make format ;; \
		10) make check ;; \
		11) make lint-local ;; \
		12) make format-local ;; \
		13) make clean ;; \
		14) make db-up ;; \
		15) make install-deps ;; \
		16) make prod-up ;; \
		17) make prod-down ;; \
		18) make prod-rebuild ;; \
		*) echo "Invalid choice!" ;; \
	esac

help: menu

# Development commands
dev:
	$(COMPOSE_CMD) up -d

stop:
	$(COMPOSE_CMD) down

logs:
	$(COMPOSE_CMD) logs -f api

restart:
	$(COMPOSE_CMD) restart api

rebuild:
	$(COMPOSE_CMD) up -d --build

# Start database only
db-up:
	$(COMPOSE_CMD) up -d postgres

# Install dependencies in container
install-deps:
	docker exec -it server-api-1 pip install -r requirements.txt

# Run tests
test:
	$(COMPOSE_CMD) exec api pytest

# Run tests with coverage
test-cov:
	$(COMPOSE_CMD) exec api pytest --cov=server --cov-report=html --cov-report=term

# Run linting
lint:
	$(COMPOSE_CMD) exec api flake8 .
	$(COMPOSE_CMD) exec api mypy .

# Format code
format:
	$(COMPOSE_CMD) exec api black .
	$(COMPOSE_CMD) exec api isort .

# Check all (format + lint)
check: format lint
	@echo "Code formatting and linting completed!"

# Local linting (if you have tools installed locally)
lint-local:
	flake8 .
	mypy .

# Local formatting (if you have tools installed locally)  
format-local:
	black .
	isort .

# Clean cache files
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage

# Production commands
prod-up:
	$(COMPOSE_CMD) -f docker-compose.prod.yml up -d

prod-down:
	$(COMPOSE_CMD) -f docker-compose.prod.yml down

prod-rebuild:
	$(COMPOSE_CMD) -f docker-compose.prod.yml up -d --build 