# NanoBanana Inpainting Service Makefile
# Provides common development and operations tasks

.PHONY: help dev lint type test e2e load build-images scan up down clean install docs

# Default target
help: ## Show this help message
	@echo "NanoBanana Inpainting Service"
	@echo "Available commands:"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development commands
dev: ## Start development environment
	@echo "Starting development environment..."
	@make -j2 dev-backend dev-frontend

dev-backend: ## Start backend development server
	@echo "Starting backend..."
	cd backend && python -m uvicorn app.main:app --reload --port 8000

dev-frontend: ## Start frontend development server
	@echo "Starting frontend..."
	cd frontend && npm run dev

install: ## Install all dependencies
	@echo "Installing dependencies..."
	@make install-backend install-frontend install-test-deps

install-backend: ## Install backend dependencies
	cd backend && pip install -r requirements.txt && pip install -r requirements-observability.txt

install-frontend: ## Install frontend dependencies
	cd frontend && npm ci

install-test-deps: ## Install test dependencies
	cd tests-e2e && npm ci

# Code quality commands
lint: ## Run linting for all components
	@echo "Running linters..."
	@make lint-backend lint-frontend

lint-backend: ## Lint backend code
	cd backend && ruff check app/ tests/ && ruff format --check app/ tests/

lint-frontend: ## Lint frontend code
	cd frontend && npm run lint

type: ## Run type checking
	@echo "Running type checks..."
	@make type-backend type-frontend

type-backend: ## Type check backend
	cd backend && mypy app/ --ignore-missing-imports

type-frontend: ## Type check frontend
	cd frontend && npx tsc --noEmit

format: ## Format code
	@echo "Formatting code..."
	@make format-backend format-frontend

format-backend: ## Format backend code
	cd backend && ruff format app/ tests/

format-frontend: ## Format frontend code
	cd frontend && npm run lint:fix

# Testing commands
test: ## Run all tests
	@echo "Running all tests..."
	@make test-backend test-frontend

test-backend: ## Run backend tests
	cd backend && python -m pytest tests/ -v --cov=app

test-frontend: ## Run frontend tests
	cd frontend && npm test

e2e: ## Run end-to-end tests
	@echo "Running E2E tests..."
	@make ensure-services-running
	cd tests-e2e && npx playwright test

contract: ## Run contract tests
	@echo "Running contract tests..."
	@make ensure-backend-running
	cd tests-contract && bash run-tests.sh

load: ## Run load tests
	@echo "Running load tests..."
	@make ensure-backend-running
	cd tests-load && bash run-tests.sh

# Infrastructure commands
build-images: ## Build Docker images
	@echo "Building Docker images..."
	docker build -f docker/backend.Dockerfile -t nanobanana-backend:latest backend/
	docker build -f docker/frontend.Dockerfile -t nanobanana-frontend:latest frontend/

scan: ## Run security scans
	@echo "Running security scans..."
	@make scan-deps scan-images

scan-deps: ## Scan dependencies for vulnerabilities
	@echo "Scanning dependencies..."
	cd backend && pip-audit || true
	cd frontend && npm audit --audit-level=high || true

scan-images: ## Scan Docker images for vulnerabilities
	@echo "Scanning Docker images..."
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:latest image nanobanana-backend:latest || true
	docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:latest image nanobanana-frontend:latest || true

# Container orchestration
up: ## Start all services with Docker Compose
	@echo "Starting services..."
	docker-compose up -d
	@echo "Services started. Backend: http://localhost:8000, Frontend: http://localhost:5173"

down: ## Stop all services
	@echo "Stopping services..."
	docker-compose down

logs: ## Show service logs
	docker-compose logs -f

restart: ## Restart all services
	@make down
	@make up

# Utility commands
clean: ## Clean up build artifacts and caches
	@echo "Cleaning up..."
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.pyc" -delete 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "coverage" -type d -exec rm -rf {} + 2>/dev/null || true
	docker system prune -f 2>/dev/null || true

