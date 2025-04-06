#!/bin/bash

# Ovechkin Goal Tracker - run.sh
# Main entry point for the Ovechkin Goal Tracker application

set -e

# Define colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Define the virtual environment directory
VENV_DIR=".venv"

# Function to check and update required AWS Parameter Store parameters
check_ssm_params() {
    # Skip this function in test mode
    if [ "${TEST_MODE:-0}" == "1" ]; then
        echo -e "${BLUE}Running in TEST_MODE, skipping AWS Parameter Store checks...${NC}"
        return 0
    fi
    
    echo -e "${BLUE}Checking AWS Parameter Store parameters...${NC}"
    
    # Define the SSM parameter prefix used for this app
    local prefix="/ovechkin-tracker"
    
    # List of required parameter names (without prefix)
    local params=("aws_region" "sender_email" "recipient_email")
    
    # Check if AWS CLI is installed
    if ! command -v aws &> /dev/null; then
        echo -e "${YELLOW}AWS CLI is not installed. Skipping Parameter Store check.${NC}"
        return 1
    fi
    
    # Check if user is authenticated with AWS
    if ! aws sts get-caller-identity &> /dev/null; then
        echo -e "${YELLOW}Not authenticated with AWS. Skipping Parameter Store check.${NC}"
        return 1
    fi
    
    # Loop over each required parameter
    for param in "${params[@]}"; do
        # Construct the full parameter name
        local full_param="${prefix}/${param}"
        
        # Attempt to retrieve the parameter from AWS Parameter Store
        echo -e "Checking parameter: ${full_param}"
        local value
        if ! value=$(aws ssm get-parameter --name "$full_param" --with-decryption --query 'Parameter.Value' --output text 2>/dev/null); then
            echo -e "${YELLOW}Parameter $full_param not found in Parameter Store.${NC}"
            value=""
        fi
        
        # If the parameter is missing or has a blank value, prompt the user for input
        if [ -z "$value" ] || [ "$value" = "None" ]; then
            echo -e "Parameter $full_param is missing or empty."
            
            # If .env file exists, try to get value from there first
            local env_value=""
            if [ -f ".env" ]; then
                case "$param" in
                    aws_region)
                        env_value=$(grep -E '^AWS_REGION=' .env | cut -d= -f2)
                        ;;
                    sender_email)
                        env_value=$(grep -E '^SENDER_EMAIL=' .env | cut -d= -f2)
                        ;;
                    recipient_email)
                        env_value=$(grep -E '^RECIPIENT_EMAIL=' .env | cut -d= -f2)
                        ;;
                esac
                
                if [ -n "$env_value" ]; then
                    echo -e "Found value in .env file: $env_value"
                    echo -e "Would you like to use this value for Parameter Store? (y/n): "
                    read -r use_env_value
                    
                    if [[ $use_env_value == "y" || $use_env_value == "Y" ]]; then
                        value="$env_value"
                    fi
                fi
            fi
            
            # If still no value, prompt user
            while [ -z "$value" ] || [ "$value" = "None" ]; do
                echo -e "Please enter a valid value for $param:"
                read -r new_value
                
                # Check if a non-empty value was provided
                if [ -n "$new_value" ]; then
                    # Update the parameter in Parameter Store
                    echo -e "Updating parameter $full_param in Parameter Store..."
                    if aws ssm put-parameter --name "$full_param" --value "$new_value" --type String --overwrite 2>/dev/null; then
                        echo -e "${GREEN}Successfully updated $full_param in Parameter Store.${NC}"
                        value="$new_value"
                    else
                        echo -e "${RED}Error: Could not update $full_param. Please check your AWS permissions.${NC}"
                        break
                    fi
                fi
            done
        else
            echo -e "${GREEN}Parameter $full_param exists with a non-empty value.${NC}"
        fi
    done
    
    echo -e "${GREEN}AWS Parameter Store check completed.${NC}"
    return 0
}

