#!/bin/bash

# Deploy Website Updater Script
# This script deploys the Lambda function and CloudFormation stack for scheduled website updates

set -e

# Define colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Function to display usage information
usage() {
    echo "Usage: $0 [--stack-name <stack-name>] [--region <aws-region>] [--schedule <schedule-expression>]" >&2
    echo ""
    echo "Options:"
    echo "  --stack-name     CloudFormation stack name for the website updater (default: ovechkin-website-updater)"
    echo "  --website-stack  Name of the static website CloudFormation stack (default: static-website)"
    echo "  --region         AWS region (default: us-east-1)"
    echo "  --schedule       Schedule expression for updates (default: cron(0 * * * ? *) - run at the top of every hour)"
    echo "                   Examples:"
    echo "                   - cron(0 * * * ? *)     - Run at the top of every hour (00:00)"
    echo "                   - cron(15 * * * ? *)    - Run at 15 minutes past every hour (00:15)"
    echo "                   - cron(0/30 * * * ? *)  - Run every 30 minutes, starting at the top of the hour"
    echo "                   - cron(0 0/2 * * ? *)   - Run every 2 hours, starting at midnight UTC"
    echo "                   - rate(30 minutes)      - Run every 30 minutes (not synchronized to clock)"
    echo "  --help           Display this help message"
    exit 1
}

# Function to get parameter from SSM Parameter Store
get_parameter() {
    local param_name=$1
    local param_value
    
    # Try to get the parameter from SSM
    param_value=$(aws ssm get-parameter --name "$param_name" --with-decryption --query "Parameter.Value" --output text 2>/dev/null)
    
    # Return the value (will be empty if the parameter doesn't exist)
    echo "$param_value"
}

# Default values
STACK_NAME="ovechkin-website-updater"
WEBSITE_STACK="static-website"
REGION=${REGION:-$(get_parameter "/ovechkin-tracker/aws_region")}
REGION=${REGION:-us-east-1}  # Default to us-east-1 if not set and not in Parameter Store
SCHEDULE="cron(0 * * * ? *)"

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_ROOT="$(dirname "$ROOT_DIR")"
CF_TEMPLATE="$ROOT_DIR/cloudformation/website-updater.yaml"
LAMBDA_DIR="$ROOT_DIR/lambda"
BUILD_DIR="$ROOT_DIR/build"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --website-stack)
            WEBSITE_STACK="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --schedule)
            SCHEDULE="$2"
            shift 2
            ;;
        --help)
            usage
            ;;
        *)
            echo "Unknown option: $1"
            usage
            ;;
    esac
done

# Create build directory if it doesn't exist
mkdir -p "$BUILD_DIR"

echo -e "${BLUE}Building Lambda deployment package...${NC}"

# Create a temporary directory for packaging
TMP_DIR=$(mktemp -d)
echo "Using temporary directory: $TMP_DIR"

# Copy Lambda function code
cp "$LAMBDA_DIR/update_website_lambda.py" "$TMP_DIR/"

# Copy the update_website.py script directly into the Lambda package
cp "$ROOT_DIR/update_website.py" "$TMP_DIR/"

# Create a directory structure for the static content
mkdir -p "$TMP_DIR/static"
cp -r "$ROOT_DIR/static"/* "$TMP_DIR/static/" 2>/dev/null || echo "No static files found to copy"

# Copy the ovechkin_tracker module if it exists
if [ -d "$PROJECT_ROOT/ovechkin_tracker" ]; then
    echo -e "${BLUE}Copying ovechkin_tracker module...${NC}"
    # Create the module directory at the root level of the Lambda package
    mkdir -p "$TMP_DIR/ovechkin_tracker"
    cp -r "$PROJECT_ROOT/ovechkin_tracker"/* "$TMP_DIR/ovechkin_tracker/"
    
    # Create an __init__.py file if it doesn't exist to make it a proper Python package
    if [ ! -f "$TMP_DIR/ovechkin_tracker/__init__.py" ]; then
        echo -e "${BLUE}Creating __init__.py file for ovechkin_tracker module...${NC}"
        touch "$TMP_DIR/ovechkin_tracker/__init__.py"
    fi
fi

# Copy the assets directory from the aws-static-website directory
if [ -d "$ROOT_DIR/assets" ]; then
    echo -e "${BLUE}Copying assets directory...${NC}"
    mkdir -p "$TMP_DIR/assets"
    cp -r "$ROOT_DIR/assets"/* "$TMP_DIR/assets/"
fi

# Install dependencies
echo -e "${BLUE}Installing dependencies...${NC}"
pip install -r "$LAMBDA_DIR/requirements-lambda.txt" -t "$TMP_DIR"

# Create zip file
echo -e "${BLUE}Creating deployment package...${NC}"
cd "$TMP_DIR"
zip -r "$BUILD_DIR/lambda_package.zip" .

# Deploy CloudFormation stack
echo -e "${BLUE}Deploying CloudFormation stack: $STACK_NAME${NC}"
aws cloudformation deploy \
    --template-file "$CF_TEMPLATE" \
    --stack-name "$STACK_NAME" \
    --parameter-overrides \
        StackName="$WEBSITE_STACK" \
        ScheduleExpression="$SCHEDULE" \
    --capabilities CAPABILITY_IAM \
    --region "$REGION"

# Update Lambda function code
echo -e "${BLUE}Updating Lambda function code...${NC}"
aws lambda update-function-code \
    --function-name ovechkin-website-updater \
    --zip-file fileb://"$BUILD_DIR/lambda_package.zip" \
    --region "$REGION"

# Clean up
rm -rf "$TMP_DIR"

echo -e "${GREEN}Website updater deployed successfully!${NC}"
echo -e "The website will be updated according to the schedule: $SCHEDULE"

# Get the Lambda function details
echo -e "${BLUE}Lambda function details:${NC}"
aws lambda get-function \
    --function-name ovechkin-website-updater \
    --query "Configuration.{FunctionName:FunctionName, Runtime:Runtime, Timeout:Timeout, MemorySize:MemorySize, LastModified:LastModified}" \
    --output table \
    --region "$REGION"

# Get the EventBridge rule details
echo -e "${BLUE}EventBridge rule details:${NC}"
aws events describe-rule \
    --name ovechkin-website-update-schedule \
    --query "{Name:Name, ScheduleExpression:ScheduleExpression, State:State}" \
    --output table \
    --region "$REGION"
