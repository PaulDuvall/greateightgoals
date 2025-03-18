#!/bin/bash

# Website Content Update Script
# This script updates the website content in S3 and invalidates the CloudFront cache

set -e

# Function to display usage information
usage() {
    echo "Usage: $0 --stack-name <stack-name> [--region <aws-region>] [--content-dir <content-directory>]" >&2
    echo ""
    echo "Options:"
    echo "  --stack-name     CloudFormation stack name"
    echo "  --region         AWS region (default: us-east-1)"
    echo "  --content-dir    Directory containing content to upload (default: ./static)"
    echo "  --help           Display this help message"
    exit 1
}

# Default values
REGION="us-east-1"

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
CONTENT_DIR="$ROOT_DIR/static"

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
        --content-dir)
            CONTENT_DIR="$2"
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

# Get S3 bucket name from stack outputs
BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='WebsiteBucketName'].OutputValue" \
    --output text \
    --region $REGION)

if [ -z "$BUCKET_NAME" ]; then
    echo "Error: Could not retrieve S3 bucket name from stack $STACK_NAME"
    exit 1
fi

echo "S3 Bucket: $BUCKET_NAME"

# Upload content to S3 bucket
echo "Uploading content from $CONTENT_DIR to S3 bucket..."
aws s3 sync $CONTENT_DIR s3://$BUCKET_NAME/ \
    --delete \
    --region $REGION

# Call the invalidate-cache script
echo "Invalidating CloudFront cache..."
"$SCRIPT_DIR/invalidate_cache.sh" --stack-name "$STACK_NAME" --region "$REGION"

echo "Content update completed successfully"
