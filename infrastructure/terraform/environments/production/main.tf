# Medical Research Platform - Production Infrastructure Configuration
# Terraform Version: ~> 1.5.0
# AWS Provider Version: ~> 5.0

# Configure Terraform backend for state management
terraform {
  backend "s3" {
    bucket         = "medical-research-platform-terraform-state"
    key            = "production/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
    kms_key_id     = var.terraform_state_kms_key_id
  }
}

# Local variables for resource naming and tagging
locals {
  name_prefix = "${var.project}-${var.environment}"
  common_tags = {
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
    HIPAA       = "compliant"
  }
}

# Networking Module - Multi-AZ VPC Setup
module "networking" {
  source = "../../modules/networking"

  project            = var.project
  environment        = var.environment
  vpc_cidr          = var.vpc_cidr
  availability_zones = var.availability_zones
  
  # Enable VPC Flow Logs for security and compliance
  enable_flow_logs    = true
  flow_logs_retention = 365  # 1 year retention for compliance

  tags = local.common_tags
}

# Database Module - Multi-AZ RDS Setup
module "database" {
  source = "../../modules/database"

  project     = var.project
  environment = var.environment
  
  # High-availability database configuration
  instance_class         = "db.r6g.xlarge"
  multi_az              = true
  backup_retention_period = 35  # 35 days backup retention
  
  # Security and monitoring features
  encryption_enabled           = true
  performance_insights_enabled = true
  
  # Network configuration
  vpc_id      = module.networking.vpc_id
  subnet_ids  = module.networking.private_subnet_ids

  tags = local.common_tags

  depends_on = [module.networking]
}

# API Module - ECS Service Configuration
module "api" {
  source = "../../modules/api"

  project     = var.project
  environment = var.environment
  
  # Auto-scaling configuration
  min_capacity = 2
  max_capacity = 10
  cpu_threshold    = 70
  memory_threshold = 80
  
  # High availability settings
  health_check_grace_period = 300
  
  # Network configuration
  vpc_id     = module.networking.vpc_id
  subnet_ids = module.networking.private_subnet_ids

  tags = local.common_tags

  depends_on = [module.networking, module.database]
}

# Security Module - WAF, Shield, and KMS Configuration
module "security" {
  source = "../../modules/security"

  project     = var.project
  environment = var.environment
  
  # Enable security features
  enable_waf             = true
  enable_shield_advanced = true
  enable_guard_duty      = true
  
  # Compliance configuration
  log_retention_days = 365  # 1 year log retention
  domain_name       = var.domain_name

  tags = local.common_tags
}

# Monitoring Module - CloudWatch Configuration
module "monitoring" {
  source = "../../modules/monitoring"

  project     = var.project
  environment = var.environment
  
  # Enhanced monitoring configuration
  enable_detailed_monitoring = true
  enable_enhanced_metrics    = true
  
  # Alerting configuration
  alert_notification_arn = var.sns_alert_topic_arn
  log_retention_days     = 365  # 1 year log retention

  tags = local.common_tags

  depends_on = [module.api, module.database]
}

# Output values for reference
output "vpc_id" {
  description = "ID of the production VPC"
  value       = module.networking.vpc_id
}

output "rds_endpoint" {
  description = "Endpoint of the production RDS instance"
  value       = module.database.rds_endpoint
  sensitive   = true
}

output "cloudwatch_log_groups" {
  description = "List of CloudWatch Log Groups"
  value       = module.monitoring.log_group_names
}

output "api_security_group_id" {
  description = "Security Group ID for API services"
  value       = module.api.security_group_id
}

output "waf_web_acl_id" {
  description = "ID of the WAF Web ACL"
  value       = module.security.waf_web_acl_id
}