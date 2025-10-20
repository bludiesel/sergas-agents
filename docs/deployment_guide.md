# Sergas Super Account Manager - Deployment Guide

## Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Infrastructure Setup](#infrastructure-setup)
4. [CI/CD Pipeline](#cicd-pipeline)
5. [Deployment Strategies](#deployment-strategies)
6. [Environment Configuration](#environment-configuration)
7. [Monitoring and Observability](#monitoring-and-observability)
8. [Rollback Procedures](#rollback-procedures)
9. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides comprehensive instructions for deploying the Sergas Super Account Manager using automated CI/CD pipelines and infrastructure as code.

### Architecture Highlights
- **Zero-downtime deployments** using blue-green strategy
- **Infrastructure as Code** with Terraform
- **Containerized deployment** using Docker and ECS Fargate
- **Automated testing** at every stage
- **Multi-environment support** (dev, staging, production)

---

## Prerequisites

### Required Tools
```bash
# Install required CLI tools
brew install terraform aws-cli jq
pip install alembic pytest

# Verify installations
terraform version  # >= 1.6.0
aws --version      # >= 2.0.0
docker --version   # >= 24.0.0
```

### AWS Configuration
```bash
# Configure AWS credentials
aws configure

# Verify access
aws sts get-caller-identity
```

### GitHub Secrets
Configure the following secrets in GitHub repository settings:

```
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
DATABASE_PASSWORD=<secure-password>
ANTHROPIC_API_KEY=<your-claude-api-key>
ZOHO_CLIENT_SECRET=<your-zoho-secret>
GRAFANA_PASSWORD=<grafana-admin-password>
```

---

## Infrastructure Setup

### 1. Initialize Terraform Backend

```bash
# Create S3 bucket for state
aws s3 mb s3://sergas-terraform-state --region us-east-1

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket sergas-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for state locking
aws dynamodb create-table \
  --table-name sergas-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 \
  --region us-east-1
```

### 2. Deploy Development Environment

```bash
cd terraform/environments/dev

# Initialize Terraform
terraform init

# Review planned changes
terraform plan -out=tfplan

# Apply infrastructure
terraform apply tfplan

# Capture outputs
terraform output > outputs.txt
```

### 3. Deploy Staging Environment

```bash
cd terraform/environments/staging

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 4. Deploy Production Environment

```bash
cd terraform/environments/production

# Production requires approval
terraform init
terraform plan -out=tfplan

# Review carefully before applying
terraform apply tfplan
```

---

## CI/CD Pipeline

### GitHub Actions Workflows

#### Continuous Integration (`.github/workflows/ci.yml`)

**Triggers:**
- Push to main, develop, or feature branches
- Pull requests to main or develop

**Jobs:**
1. **Code Quality & Linting** - Black, isort, Flake8, Pylint
2. **Type Checking** - MyPy strict type validation
3. **Security Scanning** - Bandit, Safety, CodeQL
4. **Unit & Integration Tests** - Pytest with coverage
5. **Build & Package** - Python package build
6. **Docker Build & Scan** - Container security scanning

**Usage:**
```bash
# Manually trigger CI
gh workflow run ci.yml

# Monitor workflow
gh run list --workflow=ci.yml
gh run view <run-id>
```

#### Continuous Deployment (`.github/workflows/cd.yml`)

**Triggers:**
- Push to main branch → Staging deployment
- Tagged releases (v*.*.*) → Production deployment
- Manual workflow dispatch

**Jobs:**
1. **Build & Push Docker Image** - Multi-arch builds to ECR
2. **Deploy to Environment** - Blue-green deployment
3. **Health Checks** - Comprehensive validation
4. **Traffic Switching** - Gradual migration
5. **Post-Deployment Validation** - End-to-end tests

**Manual Deployment:**
```bash
# Deploy to specific environment
gh workflow run cd.yml -f environment=staging

# Deploy specific version to production
gh workflow run cd.yml -f environment=production
```

---

## Deployment Strategies

### Blue-Green Deployment

The system uses blue-green deployment for zero-downtime releases:

#### 1. Deploy to Green Environment
```bash
./scripts/deploy/blue_green_deploy.sh production green <image-tag>
```

**What happens:**
- New task definition registered with updated image
- Green target group created/updated
- Green ECS service deployed
- Health checks verified

#### 2. Run Integration Tests
```bash
# Test green environment
pytest tests/integration --env=production-green

# Smoke tests
./scripts/deploy/smoke_tests.sh https://green-production.sergas-agents.com
```

#### 3. Switch Traffic Gradually
```bash
# 10% traffic to green
./scripts/deploy/traffic_switch.sh production 10

# Monitor for 5 minutes
./scripts/deploy/monitor_metrics.sh production 300

# 50% traffic to green
./scripts/deploy/traffic_switch.sh production 50

# Monitor for 10 minutes
./scripts/deploy/monitor_metrics.sh production 600

# 100% traffic to green
./scripts/deploy/traffic_switch.sh production 100
```

#### 4. Decommission Blue Environment
```bash
# After successful validation
./scripts/deploy/decommission_environment.sh production blue

# Tag green as new blue
./scripts/deploy/tag_environment.sh production green blue
```

### Canary Deployment (Alternative)

For more conservative rollouts:
```bash
# Deploy canary with 5% traffic
./scripts/deploy/canary_deploy.sh production 5

# Incrementally increase traffic
./scripts/deploy/canary_deploy.sh production 25
./scripts/deploy/canary_deploy.sh production 50
./scripts/deploy/canary_deploy.sh production 100
```

---

## Environment Configuration

### Development Environment

**Purpose:** Rapid development and testing
**Configuration:**
- Single AZ deployment
- Reduced capacity (1-2 tasks)
- Lower-spec instances
- Development databases
- Debug logging enabled

```bash
# Environment variables
ENV=dev
LOG_LEVEL=DEBUG
DATABASE_INSTANCE=db.t3.micro
ECS_TASK_CPU=256
ECS_TASK_MEMORY=512
```

### Staging Environment

**Purpose:** Pre-production validation
**Configuration:**
- Multi-AZ deployment
- Production-like capacity
- Similar instance specs to production
- Separate database with production data snapshot
- Info-level logging

```bash
# Environment variables
ENV=staging
LOG_LEVEL=INFO
DATABASE_INSTANCE=db.t3.medium
ECS_TASK_CPU=512
ECS_TASK_MEMORY=1024
ENABLE_AUTOSCALING=true
```

### Production Environment

**Purpose:** Live customer workloads
**Configuration:**
- Multi-AZ with high availability
- Auto-scaling enabled
- Production-grade instances
- Encrypted databases with backups
- Error-level logging with audit trails
- WAF and DDoS protection

```bash
# Environment variables
ENV=production
LOG_LEVEL=ERROR
DATABASE_INSTANCE=db.t3.large
DB_MULTI_AZ=true
ECS_TASK_CPU=1024
ECS_TASK_MEMORY=2048
ENABLE_AUTOSCALING=true
ENABLE_WAF=true
```

---

## Monitoring and Observability

### CloudWatch Metrics

**Application Metrics:**
- Request rate and latency
- Error rates and types
- Task CPU and memory utilization
- Database connections and query performance

**Infrastructure Metrics:**
- ECS service health
- Target group health
- ALB request count
- RDS performance

### Prometheus & Grafana

**Access Grafana:**
```bash
# Port forward to local
kubectl port-forward svc/grafana 3000:3000

# Open browser
open http://localhost:3000
```

**Key Dashboards:**
1. **Business Metrics** - Account reviews, approvals, sync status
2. **Application Performance** - Latency, throughput, errors
3. **Infrastructure Health** - Resource utilization, costs
4. **Error Tracking** - Exception rates, failure patterns

### Logging

**CloudWatch Logs:**
```bash
# View application logs
aws logs tail /aws/ecs/sergas-production --follow

# Search for errors
aws logs filter-pattern /aws/ecs/sergas-production --filter-pattern "ERROR"

# Export logs
aws logs create-export-task \
  --log-group-name /aws/ecs/sergas-production \
  --from 1609459200000 \
  --to 1612137600000 \
  --destination s3://sergas-logs-bucket
```

### Alerts

**Critical Alerts** (PagerDuty/Email):
- Service down
- Database connection failures
- Error rate > 5%
- CPU > 90% for 5 minutes

**Warning Alerts** (Slack):
- Slow response times
- Memory > 80%
- Failed deployments
- Backup failures

---

## Rollback Procedures

### Automatic Rollback

The CD pipeline includes automatic rollback on failure:
- Health check failures
- High error rates during traffic switch
- Failed integration tests

### Manual Rollback

#### Quick Rollback (Traffic Switch)
```bash
# Immediately switch all traffic back to blue
./scripts/deploy/rollback.sh production
```

#### Full Rollback (Previous Version)
```bash
# Identify last stable deployment
aws ecs list-task-definitions \
  --family-prefix sergas-agent-task-production \
  --sort DESC \
  | jq -r '.taskDefinitionArns[1]'

# Deploy previous version
aws ecs update-service \
  --cluster sergas-production-cluster \
  --service sergas-agent-service-production \
  --task-definition <previous-task-definition-arn>
```

#### Database Rollback
```bash
# List available backups
aws rds describe-db-snapshots \
  --db-instance-identifier sergas-production-db

# Restore from snapshot
./scripts/deploy/restore_database.sh production <snapshot-id>
```

---

## Troubleshooting

### Common Issues

#### 1. Deployment Stuck

**Symptom:** ECS tasks keep restarting
**Diagnosis:**
```bash
# Check task logs
aws logs tail /aws/ecs/sergas-production --follow

# Describe task
aws ecs describe-tasks \
  --cluster sergas-production-cluster \
  --tasks <task-id>
```

**Solutions:**
- Check environment variables
- Verify secrets access
- Check database connectivity
- Review resource limits

#### 2. Health Checks Failing

**Symptom:** Target group reports unhealthy
**Diagnosis:**
```bash
# Check health endpoint
curl https://production.sergas-agents.com/health

# Review ALB logs
aws s3 ls s3://sergas-alb-logs/production/
```

**Solutions:**
- Verify health check path
- Increase health check grace period
- Check security group rules
- Validate SSL certificates

#### 3. Database Connection Issues

**Symptom:** Application can't connect to database
**Diagnosis:**
```bash
# Test database connectivity
psql -h <db-endpoint> -U sergas_user -d sergas_agent_db

# Check security groups
aws ec2 describe-security-groups \
  --filters "Name=tag:Environment,Values=production"
```

**Solutions:**
- Verify security group rules
- Check RDS endpoint
- Validate credentials
- Check VPC routing

#### 4. Performance Degradation

**Symptom:** Slow response times
**Diagnosis:**
```bash
# Check CloudWatch metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions Name=ServiceName,Value=sergas-production

# Review database performance
aws rds describe-db-instances \
  --db-instance-identifier sergas-production-db
```

**Solutions:**
- Scale ECS tasks
- Optimize database queries
- Increase cache size
- Review application logs

---

## Best Practices

### 1. Pre-Deployment Checklist
- [ ] All tests passing
- [ ] Code reviewed and approved
- [ ] Database migrations tested
- [ ] Secrets rotated (if needed)
- [ ] Backup created
- [ ] Rollback plan documented

### 2. During Deployment
- [ ] Monitor CloudWatch metrics
- [ ] Watch application logs
- [ ] Verify health checks
- [ ] Test critical endpoints
- [ ] Monitor error rates

### 3. Post-Deployment
- [ ] Run smoke tests
- [ ] Verify integrations
- [ ] Check monitoring dashboards
- [ ] Review performance metrics
- [ ] Update documentation

### 4. Security
- [ ] Rotate secrets regularly
- [ ] Keep dependencies updated
- [ ] Review security scan results
- [ ] Audit IAM permissions
- [ ] Enable MFA for production access

---

## Support and Resources

### Documentation
- [AWS ECS Best Practices](https://docs.aws.amazon.com/ecs/)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/)
- [GitHub Actions](https://docs.github.com/en/actions)

### Internal Resources
- Architecture diagrams: `/docs/architecture/`
- Runbooks: `/docs/runbooks/`
- API documentation: `/docs/api/`

### Contact
- DevOps Team: devops@sergas.com
- On-call: Use PagerDuty
- Slack: #sergas-deployments

---

## Appendix

### A. Environment Variables Reference

See `.env.example` for complete list of required environment variables.

### B. AWS Resources Created

**Per Environment:**
- VPC with public/private subnets
- NAT Gateways
- Application Load Balancer
- ECS Cluster and Services
- RDS PostgreSQL instance
- ElastiCache Redis cluster
- S3 buckets
- CloudWatch log groups
- Route53 DNS records

### C. Cost Estimates

**Development:** ~$200/month
**Staging:** ~$500/month
**Production:** ~$1,500/month (with auto-scaling)

### D. Disaster Recovery

**RTO (Recovery Time Objective):** 30 minutes
**RPO (Recovery Point Objective):** 5 minutes

**Backup Strategy:**
- Database: Automated daily snapshots, 7-day retention
- Application: Container images in ECR
- Configuration: Terraform state in S3
- Logs: 30-day retention in CloudWatch
