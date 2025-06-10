#!/bin/bash

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="monitoring"
CHART_PATH="./charts/prometheus"
RELEASE_NAME="orbit-monitoring"

echo -e "${BLUE}🚀 Deploying Orbit Monitoring Stack${NC}"
echo ""

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo -e "${RED}❌ kubectl is not installed or not in PATH${NC}"
    exit 1
fi

# Check if helm is available
if ! command -v helm &> /dev/null; then
    echo -e "${RED}❌ Helm is not installed or not in PATH${NC}"
    exit 1
fi

# Check if we're connected to a cluster
if ! kubectl cluster-info &> /dev/null; then
    echo -e "${RED}❌ Not connected to a Kubernetes cluster${NC}"
    echo "Please configure kubectl to connect to your cluster"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"
echo ""

# Create namespace if it doesn't exist
echo -e "${YELLOW}📦 Creating namespace: $NAMESPACE${NC}"
kubectl create namespace $NAMESPACE --dry-run=client -o yaml | kubectl apply -f -

# Add Helm repositories
echo -e "${YELLOW}📦 Adding Helm repositories...${NC}"
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update

echo -e "${GREEN}✅ Helm repositories updated${NC}"
echo ""

# Update dependencies
echo -e "${YELLOW}📦 Updating chart dependencies...${NC}"
cd $CHART_PATH
helm dependency update
cd - > /dev/null

echo -e "${GREEN}✅ Dependencies updated${NC}"
echo ""

# Deploy the monitoring stack
echo -e "${YELLOW}🚀 Deploying monitoring stack...${NC}"
helm upgrade --install $RELEASE_NAME $CHART_PATH \
    --namespace $NAMESPACE \
    --wait \
    --timeout 10m \
    --create-namespace

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Monitoring stack deployed successfully!${NC}"
    echo ""
    
    # Display access information
    echo -e "${BLUE}📊 Access Information:${NC}"
    echo ""
    
    # Get LoadBalancer IPs/URLs
    echo -e "${YELLOW}Prometheus:${NC}"
    kubectl get svc -n $NAMESPACE | grep prometheus-server || echo "  Service not found"
    
    echo ""
    echo -e "${YELLOW}Grafana:${NC}"
    kubectl get svc -n $NAMESPACE | grep grafana || echo "  Service not found"
    
    echo ""
    echo -e "${BLUE}💡 Quick Access Commands:${NC}"
    echo "  Prometheus: kubectl port-forward -n $NAMESPACE svc/prometheus-server 9090:80"
    echo "  Grafana:    kubectl port-forward -n $NAMESPACE svc/grafana 3000:80"
    echo ""
    echo -e "${BLUE}🔑 Grafana Credentials:${NC}"
    echo "  Username: admin"
    echo "  Password: orbit-grafana-2024"
    echo ""
    
    # Wait for pods to be ready
    echo -e "${YELLOW}⏳ Waiting for pods to be ready...${NC}"
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=prometheus -n $NAMESPACE --timeout=300s
    kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=grafana -n $NAMESPACE --timeout=300s
    
    echo ""
    echo -e "${GREEN}🎉 All services are ready!${NC}"
    echo ""
    echo -e "${BLUE}📈 Dashboard URLs (after port-forwarding):${NC}"
    echo "  Prometheus: http://localhost:9090"
    echo "  Grafana:    http://localhost:3000"
    echo ""
    echo -e "${YELLOW}⚠️  Remember to update Slack webhook URLs in values.yaml for alerts!${NC}"
    
else
    echo ""
    echo -e "${RED}❌ Deployment failed!${NC}"
    echo ""
    echo -e "${YELLOW}Debugging information:${NC}"
    kubectl get pods -n $NAMESPACE
    exit 1
fi 