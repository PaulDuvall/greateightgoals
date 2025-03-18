#!/bin/bash

# Static Website Deployment Script
# This script deploys a CloudFormation stack for a static website and uploads content to S3

set -e

# Function to display usage information
usage() {
    echo "Usage: $0 --domain-name <domain-name> [--hosted-zone-id <hosted-zone-id>] [--stack-name <stack-name>] [--region <aws-region>] [--skip-content-upload] [--skip-dns-record] [--update-dns-record] [--force-bucket-recreation]" >&2
    echo ""
    echo "Options:"
    echo "  --domain-name        Domain name for the website (e.g., example.com)"
    echo "  --hosted-zone-id     Route 53 Hosted Zone ID for the domain (optional, will be auto-detected if not provided)"
    echo "  --stack-name         CloudFormation stack name (default: static-website)"
    echo "  --region             AWS region to deploy to (default: us-east-1)"
    echo "  --skip-content-upload Skip uploading content to S3 bucket"
    echo "  --skip-dns-record    Skip creating/updating Route 53 DNS record (use if record already exists and should remain unchanged)"
    echo "  --update-dns-record  Update existing Route 53 DNS record to point to the new CloudFront distribution (default: true)"
    echo "  --force-bucket-recreation Force recreation of the S3 bucket if it already exists (will delete existing bucket)"
    echo "  --help               Display this help message"
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
STACK_NAME=${STACK_NAME:-static-website}
REGION=${REGION:-$(get_parameter "/ovechkin-tracker/aws_region")}
REGION=${REGION:-us-east-1}  # Default to us-east-1 if not set and not in Parameter Store
SKIP_CONTENT_UPLOAD=${SKIP_CONTENT_UPLOAD:-false}
CREATE_DNS_RECORD=${CREATE_DNS_RECORD:-true}
UPDATE_DNS_RECORD=${UPDATE_DNS_RECORD:-true}
FORCE_BUCKET_RECREATION=${FORCE_BUCKET_RECREATION:-false}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --domain-name)
            DOMAIN_NAME="$2"
            shift 2
            ;;
        --hosted-zone-id)
            HOSTED_ZONE_ID="$2"
            shift 2
            ;;
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --skip-content-upload)
            SKIP_CONTENT_UPLOAD=true
            shift
            ;;
        --skip-dns-record)
            CREATE_DNS_RECORD="false"
            UPDATE_DNS_RECORD="false"
            shift
            ;;
        --update-dns-record)
            UPDATE_DNS_RECORD="true"
            shift
            ;;
        --force-bucket-recreation)
            FORCE_BUCKET_RECREATION=true
            shift
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
if [ -z "$DOMAIN_NAME" ]; then
    echo "Error: Missing required parameter --domain-name"
    usage
fi

