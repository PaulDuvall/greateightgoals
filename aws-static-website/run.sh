#!/bin/bash

# Main entry point script for the AWS Static Website solution
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
SCRIPTS_PATH="$SCRIPT_DIR/scripts"

# Default values
STACK_NAME="static-website"
REGION="us-east-1"
DOMAIN=""
CONTENT_DIR="./content"

# Function to display usage information
usage() {
    echo -e "${BLUE}AWS Static Website - Infrastructure Automation${NC}"
    echo ""
    echo "Usage: $0 <command> [options]"
    echo ""
    echo "Commands:"
    echo "  deploy [--domain-name <domain>] [--stack-name <stack-name>] [--region <aws-region>]  Deploy the static website infrastructure"
    echo "  update [--content-dir <dir>] [--stack-name <stack-name>] [--region <aws-region>]    Update website content"
    echo "  update-content [--content-dir <dir>] [--stack-name <stack-name>] [--region <aws-region>]    Update website content"
    echo "  invalidate [--stack-name <stack-name>] [--region <aws-region>]                      Invalidate CloudFront cache"
    echo "  status [--stack-name <stack-name>] [--region <aws-region>]                          Check stack status"
    echo "  deploy-updater [--schedule <rate>] [--stack-name <stack-name>] [--region <aws-region>]  Deploy the scheduled website updater"
    echo "  help                                                                                Display this help message"
    echo ""
    echo "For more information on a specific command, run: $0 <command> --help"
}

# Make sure the scripts are executable
chmod +x "$SCRIPTS_PATH/deploy.sh"
chmod +x "$SCRIPTS_PATH/update_content.sh"
chmod +x "$SCRIPTS_PATH/invalidate_cache.sh"

# Function to load environment variables if .env exists
load_env() {
    if [ -f "$SCRIPT_DIR/.env" ]; then
        source "$SCRIPT_DIR/.env"
        # Override defaults with values from .env
        STACK_NAME=${STATIC_WEBSITE_STACK_NAME:-$STACK_NAME}
        REGION=${AWS_REGION:-$REGION}
        DOMAIN=${STATIC_WEBSITE_DOMAIN:-$DOMAIN}
        CONTENT_DIR=${STATIC_WEBSITE_CONTENT_DIR:-$CONTENT_DIR}
    fi
}

# Load environment variables
load_env

# Check if a command was provided
if [ $# -eq 0 ]; then
    # Default behavior: show status if stack exists, otherwise show usage
    if aws cloudformation describe-stacks --stack-name "$STACK_NAME" --region "$REGION" &> /dev/null; then
        "$SCRIPTS_PATH/deploy.sh" --status --stack-name "$STACK_NAME" --region "$REGION"
    else
        usage
    fi
    exit 0
fi

# Parse command
COMMAND="$1"
shift

# Execute the appropriate script based on the command
case $COMMAND in
    deploy)
        "$SCRIPTS_PATH/deploy.sh" --stack-name "$STACK_NAME" --region "$REGION" "$@"
        ;;
    update)
        "$SCRIPTS_PATH/update_content.sh" --stack-name "$STACK_NAME" --region "$REGION" --content-dir "$CONTENT_DIR" "$@"
        ;;
    update-content)
        "$SCRIPTS_PATH/update_content.sh" --stack-name "$STACK_NAME" --region "$REGION" --content-dir "$CONTENT_DIR" "$@"
        ;;
    invalidate)
        "$SCRIPTS_PATH/invalidate_cache.sh" --stack-name "$STACK_NAME" --region "$REGION" "$@"
        ;;
    deploy-updater)
        if [ "$1" == "--help" ]; then
            echo "Usage: $0 deploy-updater [--schedule <schedule-expression>] [--stack-name <stack-name>] [--region <aws-region>]"
            echo ""
            echo "Options:"
            echo "  --schedule       Schedule expression for updates (default: rate(1 hour))"
            echo "  --stack-name     CloudFormation stack name for the updater (default: ovechkin-website-updater)"
            echo "  --website-stack  Name of the static website stack (default: $STACK_NAME)"
            echo "  --region         AWS region (default: $REGION)"
            exit 0
        fi
        
        # Make the deploy script executable
        chmod +x "$SCRIPTS_PATH/deploy_updater.sh"
        
        # Pass all arguments to the deploy script, including the website stack name
        "$SCRIPTS_PATH/deploy_updater.sh" --website-stack "$STACK_NAME" --region "$REGION" "$@"
        ;;
    status)
        if [ "$1" == "--help" ]; then
            echo "Usage: $0 status [--stack-name <stack-name>] [--region <aws-region>]"
            echo ""
            echo "Options:"
            echo "  --stack-name     CloudFormation stack name (default: $STACK_NAME)"
            echo "  --region         AWS region (default: $REGION)"
            exit 0
        fi
        
        # Parse arguments for status command
        while [[ $# -gt 0 ]]; do
            key="$1"
            case $key in
                --stack-name)
                    STACK_NAME="$2"
                    shift 2
                    ;;
                --region)
                    REGION="$2"
                    shift 2
                    ;;
                *)
                    echo "Unknown option: $1"
                    echo "Run '$0 status --help' for usage information."
                    exit 1
                    ;;
            esac
        done
        
        echo -e "${BLUE}Checking status of stack: $STACK_NAME${NC}"
        aws cloudformation describe-stacks \
            --stack-name "$STACK_NAME" \
            --query "Stacks[0].{Status:StackStatus, Outputs:Outputs}" \
            --output table \
            --region "$REGION"
        ;;
    help)
        usage
        ;;
    *)
        echo -e "${YELLOW}Unknown command: $COMMAND${NC}"
        usage
        ;;
esac
