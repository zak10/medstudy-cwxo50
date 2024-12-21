#!/bin/bash

# run-tests.sh
# Comprehensive test runner for backend test suites with coverage and quality checks
# Version: 1.0.0
# Dependencies:
# - pytest==7.4.0
# - flake8==6.0.0
# - mypy==1.4.0

# Enable strict shell execution
set -euo pipefail

# Global variables
export DJANGO_SETTINGS_MODULE="config.settings.test"
export PYTHONPATH="${PWD}"
export COVERAGE_MIN_THRESHOLD=80
export LOG_FILE="/tmp/test-execution.log"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
RESULTS_DIR="test-results-${TIMESTAMP}"

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Error codes
SUCCESS=0
TEST_FAILURE=1
LINT_FAILURE=2
TYPE_CHECK_FAILURE=3
COVERAGE_FAILURE=4
SETUP_FAILURE=5

setup_environment() {
    echo "Setting up test environment..."
    
    # Create log file and set permissions
    touch "${LOG_FILE}"
    chmod 644 "${LOG_FILE}"
    
    # Verify required tools are installed
    local required_tools=("pytest" "flake8" "mypy" "coverage")
    for tool in "${required_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            echo -e "${RED}Error: Required tool '$tool' is not installed${NC}" | tee -a "${LOG_FILE}"
            return ${SETUP_FAILURE}
        fi
    done
    
    # Create results directory
    mkdir -p "${RESULTS_DIR}"
    
    echo "Environment setup complete" | tee -a "${LOG_FILE}"
    return ${SUCCESS}
}

run_unit_tests() {
    echo "Running unit tests..." | tee -a "${LOG_FILE}"
    
    pytest \
        --verbose \
        --junit-xml="${RESULTS_DIR}/unit-tests.xml" \
        --cov=. \
        --cov-report=term-missing \
        --cov-report=xml:"${RESULTS_DIR}/coverage.xml" \
        -m "not integration" \
        2>&1 | tee -a "${LOG_FILE}"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ ${exit_code} -eq 0 ]; then
        echo -e "${GREEN}Unit tests passed successfully${NC}" | tee -a "${LOG_FILE}"
    else
        echo -e "${RED}Unit tests failed${NC}" | tee -a "${LOG_FILE}"
    fi
    
    return ${exit_code}
}

run_integration_tests() {
    echo "Running integration tests..." | tee -a "${LOG_FILE}"
    
    pytest \
        --verbose \
        --junit-xml="${RESULTS_DIR}/integration-tests.xml" \
        --cov=. \
        --cov-append \
        --cov-report=term-missing \
        -m "integration" \
        2>&1 | tee -a "${LOG_FILE}"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ ${exit_code} -eq 0 ]; then
        echo -e "${GREEN}Integration tests passed successfully${NC}" | tee -a "${LOG_FILE}"
    else
        echo -e "${RED}Integration tests failed${NC}" | tee -a "${LOG_FILE}"
    fi
    
    return ${exit_code}
}

run_linting() {
    echo "Running code linting checks..." | tee -a "${LOG_FILE}"
    
    flake8 \
        --config=.flake8 \
        --tee \
        --output-file="${RESULTS_DIR}/flake8.txt" \
        2>&1 | tee -a "${LOG_FILE}"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ ${exit_code} -eq 0 ]; then
        echo -e "${GREEN}Linting checks passed successfully${NC}" | tee -a "${LOG_FILE}"
    else
        echo -e "${RED}Linting checks failed${NC}" | tee -a "${LOG_FILE}"
    fi
    
    return ${exit_code}
}

run_type_checks() {
    echo "Running type checks..." | tee -a "${LOG_FILE}"
    
    mypy \
        --strict \
        --junit-xml="${RESULTS_DIR}/type-check.xml" \
        . \
        2>&1 | tee -a "${LOG_FILE}"
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ ${exit_code} -eq 0 ]; then
        echo -e "${GREEN}Type checks passed successfully${NC}" | tee -a "${LOG_FILE}"
    else
        echo -e "${RED}Type checks failed${NC}" | tee -a "${LOG_FILE}"
    fi
    
    return ${exit_code}
}

