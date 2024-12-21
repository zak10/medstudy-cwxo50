# Environment variable for deployment context
variable "environment" {
  type        = string
  description = "Deployment environment (dev/staging/prod)"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

# Instance configuration variables
variable "db_instance_class" {
  type        = string
  description = "RDS instance class for compute and memory resources"
  default     = "db.t3.large"
  validation {
    condition     = can(regex("^db\\.(t3|r5|m5)\\.", var.db_instance_class))
    error_message = "Instance class must be a valid RDS instance type (t3, r5, or m5 series)."
  }
}

variable "allocated_storage" {
  type        = number
  description = "Initial storage allocation in gigabytes"
  default     = 100
  validation {
    condition     = var.allocated_storage >= 100 && var.allocated_storage <= 16384
    error_message = "Allocated storage must be between 100 GB and 16384 GB."
  }
}

variable "max_allocated_storage" {
  type        = number
  description = "Maximum storage allocation in gigabytes for autoscaling"
  default     = 1000
  validation {
    condition     = var.max_allocated_storage >= 100 && var.max_allocated_storage <= 16384
    error_message = "Maximum allocated storage must be between 100 GB and 16384 GB."
  }
}

# Database configuration variables
variable "db_name" {
  type        = string
  description = "Name of the PostgreSQL database"
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]{0,62}$", var.db_name))
    error_message = "Database name must start with a letter, contain only alphanumeric characters and underscores, and be 1-63 characters long."
  }
}

variable "db_username" {
  type        = string
  description = "Master username for database access"
  sensitive   = true
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]{3,15}$", var.db_username))
    error_message = "Username must start with a letter, contain only alphanumeric characters and underscores, and be 4-16 characters long."
  }
}

variable "db_password" {
  type        = string
  description = "Master password for database access"
  sensitive   = true
  validation {
    condition     = can(regex("^(?=.*[A-Z])(?=.*[a-z])(?=.*\\d)(?=.*[^A-Za-z0-9]).{16,}$", var.db_password))
    error_message = "Password must be at least 16 characters long and contain at least one uppercase letter, one lowercase letter, one number, and one special character."
  }
}

# High availability and backup configuration
variable "multi_az" {
  type        = bool
  description = "Enable Multi-AZ deployment for high availability"
  default     = true
}

variable "backup_retention_period" {
  type        = number
  description = "Number of days to retain automated backups"
  default     = 35
  validation {
    condition     = var.backup_retention_period >= 7 && var.backup_retention_period <= 35
    error_message = "Backup retention period must be between 7 and 35 days."
  }
}

variable "backup_window" {
  type        = string
  description = "Daily time range for automated backups (UTC)"
  default     = "03:00-04:00"
  validation {
    condition     = can(regex("^([0-1][0-9]|2[0-3]):[0-5][0-9]-([0-1][0-9]|2[0-3]):[0-5][0-9]$", var.backup_window))
    error_message = "Backup window must be in the format HH:MM-HH:MM in UTC."
  }
}

variable "maintenance_window" {
  type        = string
  description = "Weekly time range for system maintenance (UTC)"
  default     = "sun:04:00-sun:05:00"
  validation {
    condition     = can(regex("^(mon|tue|wed|thu|fri|sat|sun):[0-2][0-9]:[0-5][0-9]-(mon|tue|wed|thu|fri|sat|sun):[0-2][0-9]:[0-5][0-9]$", var.maintenance_window))
    error_message = "Maintenance window must be in the format day:HH:MM-day:HH:MM in UTC."
  }
}

# Network configuration variables
variable "vpc_id" {
  type        = string
  description = "ID of the VPC where the database will be deployed"
  validation {
    condition     = can(regex("^vpc-[a-f0-9]{8,17}$", var.vpc_id))
    error_message = "VPC ID must be a valid vpc-* identifier."
  }
}

variable "private_subnets" {
  type        = list(string)
  description = "List of private subnet IDs for database deployment"
  validation {
    condition     = length(var.private_subnets) >= 2
    error_message = "At least two private subnets must be provided for high availability."
  }
  validation {
    condition     = alltrue([for s in var.private_subnets : can(regex("^subnet-[a-f0-9]{8,17}$", s))])
    error_message = "All subnet IDs must be valid subnet-* identifiers."
  }
}

variable "ecs_security_group_id" {
  type        = string
  description = "Security group ID for ECS tasks requiring database access"
  validation {
    condition     = can(regex("^sg-[a-f0-9]{8,17}$", var.ecs_security_group_id))
    error_message = "Security group ID must be a valid sg-* identifier."
  }
}