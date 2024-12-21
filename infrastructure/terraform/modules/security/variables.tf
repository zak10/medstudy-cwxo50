# Core Terraform functionality
terraform {
  required_version = "~> 1.5"
}

# Project name for resource naming and tagging
variable "project_name" {
  type        = string
  description = "Name of the project used for resource naming and tagging"
  default     = "medical-research-platform"
}

# Environment validation with restricted values
variable "environment" {
  type        = string
  description = "Deployment environment (staging/production) - affects security configurations"
  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either staging or production"
  }
}

# KMS key deletion window configuration
variable "kms_key_deletion_window" {
  type        = number
  description = "Number of days before KMS key deletion (7-30 days)"
  default     = 30
  validation {
    condition     = var.kms_key_deletion_window >= 7 && var.kms_key_deletion_window <= 30
    error_message = "KMS key deletion window must be between 7 and 30 days"
  }
}

# WAF rate limiting configuration
variable "waf_rate_limit" {
  type        = number
  description = "Maximum requests per 5-minute period per IP address"
  default     = 2000
  validation {
    condition     = var.waf_rate_limit >= 100 && var.waf_rate_limit <= 20000
    error_message = "WAF rate limit must be between 100 and 20000 requests per 5 minutes"
  }
}

# IP allowlist configuration
variable "allowed_ip_ranges" {
  type        = list(string)
  description = "List of CIDR blocks allowed to access the application"
  default     = ["0.0.0.0/0"]
  validation {
    condition     = alltrue([for cidr in var.allowed_ip_ranges : can(cidrhost(cidr, 0))])
    error_message = "All elements must be valid CIDR blocks"
  }
}

# KMS key rotation configuration
variable "enable_key_rotation" {
  type        = bool
  description = "Enable automatic key rotation for KMS keys (recommended for production)"
  default     = true
}

# WAF blocking rules configuration
variable "waf_block_rules_enabled" {
  type        = bool
  description = "Enable WAF blocking rules for common attacks"
  default     = true
}

# Resource tagging configuration
variable "tags" {
  type        = map(string)
  description = "Additional tags for security resources including compliance markers"
  default     = {}
}