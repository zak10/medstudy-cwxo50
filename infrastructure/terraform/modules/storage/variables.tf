# Core Terraform functionality for variable definitions
terraform {
  required_version = "~> 1.5"
}

# Environment name variable with validation
variable "environment" {
  description = "Deployment environment name for resource naming and tagging"
  type        = string

  validation {
    condition     = can(regex("^(development|staging|production)$", var.environment))
    error_message = "Environment must be one of: development, staging, production"
  }
}

# Versioning configuration variable
variable "enable_versioning" {
  description = "Enable versioning for S3 buckets to maintain file history"
  type        = bool
  default     = true
}

# Lifecycle rules configuration variable
variable "lifecycle_rules" {
  description = "Configuration for S3 bucket lifecycle rules including Glacier transitions"
  type = object({
    transition_glacier_days = number
  })

  default = {
    transition_glacier_days = 730 # 2 years default for Glacier transition
  }

  validation {
    condition     = var.lifecycle_rules.transition_glacier_days >= 30
    error_message = "Glacier transition period must be at least 30 days"
  }
}

# KMS key configuration variable
variable "kms_key_id" {
  description = "KMS key ID for S3 bucket encryption"
  type        = string

  validation {
    condition     = can(regex("^arn:aws:kms:", var.kms_key_id))
    error_message = "KMS key ID must be a valid AWS KMS key ARN"
  }
}

# Resource tagging variable
variable "tags" {
  description = "Resource tags to apply to all storage resources"
  type        = map(string)
  default     = {}

  validation {
    condition     = length(var.tags) <= 50
    error_message = "Maximum of 50 tags can be specified"
  }
}