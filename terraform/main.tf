# Sergas Super Account Manager - Main Terraform Configuration
# Infrastructure as Code for AWS deployment

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    bucket         = "sergas-terraform-state"
    key            = "sergas-agents/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sergas-terraform-locks"
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "sergas-super-account-manager"
      Environment = var.environment
      ManagedBy   = "terraform"
      Repository  = "sergas_agents"
    }
  }
}

# ===================================
# Local Variables
# ===================================
locals {
  name_prefix = "sergas-${var.environment}"

  common_tags = {
    Application = "Super Account Manager"
    Team        = "Platform Engineering"
    CostCenter  = "Engineering"
  }
}

# ===================================
# VPC Module
# ===================================
module "vpc" {
  source = "./modules/vpc"

  environment         = var.environment
  vpc_cidr            = var.vpc_cidr
  availability_zones  = var.availability_zones
  private_subnet_cidrs = var.private_subnet_cidrs
  public_subnet_cidrs  = var.public_subnet_cidrs
  enable_nat_gateway   = var.enable_nat_gateway
  enable_vpn_gateway   = var.enable_vpn_gateway

  tags = local.common_tags
}

# ===================================
# Database Module (RDS PostgreSQL)
# ===================================
module "database" {
  source = "./modules/database"

  environment             = var.environment
  vpc_id                  = module.vpc.vpc_id
  database_subnet_ids     = module.vpc.private_subnet_ids
  database_name           = var.database_name
  database_username       = var.database_username
  database_password       = var.database_password
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  multi_az                = var.db_multi_az
  backup_retention_period = var.db_backup_retention
  skip_final_snapshot     = var.environment != "production"

  allowed_security_group_ids = [module.app.ecs_security_group_id]

  tags = local.common_tags
}

# ===================================
# Redis Module (ElastiCache)
# ===================================
module "redis" {
  source = "./modules/redis"

  environment            = var.environment
  vpc_id                 = module.vpc.vpc_id
  redis_subnet_ids       = module.vpc.private_subnet_ids
  node_type              = var.redis_node_type
  num_cache_nodes        = var.redis_num_nodes
  parameter_group_family = var.redis_parameter_group
  engine_version         = var.redis_version
  automatic_failover     = var.redis_automatic_failover

  allowed_security_group_ids = [module.app.ecs_security_group_id]

  tags = local.common_tags
}

# ===================================
# Application Module (ECS Fargate)
# ===================================
module "app" {
  source = "./modules/app"

  environment         = var.environment
  vpc_id              = module.vpc.vpc_id
  private_subnet_ids  = module.vpc.private_subnet_ids
  public_subnet_ids   = module.vpc.public_subnet_ids

  # ECS Configuration
  ecs_cluster_name    = "${local.name_prefix}-cluster"
  service_name        = "${local.name_prefix}-service"
  task_cpu            = var.ecs_task_cpu
  task_memory         = var.ecs_task_memory
  desired_count       = var.ecs_desired_count
  min_capacity        = var.ecs_min_capacity
  max_capacity        = var.ecs_max_capacity

  # Container Configuration
  container_image     = var.container_image
  container_port      = var.container_port
  health_check_path   = "/health"

  # Environment Variables
  environment_variables = {
    ENV                    = var.environment
    DATABASE_HOST          = module.database.endpoint
    DATABASE_PORT          = "5432"
    DATABASE_NAME          = var.database_name
    REDIS_HOST             = module.redis.endpoint
    REDIS_PORT             = "6379"
    PROMETHEUS_PORT        = "9090"
    LOG_LEVEL              = var.log_level
  }

  # Secrets from AWS Secrets Manager
  secrets = {
    DATABASE_PASSWORD      = module.database.password_secret_arn
    ANTHROPIC_API_KEY      = var.anthropic_api_key_secret_arn
    ZOHO_CLIENT_SECRET     = var.zoho_client_secret_arn
    SECRET_KEY             = var.app_secret_key_arn
  }

  # Auto-scaling
  enable_autoscaling              = var.enable_autoscaling
  autoscaling_cpu_threshold       = var.autoscaling_cpu_threshold
  autoscaling_memory_threshold    = var.autoscaling_memory_threshold
  autoscaling_request_count       = var.autoscaling_request_count

  tags = local.common_tags
}

# ===================================
# Monitoring Module (CloudWatch + Prometheus)
# ===================================
module "monitoring" {
  source = "./modules/monitoring"

  environment    = var.environment
  vpc_id         = module.vpc.vpc_id
  subnet_ids     = module.vpc.private_subnet_ids

  # CloudWatch Log Groups
  log_retention_days = var.log_retention_days

  # Alarms
  ecs_cluster_name = module.app.ecs_cluster_name
  ecs_service_name = module.app.ecs_service_name
  rds_instance_id  = module.database.instance_id
  redis_cluster_id = module.redis.cluster_id

  # SNS Alerts
  alert_email      = var.alert_email
  slack_webhook    = var.slack_webhook_url

  tags = local.common_tags
}

# ===================================
# S3 Buckets for Storage
# ===================================
resource "aws_s3_bucket" "artifacts" {
  bucket = "${local.name_prefix}-artifacts"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-artifacts"
  })
}

resource "aws_s3_bucket_versioning" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "artifacts" {
  bucket = aws_s3_bucket.artifacts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ===================================
# WAF for Application Security
# ===================================
resource "aws_wafv2_web_acl" "main" {
  count = var.enable_waf ? 1 : 0

  name  = "${local.name_prefix}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }

  rule {
    name     = "rate-limit"
    priority = 1

    action {
      block {}
    }

    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "RateLimit"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "aws-managed-common-rule-set"
    priority = 2

    override_action {
      none {}
    }

    statement {
      managed_rule_group_statement {
        vendor_name = "AWS"
        name        = "AWSManagedRulesCommonRuleSet"
      }
    }

    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "CommonRuleSet"
      sampled_requests_enabled   = true
    }
  }

  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "${local.name_prefix}-waf"
    sampled_requests_enabled   = true
  }

  tags = local.common_tags
}

# ===================================
# Route53 DNS Records
# ===================================
data "aws_route53_zone" "main" {
  count = var.domain_name != "" ? 1 : 0
  name  = var.domain_name
}

resource "aws_route53_record" "app" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = var.environment == "production" ? var.domain_name : "${var.environment}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = module.app.load_balancer_dns
    zone_id                = module.app.load_balancer_zone_id
    evaluate_target_health = true
  }
}

# ===================================
# Outputs
# ===================================
output "vpc_id" {
  description = "VPC ID"
  value       = module.vpc.vpc_id
}

output "database_endpoint" {
  description = "Database endpoint"
  value       = module.database.endpoint
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = module.redis.endpoint
  sensitive   = true
}

output "load_balancer_dns" {
  description = "Load Balancer DNS name"
  value       = module.app.load_balancer_dns
}

output "ecs_cluster_name" {
  description = "ECS Cluster name"
  value       = module.app.ecs_cluster_name
}

output "application_url" {
  description = "Application URL"
  value       = var.domain_name != "" ? "https://${aws_route53_record.app[0].fqdn}" : "https://${module.app.load_balancer_dns}"
}
