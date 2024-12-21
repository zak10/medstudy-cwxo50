# Terraform version constraint to ensure consistent deployments
# Using Terraform 1.5.x series for infrastructure as code implementation
terraform {
  required_version = "~> 1.5.0"

  # Define required providers with specific version constraints
  required_providers {
    # AWS provider for infrastructure management including:
    # - ECS (Container orchestration)
    # - RDS (Database services)
    # - ElastiCache (Caching layer)
    # - S3 (Object storage)
    # - CloudFront (CDN)
    # - CloudWatch (Monitoring)
    # - WAF (Security)
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}