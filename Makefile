.PHONY: help lint fmt test infra-plan infra-apply infra-destroy build-all

# Default target
help:
	@echo "OrbitAgents Development Commands"
	@echo "================================"
	@echo "make lint         - Run all linters (Terraform, Python, JavaScript)"
	@echo "make fmt          - Format all code (Terraform, Python, JavaScript)"
	@echo "make test         - Run all tests"
	@echo "make infra-plan   - Run terraform plan"
	@echo "make infra-apply  - Apply terraform changes"
	@echo "make infra-destroy- Destroy terraform infrastructure"
	@echo "make build-all    - Build all Docker images"

# Linting targets
lint: lint-terraform lint-python lint-frontend

lint-terraform:
	@echo "Linting Terraform..."
	terraform fmt -check -recursive infra/
	cd infra/ && tflint

lint-python:
	@echo "Linting Python services..."
	@for service in auth query crawler ranker notify; do \
		if [ -d "services/$$service" ]; then \
			echo "Linting $$service..."; \
			cd services/$$service && \
			black --check --diff . && \
			isort --check-only --diff . && \
			flake8 . && \
			cd ../..; \
		fi; \
	done

lint-frontend:
	@echo "Linting Frontend..."
	cd frontend/ && npm run lint

# Formatting targets
fmt: fmt-terraform fmt-python fmt-frontend

fmt-terraform:
	@echo "Formatting Terraform..."
	terraform fmt -recursive infra/

fmt-python:
	@echo "Formatting Python services..."
	@for service in auth query crawler ranker notify; do \
		if [ -d "services/$$service" ]; then \
			echo "Formatting $$service..."; \
			cd services/$$service && \
			black . && \
			isort . && \
			cd ../..; \
		fi; \
	done

fmt-frontend:
	@echo "Formatting Frontend..."
	cd frontend/ && npm run format

# Testing targets
test: test-python test-frontend

test-python:
	@echo "Testing Python services..."
	@for service in auth query crawler ranker notify; do \
		if [ -d "services/$$service" ]; then \
			echo "Testing $$service..."; \
			cd services/$$service && \
			python -m pytest && \
			cd ../..; \
		fi; \
	done

test-frontend:
	@echo "Testing Frontend..."
	cd frontend/ && npm run test

# Infrastructure targets
infra-plan:
	@echo "Planning Terraform changes..."
	cd infra/ && terraform init && terraform plan

infra-apply:
	@echo "Applying Terraform changes..."
	cd infra/ && terraform init && terraform apply

infra-destroy:
	@echo "Destroying Terraform infrastructure..."
	cd infra/ && terraform destroy

# Build targets
build-all:
	@echo "Building all Docker images..."
	@for service in auth query crawler ranker notify; do \
		if [ -d "services/$$service" ]; then \
			echo "Building $$service..."; \
			cd services/$$service && \
			docker build -t orbit-agents-$$service:latest . && \
			cd ../..; \
		fi; \
	done

# Install dependencies
install-deps:
	@echo "Installing development dependencies..."
	@echo "Installing Python dependencies..."
	pip install black isort flake8 pytest
	@echo "Installing Terraform tools..."
	@echo "Please install terraform and tflint manually"
	@echo "Installing Frontend dependencies..."
	cd frontend/ && npm install

# Setup development environment
setup: install-deps
	@echo "Setting up development environment..."
	@echo "Creating pre-commit hooks..."
	@echo "Development environment setup complete!"
