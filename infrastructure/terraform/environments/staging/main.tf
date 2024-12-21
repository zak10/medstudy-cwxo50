# Main Terraform configuration file for Medical Research Platform staging environment
# Version: 1.5+
# Purpose: Orchestrates deployment of all infrastructure components with multi-AZ high availability

# Configure Terraform backend for state management
terraform {
  backend "s3" {
    bucket         = "medical-research-platform-tfstate-staging"
    key            = "terraform.tfstate"
    region         = "us-west-2"
    encrypt        = true
    dynamodb_table = "terraform-locks-staging"
  }
}

# Define common tags for resource management
locals {
  common_tags = {
    Environment     = var.environment
    Project         = "medical-research-platform"
    ManagedBy      = "terraform"
    SecurityLevel   = "hipaa-compliant"
    BackupEnabled   = "true"
    CostCenter      = "research-platform"
  }
}

# Networking module for VPC and subnet configuration
module "networking" {
  source = "../../modules/networking"

  environment         = var.environment
  vpc_cidr           = var.vpc_cidr
  availability_zones = var.availability_zones
  
  # High availability configuration
  enable_nat_gateway  = true
  single_nat_gateway  = true # Cost optimization for staging
  enable_vpn_gateway  = false
  
  tags = local.common_tags
}

# Database module for RDS deployment
module "database" {
  source = "../../modules/database"
  
  environment              = var.environment
  instance_class          = var.db_instance_class
  allocated_storage       = var.db_allocated_storage
  
  # High availability configuration
  multi_az               = true
  backup_retention_period = 7
  
  # Network configuration
  vpc_id                 = module.networking.vpc_id
  subnet_ids             = module.networking.private_subnet_ids
  
  # Security configuration
  encryption_enabled     = true
  
  tags = local.common_tags
}

# API service module for ECS deployment
module "api" {
  source = "../../modules/api"
  
  environment                 = var.environment
  instance_count             = var.instance_count
  instance_type              = var.instance_type
  
  # Network configuration
  vpc_id                     = module.networking.vpc_id
  subnet_ids                 = module.networking.private_subnet_ids
  
  # High availability configuration
  health_check_grace_period  = 300
  enable_autoscaling         = true
  min_capacity              = 2
  max_capacity              = 4
  
  tags = local.common_tags
}

# CloudWatch monitoring configuration
resource "aws_cloudwatch_metric_alarm" "api_cpu_utilization" {
  alarm_name          = "${var.environment}-api-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name        = "CPUUtilization"
  namespace          = "AWS/ECS"
  period             = "300"
  statistic          = "Average"
  threshold          = "70"
  alarm_description  = "This metric monitors ECS CPU utilization"
  alarm_actions      = []  # Add SNS topic ARN for notifications

  dimensions = {
    ClusterName = module.api.ecs_cluster_id
    ServiceName = module.api.ecs_service_name
  }

  tags = local.common_tags
}

# Output important resource identifiers
output "vpc_id" {
  description = "ID of the staging VPC"
  value       = module.networking.vpc_id
}

output "database_endpoint" {
  description = "RDS instance endpoint"
  value       = module.database.db_instance.endpoint
  sensitive   = true
}

output "api_cluster_name" {
  description = "ECS cluster name"
  value       = module.api.ecs_cluster_id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.networking.private_subnet_ids
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.networking.public_subnet_ids
}