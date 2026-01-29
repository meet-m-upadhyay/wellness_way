# WellnessWay Diet Planner - Development Commands

.PHONY: help build up down logs clean test lint format

# Default target
help:
	@echo "WellnessWay Diet Planner - Available Commands:"
	@echo ""
	@echo "  make build     - Build all Docker containers"
	@echo "  make up        - Start the development environment"
	@echo "  make down      - Stop the development environment"
	@echo "  make logs      - View logs from all services"
	@echo "  make clean     - Clean up containers and volumes"
	@echo "  make test      - Run all tests"
	@echo "  make lint      - Run linting on all code"
	@echo "  make format    - Format all code"
	@echo "  make migrate   - Run database migrations"
	@echo "  make shell-be  - Open shell in backend container"
	@echo "  make shell-fe  - Open shell in frontend container"
	@echo ""

# Docker commands
build:
	docker-compose build

up:
	docker-compose up -d
	@echo "Services starting..."
	@echo "Frontend: http://localhost:3000"
	@echo "Backend API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"

down:
	docker-compose down

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --remove-orphans
	docker system prune -f

# Development commands
shell-be:
	docker-compose exec backend /bin/bash

shell-fe:
	docker-compose exec frontend /bin/sh

# Database commands
migrate:
	docker-compose exec backend alembic upgrade head

migrate-create:
	@read -p "Enter migration message: " msg; \
	docker-compose exec backend alembic revision --autogenerate -m "$$msg"

# Testing commands
test:
	@echo "Running backend tests..."
	docker-compose exec backend pytest
	@echo "Running frontend tests..."
	docker-compose exec frontend npm test -- --coverage --watchAll=false

test-be:
	docker-compose exec backend pytest

test-fe:
	docker-compose exec frontend npm test -- --coverage --watchAll=false

# Code quality commands
lint:
	@echo "Linting backend..."
	docker-compose exec backend flake8 app/
	docker-compose exec backend mypy app/
	@echo "Linting frontend..."
	docker-compose exec frontend npm run lint

format:
	@echo "Formatting backend..."
	docker-compose exec backend black app/
	docker-compose exec backend isort app/
	@echo "Formatting frontend..."
	docker-compose exec frontend npm run format

# Setup commands
setup: build up
	@echo "Waiting for services to be ready..."
	sleep 10
	make migrate
	@echo "Setup complete!"

# Health checks
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend not ready"
	@curl -f http://localhost:3000 || echo "Frontend not ready"