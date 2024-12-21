# Terraform variables definition file for staging environment
# Version: 1.5+

# Environment name variable with validation to ensure staging environment
variable "environment" {
  type        = string
  description = "Deployment environment name"
  default     = "staging"

  validation {
    condition     = var.environment == "staging"
    error_message = "Environment must be 'staging' for this configuration"
  }
}

# AWS region variable with validation for us-west-2
variable "aws_region" {
  type        = string
  description = "AWS region for staging environment deployment"
  default     = "us-west-2"

  validation {
    condition     = can(regex("^us-west-2$", var.aws_region))
    error_message = "AWS region must be us-west-2 for staging environment"
  }
}

# VPC CIDR block variable with validation
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the staging VPC"
  default     = "10.1.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block"
  }
}

# Availability zones variable with validation for high availability
variable "availability_zones" {
  type        = list(string)
  description = "List of AWS availability zones for multi-AZ deployment"
  default     = ["us-west-2a", "us-west-2b"]

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least 2 availability zones must be specified for high availability"
  }
}

# RDS instance class variable with validation
variable "db_instance_class" {
  type        = string
  description = "RDS instance class for staging environment"
  default     = "db.t3.medium"

  validation {
    condition     = can(regex("^db\\.t3\\.(medium|large)$", var.db_instance_class))
    error_message = "DB instance class must be db.t3.medium or db.t3.large for staging"
  }
}

# RDS allocated storage variable with validation
variable "db_allocated_storage" {
  type        = number
  description = "Allocated storage size in GB for RDS instance"
  default     = 50

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 100
    error_message = "Allocated storage must be between 20 and 100 GB for staging"
  }
}

# ECS instance count variable with validation
variable "instance_count" {
  type        = number
  description = "Number of ECS instances for the API service"
  default     = 2

  validation {
    condition     = var.instance_count >= 2 && var.instance_count <= 4
    error_message = "Instance count must be between 2 and 4 for staging environment"
  }
}

# EC2 instance type variable with validation
variable "instance_type" {
  type        = string
  description = "EC2 instance type for ECS tasks"
  default     = "t3.medium"

  validation {
    condition     = can(regex("^t3\\.(small|medium)$", var.instance_type))
    error_message = "Instance type must be t3.small or t3.medium for staging"
  }
}

# CloudWatch monitoring variable
variable "enable_monitoring" {
  type        = bool
  description = "Enable detailed CloudWatch monitoring"
  default     = true
}

# Resource tagging variable
variable "tags" {
  type        = map(string)
  description = "Common tags for all resources in staging environment"
  default = {
    Environment  = "staging"
    Project      = "medical-research-platform"
    ManagedBy    = "terraform"
  }
}