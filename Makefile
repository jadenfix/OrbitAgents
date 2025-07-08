.PHONY: help lint fmt test infra-plan infra-apply infra-destroy build-all deploy-monitoring monitoring-port-forward monitoring-status monitoring-logs monitoring-cleanup start-free start-minimal stop clean setup-local demo quick-start

# Default target
help:
	@echo "🚀 OrbitAgents Development Commands"
	@echo "==================================="
	@echo "🆓 FREE TIER COMMANDS:"
	@echo "make start-free      - Start free tier development stack"
	@echo "make start-minimal   - Start minimal stack (SQLite + local storage)"
	@echo "make stop            - Stop all services"
	@echo "make setup-local     - Setup local development environment"
	@echo "make demo            - Run demo automation tasks"
	@echo "make quick-start     - Complete setup for new developers"
	@echo ""
	@echo "🔧 DEVELOPMENT COMMANDS:"
	@echo "make lint            - Run all linters (Terraform, Python, JavaScript)"
	@echo "make fmt             - Format all code (Terraform, Python, JavaScript)"
	@echo "make test            - Run all tests"
	@echo "make build-all       - Build all Docker images"
	@echo ""
	@echo "☁️ INFRASTRUCTURE COMMANDS:"
	@echo "make infra-plan      - Run terraform plan"
	@echo "make infra-apply     - Apply terraform changes"
	@echo "make infra-destroy   - Destroy terraform infrastructure"
	@echo ""
	@echo "📊 MONITORING COMMANDS:"
	@echo "make deploy-monitoring - Deploy Prometheus + Grafana monitoring stack"
	@echo "make monitoring-port-forward - Port forward monitoring services"
	@echo "make monitoring-status - Check monitoring stack status"

# FREE TIER COMMANDS
start-free:
	@echo "🚀 Starting OrbitAgents Free Tier..."
	docker-compose -f docker-compose.minimal.yml up -d
	@echo "⏳ Waiting for services to start..."
	sleep 15
	@echo "🎉 OrbitAgents infrastructure is running!"
	@echo "� Run 'make test-services' to verify everything works"

start-minimal:
	@echo "🚀 Starting Minimal Stack..."
	docker-compose -f docker-compose.minimal.yml up -d
	@echo "✅ Minimal stack running!"

test-services:
	@echo "🧪 Testing all services..."
	./scripts/test_deployment.sh

deploy-full:
	@echo "� Full deployment with testing..."
	./scripts/deploy_and_test.sh

stop:
	@echo "�🛑 Stopping OrbitAgents..."
	docker-compose -f docker-compose.minimal.yml down
	docker-compose -f docker-compose.free.yml down
	@echo "✅ Services stopped!"

clean:
	@echo "🧹 Cleaning up containers, images, and volumes..."
	docker-compose -f docker-compose.minimal.yml down -v
	docker-compose -f docker-compose.free.yml down -v
	docker system prune -f
	@echo "✅ Cleanup complete!"

setup-local:
	@echo "🔧 Setting up local development environment..."
	mkdir -p data/postgres data/redis data/opensearch data/minio
	mkdir -p logs screenshots downloads
	chmod 755 data logs screenshots downloads
	@echo "✅ Local development environment ready!"

demo:
	@echo "🎭 Running demo automation tasks..."
	@echo "Make sure services are running first with 'make start-free'"
	curl -X POST http://localhost:8003/automation/web-action \
		-H "Content-Type: application/json" \
		-d '{"url": "https://example.com", "actions": [{"type": "screenshot"}]}' || echo "❌ Services not running - use 'make start-free' first"
	@echo "✅ Demo tasks completed! Check results at http://localhost:8003/docs"

quick-start:
	@echo "🚀 Quick Start for New Developers"
	@echo "================================="
	@echo "1. Setting up local environment..."
	make setup-local
	@echo "2. Starting services..."
	make start-free
	@echo "3. Testing services..."
	make test-services
	@echo "4. Running demos..."
	make demo
	@echo ""
	@echo "🎉 You're ready to go!"
	@echo "📚 Visit http://localhost:3001 to get started"
	@echo "📖 API docs at http://localhost:8003/docs"

status:
	@echo "📊 Service Status:"
	@echo "=================="
	docker-compose -f docker-compose.minimal.yml ps
	@echo ""
	@echo "🌐 Endpoints:"
	@echo "Auth Service:    http://localhost:8001/docs"
	@echo "Query Service:   http://localhost:8002/docs"
	@echo "Browser Agent:   http://localhost:8003/docs"
	@echo "OpenSearch:      http://localhost:9200"
	@echo "MinIO Console:   http://localhost:9001"
	@echo "Ollama:          http://localhost:11434"

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
