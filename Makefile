.PHONY: help install run dev docker-build docker-up docker-down docker-logs test clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	python -m pip install --upgrade pip
	pip install -r requirements.txt

run: ## Run the bot locally
	python main.py

dev: ## Run the bot with auto-reload (using python)
	python main.py

docker-build: ## Build Docker image
	docker-compose build

docker-up: ## Start services with Docker Compose
	docker-compose up -d

docker-down: ## Stop services
	docker-compose down

docker-logs: ## Show Docker logs
	docker-compose logs -f bot

docker-restart: ## Restart bot service
	docker-compose restart bot

docker-clean: ## Stop and remove containers, networks, and volumes
	docker-compose down -v

redis-cli: ## Connect to Redis CLI
	docker-compose exec redis redis-cli

redis-monitor: ## Monitor Redis commands
	docker-compose exec redis redis-cli monitor

redis-flush: ## Flush all Redis data (⚠️ USE WITH CAUTION)
	docker-compose exec redis redis-cli FLUSHALL

shell: ## Open shell in bot container
	docker-compose exec bot /bin/bash

test: ## Run tests
	pytest tests/

lint: ## Run linter
	flake8 src/ config/ main.py
	mypy src/ config/ main.py

format: ## Format code
	black src/ config/ main.py
	isort src/ config/ main.py

clean: ## Clean Python cache files
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete

setup-env: ## Create .env from .env.example
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env file. Please edit it with your credentials."; \
	else \
		echo ".env file already exists."; \
	fi
