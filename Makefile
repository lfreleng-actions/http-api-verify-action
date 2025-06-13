# SPDX-License-Identifier: Apache-2.0
# SPDX-FileCopyrightText: 2025 The Linux Foundation

.PHONY: help install install-test install-dev test test-cov lint format clean docker-build docker-run

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install-pdm: ## Install PDM package manager with caching
	pip install --cache-dir ~/.cache/pip pdm==2.24.2

install: ## Install dependencies using PDM
	pdm install

install-test: ## Install test dependencies using PDM
	pdm install -G test

install-dev: ## Install development dependencies using PDM
	pdm install -G dev -G test

test: install-test ## Run tests
	pdm run pytest tests/ -v

test-cov: install-test ## Run tests with coverage
	pdm run pytest tests/ --cov=http_api_tool --cov-report=html --cov-report=term

lint: ## Run linting checks
	pdm run pre-commit run --all-files

format: ## Format code
	pdm run pre-commit run --all-files ruff-format

clean: ## Clean build artifacts
	rm -rf __pycache__/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf coverage_html_report/
	rm -rf .coverage
	rm -rf bandit-report.json
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete

docker-build: ## Build Docker image with caching
	DOCKER_BUILDKIT=1 docker build \
		--cache-from http-api-tool:latest \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		-t http-api-tool .

docker-build-push: ## Build and push Docker image with registry caching
	DOCKER_BUILDKIT=1 docker build \
		--cache-from ghcr.io/$(shell echo $(GITHUB_REPOSITORY) | tr '[:upper:]' '[:lower:]'):latest \
		--cache-to type=registry,ref=ghcr.io/$(shell echo $(GITHUB_REPOSITORY) | tr '[:upper:]' '[:lower:]'):buildcache,mode=max \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		-t http-api-tool \
		-t ghcr.io/$(shell echo $(GITHUB_REPOSITORY) | tr '[:upper:]' '[:lower:]'):latest \
		--push .

docker-run: ## Run Docker container (example)
	docker run --rm http-api-tool \
		test \
		--url https://httpbin.org/get \
		--http-method GET \
		--expected-http-code 200

pre-commit-install: ## Install pre-commit hooks
	pdm run pre-commit install

pre-commit-run: ## Run pre-commit hooks on all files
	pdm run pre-commit run --all-files

ci: install-dev lint test ## Run CI pipeline locally

setup-dev: install-dev pre-commit-install ## Setup development environment

bootstrap: install-pdm install-dev ## Bootstrap the development environment from scratch
