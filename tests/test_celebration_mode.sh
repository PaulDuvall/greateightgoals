#!/bin/bash

# Test script for verifying the celebration mode functionality
# This script tests both the standard website update and the celebration mode

# Define colors for output
RED="\033[0;31m"
GREEN="\033[0;32m"
YELLOW="\033[0;33m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Create a temporary directory for testing
TEST_DIR="$(mktemp -d)"
echo -e "${BLUE}Created temporary test directory: $TEST_DIR${NC}"

# Function to clean up when the script exits
cleanup() {
    echo -e "${BLUE}Cleaning up temporary test directory...${NC}"
    rm -rf "$TEST_DIR"
    echo -e "${BLUE}Cleanup complete.${NC}"
}

# Register the cleanup function to run when the script exits
trap cleanup EXIT

# Function to run a test and report the result
run_test() {
    local test_name=$1
    local command=$2
    local expected_pattern=$3
    local unexpected_pattern=$4
    
    echo -e "\n${YELLOW}Running test: $test_name${NC}"
    echo -e "${BLUE}Command: $command${NC}"
    
    # Run the command
    eval "$command"
    local exit_code=$?
    
    if [ $exit_code -ne 0 ]; then
        echo -e "${RED}Test failed: Command returned non-zero exit code $exit_code${NC}"
        return 1
    fi
    
    # Check if the index.html file exists
    if [ ! -f "$PROJECT_ROOT/aws-static-website/static/index.html" ]; then
        echo -e "${RED}Test failed: index.html file was not created${NC}"
        return 1
    fi
    
    # Copy the index.html file to the test directory for analysis
    cp "$PROJECT_ROOT/aws-static-website/static/index.html" "$TEST_DIR/index.html"
    
    # Check for expected pattern
    if ! grep -qE "$expected_pattern" "$TEST_DIR/index.html"; then
        echo -e "${RED}Test failed: Expected pattern '$expected_pattern' not found in index.html${NC}"
        return 1
    fi
    
    # Check for unexpected pattern (if provided)
    if [ -n "$unexpected_pattern" ] && grep -qE "$unexpected_pattern" "$TEST_DIR/index.html"; then
        echo -e "${RED}Test failed: Unexpected pattern '$unexpected_pattern' found in index.html${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Test passed: $test_name${NC}"
    return 0
}

# Function to run all tests
run_all_tests() {
    local failures=0
    
    # Test 1: Standard website update
    if ! run_test "Standard website update" \
        "cd $PROJECT_ROOT && ./run.sh update-website" \
        "Ovechkin Goal Tracker" \
        "RECORD BROKEN"; then
        ((failures++))
    fi
    
    # Test 2: Celebration mode
    if ! run_test "Celebration mode" \
        "cd $PROJECT_ROOT && ./run.sh update-website --celebrate" \
        "RECORD BROKEN" \
        ""; then
        ((failures++))
    fi
    
    # Test 3: Verify celebration content has specific elements
    if ! run_test "Celebration content verification" \
        "cd $PROJECT_ROOT && ./run.sh update-website --celebrate" \
        "surpassed Wayne Gretzky" \
        ""; then
        ((failures++))
    fi
    
    # Test 4: Verify confetti animation is present in celebration mode
    if ! run_test "Confetti animation verification" \
        "cd $PROJECT_ROOT && ./run.sh update-website --celebrate" \
        "confetti" \
        ""; then
        ((failures++))
    fi
    
    # Test 5: Verify goal numbers are present in celebration mode
    if ! run_test "Goal numbers verification" \
        "cd $PROJECT_ROOT && ./run.sh update-website --celebrate" \
        "895" \
        ""; then
        ((failures++))
    fi
    
    # Report overall results
    if [ $failures -eq 0 ]; then
        echo -e "\n${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}$failures test(s) failed.${NC}"
        return 1
    fi
}

# Main execution
echo -e "${YELLOW}Starting celebration mode tests...${NC}"
run_all_tests
exit $?