docs: ## Generate and serve documentation
	@echo "Serving documentation..."
	@echo "API Docs: http://localhost:8000/docs"
	@echo "Runbook: docs/runbook.md"
	@echo "README: README.md"

# Health checks
health: ## Check service health
	@echo "Checking service health..."
	@curl -f http://localhost:8000/api/health 2>/dev/null && echo "✓ Backend healthy" || echo "✗ Backend unhealthy"
	@curl -f http://localhost:5173 2>/dev/null && echo "✓ Frontend healthy" || echo "✗ Frontend unhealthy"

metrics: ## Show metrics endpoint
	@echo "Metrics available at: http://localhost:8000/metrics"
	@curl -s http://localhost:8000/metrics 2>/dev/null | head -20 || echo "Metrics not available"

# Helper targets
ensure-backend-running:
	@curl -f http://localhost:8000/api/health >/dev/null 2>&1 || \
		(echo "Backend not running. Start with: make dev-backend" && exit 1)

ensure-frontend-running:
	@curl -f http://localhost:5173 >/dev/null 2>&1 || \
		(echo "Frontend not running. Start with: make dev-frontend" && exit 1)

ensure-services-running: ensure-backend-running ensure-frontend-running

# CI/CD targets
ci-backend: lint-backend type-backend test-backend ## Run backend CI pipeline
ci-frontend: lint-frontend type-frontend test-frontend ## Run frontend CI pipeline
ci-full: ci-backend ci-frontend e2e contract ## Run full CI pipeline

# Release targets
version: ## Show current version
	@echo "Backend version: $(shell cd backend && python -c "import app; print(getattr(app, '__version__', '1.0.0'))" 2>/dev/null || echo '1.0.0')"
	@echo "Frontend version: $(shell cd frontend && node -p "require('./package.json').version" 2>/dev/null || echo '1.0.0')"

release: ## Prepare release
	@echo "Preparing release..."
	@make ci-full
	@make build-images
	@make scan
	@echo "Release ready!"

# Environment setup
setup-dev: ## Set up development environment
	@echo "Setting up development environment..."
	@command -v python3 >/dev/null || (echo "Python 3 required" && exit 1)
	@command -v node >/dev/null || (echo "Node.js required" && exit 1)
	@command -v docker >/dev/null || (echo "Docker required" && exit 1)
	cd backend && python -m venv .venv || python3 -m venv .venv
	@echo "Virtual environment created. Activate with:"
	@echo "  cd backend && source .venv/bin/activate  # Linux/Mac"
	@echo "  cd backend && .venv\\Scripts\\activate     # Windows"
	@make install
	@echo "Development environment ready!"

# Production deployment helpers
prod-build: ## Build production images with tags
	@echo "Building production images..."
	docker build \
		--build-arg BUILD_VERSION=$(shell git rev-parse HEAD) \
		--build-arg BUILD_DATE=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
		-f docker/backend.Dockerfile \
		-t nanobanana-backend:$(shell git rev-parse HEAD) \
		-t nanobanana-backend:latest \
		backend/
	docker build \
		--build-arg BUILD_VERSION=$(shell git rev-parse HEAD) \
		--build-arg BUILD_DATE=$(shell date -u +"%Y-%m-%dT%H:%M:%SZ") \
		-f docker/frontend.Dockerfile \
		-t nanobanana-frontend:$(shell git rev-parse HEAD) \
		-t nanobanana-frontend:latest \
		frontend/

# Monitoring and observability
monitor: ## Show monitoring endpoints
	@echo "Monitoring endpoints:"
	@echo "  Health:  http://localhost:8000/api/health"
	@echo "  Metrics: http://localhost:8000/metrics"
	@echo "  Traces:  Configure OTEL_EXPORTER_OTLP_ENDPOINT"
	@echo "  Logs:    JSON structured logs to stdout"

# Database and storage (for future use)
backup: ## Backup application data
	@echo "No persistent data to backup currently"

restore: ## Restore application data
	@echo "No persistent data to restore currently"
