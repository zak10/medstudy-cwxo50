# Terraform ~> 1.5 required for advanced validation features

# Project Configuration
variable "project" {
  type        = string
  description = "Project name for resource tagging and identification"
  default     = "medical-research-platform"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens"
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment name - must be 'production' for this configuration"
  default     = "production"

  validation {
    condition     = var.environment == "production"
    error_message = "Environment must be 'production' in production variables"
  }
}

# AWS Region Configuration
variable "aws_region" {
  type        = string
  description = "AWS region for infrastructure deployment"
  default     = "us-east-1"

  validation {
    condition     = can(regex("^us-[a-z]+-[0-9]+$", var.aws_region))
    error_message = "AWS region must be a valid US region identifier"
  }
}

# Network Configuration
variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the production VPC network"
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block"
  }
}

variable "availability_zones" {
  type        = list(string)
  description = "List of AWS availability zones for multi-AZ deployment"
  default     = ["us-east-1a", "us-east-1b", "us-east-1c"]
}

# Database Configuration
variable "db_instance_class" {
  type        = string
  description = "RDS instance class for production database"
  default     = "db.r6g.xlarge"
}

variable "db_backup_retention_days" {
  type        = number
  description = "Number of days to retain RDS automated backups"
  default     = 30

  validation {
    condition     = var.db_backup_retention_days >= 30
    error_message = "Backup retention must be at least 30 days for production"
  }
}

# API Service Configuration
variable "api_instance_count" {
  type        = number
  description = "Number of API service instances to run"
  default     = 3

  validation {
    condition     = var.api_instance_count >= 2
    error_message = "Production must run at least 2 API instances for high availability"
  }
}

variable "api_instance_type" {
  type        = string
  description = "EC2 instance type for API services"
  default     = "t3.large"
}

# Security Configuration
variable "enable_waf" {
  type        = bool
  description = "Enable AWS WAF for API and frontend protection"
  default     = true

  validation {
    condition     = var.enable_waf == true
    error_message = "WAF must be enabled in production"
  }
}

variable "enable_shield" {
  type        = bool
  description = "Enable AWS Shield Advanced for DDoS protection"
  default     = true
}

# Domain Configuration
variable "domain_name" {
  type        = string
  description = "Production domain name for the platform"
  default     = "research.medical-platform.com"

  validation {
    condition     = can(regex("^[a-z0-9.-]+$", var.domain_name))
    error_message = "Domain name must be a valid DNS name"
  }
}

# Monitoring Configuration
variable "enable_monitoring_alerts" {
  type        = bool
  description = "Enable CloudWatch monitoring alerts"
  default     = true

  validation {
    condition     = var.enable_monitoring_alerts == true
    error_message = "Monitoring alerts must be enabled in production"
  }
}

variable "log_retention_days" {
  type        = number
  description = "Number of days to retain CloudWatch logs"
  default     = 90

  validation {
    condition     = var.log_retention_days >= 90
    error_message = "Log retention must be at least 90 days for compliance"
  }
}