# Function to print usage information
print_usage() {
    echo -e "${BLUE}Ovechkin Goal Tracker - Usage${NC}"
    echo -e "\nUsage: ./run.sh [command] [options]\n"
    echo -e "Commands:"
    echo -e "  ${GREEN}setup${NC}       - Set up the virtual environment and install dependencies"
    echo -e "  ${GREEN}setup-lambda${NC} - Set up the environment with Lambda-specific dependencies"
    echo -e "  ${GREEN}stats${NC}       - Display Ovechkin's current stats"
    echo -e "  ${GREEN}email${NC}       - Send an email to the default recipient"
    echo -e "  ${GREEN}email-to${NC}    - Send an email to a specific address"
    echo -e "  ${GREEN}configure${NC}   - Configure email settings"
    echo -e "  ${GREEN}test-lambda${NC} - Test the Lambda function locally"
    echo -e "  ${GREEN}test${NC}        - Run all tests"
    echo -e "  ${GREEN}install-test-deps${NC} - Install test dependencies (pytest-cov)"
    echo -e "  ${GREEN}update-website${NC} - Update the static website with the latest Ovechkin stats"
    echo -e "  ${GREEN}update-schedule${NC} - Update the EventBridge schedule for the website updater"
    echo -e "  ${GREEN}deploy${NC}      - Deploy the static website infrastructure"
    echo -e "  ${GREEN}update-content${NC} - Update the static website content"
    echo -e "  ${GREEN}invalidate${NC}  - Invalidate the CloudFront cache"
    echo -e "  ${GREEN}status${NC}      - Check the CloudFormation stack status"
    echo -e "  ${GREEN}help${NC}        - Display this help message"
    echo -e "\nExamples:"
    echo -e "  ./run.sh setup"
    echo -e "  ./run.sh stats"
    echo -e "  ./run.sh email"
    echo -e "  ./run.sh email-to user@example.com"
    echo -e "  ./run.sh test-lambda"
    echo -e "  ./run.sh test"
    echo -e "  ./run.sh install-test-deps"
    echo -e "  ./run.sh update-website"
    echo -e "  ./run.sh update-schedule --schedule 'rate(3 minutes)'"
    echo -e "  ./run.sh deploy"
    echo -e "  ./run.sh update-content"
    echo -e "  ./run.sh invalidate"
    echo -e "  ./run.sh status"
    echo -e "  ./run.sh help"
}

# Function to set up the virtual environment
setup_env() {
    echo -e "${BLUE}Setting up virtual environment...${NC}"
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}Python 3 is not installed. Please install Python 3 and try again.${NC}"
        exit 1
    fi
    
    # Check if virtual environment exists and has a valid interpreter
    if [ -d "$VENV_DIR" ]; then
        # Test if the virtual environment's Python interpreter is valid
        if ! "$VENV_DIR/bin/python3" --version &> /dev/null; then
            echo -e "${YELLOW}Existing virtual environment has an invalid Python interpreter. Recreating...${NC}"
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
        fi
    else
        # Create virtual environment if it doesn't exist
        echo -e "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install dependencies
    echo -e "Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r requirements.txt
    
    echo -e "${GREEN}Setup complete!${NC}"
}

# Function to set up the virtual environment with Lambda dependencies
setup_lambda_env() {
    echo -e "${BLUE}Setting up Lambda environment...${NC}"
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        echo -e "${YELLOW}Python 3 is not installed. Please install Python 3 and try again.${NC}"
        exit 1
    fi
    
    # Check if virtual environment exists and has a valid interpreter
    if [ -d "$VENV_DIR" ]; then
        # Test if the virtual environment's Python interpreter is valid
        if ! "$VENV_DIR/bin/python3" --version &> /dev/null; then
            echo -e "${YELLOW}Existing virtual environment has an invalid Python interpreter. Recreating...${NC}"
            rm -rf "$VENV_DIR"
            python3 -m venv "$VENV_DIR"
        fi
    else
        # Create virtual environment if it doesn't exist
        echo -e "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment
    source "$VENV_DIR/bin/activate"
    
    # Install dependencies from both requirements files
    echo -e "Installing dependencies..."
    "$VENV_DIR/bin/pip" install --upgrade pip
    "$VENV_DIR/bin/pip" install -r requirements.txt
    
    # Check if Lambda requirements file exists
    if [ -f "lambda/requirements-lambda.txt" ]; then
        "$VENV_DIR/bin/pip" install -r lambda/requirements-lambda.txt
    else
        echo -e "${YELLOW}Lambda requirements file not found. Skipping Lambda-specific dependencies.${NC}"
    fi
    
    echo -e "${GREEN}Lambda setup complete!${NC}"
}

