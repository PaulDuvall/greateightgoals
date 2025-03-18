#!/bin/bash

# setup_oidc.sh - Automated AWS OIDC Authentication Setup for GitHub Actions
# This script automates the deployment of AWS OIDC authentication for GitHub Actions
# and sets the necessary GitHub repository variable.

set -e

# Default values
REGION="us-east-1"
STACK_NAME="thegr8chase-github-oidc"
GITHUB_ORG=""
REPO_NAME=""
BRANCH_NAME="main"
GITHUB_TOKEN=""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CLOUDFORMATION_DIR="${SCRIPT_DIR}/../cloudformation"

# Function to display usage information
usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --region REGION            AWS region (default: us-east-1)"
  echo "  --stack-name STACK_NAME    CloudFormation stack name (default: thegr8chase-github-oidc)"
  echo "  --github-org ORG_NAME      GitHub organization name (required)"
  echo "  --repo-name REPO_NAME      GitHub repository name (required)"
  echo "  --branch-name BRANCH_NAME  GitHub branch name (default: main)"
  echo "  --github-token TOKEN       GitHub Personal Access Token with repo and workflow scopes (required)"
  echo "  --help                     Display this help message"
  exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
  case "$1" in
    --region)
      REGION="$2"
      shift 2
      ;;
    --stack-name)
      STACK_NAME="$2"
      shift 2
      ;;
    --github-org)
      GITHUB_ORG="$2"
      shift 2
      ;;
    --repo-name)
      REPO_NAME="$2"
      shift 2
      ;;
    --branch-name)
      BRANCH_NAME="$2"
      shift 2
      ;;
    --github-token)
      GITHUB_TOKEN="$2"
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

# Validate required parameters
if [[ -z "$GITHUB_TOKEN" ]]; then
  echo "Error: GitHub token is required. Use --github-token to provide it."
  usage
fi

# Auto-detect GitHub org and repo if not provided
if [[ -z "$GITHUB_ORG" || -z "$REPO_NAME" ]]; then
  # Try to get from git remote URL
  REMOTE_URL=$(git -C "$PROJECT_ROOT" config --get remote.origin.url)
  if [[ $REMOTE_URL =~ github.com[:/]([^/]+)/([^/.]+)(.git)? ]]; then
    if [[ -z "$GITHUB_ORG" ]]; then
      GITHUB_ORG="${BASH_REMATCH[1]}"
      echo "Auto-detected GitHub organization: $GITHUB_ORG"
    fi
    if [[ -z "$REPO_NAME" ]]; then
      REPO_NAME="${BASH_REMATCH[2]}"
      echo "Auto-detected repository name: $REPO_NAME"
    fi
  else
    echo "Error: Could not auto-detect GitHub organization and repository."
    echo "Please provide them using --github-org and --repo-name options."
    usage
  fi
fi

# Confirm detected values
echo "\nDeployment Configuration:"
echo "AWS Region: $REGION"
echo "Stack Name: $STACK_NAME"
echo "GitHub Organization: $GITHUB_ORG"
echo "Repository Name: $REPO_NAME"
echo "Branch Name: $BRANCH_NAME"
echo ""

# Deploy or update CloudFormation stack
echo "Deploying CloudFormation stack for OIDC authentication..."
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$CLOUDFORMATION_DIR/github_oidc.yaml" \
  --parameter-overrides \
    GitHubOrg="$GITHUB_ORG" \
    RepositoryName="$REPO_NAME" \
    BranchName="$BRANCH_NAME" \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --no-fail-on-empty-changeset

# Wait for stack to complete - use a more reliable approach
echo "Waiting for stack deployment to complete..."
# Wait a few seconds to ensure the stack update has started
sleep 5

# Check stack status in a loop
while true; do
  STATUS=$(aws cloudformation describe-stacks \
    --region "$REGION" \
    --stack-name "$STACK_NAME" \
    --query "Stacks[0].StackStatus" \
    --output text)
  
  if [[ "$STATUS" == *"COMPLETE"* ]]; then
    if [[ "$STATUS" == "CREATE_COMPLETE" || "$STATUS" == "UPDATE_COMPLETE" ]]; then
      echo "Stack deployment completed successfully."
      break
    elif [[ "$STATUS" == *"ROLLBACK_COMPLETE"* || "$STATUS" == *"FAILED"* ]]; then
      echo "Stack deployment failed with status: $STATUS"
      exit 1
    fi
  elif [[ "$STATUS" == *"IN_PROGRESS"* ]]; then
    echo "Stack deployment in progress... (Status: $STATUS)"
    sleep 10
  else
    echo "Unexpected stack status: $STATUS"
    exit 1
  fi
done

# Get the IAM Role ARN from stack outputs
ROLE_ARN=$(aws cloudformation describe-stacks \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --query "Stacks[0].Outputs[?OutputKey=='RoleARN'].OutputValue" \
  --output text)

echo "\nDeployment complete!"
echo "IAM Role ARN: $ROLE_ARN"

# Set GitHub repository variable
echo "\nSetting GitHub repository variable AWS_ROLE_TO_ASSUME..."

# First try to update the variable (if it exists)
UPDATE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$GITHUB_ORG/$REPO_NAME/actions/variables/AWS_ROLE_TO_ASSUME" \
  -d "{\"name\":\"AWS_ROLE_TO_ASSUME\",\"value\":\"$ROLE_ARN\"}")

# If update fails (variable doesn't exist), create it
if [[ "$UPDATE_RESPONSE" == "404" ]]; then
  echo "Variable does not exist, creating it..."
  CREATE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/$GITHUB_ORG/$REPO_NAME/actions/variables" \
    -d "{\"name\":\"AWS_ROLE_TO_ASSUME\",\"value\":\"$ROLE_ARN\"}")
  
  if [[ "$CREATE_RESPONSE" == "201" ]]; then
    echo "Successfully created GitHub variable AWS_ROLE_TO_ASSUME"
  else
    echo "Failed to create GitHub variable. HTTP status: $CREATE_RESPONSE"
    echo "Please check your GitHub token has the correct permissions (repo and workflow scopes)."
  fi
elif [[ "$UPDATE_RESPONSE" == "204" ]]; then
  echo "Successfully updated GitHub variable AWS_ROLE_TO_ASSUME"
else
  echo "Failed to update GitHub variable. HTTP status: $UPDATE_RESPONSE"
  echo "Please check your GitHub token has the correct permissions (repo and workflow scopes)."
fi

echo "\n✅ Setup complete! GitHub Actions workflows can now use OIDC authentication with AWS."
echo "Use the following configuration in your GitHub Actions workflow:"
echo ""
echo "jobs:"
echo "  deploy:"
echo "    permissions:"
echo "      id-token: write   # Required for OIDC"
echo "      contents: read"
echo "    steps:"
echo "      - name: Configure AWS credentials"
echo "        uses: aws-actions/configure-aws-credentials@v2"
echo "        with:"
echo "          role-to-assume: \${{ vars.AWS_ROLE_TO_ASSUME }}"
echo "          aws-region: $REGION"
echo ""
echo "The AWS_ROLE_TO_ASSUME variable has been automatically set in your GitHub repository."
