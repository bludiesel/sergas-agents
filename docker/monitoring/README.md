# Sergas Monitoring Stack

Production-ready observability infrastructure with Prometheus, Grafana, and AlertManager.

## Quick Start

```bash
# Start monitoring stack
cd docker/monitoring
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| Grafana | 3000 | Dashboards and visualization |
| Prometheus | 9090 | Metrics collection and storage |
| AlertManager | 9093 | Alert routing and management |
| Node Exporter | 9100 | System metrics |
| cAdvisor | 8080 | Container metrics |
| PostgreSQL Exporter | 9187 | Database metrics |
| Redis Exporter | 9121 | Cache metrics |
| Pushgateway | 9091 | Batch job metrics |
| Blackbox Exporter | 9115 | Endpoint monitoring |

## Access Credentials

**Grafana:**
- URL: http://localhost:3000
- Username: `admin`
- Password: `sergas_admin_2025` (change in production!)

## Configuration Files

- `docker-compose.yml` - Service definitions
- `../../config/prometheus/prometheus.yml` - Prometheus configuration
- `../../config/alerts/alert_rules.yml` - Alert rules
- `../../config/alerts/alertmanager.yml` - Alert routing
- `../../grafana/dashboards/` - Pre-configured dashboards

## Available Dashboards

1. **System Overview** - Overall health and performance
2. **Agent Performance** - AI agent monitoring
3. **Sync Pipeline** - Zoho integration metrics
4. **Error Tracking** - Error monitoring and analysis
5. **Business Metrics** - KPIs and business analytics

## Useful Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a service
docker-compose restart prometheus

# View logs
docker-compose logs -f grafana

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload

# Test AlertManager config
docker-compose exec alertmanager amtool check-config /etc/alertmanager/config.yml
```

## Troubleshooting

### Dashboards not loading
```bash
# Verify datasource
curl http://localhost:3000/api/datasources

# Check Prometheus connectivity
docker-compose exec grafana wget -O- http://prometheus:9090/-/healthy
```

### Prometheus not scraping
```bash
# Check targets
curl http://localhost:9090/api/v1/targets | jq

# Verify network connectivity
docker-compose exec prometheus ping sergas_app
```

### High memory usage
```bash
# Check Prometheus storage
docker-compose exec prometheus df -h /prometheus

# Reduce retention if needed (edit docker-compose.yml)
--storage.tsdb.retention.time=15d
```

## Documentation

See `/docs/monitoring_setup_guide.md` for comprehensive documentation.

## Support

- Slack: #sergas-monitoring
- Email: devops@sergas.com
- Documentation: /docs/monitoring_setup_guide.md
