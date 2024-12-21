# Terraform ~> 1.5

# Required Variables
variable "environment" {
  description = "Deployment environment (staging/production)"
  type        = string

  validation {
    condition     = can(regex("^(staging|production)$", var.environment))
    error_message = "Environment must be either staging or production"
  }
}

variable "grafana_admin_password" {
  description = "Admin password for Grafana dashboard"
  type        = string
  sensitive   = true
}

variable "alert_notification_email" {
  description = "Email address for monitoring alerts"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_notification_email))
    error_message = "Must provide a valid email address"
  }
}

# Optional Variables with Defaults
variable "monitoring_namespace" {
  description = "Kubernetes namespace for monitoring tools"
  type        = string
  default     = "monitoring"
}

variable "retention_in_days" {
  description = "CloudWatch log retention period in days"
  type        = number
  default     = 30

  validation {
    condition = contains([
      1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653
    ], var.retention_in_days)
    error_message = "Retention days must be a valid CloudWatch retention period"
  }
}

variable "enable_alerts" {
  description = "Flag to enable/disable monitoring alerts"
  type        = bool
  default     = true
}

variable "prometheus_retention_days" {
  description = "Data retention period for Prometheus in days"
  type        = number
  default     = 15

  validation {
    condition     = var.prometheus_retention_days >= 1 && var.prometheus_retention_days <= 90
    error_message = "Prometheus retention must be between 1 and 90 days"
  }
}

variable "prometheus_scrape_interval" {
  description = "Interval between metric scrapes in Prometheus"
  type        = string
  default     = "15s"

  validation {
    condition     = can(regex("^[0-9]+(s|m)$", var.prometheus_scrape_interval))
    error_message = "Scrape interval must be in seconds (s) or minutes (m)"
  }
}

# Output for use in other modules
output "monitoring_variables" {
  description = "Monitoring configuration variables for use in other modules"
  value = {
    environment          = var.environment
    monitoring_namespace = var.monitoring_namespace
    retention_in_days    = var.retention_in_days
  }
}