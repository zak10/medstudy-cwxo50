# Core Terraform configuration
terraform {
  required_version = "~> 1.5"
}

# Project identification variables
variable "project_name" {
  description = "Name of the project used for resource naming and tagging"
  type        = string

  validation {
    condition     = length(var.project_name) > 0 && length(var.project_name) <= 32
    error_message = "Project name must be between 1 and 32 characters"
  }
}

variable "environment" {
  description = "Deployment environment (staging/production) for resource configuration"
  type        = string

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'"
  }
}

# Container configuration variables
variable "api_container_image" {
  description = "Docker image URI for the API container from ECR"
  type        = string

  validation {
    condition     = can(regex("^\\d+\\.dkr\\.ecr\\..*\\.amazonaws\\.com/.*:.*$", var.api_container_image))
    error_message = "Container image must be a valid ECR URI"
  }
}

variable "api_container_port" {
  description = "Port exposed by the API container for service communication"
  type        = number
  default     = 8000

  validation {
    condition     = var.api_container_port > 0 && var.api_container_port < 65536
    error_message = "Container port must be between 1 and 65535"
  }
}

# ECS task configuration variables
variable "desired_count" {
  description = "Desired number of API container instances for high availability"
  type        = number
  default     = 2

  validation {
    condition     = var.desired_count >= 2
    error_message = "Desired count must be at least 2 for high availability"
  }
}

variable "cpu" {
  description = "CPU units for the API container (2048 = 2 vCPU) as per ECS configuration"
  type        = number
  default     = 2048

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096], var.cpu)
    error_message = "CPU units must be one of [256, 512, 1024, 2048, 4096]"
  }
}

variable "memory" {
  description = "Memory allocation for the API container in MB as per ECS configuration"
  type        = number
  default     = 4096

  validation {
    condition     = var.memory >= 512 && var.memory <= 30720
    error_message = "Memory must be between 512 and 30720 MB"
  }
}

# Health check configuration variables
variable "health_check_path" {
  description = "Path for container health checks to verify service status"
  type        = string
  default     = "/api/v1/health"

  validation {
    condition     = can(regex("^/.*$", var.health_check_path))
    error_message = "Health check path must start with /"
  }
}

variable "health_check_interval" {
  description = "Interval between health checks in seconds for monitoring"
  type        = number
  default     = 30

  validation {
    condition     = var.health_check_interval >= 5 && var.health_check_interval <= 300
    error_message = "Health check interval must be between 5 and 300 seconds"
  }
}

# Auto-scaling configuration variables
variable "min_capacity" {
  description = "Minimum number of tasks for auto-scaling to maintain availability"
  type        = number
  default     = 2

  validation {
    condition     = var.min_capacity >= 2
    error_message = "Minimum capacity must be at least 2 for high availability"
  }
}

variable "max_capacity" {
  description = "Maximum number of tasks for auto-scaling during high load"
  type        = number
  default     = 10

  validation {
    condition     = var.max_capacity >= var.min_capacity
    error_message = "Maximum capacity must be greater than or equal to minimum capacity"
  }
}

# Logging configuration variables
variable "log_retention_days" {
  description = "Number of days to retain CloudWatch logs for compliance"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.log_retention_days)
    error_message = "Log retention days must be one of the allowed CloudWatch values"
  }
}