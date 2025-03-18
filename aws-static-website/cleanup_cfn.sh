#!/bin/bash
# cleanup-cfn.sh
# This script cleans up the AWS CloudFormation stack generated for the static website in this directory.

# Ensure the script exits on any error
set -e

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI is not installed. Please install it and try again."
    exit 1
fi

# Check for required argument: CloudFormation Stack Name
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <CFN_STACK_NAME>"
    exit 1
fi

STACK_NAME="$1"

echo "Initiating deletion of CloudFormation stack: $STACK_NAME"

# Delete the CloudFormation stack
aws cloudformation delete-stack --stack-name "$STACK_NAME"

echo "Waiting for stack deletion to complete..."

# Wait until the deletion is complete
aws cloudformation wait stack-delete-complete --stack-name "$STACK_NAME"

echo "CloudFormation stack '$STACK_NAME' has been successfully deleted."
