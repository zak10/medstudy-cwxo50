#!/bin/bash

# OpenAPI Specification Generator for Medical Research Platform
# Version: 1.0.0
# Generates comprehensive OpenAPI/Swagger documentation from Django Ninja API implementation

set -e  # Exit on error
set -u  # Exit on undefined variables

# Configuration constants
OPENAPI_VERSION="3.1.0"
API_VERSION="v1"
OUTPUT_FILE="docs/openapi.yaml"
PYTHON_PATH="python"
LOG_FILE="docs/openapi-generation.log"
VALIDATION_REPORT="docs/openapi-validation.json"

# Required package versions
DJANGO_NINJA_VERSION="0.22.0"
PYYAML_VERSION="6.0.0"

# Create necessary directories
mkdir -p "$(dirname "$OUTPUT_FILE")" "$(dirname "$LOG_FILE")"

# Configure logging
setup_logging() {
    # Ensure log directory exists
    mkdir -p "$(dirname "$LOG_FILE")"
    
    # Initialize log file with timestamp
    echo "=== OpenAPI Generation Log $(date -u '+%Y-%m-%d %H:%M:%S UTC') ===" > "$LOG_FILE"
    
    # Set up log function
    log() {
        echo "[$(date -u '+%Y-%m-%d %H:%M:%S UTC')] $1" | tee -a "$LOG_FILE"
    }
}

# Verify required dependencies
check_dependencies() {
    log "Checking dependencies..."
    
    # Check Python version
    if ! command -v $PYTHON_PATH >/dev/null 2>&1; then
        log "ERROR: Python not found"
        return 1
    fi
    
    # Check django-ninja version
    INSTALLED_NINJA_VERSION=$($PYTHON_PATH -c "import django_ninja; print(django_ninja.__version__)" 2>/dev/null || echo "0")
    if [ "$(printf '%s\n' "$DJANGO_NINJA_VERSION" "$INSTALLED_NINJA_VERSION" | sort -V | head -n1)" != "$DJANGO_NINJA_VERSION" ]; then
        log "ERROR: django-ninja >= $DJANGO_NINJA_VERSION required"
        return 1
    fi
    
    # Check PyYAML version
    INSTALLED_YAML_VERSION=$($PYTHON_PATH -c "import yaml; print(yaml.__version__)" 2>/dev/null || echo "0")
    if [ "$(printf '%s\n' "$PYYAML_VERSION" "$INSTALLED_YAML_VERSION" | sort -V | head -n1)" != "$PYYAML_VERSION" ]; then
        log "ERROR: PyYAML >= $PYYAML_VERSION required"
        return 1
    fi
    
    log "All dependencies satisfied"
    return 0
}

# Generate OpenAPI specification
generate_spec() {
    log "Generating OpenAPI specification..."
    
    # Create Python script for spec generation
    cat > /tmp/generate_spec.py << 'EOF'
from django_ninja import NinjaAPI
from api.v1.views import api_router
from api.v1.schemas import APIResponse
import yaml
import json
from datetime import datetime

def generate():
    # Base specification
    spec = {
        "openapi": "3.1.0",
        "info": {
            "title": "Medical Research Platform API",
            "version": "1.0.0",
            "description": "API for community-driven medical research protocols",
            "contact": {
                "name": "API Support",
                "email": "api-support@example.com"
            }
        },
        "servers": [
            {
                "url": "/api/v1",
                "description": "Production API"
            }
        ],
        "security": [
            {"bearerAuth": []}
        ]
    }
    
    # Add security schemes
    spec["components"] = {
        "securitySchemes": {
            "bearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "JWT token authentication"
            }
        },
        "schemas": {}
    }
    
    # Add rate limiting documentation
    spec["components"]["schemas"]["RateLimit"] = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer"},
            "remaining": {"type": "integer"},
            "reset": {"type": "string", "format": "date-time"}
        }
    }
    
    # Extract paths and schemas from router
    paths = api_router.get_openapi_paths()
    schemas = api_router.get_openapi_components()
    
    # Add paths to spec
    spec["paths"] = paths
    
    # Add schemas to components
    spec["components"]["schemas"].update(schemas)
    
    # Add common responses
    spec["components"]["responses"] = {
        "ValidationError": {
            "description": "Validation error response",
            "content": {
                "application/json": {
                    "schema": {"$ref": "#/components/schemas/APIResponse"}
                }
            }
        }
    }
    
    return spec

if __name__ == "__main__":
    spec = generate()
    print(yaml.dump(spec, sort_keys=False, allow_unicode=True))
EOF
    
    # Generate specification
    $PYTHON_PATH /tmp/generate_spec.py > "$OUTPUT_FILE"
    
    # Clean up
    rm /tmp/generate_spec.py
    
    log "Specification generated successfully"
}

# Validate generated specification
validate_spec() {
    log "Validating OpenAPI specification..."
    
    # Create Python validation script
    cat > /tmp/validate_spec.py << 'EOF'
import yaml
import json
from jsonschema import validate
import sys

def validate_spec(spec_file):
    try:
        with open(spec_file, 'r') as f:
            spec = yaml.safe_load(f)
        
        # Basic validation checks
        required_fields = ['openapi', 'info', 'paths']
        for field in required_fields:
            if field not in spec:
                raise ValueError(f"Missing required field: {field}")
        
        # Validate version
        if spec['openapi'] != "3.1.0":
            raise ValueError(f"Invalid OpenAPI version: {spec['openapi']}")
        
        # Validate security schemes
        if 'components' in spec and 'securitySchemes' in spec['components']:
            schemes = spec['components']['securitySchemes']
            if not any(s.get('type') == 'http' for s in schemes.values()):
                raise ValueError("Missing HTTP authentication scheme")
        
        print(json.dumps({"valid": True}))
        return 0
        
    except Exception as e:
        print(json.dumps({"valid": False, "error": str(e)}))
        return 1

if __name__ == "__main__":
    sys.exit(validate_spec(sys.argv[1]))
EOF
    
    # Run validation
    $PYTHON_PATH /tmp/validate_spec.py "$OUTPUT_FILE" > "$VALIDATION_REPORT"
    
    # Check validation result
    if [ $? -ne 0 ]; then
        log "ERROR: Specification validation failed"
        return 1
    fi
    
    # Clean up
    rm /tmp/validate_spec.py
    
    log "Specification validated successfully"
    return 0
}

# Main execution
main() {
    log "Starting OpenAPI specification generation..."
    
    # Check dependencies
    if ! check_dependencies; then
        log "ERROR: Dependency check failed"
        return 1
    fi
    
    # Generate specification
    if ! generate_spec; then
        log "ERROR: Specification generation failed"
        return 1
    fi
    
    # Validate specification
    if ! validate_spec; then
        log "ERROR: Specification validation failed"
        return 1
    fi
    
    log "OpenAPI specification generated successfully"
    log "Output file: $OUTPUT_FILE"
    log "Validation report: $VALIDATION_REPORT"
    return 0
}

# Initialize logging and run main function
setup_logging
main

exit $?