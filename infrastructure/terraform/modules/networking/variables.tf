# AWS VPC CIDR block variable with validation to ensure valid IPv4 CIDR format
variable "vpc_cidr" {
  type        = string
  description = "The CIDR block for the VPC"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block"
  }
}

# Environment name variable with validation for allowed values
variable "environment" {
  type        = string
  description = "Environment name for resource tagging (e.g., staging, production)"

  validation {
    condition     = contains(["staging", "production"], var.environment)
    error_message = "Environment must be either staging or production"
  }
}

# Availability zones variable with validation for high availability requirement
variable "availability_zones" {
  type        = list(string)
  description = "List of AWS availability zones for subnet distribution"

  validation {
    condition     = length(var.availability_zones) >= 2
    error_message = "At least two availability zones must be specified for high availability"
  }
}

# Private subnet CIDR blocks variable with validation for AZ count matching
variable "private_subnet_cidrs" {
  type        = list(string)
  description = "List of CIDR blocks for private subnets, one per availability zone"

  validation {
    condition     = length(var.private_subnet_cidrs) == length(var.availability_zones)
    error_message = "Number of private subnet CIDRs must match number of availability zones"
  }

  validation {
    condition     = alltrue([for cidr in var.private_subnet_cidrs : can(cidrhost(cidr, 0))])
    error_message = "All private subnet CIDRs must be valid IPv4 CIDR blocks"
  }
}

# Public subnet CIDR blocks variable with validation for AZ count matching
variable "public_subnet_cidrs" {
  type        = list(string)
  description = "List of CIDR blocks for public subnets, one per availability zone"

  validation {
    condition     = length(var.public_subnet_cidrs) == length(var.availability_zones)
    error_message = "Number of public subnet CIDRs must match number of availability zones"
  }

  validation {
    condition     = alltrue([for cidr in var.public_subnet_cidrs : can(cidrhost(cidr, 0))])
    error_message = "All public subnet CIDRs must be valid IPv4 CIDR blocks"
  }
}

# NAT gateway enablement flag with default value
variable "enable_nat_gateway" {
  type        = bool
  description = "Whether to create NAT gateways for private subnet internet access"
  default     = true
}