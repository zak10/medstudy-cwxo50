# AWS S3 Storage Module for Medical Research Platform
# Version: 1.0.0
# Provider Requirements
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Primary S3 bucket for medical research data storage
resource "aws_s3_bucket" "main" {
  bucket_prefix = "mrp-${var.environment}-data"
  force_destroy = false

  tags = merge(
    var.tags,
    {
      Name        = "mrp-${var.environment}-data"
      Environment = var.environment
      Purpose     = "Medical Research Data Storage"
      Compliance  = "HIPAA"
    }
  )
}

# Enable versioning for data protection and audit trails
resource "aws_s3_bucket_versioning" "main" {
  bucket = aws_s3_bucket.main.id
  versioning_configuration {
    status = var.enable_versioning ? "Enabled" : "Disabled"
  }
}

# Configure server-side encryption using KMS
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = var.kms_key_id
      sse_algorithm     = "aws:kms"
    }
    bucket_key_enabled = true
  }
}

# Configure lifecycle rules for data archival
resource "aws_s3_bucket_lifecycle_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    id     = "archive_old_data"
    status = "Enabled"

    transition {
      days          = var.lifecycle_rules.transition_glacier_days
      storage_class = "GLACIER"
    }
  }

  rule {
    id     = "cleanup_old_versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 365
    }
  }
}

# Block all public access for security
resource "aws_s3_bucket_public_access_block" "main" {
  bucket = aws_s3_bucket.main.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# Enable access logging for audit and compliance
resource "aws_s3_bucket_logging" "main" {
  bucket = aws_s3_bucket.main.id

  target_bucket = aws_s3_bucket.main.id
  target_prefix = "access-logs/"
}

# Output the bucket ID for reference
output "bucket_id" {
  description = "ID of the created S3 bucket"
  value       = aws_s3_bucket.main.id
}

# Output the bucket ARN for IAM policies
output "bucket_arn" {
  description = "ARN of the created S3 bucket"
  value       = aws_s3_bucket.main.arn
}