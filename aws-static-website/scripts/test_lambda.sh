#!/bin/bash

# Script to test the Ovechkin website updater Lambda function
# Following the twelve-factor app methodology

set -e

# Define colors for output
GREEN="\033[0;32m"
YELLOW="\033[1;33m"
RED="\033[0;31m"
BLUE="\033[0;34m"
NC="\033[0m" # No Color

# Default values
REGION="us-east-1"
FUNCTION_NAME="greateightgoals-website-updater"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  key="$1"
  case $key in
    --region)
      REGION="$2"
      shift 2
      ;;
    --function-name)
      FUNCTION_NAME="$2"
      shift 2
      ;;
    --help)
      echo -e "${BLUE}Test Ovechkin Website Updater Lambda Function${NC}"
      echo ""
      echo "Usage: $0 [options]"
      echo ""
      echo "Options:"
      echo "  --region <aws-region>        AWS region (default: us-east-1)"
      echo "  --function-name <name>       Lambda function name (default: greateightgoals-website-updater)"
      echo "  --help                       Display this help message"
      exit 0
      ;;
    *)
      echo -e "${YELLOW}Unknown option: $1${NC}"
      echo "Run '$0 --help' for usage information."
      exit 1
      ;;
  esac
done

echo -e "${BLUE}Testing Lambda function: $FUNCTION_NAME in region $REGION${NC}"

# Check if the function exists
echo -e "${BLUE}Checking if Lambda function exists...${NC}"
aws lambda get-function \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --query 'Configuration.{Name:FunctionName, Runtime:Runtime, Memory:MemorySize, Timeout:Timeout}' \
  --output table

# Invoke the Lambda function
echo -e "${BLUE}Invoking Lambda function...${NC}"
LOG_FILE="/tmp/lambda_output.json"

aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --region "$REGION" \
  --log-type Tail \
  --query 'LogResult' \
  --output text \
  --payload '{}' \
  "$LOG_FILE" | base64 --decode

echo -e "${GREEN}Lambda function executed. Response saved to $LOG_FILE${NC}"
echo -e "${BLUE}Response content:${NC}"
cat "$LOG_FILE" | jq .

echo -e "${BLUE}Checking CloudWatch logs for recent invocations...${NC}"

# Get the log group name
LOG_GROUP_NAME="/aws/lambda/$FUNCTION_NAME"

# Get the most recent log stream
LATEST_STREAM=$(aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP_NAME" \
  --region "$REGION" \
  --order-by LastEventTime \
  --descending \
  --limit 1 \
  --query 'logStreams[0].logStreamName' \
  --output text)

echo -e "${BLUE}Latest log stream: $LATEST_STREAM${NC}"

# Get the most recent logs
aws logs get-log-events \
  --log-group-name "$LOG_GROUP_NAME" \
  --log-stream-name "$LATEST_STREAM" \
  --region "$REGION" \
  --limit 20 \
  --query 'events[*].message' \
  --output text

echo -e "${GREEN}Test completed.${NC}"