# Auto-detect hosted zone ID if not provided
if [ -z "$HOSTED_ZONE_ID" ]; then
    echo "Hosted zone ID not provided. Attempting to auto-detect..."
    
    # Extract the base domain (e.g., example.com from sub.example.com)
    # First, try to find the exact domain
    HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
        --dns-name "$DOMAIN_NAME." \
        --query "HostedZones[?Name=='$DOMAIN_NAME.'].Id" \
        --output text \
        --region $REGION | sed 's|/hostedzone/||')
    
    # If not found, try to find the parent domain
    if [ -z "$HOSTED_ZONE_ID" ]; then
        # Split the domain by dots and remove subdomains one by one
        DOMAIN_PARTS=(${DOMAIN_NAME//./ })
        DOMAIN_PARTS_COUNT=${#DOMAIN_PARTS[@]}
        
        if [ $DOMAIN_PARTS_COUNT -gt 1 ]; then
            # Try with the parent domain (e.g., example.com for sub.example.com)
            PARENT_DOMAIN="${DOMAIN_PARTS[$(($DOMAIN_PARTS_COUNT-2))]}.${DOMAIN_PARTS[$(($DOMAIN_PARTS_COUNT-1))]}"
            
            HOSTED_ZONE_ID=$(aws route53 list-hosted-zones-by-name \
                --dns-name "$PARENT_DOMAIN." \
                --query "HostedZones[?Name=='$PARENT_DOMAIN.'].Id" \
                --output text \
                --region $REGION | sed 's|/hostedzone/||')
        fi
    fi
    
    # If still not found, list all hosted zones and let the user choose
    if [ -z "$HOSTED_ZONE_ID" ]; then
        echo "Could not automatically determine the hosted zone ID for $DOMAIN_NAME"
        echo "Available hosted zones:"
        
        aws route53 list-hosted-zones \
            --query "HostedZones[].{ID:Id,Name:Name,Private:Config.PrivateZone}" \
            --output table \
            --region $REGION
        
        echo "Please provide the hosted zone ID using --hosted-zone-id option"
        exit 1
    else
        echo "Found hosted zone ID: $HOSTED_ZONE_ID for domain: $DOMAIN_NAME"
    fi
fi

# Check if DNS record already exists and set flag accordingly
if [ "$CREATE_DNS_RECORD" = "true" ]; then
    echo "Checking if DNS record already exists..."
    EXISTING_RECORD=$(aws route53 list-resource-record-sets \
        --hosted-zone-id $HOSTED_ZONE_ID \
        --query "ResourceRecordSets[?Name=='$DOMAIN_NAME.' && Type=='A']" \
        --output text \
        --region $REGION)
    
    if [ -n "$EXISTING_RECORD" ]; then
        echo "DNS record for $DOMAIN_NAME already exists."
        if [ "$UPDATE_DNS_RECORD" = "true" ]; then
            echo "Will update the existing DNS record after CloudFront deployment."
            CREATE_DNS_RECORD="false"
        else
            echo "Setting --skip-dns-record flag. Existing DNS record will remain unchanged."
            CREATE_DNS_RECORD="false"
        fi
    fi
fi

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
TEMPLATE_PATH="$ROOT_DIR/templates/static-website.yaml"
STATIC_CONTENT_DIR="$ROOT_DIR/static"

# Check if the S3 bucket already exists
BUCKET_NAME="${DOMAIN_NAME}-website"
BUCKET_EXISTS=$(aws s3api head-bucket --bucket "$BUCKET_NAME" 2>&1 || true)

if [[ -z "$BUCKET_EXISTS" ]]; then
    echo "S3 bucket '$BUCKET_NAME' already exists."
    
    # If force-bucket-recreation is set, delete the existing bucket
    if [ "$FORCE_BUCKET_RECREATION" = true ]; then
        echo "--force-bucket-recreation flag is set. Deleting existing bucket..."
        
        # First, empty the bucket
        echo "Emptying bucket contents..."
        aws s3 rm s3://$BUCKET_NAME/ --recursive --region $REGION
        
        # Delete the bucket
        echo "Deleting bucket..."
        aws s3api delete-bucket --bucket $BUCKET_NAME --region $REGION
        
        echo "Bucket deleted successfully. It will be recreated during stack deployment."
        
        # Wait a moment for AWS to fully process the deletion
        echo "Waiting for bucket deletion to complete..."
        sleep 5
    else
        echo "Using existing bucket. Use --force-bucket-recreation to recreate the bucket if needed."
    fi
fi

# Validate template
echo "Validating CloudFormation template..."
aws cloudformation validate-template \
    --template-body file://$TEMPLATE_PATH \
    --region $REGION

# Deploy CloudFormation stack
echo "Deploying CloudFormation stack: $STACK_NAME..."
CFN_DEPLOY_RESULT=$(aws cloudformation deploy \
    --template-file $TEMPLATE_PATH \
    --stack-name $STACK_NAME \
    --parameter-overrides \
        DomainName=$DOMAIN_NAME \
        HostedZoneId=$HOSTED_ZONE_ID \
        CreateDnsRecord=$CREATE_DNS_RECORD \
    --capabilities CAPABILITY_IAM \
    --region $REGION \
    --tags Project=StaticWebsite Environment=Production 2>&1 || true)

# Check if there were any errors during deployment
if [[ "$CFN_DEPLOY_RESULT" == *"Error"* && "$CFN_DEPLOY_RESULT" != *"No changes to deploy"* ]]; then
    # Check if it's just the S3 bucket already exists error
    if [[ "$CFN_DEPLOY_RESULT" == *"already exists"* && "$CFN_DEPLOY_RESULT" == *"$BUCKET_NAME"* ]]; then
        echo "Deployment encountered an error because the S3 bucket already exists."
        echo "To fix this, you can:"
        echo "1. Delete the stack and redeploy"
        echo "2. Use --force-bucket-recreation flag to delete and recreate the bucket"
        exit 1
    else
        echo "Error deploying CloudFormation stack:"
        echo "$CFN_DEPLOY_RESULT"
        exit 1
    fi
else
    echo "$CFN_DEPLOY_RESULT"
fi

# Wait for stack to complete
echo "Waiting for stack deployment to complete..."
aws cloudformation wait stack-create-complete --stack-name $STACK_NAME --region $REGION || \
aws cloudformation wait stack-update-complete --stack-name $STACK_NAME --region $REGION || true

# Get S3 bucket name from stack outputs or use the default
STACK_BUCKET_NAME=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='WebsiteBucketName'].OutputValue" \
    --output text \
    --region $REGION 2>/dev/null || echo "")

if [ -z "$STACK_BUCKET_NAME" ]; then
    echo "Could not get bucket name from stack outputs. Using default: $BUCKET_NAME"
    BUCKET_NAME="$BUCKET_NAME"
else
    BUCKET_NAME="$STACK_BUCKET_NAME"
fi

# Get CloudFront distribution ID from stack outputs
DISTRIBUTION_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDistributionId'].OutputValue" \
    --output text \
    --region $REGION 2>/dev/null || echo "")

# Get CloudFront domain name from stack outputs
CLOUDFRONT_DOMAIN=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='CloudFrontDomainName'].OutputValue" \
    --output text \
    --region $REGION 2>/dev/null || echo "")

# If we couldn't get the CloudFront domain from stack outputs, try to get it directly
if [ -z "$CLOUDFRONT_DOMAIN" ] && [ -n "$DISTRIBUTION_ID" ]; then
    CLOUDFRONT_DOMAIN=$(aws cloudfront get-distribution \
        --id $DISTRIBUTION_ID \
        --query "Distribution.DomainName" \
        --output text \
        --region $REGION 2>/dev/null || echo "")
fi

# Get website URL from stack outputs
WEBSITE_URL=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
    --query "Stacks[0].Outputs[?OutputKey=='WebsiteURL'].OutputValue" \
    --output text \
    --region $REGION 2>/dev/null || echo "https://$DOMAIN_NAME")

