# OrbitAgents

> AI-powered web search and information agents platform

[![CI/CD Pipeline](https://github.com/your-org/OrbitAgents/workflows/CI/CD%20Pipeline/badge.svg)](https://github.com/your-org/OrbitAgents/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Terraform](https://img.shields.io/badge/Terraform-1.6+-purple.svg)](https://www.terraform.io/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)](https://www.typescriptlang.org/)

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Prerequisites](#prerequisites)
- [Quick Setup](#quick-setup)
- [Development](#development)
- [Services](#services)
- [Infrastructure](#infrastructure)
- [Contributing](#contributing)
- [License](#license)

## Overview

OrbitAgents is a modern, cloud-native platform for AI-powered web search and information retrieval. Built with a microservices architecture, it provides intelligent agents that can crawl, analyze, rank, and deliver relevant information to users.

### 🆓 **100% FREE TIER AVAILABLE**

Run the entire OrbitAgents platform using only free and open-source tools:

```bash
git clone https://github.com/your-org/OrbitAgents
cd OrbitAgents
make quick-start
```

**Free Stack Includes:**
- 🗄️ **PostgreSQL** (free database)
- 🔍 **OpenSearch** (free Elasticsearch alternative)
- 📦 **MinIO** (free S3-compatible storage)
- 🤖 **Ollama** (free local AI models)
- 🌐 **Playwright** (free browser automation)
- 📊 **Prometheus + Grafana** (free monitoring)
- 🔄 **Redis** (free message queue)
- 🚀 **GitHub Actions** (free CI/CD)

### Key Features

- 🤖 **AI-Powered Search**: Intelligent information retrieval and ranking
- 🌐 **Browser Automation**: Visual automation builder with Playwright
- 🏗️ **Microservices Architecture**: Scalable and maintainable service design
- ☁️ **Cloud Native**: Built for AWS with Kubernetes orchestration
- 🔒 **Secure**: Authentication, authorization, and data protection
- 📊 **Observable**: Comprehensive monitoring and logging
- 🚀 **CI/CD Ready**: Automated testing, building, and deployment
- 💰 **Cost Optimized**: Free tier uses only open-source tools

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│    Frontend     │    │   API Gateway   │    │   Load Balancer │
│   (React/TS)    │◄──►│                 │◄──►│      (ALB)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │ Auth Service │ │Query Service│ │   Notify   │
        │   (FastAPI)  │ │  (FastAPI)  │ │  Service   │
        └──────────────┘ └─────────────┘ └────────────┘
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │   Crawler    │ │   Ranker    │ │ PostgreSQL │
        │   Service    │ │   Service   │ │    (RDS)   │
        │   (FastAPI)  │ │  (FastAPI)  │ │            │
        └──────────────┘ └─────────────┘ └────────────┘
```

## Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **AWS CLI** (v2.0+) - [Installation Guide](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- **Terraform** (v1.6+) - [Installation Guide](https://learn.hashicorp.com/tutorials/terraform/install-cli)
- **kubectl** (v1.28+) - [Installation Guide](https://kubernetes.io/docs/tasks/tools/install-kubectl/)
- **Docker** (v24.0+) - [Installation Guide](https://docs.docker.com/get-docker/)
- **Node.js** (v18+) - [Installation Guide](https://nodejs.org/)
- **Python** (v3.11+) - [Installation Guide](https://www.python.org/downloads/)

### Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/OrbitAgents.git
   cd OrbitAgents
   ```

2. **Configure AWS credentials**
   ```bash
   aws configure
   ```

3. **Initialize and apply infrastructure**
   ```bash
   make infra-plan    # Review planned changes
   make infra-apply   # Apply infrastructure
   ```

4. **Configure kubectl for EKS**
   ```bash
   aws eks update-kubeconfig --region us-west-2 --name orbit-agents-cluster
   ```

5. **Install development dependencies**
   ```bash
   make install-deps
   ```

6. **Start development environment**
   ```bash
   # Terminal 1: Start frontend
   cd frontend/
   npm run dev
   
   # Terminal 2: Start auth service
   cd services/auth/
   python -m uvicorn main:app --reload --port 8001
   
   # Terminal 3: Start query service
   cd services/query/
   python -m uvicorn main:app --reload --port 8002
   ```

## Development

### Available Commands

```bash
make help           # Show all available commands
make lint           # Run all linters
make fmt            # Format all code
make test           # Run all tests
make build-all      # Build all Docker images
make infra-plan     # Plan Terraform changes
make infra-apply    # Apply Terraform changes
```

### Code Style

- **Python**: Black, isort, flake8
- **TypeScript**: ESLint, Prettier
- **Terraform**: terraform fmt, tflint

### Testing

```bash
# Run all tests
make test

# Run specific service tests
cd services/auth/
python -m pytest

# Run frontend tests
cd frontend/
npm run test
```

## Services

### Authentication Service (`services/auth/`)
- User registration and login
- JWT token management
- Password hashing and validation
- **Port**: 8000

### Query Service (`services/query/`)
- Search query processing
- Result aggregation
- User preference handling
- **Port**: 8000

### Crawler Service (`services/crawler/`)
- Web content crawling
- Content extraction and parsing
- Crawl scheduling and management
- **Port**: 8000

### Ranker Service (`services/ranker/`)
- Search result ranking
- AI-powered relevance scoring
- Personalization algorithms
- **Port**: 8000

### Notification Service (`services/notify/`)
- Email notifications
- Real-time alerts
- Notification preferences
- **Port**: 8000

## Infrastructure

### AWS Resources

- **VPC**: Custom VPC with public/private subnets
- **EKS**: Kubernetes cluster for container orchestration
- **RDS**: PostgreSQL database for persistent storage
- **ECR**: Container registry for Docker images
- **ALB**: Application load balancer for traffic distribution
- **Route53**: DNS management
- **CloudWatch**: Monitoring and logging

### Terraform Modules

```bash
cd infra/
terraform plan    # Review changes
terraform apply   # Apply changes
terraform destroy # Clean up resources
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Built with ❤️ by the OrbitAgents Team**
