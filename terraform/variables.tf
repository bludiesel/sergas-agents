# Sergas Super Account Manager - Terraform Variables

# ===================================
# General Variables
# ===================================
variable "environment" {
  description = "Environment name (dev, staging, production)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "Environment must be dev, staging, or production."
  }
}

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Domain name for the application"
  type        = string
  default     = ""
}

# ===================================
# VPC Configuration
# ===================================
variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  description = "List of availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]
}

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets"
  type        = bool
  default     = true
}

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway"
  type        = bool
  default     = false
}

# ===================================
# Database Configuration (RDS)
# ===================================
variable "database_name" {
  description = "Name of the PostgreSQL database"
  type        = string
  default     = "sergas_agent_db"
}

variable "database_username" {
  description = "Database master username"
  type        = string
  default     = "sergas_admin"
}

variable "database_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.medium"
}

variable "db_allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 100
}

variable "db_multi_az" {
  description = "Enable Multi-AZ deployment"
  type        = bool
  default     = false
}

variable "db_backup_retention" {
  description = "Backup retention period in days"
  type        = number
  default     = 7
}

# ===================================
# Redis Configuration (ElastiCache)
# ===================================
variable "redis_node_type" {
  description = "ElastiCache node type"
  type        = string
  default     = "cache.t3.medium"
}

variable "redis_num_nodes" {
  description = "Number of cache nodes"
  type        = number
  default     = 1
}

variable "redis_parameter_group" {
  description = "Redis parameter group family"
  type        = string
  default     = "redis7"
}

variable "redis_version" {
  description = "Redis engine version"
  type        = string
  default     = "7.0"
}

variable "redis_automatic_failover" {
  description = "Enable automatic failover"
  type        = bool
  default     = false
}

# ===================================
# ECS Configuration
# ===================================
variable "ecs_task_cpu" {
  description = "CPU units for ECS task"
  type        = number
  default     = 512
}

variable "ecs_task_memory" {
  description = "Memory for ECS task in MB"
  type        = number
  default     = 1024
}

variable "ecs_desired_count" {
  description = "Desired number of ECS tasks"
  type        = number
  default     = 2
}

variable "ecs_min_capacity" {
  description = "Minimum number of tasks"
  type        = number
  default     = 1
}

variable "ecs_max_capacity" {
  description = "Maximum number of tasks"
  type        = number
  default     = 10
}

variable "container_image" {
  description = "Docker container image"
  type        = string
}

variable "container_port" {
  description = "Container port"
  type        = number
  default     = 8000
}

# ===================================
# Auto-scaling Configuration
# ===================================
variable "enable_autoscaling" {
  description = "Enable ECS auto-scaling"
  type        = bool
  default     = true
}

variable "autoscaling_cpu_threshold" {
  description = "CPU percentage threshold for scaling"
  type        = number
  default     = 70
}

variable "autoscaling_memory_threshold" {
  description = "Memory percentage threshold for scaling"
  type        = number
  default     = 80
}

variable "autoscaling_request_count" {
  description = "Request count threshold per target"
  type        = number
  default     = 1000
}

# ===================================
# Secrets Configuration
# ===================================
variable "anthropic_api_key_secret_arn" {
  description = "ARN of Anthropic API key in Secrets Manager"
  type        = string
}

variable "zoho_client_secret_arn" {
  description = "ARN of Zoho client secret in Secrets Manager"
  type        = string
}

variable "app_secret_key_arn" {
  description = "ARN of application secret key in Secrets Manager"
  type        = string
}

# ===================================
# Monitoring Configuration
# ===================================
variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 30
}

variable "log_level" {
  description = "Application log level"
  type        = string
  default     = "INFO"
}

variable "alert_email" {
  description = "Email for CloudWatch alerts"
  type        = string
  default     = ""
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for alerts"
  type        = string
  default     = ""
  sensitive   = true
}

# ===================================
# Security Configuration
# ===================================
variable "enable_waf" {
  description = "Enable AWS WAF"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the application"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