check_coverage() {
    echo "Checking test coverage..." | tee -a "${LOG_FILE}"
    
    # Generate HTML coverage report
    coverage html --directory="${RESULTS_DIR}/htmlcov"
    
    # Get current coverage percentage
    local coverage_result=$(coverage report | tail -1 | awk '{print $NF}' | sed 's/%//')
    
    echo "Coverage: ${coverage_result}% (minimum: ${COVERAGE_MIN_THRESHOLD}%)" | tee -a "${LOG_FILE}"
    
    if (( $(echo "${coverage_result} < ${COVERAGE_MIN_THRESHOLD}" | bc -l) )); then
        echo -e "${RED}Coverage is below minimum threshold${NC}" | tee -a "${LOG_FILE}"
        return ${COVERAGE_FAILURE}
    else
        echo -e "${GREEN}Coverage check passed successfully${NC}" | tee -a "${LOG_FILE}"
        return ${SUCCESS}
    fi
}

cleanup() {
    echo "Generating test summary..." | tee -a "${LOG_FILE}"
    
    # Create summary file
    {
        echo "Test Execution Summary"
        echo "====================="
        echo "Timestamp: $(date)"
        echo "Results Directory: ${RESULTS_DIR}"
        echo ""
        echo "Test Results:"
        echo "------------"
        [ -f "${RESULTS_DIR}/unit-tests.xml" ] && echo "Unit Tests: $(grep 'failures=' "${RESULTS_DIR}/unit-tests.xml" | head -1)"
        [ -f "${RESULTS_DIR}/integration-tests.xml" ] && echo "Integration Tests: $(grep 'failures=' "${RESULTS_DIR}/integration-tests.xml" | head -1)"
        [ -f "${RESULTS_DIR}/flake8.txt" ] && echo "Linting Issues: $(wc -l < "${RESULTS_DIR}/flake8.txt")"
        [ -f "${RESULTS_DIR}/type-check.xml" ] && echo "Type Check Issues: $(grep 'failures=' "${RESULTS_DIR}/type-check.xml" | head -1)"
        echo ""
        echo "Coverage Report:"
        echo "---------------"
        coverage report || true
    } > "${RESULTS_DIR}/summary.txt"
    
    # Archive results
    tar -czf "test-results-${TIMESTAMP}.tar.gz" "${RESULTS_DIR}"
    
    echo -e "${YELLOW}Test results archived to: test-results-${TIMESTAMP}.tar.gz${NC}"
    echo -e "${YELLOW}Detailed summary available in: ${RESULTS_DIR}/summary.txt${NC}"
}

main() {
    local exit_code=${SUCCESS}
    
    # Set up trap for cleanup
    trap cleanup EXIT
    
    # Initialize test environment
    if ! setup_environment; then
        echo -e "${RED}Environment setup failed${NC}" | tee -a "${LOG_FILE}"
        return ${SETUP_FAILURE}
    fi
    
    # Run all test suites and quality checks
    run_unit_tests || exit_code=$?
    run_integration_tests || exit_code=$?
    run_linting || exit_code=$?
    run_type_checks || exit_code=$?
    check_coverage || exit_code=$?
    
    if [ ${exit_code} -eq 0 ]; then
        echo -e "${GREEN}All tests and checks passed successfully${NC}" | tee -a "${LOG_FILE}"
    else
        echo -e "${RED}Some tests or checks failed${NC}" | tee -a "${LOG_FILE}"
    fi
    
    return ${exit_code}
}

# Execute main function
main "$@"
```

This shell script provides a comprehensive test runner for the backend with the following features:

1. Strict shell execution mode with proper error handling
2. Environment setup and verification of required tools
3. Execution of unit tests and integration tests using pytest
4. Code quality checks with flake8
5. Static type checking with mypy
6. Test coverage verification against minimum threshold
7. Detailed logging and result archival
8. Color-coded console output for better readability
9. Cleanup operations with proper trap handling
10. Comprehensive test summary generation

The script follows all the requirements from the specification and implements proper error handling with specific exit codes for different types of failures. It also maintains detailed logs and generates comprehensive reports for test results, coverage, and quality checks.

The script should be made executable with:
```bash
chmod 755 src/backend/scripts/run-tests.sh