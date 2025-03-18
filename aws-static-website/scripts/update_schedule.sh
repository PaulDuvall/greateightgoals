#!/bin/bash

# Update EventBridge Schedule Script
# This script updates the schedule expression for the Ovechkin website updater EventBridge rule

set -e

# Define colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Function to display usage information
usage() {
    echo "Usage: $0 [--rule-name <rule-name>] [--region <aws-region>] [--schedule <schedule-expression>]" >&2
    echo ""
    echo "Options:"
    echo "  --rule-name     EventBridge rule name (default: ovechkin-website-update-schedule)"
    echo "  --region        AWS region (default: us-east-1)"
    echo "  --schedule      Schedule expression for updates (required)"
    echo "  --help          Display this help message"
    echo ""
    echo "Schedule Expression Examples:"
    echo "  rate(15 minutes) - Run every 15 minutes"
    echo "  rate(1 hour)     - Run every hour"
    echo "  rate(1 day)      - Run every day"
    echo "  cron(0 */1 * * ? *) - Run every hour at the top of the hour"
    echo "  cron(0 12 * * ? *) - Run at 12:00 PM UTC every day"
    exit 1
}

# Default values
RULE_NAME="ovechkin-website-update-schedule"
REGION="us-east-1"
SCHEDULE=""

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --rule-name)
            RULE_NAME="$2"
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

# Check if schedule is provided
if [ -z "$SCHEDULE" ]; then
    echo -e "${RED}Error: Schedule expression is required.${NC}"
    usage
fi

# Validate schedule expression format
if [[ ! "$SCHEDULE" =~ ^(rate\([0-9]+\ (minute|minutes|hour|hours|day|days)\)|cron\(.+\))$ ]]; then
    echo -e "${YELLOW}Warning: Schedule expression format may not be valid.${NC}"
    echo -e "Valid examples: rate(15 minutes), rate(1 hour), cron(0 12 * * ? *)"
    echo -e "Do you want to continue? (y/n)"
    read -r continue_anyway
    if [[ ! "$continue_anyway" =~ ^[Yy]$ ]]; then
        echo -e "Aborting."
        exit 1
    fi
fi

# Update the EventBridge rule schedule
echo -e "${BLUE}Updating EventBridge rule schedule...${NC}"
echo -e "Rule name: $RULE_NAME"
echo -e "New schedule: $SCHEDULE"

# Check if the rule exists
if ! aws events describe-rule --name "$RULE_NAME" --region "$REGION" &>/dev/null; then
    echo -e "${RED}Error: Rule '$RULE_NAME' does not exist in region '$REGION'.${NC}"
    exit 1
fi

# Update the rule schedule
if aws events put-rule \
    --name "$RULE_NAME" \
    --schedule-expression "$SCHEDULE" \
    --region "$REGION"; then
    echo -e "${GREEN}Successfully updated schedule for rule '$RULE_NAME'.${NC}"
    
    # Get the updated rule details
    echo -e "${BLUE}Updated EventBridge rule details:${NC}"
    aws events describe-rule \
        --name "$RULE_NAME" \
        --query "{Name:Name, ScheduleExpression:ScheduleExpression, State:State}" \
        --output table \
        --region "$REGION"
    
    # Get the Lambda function details
    echo -e "${BLUE}Lambda function details:${NC}"
    LAMBDA_FUNCTION="ovechkin-website-updater"
    aws lambda get-function \
        --function-name "$LAMBDA_FUNCTION" \
        --query "Configuration.{FunctionName:FunctionName, Runtime:Runtime, Timeout:Timeout, MemorySize:MemorySize, LastModified:LastModified}" \
        --output table \
        --region "$REGION"
else
    echo -e "${RED}Failed to update schedule for rule '$RULE_NAME'.${NC}"
    exit 1
fi
