# Orbit Monitoring & Observability

This document describes the monitoring and observability setup for the Orbit platform, including Prometheus metrics, Grafana dashboards, and Alertmanager notifications.

## 🎯 Overview

The Orbit monitoring stack provides comprehensive observability for:

- **Query Service**: Parse latency (p95), search performance, API error rates
- **Crawler Service**: Crawl job success/failure rates, crawl lag, data processing metrics
- **Auth Service**: Authentication metrics, token validation performance
- **Infrastructure**: Node metrics, resource utilization, system health

## 📊 Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Orbit Services│    │   Prometheus    │    │     Grafana     │
│                 │    │                 │    │                 │
│ /metrics        ├────▶ Scraping        ├────▶ Dashboards     │
│ endpoints       │    │ & Storage       │    │ & Visualization │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Alertmanager   │    │    Slack        │
                       │                 ├────▶ Notifications  │
                       │ Alert Rules     │    │                 │
                       └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Deploy Monitoring Stack

```bash
# Using Makefile (recommended)
make deploy-monitoring

# Or using script directly
./scripts/deploy-monitoring.sh
```

### Access Services

```bash
# Port forward to access locally
make monitoring-port-forward

# Manual port forwarding
kubectl port-forward -n monitoring svc/prometheus-server 9090:80 &
kubectl port-forward -n monitoring svc/grafana 3000:80 &
```

**Access URLs:**
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000
  - Username: `admin`
  - Password: `orbit-grafana-2024`

## 📈 Key Metrics

### Query Service Metrics

| Metric | Description | Type |
|--------|-------------|------|
| `http_requests_total` | Total HTTP requests | Counter |
| `query_parse_duration_seconds` | Parse latency | Histogram |
| `property_search_duration_seconds` | Search latency | Histogram |
| `cache_operations_total` | Cache hit/miss rates | Counter |
| `opensearch_operations_total` | OpenSearch operation results | Counter |
| `errors_total` | Error counts by type | Counter |
| `active_connections` | Current active connections | Gauge |

### Crawler Service Metrics

| Metric | Description | Type |
|--------|-------------|------|
| `crawl_jobs_total` | Crawl job counts by status | Counter |
| `crawl_duration_seconds` | Time spent on crawl jobs | Histogram |
| `crawl_lag_seconds` | Time since last successful crawl | Gauge |
| `listings_processed_total` | Listings processed by status | Counter |
| `data_upload_duration_seconds` | S3 upload duration | Histogram |
| `index_operations_total` | Indexing operation results | Counter |
| `active_crawl_jobs` | Currently active crawl jobs | Gauge |

## 🚨 Alerting Rules

### Critical Alerts

1. **Service Down**
   - Condition: `up == 0`
   - Duration: 1 minute
   - Action: Immediate Slack notification

2. **Crawl Job Failure**
   - Condition: Any crawl job fails
   - Duration: Immediate
   - Action: Critical Slack alert

### Warning Alerts

1. **High 5xx Error Rate**
   - Condition: > 1% for 5 minutes
   - Action: Warning Slack notification

2. **High Parse Latency**
   - Condition: p95 > 2 seconds for 5 minutes
   - Action: Performance warning

## 📱 Slack Integration

### Setup Slack Notifications

1. Create a Slack app and get webhook URL
2. Update `charts/prometheus/values.yaml`:

```yaml
alertmanager:
  config:
    global:
      slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
    
    receivers:
      - name: 'slack-critical'
        slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
            channel: '#alerts-critical'
            
      - name: 'slack-warnings'
        slack_configs:
          - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
            channel: '#alerts'
```

3. Redeploy monitoring stack:

```bash
make deploy-monitoring
```

## 📊 Grafana Dashboards

### Pre-configured Dashboards

1. **Orbit Services Dashboard**
   - API request rates
   - 5xx error rates
   - Parse latency (p95)
   - Crawl lag monitoring

2. **Node Exporter Dashboard**
   - System metrics
   - Resource utilization
   - Network and disk I/O

### Custom Dashboard Queries

