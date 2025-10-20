# Sergas Super Account Manager - Terraform Infrastructure

## Overview

This directory contains Infrastructure as Code (IaC) for deploying the Sergas Super Account Manager to AWS using Terraform.

## Directory Structure

```
terraform/
├── main.tf                 # Root module - orchestrates all infrastructure
├── variables.tf            # Input variables
├── outputs.tf              # Output values
├── modules/                # Reusable modules
│   ├── vpc/               # VPC and networking
│   ├── database/          # RDS PostgreSQL
│   ├── redis/             # ElastiCache Redis
│   ├── app/               # ECS Fargate application
│   └── monitoring/        # CloudWatch, alarms, dashboards
└── environments/          # Environment-specific configurations
    ├── dev/               # Development environment
    ├── staging/           # Staging environment
    └── prod/              # Production environment
```

## Prerequisites

- Terraform >= 1.6.0
- AWS CLI configured with appropriate credentials
- S3 bucket for Terraform state (`sergas-terraform-state`)
- DynamoDB table for state locking (`sergas-terraform-locks`)

## Quick Start

### 1. Initialize Backend

```bash
# Create S3 bucket for state
aws s3 mb s3://sergas-terraform-state --region us-east-1
aws s3api put-bucket-versioning \
  --bucket sergas-terraform-state \
  --versioning-configuration Status=Enabled

# Create DynamoDB table for locking
aws dynamodb create-table \
  --table-name sergas-terraform-locks \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5
```

### 2. Deploy Development Environment

```bash
cd environments/dev

# Create terraform.tfvars
cat > terraform.tfvars <<EOF
database_password = "your-secure-password"
container_image = "123456789012.dkr.ecr.us-east-1.amazonaws.com/sergas-super-account-manager:latest"
anthropic_api_key_secret_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:anthropic-api-key"
zoho_client_secret_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:zoho-client-secret"
app_secret_key_arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:app-secret-key"
alert_email = "alerts@sergas.com"
EOF

# Initialize and apply
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

### 3. Deploy Staging/Production

```bash
cd environments/staging  # or environments/prod

# Create terraform.tfvars with appropriate values
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

## Module Documentation

### VPC Module

Creates isolated network infrastructure:
- VPC with public and private subnets across multiple AZs
- Internet Gateway for public internet access
- NAT Gateways for private subnet internet access
- Route tables and associations
- VPC Flow Logs for network monitoring

**Inputs:**
- `vpc_cidr`: CIDR block for VPC
- `availability_zones`: List of AZs to use
- `public_subnet_cidrs`: CIDR blocks for public subnets
- `private_subnet_cidrs`: CIDR blocks for private subnets

### Database Module

Deploys managed PostgreSQL database:
- RDS PostgreSQL 16 instance
- Multi-AZ for high availability (production)
- Automated backups with configurable retention
- Performance Insights enabled
- Enhanced monitoring
- Encrypted at rest

**Inputs:**
- `instance_class`: RDS instance type (e.g., db.t3.medium)
- `allocated_storage`: Storage in GB
- `multi_az`: Enable Multi-AZ deployment
- `backup_retention_period`: Backup retention in days

### Application Module

Deploys containerized application on ECS Fargate:
- ECS cluster and service
- Fargate tasks (serverless containers)
- Application Load Balancer
- Auto-scaling based on CPU/memory/requests
- CloudWatch log groups
- IAM roles and policies

**Inputs:**
- `task_cpu`: CPU units (256, 512, 1024, 2048, 4096)
- `task_memory`: Memory in MB
- `desired_count`: Number of tasks to run
- `container_image`: Docker image URI

### Monitoring Module

Sets up observability infrastructure:
- CloudWatch log groups with retention
- CloudWatch alarms for critical metrics
- SNS topics for alerting
- Custom dashboards
- Performance insights

**Inputs:**
- `log_retention_days`: Log retention period
- `alert_email`: Email for alerts
- `slack_webhook`: Slack webhook for notifications

