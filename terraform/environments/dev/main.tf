# Development Environment Configuration

terraform {
  backend "s3" {
    bucket         = "sergas-terraform-state"
    key            = "sergas-agents/dev/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "sergas-terraform-locks"
  }
}

module "infrastructure" {
  source = "../../"

  environment = "dev"
  aws_region  = "us-east-1"

  # VPC Configuration
  vpc_cidr             = "10.0.0.0/16"
  availability_zones   = ["us-east-1a", "us-east-1b"]
  private_subnet_cidrs = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnet_cidrs  = ["10.0.101.0/24", "10.0.102.0/24"]
  enable_nat_gateway   = true

  # Database Configuration
  database_name           = "sergas_agent_db_dev"
  database_username       = "sergas_dev"
  database_password       = var.database_password
  db_instance_class       = "db.t3.micro"
  db_allocated_storage    = 20
  db_multi_az             = false
  db_backup_retention     = 3

  # Redis Configuration
  redis_node_type         = "cache.t3.micro"
  redis_num_nodes         = 1
  redis_automatic_failover = false

  # ECS Configuration
  ecs_task_cpu        = 256
  ecs_task_memory     = 512
  ecs_desired_count   = 1
  ecs_min_capacity    = 1
  ecs_max_capacity    = 3
  container_image     = var.container_image
  container_port      = 8000

  # Auto-scaling
  enable_autoscaling           = false
  autoscaling_cpu_threshold    = 70
  autoscaling_memory_threshold = 80

  # Secrets
  anthropic_api_key_secret_arn = var.anthropic_api_key_secret_arn
  zoho_client_secret_arn       = var.zoho_client_secret_arn
  app_secret_key_arn           = var.app_secret_key_arn

  # Monitoring
  log_retention_days = 7
  log_level          = "DEBUG"
  alert_email        = var.alert_email

  # Security
  enable_waf = false
}

output "application_url" {
  value = module.infrastructure.application_url
}

output "load_balancer_dns" {
  value = module.infrastructure.load_balancer_dns
}
