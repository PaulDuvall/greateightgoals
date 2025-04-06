#!/bin/bash

# Test script for verifying the AWS Lambda function handles the celebration flag
# This script tests the Lambda function's ability to process the celebrate parameter

# Define colors for output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Set environment variable for local testing
export LOCAL_DEV=true

# Function to run a test and report the result
run_lambda_test() {
    local test_name=$1
    local event_json=$2
    local expected_output=$3
    
    echo -e "\n${YELLOW}Running test: $test_name${NC}"
    
    # Create a temporary event file
    local event_file="$SCRIPT_DIR/temp_event.json"
    echo "$event_json" > "$event_file"
    
    echo -e "${BLUE}Event: $event_json${NC}"
    
    # Setup and activate the virtual environment
    cd "$PROJECT_ROOT"
    source ./.venv/bin/activate
    
    # Run the Lambda function locally
    output=$(python3 "$PROJECT_ROOT/aws-static-website/update_website_lambda.py" "$event_file" 2>&1)
    local exit_code=$?
    
    echo -e "${BLUE}Output: $output${NC}"
    
    # Clean up the temporary event file
    rm -f "$event_file"
    
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}Test failed: Lambda function returned non-zero exit code $exit_code${NC}"
        return 1
    fi
    
    # Check for expected output
    if ! echo "$output" | grep -q "$expected_output"; then
        echo -e "${RED}Test failed: Expected output '$expected_output' not found in Lambda response${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Test passed: $test_name${NC}"
    return 0
}

# Function to run all tests
run_all_lambda_tests() {
    local failures=0
    
    # Test 1: Standard Lambda invocation
    if ! run_lambda_test "Standard Lambda invocation" \
        '{"source": "aws.events"}' \
        "Website updated successfully"; then
        ((failures++))
    fi
    
    # Test 2: Lambda invocation with celebration flag
    if ! run_lambda_test "Lambda invocation with celebration flag" \
        '{"source": "aws.events", "celebrate": true}' \
        "Celebration mode activated"; then
        ((failures++))
    fi
    
    # Report overall results
    if [ $failures -eq 0 ]; then
        echo -e "\n${GREEN}All Lambda tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}$failures Lambda test(s) failed.${NC}"
        return 1
    fi
}

# Main execution
echo -e "${YELLOW}Starting Lambda celebration mode tests...${NC}"
run_all_lambda_tests
exit $?
