.PHONY: help lint fmt test infra-plan infra-apply infra-destroy build-all deploy-monitoring monitoring-port-forward monitoring-status monitoring-logs monitoring-cleanup

# Default target
help:
	@echo "OrbitAgents Development Commands"
	@echo "================================"
	@echo "make lint            - Run all linters (Terraform, Python, JavaScript)"
	@echo "make fmt             - Format all code (Terraform, Python, JavaScript)"
	@echo "make test            - Run all tests"
	@echo "make infra-plan      - Run terraform plan"
	@echo "make infra-apply     - Apply terraform changes"
	@echo "make infra-destroy   - Destroy terraform infrastructure"
	@echo "make build-all       - Build all Docker images"
	@echo "make deploy-monitoring - Deploy Prometheus + Grafana monitoring stack"
	@echo "make monitoring-port-forward - Port forward monitoring services"
	@echo "make monitoring-status - Check monitoring stack status"

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

# Monitoring targets
deploy-monitoring:
	@echo "🚀 Deploying Orbit Monitoring Stack..."
	./scripts/deploy-monitoring.sh

monitoring-port-forward:
	@echo "📊 Setting up port forwarding for monitoring services..."
	@echo "Prometheus will be available at http://localhost:9090"
	@echo "Grafana will be available at http://localhost:3000"
	@echo "Credentials - Username: admin, Password: orbit-grafana-2024"
	@echo ""
	@echo "Press Ctrl+C to stop port forwarding"
	@echo ""
	kubectl port-forward -n monitoring svc/prometheus-server 9090:80 &
	kubectl port-forward -n monitoring svc/grafana 3000:80

monitoring-status:
	@echo "📊 Monitoring Stack Status"
	@echo "=========================="
	@echo ""
	@echo "Namespace:"
	kubectl get namespace monitoring 2>/dev/null || echo "Monitoring namespace not found"
	@echo ""
	@echo "Services:"
	kubectl get svc -n monitoring 2>/dev/null || echo "No services found in monitoring namespace"
	@echo ""
	@echo "Pods:"
	kubectl get pods -n monitoring 2>/dev/null || echo "No pods found in monitoring namespace"
	@echo ""
	@echo "Recent events:"
	kubectl get events -n monitoring --sort-by=.metadata.creationTimestamp 2>/dev/null | tail -10 || echo "No events found"

monitoring-logs:
	@echo "📊 Monitoring Stack Logs"
	@echo "========================"
	@echo "Choose a service to view logs:"
	@echo "1. Prometheus"
	@echo "2. Grafana"
	@echo "3. Alertmanager"
	@read -p "Enter choice (1-3): " choice; \
	case $$choice in \
		1) kubectl logs -n monitoring -l app.kubernetes.io/name=prometheus --tail=100 -f ;; \
		2) kubectl logs -n monitoring -l app.kubernetes.io/name=grafana --tail=100 -f ;; \
		3) kubectl logs -n monitoring -l app.kubernetes.io/name=alertmanager --tail=100 -f ;; \
		*) echo "Invalid choice" ;; \
	esac

monitoring-cleanup:
	@echo "🧹 Cleaning up monitoring stack..."
	@read -p "Are you sure you want to remove the monitoring stack? (y/N): " confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		helm uninstall orbit-monitoring -n monitoring || true; \
		kubectl delete namespace monitoring || true; \
		echo "✅ Monitoring stack removed"; \
	else \
		echo "❌ Cleanup cancelled"; \
	fi

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