#### API Request Rate
```promql
sum(rate(http_requests_total[5m])) by (service)
```

#### Error Rate by Service
```promql
(sum(rate(http_requests_total{status_code=~"5.."}[5m])) by (service) / 
 sum(rate(http_requests_total[5m])) by (service)) * 100
```

#### Parse Latency p95
```promql
histogram_quantile(0.95, sum(rate(query_parse_duration_seconds_bucket[5m])) by (le))
```

#### Crawl Lag in Hours
```promql
crawl_lag_seconds / 3600
```

## 🛠 Management Commands

### Check Status
```bash
make monitoring-status
```

### View Logs
```bash
make monitoring-logs
```

### Cleanup
```bash
make monitoring-cleanup
```

## 🔧 Configuration

### Resource Limits

Default resource limits in `values.yaml`:

```yaml
prometheus:
  prometheus:
    prometheusSpec:
      resources:
        requests:
          memory: 512Mi
          cpu: 200m
        limits:
          memory: 2Gi
          cpu: 1000m

grafana:
  resources:
    requests:
      memory: 256Mi
      cpu: 100m
    limits:
      memory: 512Mi
      cpu: 500m
```

### Storage Configuration

```yaml
prometheus:
  prometheus:
    prometheusSpec:
      retention: 30d
      retentionSize: 10GB
      storageSpec:
        volumeClaimTemplate:
          spec:
            accessModes: ["ReadWriteOnce"]
            resources:
              requests:
                storage: 20Gi
```

### Scrape Configuration

Services are scraped with different intervals:
- Query Service: 15 seconds
- Crawler Service: 30 seconds  
- Auth Service: 15 seconds

## 🐛 Troubleshooting

### Common Issues

#### Prometheus Not Scraping Services

1. Check service discovery:
```bash
kubectl get svc -n default | grep -E "(query|crawler|auth)"
```

2. Verify metrics endpoints:
```bash
kubectl port-forward svc/query-service 8000:8000
curl http://localhost:8000/metrics
```

3. Check Prometheus targets:
   - Go to http://localhost:9090/targets
   - Verify all services are "UP"

#### Grafana Dashboard Not Loading

1. Check data source configuration:
   - Go to Configuration → Data Sources
   - Test Prometheus connection

2. Verify Prometheus URL:
   - Should be `http://prometheus-server:80`

#### Alerts Not Firing

1. Check alert rules in Prometheus:
   - Go to http://localhost:9090/alerts

2. Verify Alertmanager configuration:
```bash
kubectl logs -n monitoring -l app.kubernetes.io/name=alertmanager
```

#### Missing Metrics

1. Check service logs:
```bash
kubectl logs -n default deployment/query-service
kubectl logs -n default deployment/crawler-service
```

2. Verify prometheus-client library is installed:
```bash
pip list | grep prometheus-client
```

### Debug Commands

```bash
# Check all monitoring pods
kubectl get pods -n monitoring

# Describe a specific pod
kubectl describe pod -n monitoring <pod-name>

# Check events in monitoring namespace
kubectl get events -n monitoring --sort-by=.metadata.creationTimestamp

# View Prometheus configuration
kubectl get configmap -n monitoring prometheus-server -o yaml
```

## 🔒 Security Considerations

1. **Default Passwords**: Change default Grafana password in production
2. **Network Policies**: Implement network policies to restrict access
3. **RBAC**: Configure proper RBAC for monitoring services
4. **TLS**: Enable TLS for production deployments

## 📚 Additional Resources

- [Prometheus Query Language](https://prometheus.io/docs/prometheus/latest/querying/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Alertmanager Configuration](https://prometheus.io/docs/alerting/latest/configuration/)
- [PromQL Examples](https://prometheus.io/docs/prometheus/latest/querying/examples/)

## 🤝 Contributing

To add new metrics or dashboards:

1. Add metrics to service code using `prometheus-client`
2. Update scrape configurations in `values.yaml`
3. Create or update Grafana dashboards
4. Add corresponding alert rules if needed
5. Update this documentation

For questions or issues, please check existing GitHub issues or create a new one. 