# Function to activate the virtual environment
activate_venv() {
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        echo -e "Virtual environment activated."
    else
        echo -e "${YELLOW}Virtual environment not found. Running setup...${NC}"
        setup_env
    fi
}

# Function to activate the virtual environment with Lambda dependencies
activate_lambda_venv() {
    if [ -d "$VENV_DIR" ]; then
        source "$VENV_DIR/bin/activate"
        echo -e "Virtual environment activated."
    else
        echo -e "${YELLOW}Virtual environment not found. Running Lambda setup...${NC}"
        setup_lambda_env
    fi
}

# Function to display Ovechkin stats
show_stats() {
    activate_venv
    
    echo -e "${BLUE}Displaying Ovechkin stats...${NC}"
    
    # Set up debug logging if DEBUG environment variable is set
    if [ -n "${DEBUG:-}" ]; then
        python3 -c "import logging; logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')" &>/dev/null
        python3 main.py stats
    else
        python3 main.py stats
    fi
    
    echo -e "\n${GREEN}Ovechkin Goal Tracker - Stats displayed successfully!${NC}"
}

# Function to configure email settings
configure_email() {
    activate_venv
    echo -e "${BLUE}Configuring Email Settings${NC}"
    
    # Check if .env file exists
    if [ -f ".env" ] && [ "${TEST_MODE:-0}" != "1" ]; then
        echo -e "Existing .env file found."
        echo -e "Would you like to update it? (y/n): "
        read -r update_env
        
        if [[ $update_env != "y" && $update_env != "Y" ]]; then
            echo -e "Configuration unchanged."
            return
        fi
    fi
    
    # Get AWS region
    echo -e "\nEnter AWS Region (default: us-east-1): "
    read -r aws_region
    aws_region=${aws_region:-us-east-1}
    
    # Get sender email
    echo -e "\nEnter Sender Email (must be verified in SES): "
    read -r sender_email
    
    # Get recipient email
    echo -e "\nEnter Default Recipient Email: "
    read -r recipient_email
    
    # Write to .env file
    echo "# Ovechkin Tracker Email Configuration" > .env
    echo "AWS_REGION=$aws_region" >> .env
    echo "SENDER_EMAIL=$sender_email" >> .env
    echo "RECIPIENT_EMAIL=$recipient_email" >> .env
    
    echo -e "\n${GREEN}Email configuration saved to .env file.${NC}"
    echo -e "${YELLOW}Note: Make sure the sender email is verified in Amazon SES.${NC}"
    echo -e "${YELLOW}If you want to use AWS Parameter Store instead, set up the parameters manually.${NC}"
}

# Function to send email with Ovechkin stats
send_email() {
    activate_venv
    
    if [ "$1" == "" ]; then
        echo -e "Attempting to send email with default recipient..."
        python3 main.py email
    else
        echo -e "Attempting to send email to $1..."
        python3 main.py email-to "$1"
    fi
}

# Function to test the Lambda function locally
test_lambda() {
    activate_lambda_venv
    
    echo -e "${BLUE}Testing Lambda function locally...${NC}"
    
    # Check if test script exists in tests directory
    if [ -f "tests/test_lambda_local.py" ]; then
        python3 tests/test_lambda_local.py "$@"
    else
        # Fallback to direct lambda_function.py execution
        echo -e "${YELLOW}tests/test_lambda_local.py not found, running lambda_function.py directly${NC}"
        python3 lambda/lambda_function.py
    fi
}

# Function to install test dependencies
install_test_deps() {
    echo -e "${BLUE}Installing test dependencies...${NC}"
    
    # Check if virtual environment exists
    if [ ! -d "$VENV_DIR" ]; then
        echo -e "${YELLOW}Virtual environment not found. Setting up first...${NC}"
        setup_env
    else
        # Activate virtual environment
        source "$VENV_DIR/bin/activate"
    fi
    
    # Install pytest-cov
    echo -e "Installing pytest-cov..."
    "$VENV_DIR/bin/pip" install pytest-cov
    
    echo -e "${GREEN}Test dependencies installed!${NC}"
}

# Function to run all tests
run_tests() {
    activate_venv
    
    echo -e "${BLUE}Running all tests...${NC}"
    
    # Run pytest with verbose output and coverage reporting
    python -m pytest tests/ -v --cov=ovechkin_tracker --cov=lambda --cov-report=term-missing
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}All tests passed!${NC}"
    else
        echo -e "${RED}Some tests failed.${NC}"
        exit 1
    fi
}