## Environment Configurations

### Development

- **Purpose:** Rapid development and testing
- **Cost:** ~$200/month
- **Configuration:**
  - Single AZ
  - db.t3.micro database
  - 1-2 Fargate tasks
  - No auto-scaling
  - 7-day log retention

### Staging

- **Purpose:** Pre-production validation
- **Cost:** ~$500/month
- **Configuration:**
  - Multi-AZ
  - db.t3.medium database
  - 2-4 Fargate tasks
  - Auto-scaling enabled
  - 14-day log retention

### Production

- **Purpose:** Live customer workloads
- **Cost:** ~$1,500/month
- **Configuration:**
  - Multi-AZ with high availability
  - db.t3.large database with Multi-AZ
  - 3+ Fargate tasks with auto-scaling
  - WAF enabled
  - 30-day log retention
  - Deletion protection

## State Management

Terraform state is stored in S3 with:
- **Encryption:** Server-side encryption enabled
- **Versioning:** Full version history
- **Locking:** DynamoDB-based state locking

State file location: `s3://sergas-terraform-state/sergas-agents/{environment}/terraform.tfstate`

## Common Operations

### View Current State

```bash
terraform show
terraform state list
```

### Update Resources

```bash
# Modify variables in terraform.tfvars or main.tf
terraform plan
terraform apply
```

### Destroy Environment

```bash
# CAUTION: This will destroy all resources
terraform destroy
```

### Import Existing Resources

```bash
# Import existing resource
terraform import module.vpc.aws_vpc.main vpc-12345678
```

### Targeted Updates

```bash
# Update only specific resource
terraform apply -target=module.database.aws_db_instance.main
```

## Security Best Practices

1. **Secrets Management:**
   - Never commit sensitive values to version control
   - Use AWS Secrets Manager for credentials
   - Reference secrets via ARNs in Terraform

2. **Access Control:**
   - Use IAM roles with least privilege
   - Enable MFA for production access
   - Audit access with CloudTrail

3. **Network Security:**
   - Private subnets for databases and application
   - Security groups with minimal required access
   - VPC Flow Logs enabled

4. **Encryption:**
   - Encryption at rest for RDS and S3
   - TLS/SSL for data in transit
   - Encrypted Terraform state

## Troubleshooting

### State Lock Issues

```bash
# Force unlock (use with caution)
terraform force-unlock <lock-id>
```

### Resource Already Exists

```bash
# Import existing resource
terraform import <resource-address> <resource-id>
```

### Permission Denied

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check IAM permissions
aws iam get-user-policy --user-name <username> --policy-name <policy-name>
```

### Apply Failures

```bash
# Enable debug logging
TF_LOG=DEBUG terraform apply

# Review error messages carefully
# Common issues: quota limits, naming conflicts, dependency issues
```

## Cost Optimization

- Use Reserved Instances for predictable workloads
- Enable auto-scaling to match demand
- Use Savings Plans for ECS Fargate
- Review and delete unused resources
- Monitor costs with AWS Cost Explorer

## Monitoring and Alerts

Key metrics to monitor:
- ECS service health and task count
- Database CPU and storage utilization
- Application response times and error rates
- Load balancer request count

Alerts configured for:
- Service down
- High CPU/memory usage
- Database connection failures
- Elevated error rates

## Disaster Recovery

**RTO:** 30 minutes
**RPO:** 5 minutes

**Backup Strategy:**
- Automated daily database snapshots (7-30 day retention)
- Continuous RDS transaction logs
- Terraform state versioning in S3
- Container images in ECR with lifecycle policies

**Recovery Procedure:**
1. Restore database from snapshot
2. Deploy latest known-good container image
3. Verify health checks
4. Switch DNS/traffic

## Support

For issues or questions:
- Review [Deployment Guide](/docs/deployment_guide.md)
- Check Terraform documentation
- Contact DevOps team: devops@sergas.com

## References

- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
