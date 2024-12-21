# AWS Provider configuration with version constraint
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# RDS Subnet Group for database placement
resource "aws_db_subnet_group" "db_subnet_group" {
  name        = "medical-research-${var.environment}"
  description = "Database subnet group for Medical Research Platform ${var.environment}"
  subnet_ids  = var.private_subnets

  tags = {
    Name        = "medical-research-db-subnet-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    Managed_By  = "terraform"
  }
}

# Security Group for RDS instance
resource "aws_security_group" "db_security_group" {
  name        = "medical-research-db-${var.environment}"
  description = "Security group for Medical Research Platform database ${var.environment}"
  vpc_id      = var.vpc_id

  # Ingress rule for PostgreSQL access from ECS services
  ingress {
    description     = "PostgreSQL access from ECS services"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [var.ecs_security_group_id]
  }

  # Prevent all outbound traffic except responses
  egress {
    description = "Allow outbound responses only"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name        = "medical-research-db-sg-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    Managed_By  = "terraform"
  }
}

# IAM Role for Enhanced Monitoring
resource "aws_iam_role" "rds_monitoring_role" {
  name = "medical-research-rds-monitoring-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        }
      }
    ]
  })

  managed_policy_arns = ["arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"]

  tags = {
    Environment = var.environment
    Compliance  = "HIPAA"
    Managed_By  = "terraform"
  }
}

# Primary RDS Instance
resource "aws_db_instance" "db_instance" {
  identifier     = "medical-research-${var.environment}"
  engine         = "postgres"
  engine_version = "15.3"

  # Instance Configuration
  instance_class        = var.db_instance_class
  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id           = aws_kms_key.rds_encryption_key.arn

  # Database Configuration
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  port     = 5432

  # Network Configuration
  multi_az               = var.multi_az
  db_subnet_group_name   = aws_db_subnet_group.db_subnet_group.name
  vpc_security_group_ids = [aws_security_group.db_security_group.id]

  # Backup Configuration
  backup_retention_period   = var.backup_retention_period
  backup_window            = var.backup_window
  maintenance_window       = var.maintenance_window
  copy_tags_to_snapshot    = true
  delete_automated_backups = false
  deletion_protection      = true
  skip_final_snapshot      = false
  final_snapshot_identifier = "medical-research-${var.environment}-final"

  # Performance and Monitoring
  performance_insights_enabled          = true
  performance_insights_retention_period = 7
  monitoring_interval                   = 60
  monitoring_role_arn                   = aws_iam_role.rds_monitoring_role.arn
  enabled_cloudwatch_logs_exports       = ["postgresql", "upgrade"]

  # Parameter Group
  parameter_group_name = aws_db_parameter_group.postgres_params.name

  # Auto Minor Version Upgrade
  auto_minor_version_upgrade = true

  tags = {
    Name        = "medical-research-db-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    Backup      = "Required"
    Encryption  = "AES-256"
    Managed_By  = "terraform"
  }
}

# KMS Key for RDS Encryption
resource "aws_kms_key" "rds_encryption_key" {
  description             = "KMS key for RDS encryption - ${var.environment}"
  deletion_window_in_days = 7
  enable_key_rotation     = true

  tags = {
    Name        = "medical-research-rds-key-${var.environment}"
    Environment = var.environment
    Compliance  = "HIPAA"
    Managed_By  = "terraform"
  }
}

# KMS Key Alias
resource "aws_kms_alias" "rds_encryption_key_alias" {
  name          = "alias/medical-research-rds-${var.environment}"
  target_key_id = aws_kms_key.rds_encryption_key.key_id
}

# Custom Parameter Group
resource "aws_db_parameter_group" "postgres_params" {
  family = "postgres15"
  name   = "medical-research-params-${var.environment}"

  parameter {
    name  = "log_connections"
    value = "1"
  }

  parameter {
    name  = "log_disconnections"
    value = "1"
  }

  parameter {
    name  = "log_checkpoints"
    value = "1"
  }

  parameter {
    name  = "log_min_duration_statement"
    value = "1000"
  }

  tags = {
    Environment = var.environment
    Compliance  = "HIPAA"
    Managed_By  = "terraform"
  }
}

# Outputs
output "db_instance_endpoint" {
  description = "The connection endpoint for the RDS instance"
  value       = aws_db_instance.db_instance.endpoint
}

output "db_instance_id" {
  description = "The ID of the RDS instance"
  value       = aws_db_instance.db_instance.id
}

output "db_security_group_id" {
  description = "The ID of the database security group"
  value       = aws_security_group.db_security_group.id
}