.PHONY: menu help lint format clean dev dev-up dev-reset dev-build dev-deploy stop logs restart rebuild prod-up prod-down prod-rebuild

# Docker commands
COMPOSE_CMD = docker compose

# Default target
menu:
	@echo "Select command to run:"
	@echo "1) dev           - Start development environment"
	@echo "2) stop          - Stop all services"
	@echo "3) logs          - Show API logs"
	@echo "4) restart       - Restart API service"
	@echo "5) rebuild       - Rebuild and restart services"
	@echo "6) lint          - Run linting"
	@echo "7) format        - Format code"
	@echo "8) check         - Format + lint"
	@echo "9) lint-local    - Run linting locally"
	@echo "10) format-local - Format code locally"
	@echo "11) clean        - Clean cache files"
	@echo "12) db-up        - Start database only"
	@echo "13) dev-up       - Start development environment"
	@echo "14) dev-reset    - Reset dev environment (remove volumes/images)"
	@echo "15) dev-build    - Build dev image (no cache)"
	@echo "16) dev-deploy   - Deploy dev containers (force recreate)"
	@echo "17) prod-up      - Start production environment"
	@echo "18) prod-down    - Stop production environment"
	@echo "19) prod-rebuild - Rebuild production environment"
	@read -p "Enter choice [1-19]: " choice; \
	case $$choice in \
		1) make dev ;; \
		2) make stop ;; \
		3) make logs ;; \
		4) make restart ;; \
		5) make rebuild ;; \
		6) make lint ;; \
		7) make format ;; \
		8) make check ;; \
		9) make lint-local ;; \
		10) make format-local ;; \
		11) make clean ;; \
		12) make db-up ;; \
		13) make dev-up ;; \
		14) make dev-reset ;; \
		15) make dev-build ;; \
		16) make dev-deploy ;; \
		17) make prod-up ;; \
		18) make prod-down ;; \
		19) make prod-rebuild ;; \
		*) echo "Invalid choice!" ;; \
	esac

help: menu

# Development commands
dev:
	$(COMPOSE_CMD) up -d

dev-up:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d

dev-reset:
	$(COMPOSE_CMD) -f docker-compose.dev.yml down -v --remove-orphans
	docker system prune -a -f
	docker volume prune -f

dev-build:
	$(COMPOSE_CMD) -f docker-compose.dev.yml build --no-cache

dev-deploy:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d --force-recreate

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



# Run linting
lint:
	$(COMPOSE_CMD) exec api flake8 .
	$(COMPOSE_CMD) exec api mypy . --ignore-missing-imports

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
	mypy . --ignore-missing-imports

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