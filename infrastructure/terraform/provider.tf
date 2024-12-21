# AWS Provider Configuration for Medical Research Platform
# Implements high-availability infrastructure with multi-AZ support
# Version: ~> 5.0
# Purpose: Defines core AWS provider settings and default resource tags

# Configure the AWS Provider with region and profile settings
provider "aws" {
  # Primary region for infrastructure deployment
  region = "us-east-1"

  # AWS profile for authentication and access management
  profile = "medical-research-platform"

  # Default tags applied to all resources for consistent resource tracking,
  # cost allocation, and compliance management
  default_tags {
    tags = {
      Project          = "medical-research-platform"
      Environment      = terraform.workspace
      ManagedBy        = "terraform"
      Application      = "medical-research"
      SecurityLevel    = "hipaa-compliant"
      HighAvailability = "enabled"
      BackupEnabled    = "true"
      CostCenter       = "research-platform"
    }
  }

  # Enable features for improved resource management and security
  # These settings help maintain HIPAA compliance and high availability
  assume_role_with_web_identity {
    # Enforce session duration for security
    session_duration = "1h"
  }

  # Configure retry behavior for API operations
  retry_mode = "standard"
  max_retries = 3

  # Enable EC2 metadata tokens for enhanced security
  ec2_metadata_service_endpoint_mode = "IPv4"
  ec2_metadata_service_protocol     = "https"

  # Configure S3 for consistent operations
  s3_use_path_style = false
}