# Terraform ~> 1.5

variable "project_name" {
  type        = string
  description = "Name of the project used for resource naming and tagging. Must be lowercase alphanumeric with hyphens only."

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  type        = string
  description = "Deployment environment identifier. Must be either 'staging' or 'production'."

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either 'staging' or 'production'."
  }
}

variable "domain_name" {
  type        = string
  description = "Fully qualified domain name for the CloudFront distribution. Must be a valid domain name format."

  validation {
    condition     = can(regex("^([a-zA-Z0-9-]+\\.)+[a-zA-Z]{2,}$", var.domain_name))
    error_message = "Domain name must be a valid fully qualified domain name format."
  }
}

variable "enable_waf" {
  type        = bool
  default     = true
  description = "Flag to enable WAF protection. Requires valid waf_acl_arn when enabled."
}

variable "waf_acl_arn" {
  type        = string
  description = "ARN of the WAF web ACL to associate with CloudFront. Required when enable_waf is true. Must be a valid WAF ACL ARN."

  validation {
    condition     = var.waf_acl_arn == "" || can(regex("^arn:aws:wafv2:[a-z0-9-]+:[0-9]{12}:global/webacl/[a-zA-Z0-9-_]+/[a-f0-9-]+$", var.waf_acl_arn))
    error_message = "WAF ACL ARN must be a valid AWS WAFv2 web ACL ARN format or empty string."
  }
}

variable "cloudfront_price_class" {
  type        = string
  default     = "PriceClass_100"
  description = "CloudFront distribution price class affecting global reach and cost. See AWS documentation for pricing details."

  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.cloudfront_price_class)
    error_message = "CloudFront price class must be one of: PriceClass_100, PriceClass_200, PriceClass_All."
  }
}

variable "s3_lifecycle_glacier_days" {
  type        = number
  default     = 90
  description = "Number of days after which objects should transition to Glacier storage class for cost optimization. Minimum 30 days."

  validation {
    condition     = var.s3_lifecycle_glacier_days >= 30
    error_message = "S3 lifecycle transition to Glacier must be at least 30 days."
  }
}