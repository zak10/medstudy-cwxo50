# Provider versions and configurations
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    helm = {
      source  = "hashicorp/helm"
      version = "~> 2.10"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.23"
    }
  }
  required_version = ">= 1.5.0"
}

# Create monitoring namespace in Kubernetes
resource "kubernetes_namespace" "monitoring" {
  metadata {
    name = var.monitoring_namespace
    
    labels = {
      environment = var.environment
      managed-by  = "terraform"
      purpose     = "monitoring"
    }
    
    annotations = {
      "monitoring.medical-research.io/description" = "Namespace for monitoring infrastructure"
    }
  }
}

# CloudWatch Log Group for application logs
resource "aws_cloudwatch_log_group" "app_logs" {
  name              = "/medical-research/${var.environment}"
  retention_in_days = var.retention_in_days
  
  tags = {
    Environment = var.environment
    Service     = "monitoring"
    ManagedBy   = "terraform"
  }

  kms_key_id = aws_kms_key.log_encryption.arn
}

# KMS key for log encryption
resource "aws_kms_key" "log_encryption" {
  description             = "KMS key for CloudWatch Logs encryption"
  deletion_window_in_days = 7
  enable_key_rotation     = true
  
  tags = {
    Environment = var.environment
    Service     = "monitoring"
    Purpose     = "log-encryption"
  }
}

# Prometheus Helm Release
resource "helm_release" "prometheus" {
  name       = "prometheus"
  repository = "https://prometheus-community.github.io/helm-charts"
  chart      = "prometheus"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "15.10.0"  # Specify exact version for production stability
  
  values = [
    yamlencode({
      server = {
        retention           = "${var.prometheus_retention_days}d"
        global = {
          scrape_interval = var.prometheus_scrape_interval
        }
        persistentVolume = {
          enabled = true
          size    = "50Gi"
        }
        resources = {
          requests = {
            cpu    = "500m"
            memory = "1Gi"
          }
          limits = {
            cpu    = "2000m"
            memory = "4Gi"
          }
        }
        securityContext = {
          runAsNonRoot = true
          runAsUser    = 65534
        }
      }
      alertmanager = {
        enabled = true
        persistentVolume = {
          enabled = true
          size    = "10Gi"
        }
      }
      networkPolicy = {
        enabled = true
      }
      nodeExporter = {
        enabled = true
      }
    })
  ]

  depends_on = [kubernetes_namespace.monitoring]
}

# Grafana Helm Release
resource "helm_release" "grafana" {
  name       = "grafana"
  repository = "https://grafana.github.io/helm-charts"
  chart      = "grafana"
  namespace  = kubernetes_namespace.monitoring.metadata[0].name
  version    = "6.50.0"  # Specify exact version for production stability
  
  values = [
    yamlencode({
      adminPassword = var.grafana_admin_password
      datasources = {
        "prometheus.yaml" = {
          apiVersion  = 1
          datasources = [{
            name      = "Prometheus"
            type      = "prometheus"
            url       = "http://prometheus-server"
            access    = "proxy"
            isDefault = true
          }]
        }
      }
      persistence = {
        enabled = true
        size    = "10Gi"
      }
      resources = {
        requests = {
          cpu    = "200m"
          memory = "512Mi"
        }
        limits = {
          cpu    = "1000m"
          memory = "1Gi"
        }
      }
      securityContext = {
        runAsNonRoot = true
        runAsUser    = 472
      }
      serviceMonitor = {
        enabled = true
      }
      ingress = {
        enabled = true
        annotations = {
          "kubernetes.io/ingress.class" = "nginx"
        }
      }
    })
  ]

  depends_on = [helm_release.prometheus]
}

# SNS Topic for alerts
resource "aws_sns_topic" "alerts" {
  count = var.enable_alerts ? 1 : 0
  
  name = "monitoring-alerts-${var.environment}"
  
  tags = {
    Environment = var.environment
    Service     = "monitoring"
    Purpose     = "alerts"
  }
}

# SNS Topic subscription for email notifications
resource "aws_sns_topic_subscription" "email" {
  count = var.enable_alerts ? 1 : 0
  
  topic_arn = aws_sns_topic.alerts[0].arn
  protocol  = "email"
  endpoint  = var.alert_notification_email
}

# CloudWatch Metric Alarms
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  count = var.enable_alerts ? 1 : 0
  
  alarm_name          = "high-error-rate-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name        = "5XXError"
  namespace          = "AWS/ApplicationELB"
  period             = 300
  statistic          = "Average"
  threshold          = 5
  alarm_description  = "This metric monitors API error rate"
  alarm_actions      = [aws_sns_topic.alerts[0].arn]
  
  dimensions = {
    Environment = var.environment
  }
  
  tags = {
    Environment = var.environment
    Service     = "monitoring"
    AlertType   = "ErrorRate"
  }
}

# Outputs for use in other modules
output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group"
  value       = aws_cloudwatch_log_group.app_logs.name
}

output "prometheus_endpoint" {
  description = "Endpoint for Prometheus server"
  value       = "http://prometheus-server.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local"
}

output "grafana_endpoint" {
  description = "Endpoint for Grafana dashboard"
  value       = "http://grafana.${kubernetes_namespace.monitoring.metadata[0].name}.svc.cluster.local"
}