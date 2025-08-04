.PHONY: menu dev-up dev-reset dev-build dev-deploy dev-stop db-up

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
	@read -p "Enter choice [1-15]: " choice; \
	case $$choice in \
		1) make dev-up ;; \
		2) make dev-stop ;; \
		3) make dev-reset ;; \
		4) make dev-build ;; \
		5) make dev-deploy ;; \
		6) make db-up ;; \
		*) echo "Invalid choice!" ;; \
	esac

dev-up:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d

dev-reset:
	$(COMPOSE_CMD) -f docker-compose.dev.yml down -v --remove-orphans
	docker image prune -f --filter label=com.docker.compose.project=server
	docker volume prune -f --filter label=com.docker.compose.project=server

dev-build:
	$(COMPOSE_CMD) -f docker-compose.dev.yml build --no-cache

dev-deploy:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d --force-recreate

dev-stop:
	$(COMPOSE_CMD) -f docker-compose.dev.yml down

# Start database only
db-up:
	$(COMPOSE_CMD) -f docker-compose.dev.yml up -d postgres


 