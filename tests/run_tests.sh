#!/bin/bash

# Run tests for the AWS Static Website Infrastructure
# Following the twelve-factor app methodology

set -e

# Define colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"

# Default values
RUN_UNIT_TESTS=true
RUN_INTEGRATION_TESTS=false
GENERATE_COVERAGE=false
PYTHON_CMD="python3"
VENV_DIR="$ROOT_DIR/.venv"

# Function to display usage information
usage() {
    echo -e "${BLUE}AWS Static Website - Test Runner${NC}"
    echo ""
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --all                Run all tests (default)"
    echo "  --unit               Run unit tests only"
    echo "  --integration        Run integration tests only (requires AWS credentials)"
    echo "  --coverage           Generate test coverage report"
    echo "  --python <cmd>       Python command to use (default: python3)"
    echo "  --help               Display this help message"
    echo ""
    echo "Examples:"
    echo "  $0                   Run unit tests (default)"
    echo "  $0 --all --coverage  Run all tests with coverage report"
    echo "  $0 --unit            Run only unit tests"
    echo "  $0 --integration     Run only integration tests"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --all)
            RUN_UNIT_TESTS=true
            RUN_INTEGRATION_TESTS=true
            shift
            ;;
        --unit)
            RUN_UNIT_TESTS=true
            RUN_INTEGRATION_TESTS=false
            shift
            ;;
        --integration)
            RUN_UNIT_TESTS=false
            RUN_INTEGRATION_TESTS=true
            shift
            ;;
        --coverage)
            GENERATE_COVERAGE=true
            shift
            ;;
        --python)
            PYTHON_CMD="$2"
            shift 2
            ;;
        --help)
            usage
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Unknown option: $1${NC}"
            usage
            exit 1
            ;;
    esac
 done

# Check if Python is installed
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo -e "${RED}$PYTHON_CMD is required but not installed. Please install Python 3.${NC}"
    exit 1
fi

# Create and activate virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv "$VENV_DIR"
fi

# Activate virtual environment
source "$VENV_DIR/bin/activate"

# Install test dependencies
echo -e "${BLUE}Installing test dependencies...${NC}"
pip install -q -r "$SCRIPT_DIR/requirements-test.txt"

# Run unit tests
if [ "$RUN_UNIT_TESTS" = true ]; then
    echo -e "${BLUE}Running unit tests...${NC}"
    
    if [ "$GENERATE_COVERAGE" = true ]; then
        python -m pytest "$SCRIPT_DIR" -v --cov=aws-static-website --cov-report=term --cov-report=html:"$ROOT_DIR/coverage"
    else
        python -m pytest "$SCRIPT_DIR" -v
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Unit tests passed!${NC}"
    else
        echo -e "${RED}Unit tests failed.${NC}"
        exit 1
    fi
fi

# Run integration tests (if AWS credentials are available)
if [ "$RUN_INTEGRATION_TESTS" = true ]; then
    echo -e "${BLUE}Checking AWS credentials...${NC}"
    if aws sts get-caller-identity &> /dev/null; then
        echo -e "${BLUE}Running integration tests...${NC}"
        
        # Currently, we don't have integration tests that require actual AWS resources
        # This section can be expanded when integration tests are added
        echo -e "${YELLOW}No integration tests defined yet. Skipping.${NC}"
    else
        echo -e "${RED}AWS credentials not found or invalid. Skipping integration tests.${NC}"
        echo -e "To run integration tests, configure your AWS credentials using:"
        echo -e "  aws configure"
        exit 1
    fi
fi

# Deactivate virtual environment
deactivate

echo -e "${GREEN}All tests completed successfully!${NC}"
