#!/bin/bash

# CloudFront Cache Invalidation Script
# This script creates a CloudFront invalidation to ensure fresh content

set -e

# Function to display usage information
usage() {
    echo "Usage: $0 --stack-name <stack-name> [--region <aws-region>] [--paths <paths>]" >&2
    echo ""
    echo "Options:"
    echo "  --stack-name     CloudFormation stack name"
    echo "  --region         AWS region (default: us-east-1)"
    echo "  --paths          Paths to invalidate (default: '/*')"
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
REGION=${REGION:-$(get_parameter "/ovechkin-tracker/aws_region")}
REGION=${REGION:-us-east-1}  # Default to us-east-1 if not set and not in Parameter Store
PATHS="/*"

# Parse command line arguments
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
        --paths)
            PATHS="$2"
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

# Check required parameters
if [ -z "$STACK_NAME" ]; then
    echo "Error: Missing required parameters"
    usage
fi

# Get CloudFront distribution ID from stack outputs
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
    --output text \
    --region $REGION)

if [ -z "$DISTRIBUTION_ID" ]; then
    echo "Error: Could not retrieve CloudFront distribution ID from stack $STACK_NAME"
    exit 1
fi

echo "CloudFront Distribution ID: $DISTRIBUTION_ID"

# Create CloudFront invalidation
echo "Creating CloudFront invalidation for paths: $PATHS"
INVALIDATION_ID=$(aws cloudfront create-invalidation \
    --distribution-id $DISTRIBUTION_ID \
    --paths $PATHS \
    --query "Invalidation.Id" \
    --output text)

echo "CloudFront invalidation created: $INVALIDATION_ID"
echo "Waiting for invalidation to complete..."
aws cloudfront wait invalidation-completed \
    --distribution-id $DISTRIBUTION_ID \
    --id $INVALIDATION_ID

echo "CloudFront invalidation completed successfully"