echo "S3 Bucket: $BUCKET_NAME"

if [ -n "$DISTRIBUTION_ID" ]; then
    echo "CloudFront Distribution ID: $DISTRIBUTION_ID"
fi

if [ -n "$CLOUDFRONT_DOMAIN" ]; then
    echo "CloudFront Domain: $CLOUDFRONT_DOMAIN"
fi

echo "Website URL: $WEBSITE_URL"

# Update existing DNS records if needed
if [ "$UPDATE_DNS_RECORD" = "true" ] && [ "$CREATE_DNS_RECORD" = "false" ] && [ -n "$CLOUDFRONT_DOMAIN" ]; then
    echo "Updating existing DNS records to point to the new CloudFront distribution..."
    
    # Create a temporary JSON file for the change batch
    TEMP_FILE=$(mktemp)
    
    # Create the change batch for A record
    cat > $TEMP_FILE << EOF
{
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$DOMAIN_NAME",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "$CLOUDFRONT_DOMAIN",
          "EvaluateTargetHealth": false
        }
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$DOMAIN_NAME",
        "Type": "AAAA",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "$CLOUDFRONT_DOMAIN",
          "EvaluateTargetHealth": false
        }
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "www.$DOMAIN_NAME",
        "Type": "A",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "$CLOUDFRONT_DOMAIN",
          "EvaluateTargetHealth": false
        }
      }
    },
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "www.$DOMAIN_NAME",
        "Type": "AAAA",
        "AliasTarget": {
          "HostedZoneId": "Z2FDTNDATAQYW2",
          "DNSName": "$CLOUDFRONT_DOMAIN",
          "EvaluateTargetHealth": false
        }
      }
    }
  ]
}
EOF
    
    # Apply the change batch
    aws route53 change-resource-record-sets \
        --hosted-zone-id $HOSTED_ZONE_ID \
        --change-batch file://$TEMP_FILE \
        --region $REGION
    
    # Remove the temporary file
    rm $TEMP_FILE
    
    echo "DNS records updated successfully"
fi

# Upload content to S3 bucket if not skipped
if [ "$SKIP_CONTENT_UPLOAD" = false ] && [ -n "$BUCKET_NAME" ]; then
    echo "Uploading static content to S3 bucket..."
    aws s3 sync $STATIC_CONTENT_DIR s3://$BUCKET_NAME/ \
        --delete \
        --region $REGION
    
    # Create CloudFront invalidation to clear cache if distribution ID is available
    if [ -n "$DISTRIBUTION_ID" ]; then
        echo "Creating CloudFront invalidation to clear cache..."
        INVALIDATION_ID=$(aws cloudfront create-invalidation \
            --distribution-id $DISTRIBUTION_ID \
            --paths "/*" \
            --query "Invalidation.Id" \
            --output text)
        
        if [ -n "$INVALIDATION_ID" ]; then
            echo "CloudFront invalidation created: $INVALIDATION_ID"
            echo "Waiting for invalidation to complete..."
            aws cloudfront wait invalidation-completed \
                --distribution-id $DISTRIBUTION_ID \
                --id $INVALIDATION_ID
            
            echo "CloudFront invalidation completed"
        else
            echo "Failed to create CloudFront invalidation. You may need to manually invalidate the cache."
        fi
    else
        echo "CloudFront distribution ID not available. Skipping cache invalidation."
    fi
fi

echo ""
echo "Deployment completed successfully!"
echo "Website URL: $WEBSITE_URL"
echo "Note: It may take a few minutes for DNS changes to propagate and for the certificate validation to complete."
