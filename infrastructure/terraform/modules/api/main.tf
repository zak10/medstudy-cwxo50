# Provider configuration with version constraint
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# ECS Cluster with container insights enabled
resource "aws_ecs_cluster" "ecs_cluster" {
  name = "${var.project_name}-${var.environment}-api-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECS Task Definition with enhanced configuration
resource "aws_ecs_task_definition" "ecs_task_definition" {
  family                   = "${var.project_name}-${var.environment}-api"
  cpu                      = var.cpu
  memory                   = var.memory
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = module.security.ecs_execution_role_arn
  task_role_arn           = module.security.ecs_task_role_arn

  container_definitions = jsonencode([
    {
      name         = "api"
      image        = var.api_container_image
      essential    = true
      portMappings = [
        {
          containerPort = var.api_container_port
          protocol      = "tcp"
        }
      ]
      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.api_container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api_logs.name
          awslogs-region        = data.aws_region.current.name
          awslogs-stream-prefix = "api"
        }
      }
      environment = [
        {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      ]
    }
  ])

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# ECS Service with advanced deployment configuration
resource "aws_ecs_service" "ecs_service" {
  name                              = "${var.project_name}-${var.environment}-api"
  cluster                          = aws_ecs_cluster.ecs_cluster.id
  task_definition                  = aws_ecs_task_definition.ecs_task_definition.arn
  desired_count                    = var.desired_count
  launch_type                      = "FARGATE"
  platform_version                 = "LATEST"
  health_check_grace_period_seconds = 60

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  deployment_controller {
    type = "ECS"
  }

  network_configuration {
    subnets          = module.networking.private_subnet_ids
    security_groups  = [aws_security_group.api_service.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = var.api_container_port
  }

  service_registries {
    registry_arn = aws_service_discovery_service.api.arn
  }

  lifecycle {
    ignore_changes = [desired_count]
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# CloudWatch Log Group with encryption
resource "aws_cloudwatch_log_group" "api_logs" {
  name              = "/ecs/${var.project_name}-${var.environment}-api"
  retention_in_days = var.log_retention_days
  kms_key_id       = var.kms_key_arn

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Auto-scaling target configuration
resource "aws_appautoscaling_target" "api_scaling_target" {
  max_capacity       = var.max_capacity
  min_capacity       = var.min_capacity
  resource_id        = "service/${aws_ecs_cluster.ecs_cluster.name}/${aws_ecs_service.ecs_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# CPU-based auto-scaling policy
resource "aws_appautoscaling_policy" "api_cpu_scaling" {
  name               = "${var.project_name}-${var.environment}-api-cpu-scaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.api_scaling_target.resource_id
  scalable_dimension = aws_appautoscaling_target.api_scaling_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.api_scaling_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 300
    scale_out_cooldown = 60
  }
}

# Target Group for ALB
resource "aws_lb_target_group" "api" {
  name                 = "${var.project_name}-${var.environment}-api"
  port                 = var.api_container_port
  protocol             = "HTTP"
  vpc_id               = module.networking.vpc_id
  target_type          = "ip"
  deregistration_delay = 30

  health_check {
    path                = var.health_check_path
    interval            = var.health_check_interval
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200-299"
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Security Group for API service
resource "aws_security_group" "api_service" {
  name_prefix = "${var.project_name}-${var.environment}-api-service"
  vpc_id      = module.networking.vpc_id

  ingress {
    from_port       = var.api_container_port
    to_port         = var.api_container_port
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Environment = var.environment
    Project     = var.project_name
  }
}

# Service Discovery for API service
resource "aws_service_discovery_service" "api" {
  name = "${var.project_name}-${var.environment}-api"

  dns_config {
    namespace_id = aws_service_discovery_private_dns_namespace.api.id
    
    dns_records {
      ttl  = 10
      type = "A"
    }

    routing_policy = "MULTIVALUE"
  }

  health_check_custom_config {
    failure_threshold = 1
  }
}

# Private DNS namespace for service discovery
resource "aws_service_discovery_private_dns_namespace" "api" {
  name        = "${var.project_name}-${var.environment}.local"
  vpc         = module.networking.vpc_id
  description = "Private DNS namespace for API service discovery"
}

# Output values
output "api_cluster_name" {
  value       = aws_ecs_cluster.ecs_cluster.name
  description = "ECS cluster name for API service"
}

output "api_service_name" {
  value       = aws_ecs_service.ecs_service.name
  description = "ECS service name for API deployment"
}

output "api_task_definition_arn" {
  value       = aws_ecs_task_definition.ecs_task_definition.arn
  description = "ARN of the API task definition"
}

output "api_target_group_arn" {
  value       = aws_lb_target_group.api.arn
  description = "ARN of the API target group"
}