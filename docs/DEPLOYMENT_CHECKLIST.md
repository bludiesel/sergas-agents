# Deployment Checklist - Sergas Super Account Manager

## Pre-Deployment

### Infrastructure Setup
- [ ] AWS account configured with appropriate permissions
- [ ] S3 bucket created for Terraform state
- [ ] DynamoDB table created for state locking
- [ ] ECR repository created for Docker images
- [ ] Secrets created in AWS Secrets Manager:
  - [ ] Database password
  - [ ] Anthropic API key
  - [ ] Zoho client credentials
  - [ ] Application secret key

### GitHub Configuration
- [ ] Repository secrets configured:
  - [ ] AWS_ACCESS_KEY_ID
  - [ ] AWS_SECRET_ACCESS_KEY
  - [ ] Database passwords (per environment)
  - [ ] API keys and credentials
- [ ] Branch protection rules enabled
- [ ] Required status checks configured

### Local Development
- [ ] Terraform installed (>= 1.6.0)
- [ ] AWS CLI configured and tested
- [ ] Docker installed and running
- [ ] All deployment scripts executable (`chmod +x scripts/deploy/*.sh`)

## Development Environment Deployment

- [ ] Review terraform/environments/dev/terraform.tfvars
- [ ] Initialize Terraform: `terraform init`
- [ ] Plan deployment: `terraform plan -out=tfplan`
- [ ] Apply infrastructure: `terraform apply tfplan`
- [ ] Verify outputs: `terraform output`
- [ ] Test application URL
- [ ] Run smoke tests: `./scripts/deploy/smoke_tests.sh <url>`
- [ ] Verify monitoring dashboards

## Staging Environment Deployment

- [ ] Code review completed and approved
- [ ] All CI tests passing
- [ ] Review terraform/environments/staging/terraform.tfvars
- [ ] Create database backup
- [ ] Deploy infrastructure: `terraform apply`
- [ ] Deploy application (blue-green):
  ```bash
  ./scripts/deploy/blue_green_deploy.sh staging green <image-tag>
  ```
- [ ] Run integration tests
- [ ] Switch traffic gradually:
  - [ ] 10% traffic
  - [ ] Monitor for 5 minutes
  - [ ] 50% traffic
  - [ ] Monitor for 10 minutes
  - [ ] 100% traffic
- [ ] Comprehensive health checks
- [ ] Decommission old environment
- [ ] Update documentation if needed

## Production Deployment

### Pre-Deployment Validation
- [ ] Staging deployment successful and validated
- [ ] All stakeholders notified
- [ ] Maintenance window scheduled (if needed)
- [ ] Rollback plan documented and tested
- [ ] Team on standby for monitoring

### Backup Creation
- [ ] Database snapshot created
- [ ] Current configuration exported
- [ ] Verify backup integrity

### Deployment Execution
- [ ] Deploy to green environment:
  ```bash
  ./scripts/deploy/blue_green_deploy.sh production green <image-tag>
  ```
- [ ] Run database migrations (dry-run first):
  ```bash
  ./scripts/deploy/run_migrations.sh production --dry-run
  ./scripts/deploy/run_migrations.sh production
  ```
- [ ] Comprehensive health checks:
  ```bash
  ./scripts/deploy/health_check.sh <url> --comprehensive
  ```
- [ ] Run smoke tests
- [ ] Run E2E test suite

### Traffic Migration
- [ ] Switch 10% traffic to green
- [ ] Monitor metrics for 5 minutes
- [ ] Validate error rates < 0.1%
- [ ] Switch 50% traffic to green
- [ ] Monitor metrics for 10 minutes
- [ ] Validate performance metrics
- [ ] Switch 100% traffic to green
- [ ] Monitor metrics for 15 minutes
- [ ] Final validation

### Completion
- [ ] Decommission blue environment
- [ ] Tag green as new blue
- [ ] Clean up old resources
- [ ] Update DNS records (if needed)
- [ ] Notify stakeholders of successful deployment

## Post-Deployment

### Validation
- [ ] All health checks passing
- [ ] API endpoints responding correctly
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] Monitoring dashboards showing healthy metrics
- [ ] No elevated error rates
- [ ] Performance within acceptable ranges

### Documentation
- [ ] Update deployment logs
- [ ] Document any issues encountered
- [ ] Update runbooks if needed
- [ ] Record deployment timestamp and version

### Monitoring
- [ ] CloudWatch alarms configured and active
- [ ] Prometheus metrics being collected
- [ ] Grafana dashboards accessible
- [ ] Log aggregation working
- [ ] Alert routing verified

## Rollback Procedure

### Automated Rollback (if deployment fails)
The CD pipeline will automatically rollback if:
- Health checks fail
- Error rate exceeds threshold
- Integration tests fail

### Manual Rollback
If manual rollback is needed:
1. [ ] Execute rollback script:
   ```bash
   ./scripts/deploy/rollback.sh production
   ```
2. [ ] Verify traffic switched to blue
3. [ ] Check health status
4. [ ] Restore database if needed:
   ```bash
   ./scripts/deploy/restore_database.sh production <snapshot-id>
   ```
5. [ ] Notify stakeholders
6. [ ] Document rollback reason
7. [ ] Create incident report

## Monitoring Checklist

### First Hour
- [ ] Monitor error rates every 5 minutes
- [ ] Check response times
- [ ] Verify database connections
- [ ] Review application logs
- [ ] Monitor resource utilization

### First Day
- [ ] Review all monitoring dashboards
- [ ] Check for any anomalies
- [ ] Validate backup jobs ran successfully
- [ ] Review cost metrics
- [ ] Confirm no security alerts

### First Week
- [ ] Weekly deployment report
- [ ] Performance trend analysis
- [ ] Cost optimization review
- [ ] Security scan results review
- [ ] Capacity planning assessment

## Emergency Contacts

- **DevOps Lead:** devops@sergas.com
- **On-Call Engineer:** Use PagerDuty
- **Security Team:** security@sergas.com
- **Infrastructure Team:** infrastructure@sergas.com

## Notes

_Use this space to document deployment-specific notes, issues, or learnings:_

---

**Deployment Date:** ___________
**Deployed By:** ___________
**Version:** ___________
**Status:** ___________