# Function to update the static website with the latest Ovechkin stats
update_website() {
    echo -e "${BLUE}Updating website with the latest Ovechkin stats...${NC}"
    
    # Check if the celebrate flag is provided
    if [ "$1" == "--celebrate" ]; then
        echo -e "${BLUE}Activating celebration mode for Ovechkin breaking Gretzky's record!${NC}"
        
        # Get the directory where the script is located
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        
        # Setup and activate the virtual environment
        setup_env
        activate_venv
        
        # Run the celebration script
        python3 "$SCRIPT_DIR/aws-static-website/celebrate.py"
    else
        # Get the directory where the script is located
        SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
        
        # Setup and activate the virtual environment
        setup_env
        activate_venv
        
        # Run the update_website.py script
        python3 "$SCRIPT_DIR/aws-static-website/update_website.py"
    fi
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Website updated successfully!${NC}"
        echo -e "${YELLOW}To deploy the updated website, run the CloudFormation deployment script.${NC}"
    else
        echo -e "${RED}Failed to update website. See error messages above.${NC}"
        return 1
    fi
}

# Function to update the EventBridge schedule for the website updater
update_schedule() {
    echo -e "${BLUE}Updating EventBridge schedule for website updater...${NC}"
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Call the update_schedule.sh script with all arguments passed to this function
    "$SCRIPT_DIR/aws-static-website/scripts/update_schedule.sh" "$@"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Schedule update completed successfully!${NC}"
    else
        echo -e "${RED}Schedule update failed. See error messages above.${NC}"
        exit 1
    fi
}

# Function to deploy the static website infrastructure
deploy() {
    echo -e "${BLUE}Deploying static website infrastructure...${NC}"
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Call the deploy.sh script with all arguments passed to this function
    "$SCRIPT_DIR/aws-static-website/scripts/deploy.sh" "$@"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Deployment completed successfully!${NC}"
    else
        echo -e "${RED}Deployment failed. See error messages above.${NC}"
        exit 1
    fi
}

# Function to update the static website content
update_content() {
    update_website
}

# Function to invalidate the CloudFront cache
invalidate() {
    echo -e "${BLUE}Invalidating CloudFront cache...${NC}"
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Call the invalidate_cloudfront.sh script with all arguments passed to this function
    "$SCRIPT_DIR/aws-static-website/scripts/invalidate_cloudfront.sh" "$@"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Cache invalidation completed successfully!${NC}"
    else
        echo -e "${RED}Cache invalidation failed. See error messages above.${NC}"
        exit 1
    fi
}

# Function to check the CloudFormation stack status
status() {
    echo -e "${BLUE}Checking CloudFormation stack status...${NC}"
    
    # Get the directory where the script is located
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    
    # Call the check_status.sh script with all arguments passed to this function
    "$SCRIPT_DIR/aws-static-website/scripts/check_status.sh" "$@"
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Status check completed successfully!${NC}"
    else
        echo -e "${RED}Status check failed. See error messages above.${NC}"
        exit 1
    fi
}

# Main script logic
if [ $# -eq 0 ]; then
    print_usage
    exit 0
fi

check_ssm_params

command=$1
shift

case $command in
    setup)
        setup_env
        ;;
    setup-lambda)
        setup_lambda_env
        ;;
    stats)
        show_stats
        ;;
    email)
        send_email
        ;;
    email-to)
        if [ $# -eq 0 ]; then
            echo -e "${YELLOW}Error: No email address provided.${NC}"
            echo -e "Usage: ./run.sh email-to user@example.com"
            exit 1
        fi
        send_email "$1"
        ;;
    configure)
        configure_email
        ;;
    test-lambda)
        test_lambda "$@"
        ;;
    test)
        run_tests
        ;;
    install-test-deps)
        install_test_deps
        ;;
    update-website)
        update_website "$@"
        ;;
    update-content)
        update_website
        ;;
    update-schedule)
        update_schedule "$@"
        ;;
    deploy)
        deploy "$@"
        ;;
    invalidate)
        invalidate "$@"
        ;;
    status)
        status "$@"
        ;;
    help)
        print_usage
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $command${NC}"
        print_usage
        exit 1
        ;;
esac