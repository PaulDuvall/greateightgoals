#!/bin/bash

# setup_openai_oidc.sh - Automated AWS OIDC Authentication Setup for GitHub Actions with OpenAI API Access
# This script automates the deployment of AWS OIDC authentication for GitHub Actions
# with specific permissions to access the OpenAI API key from Parameter Store.

set -e

# Default values
REGION="us-east-1"
STACK_NAME="thegr8chase-github-oidc-openai"
GITHUB_ORG=""
REPO_NAME=""
BRANCH_NAME="main"
GITHUB_TOKEN=""
PARAMETER_NAME="/ovechkin-tracker/openai_api_key"
OPENAI_API_KEY=""

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CLOUDFORMATION_DIR="${SCRIPT_DIR}/../cloudformation"

# Function to display usage information
usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  --region REGION            AWS region (default: us-east-1)"
  echo "  --stack-name STACK_NAME    CloudFormation stack name (default: thegr8chase-github-oidc-openai)"
  echo "  --github-org ORG_NAME      GitHub organization name (required)"
  echo "  --repo-name REPO_NAME      GitHub repository name (required)"
  echo "  --branch-name BRANCH_NAME  GitHub branch name (default: main)"
  echo "  --github-token TOKEN       GitHub Personal Access Token with repo and workflow scopes (required)"
  echo "  --parameter-name NAME      AWS Parameter Store parameter name (default: /ovechkin-tracker/openai_api_key)"
  echo "  --openai-api-key KEY       OpenAI API key to store in Parameter Store (optional)"
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
    --parameter-name)
      PARAMETER_NAME="$2"
      shift 2
      ;;
    --openai-api-key)
      OPENAI_API_KEY="$2"
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
  if [[ $REMOTE_URL =~ github\.com[:/]([^/]+)/([^/.]+) ]]; then
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
echo -e "\nDeployment Configuration:"
echo "AWS Region: $REGION"
echo "Stack Name: $STACK_NAME"
echo "GitHub Organization: $GITHUB_ORG"
echo "Repository Name: $REPO_NAME"
echo "Branch Name: $BRANCH_NAME"
echo "Parameter Name: $PARAMETER_NAME"
echo ""

# Store OpenAI API key in Parameter Store if provided
if [[ -n "$OPENAI_API_KEY" ]]; then
  echo "Storing OpenAI API key in Parameter Store..."
  aws ssm put-parameter \
    --region "$REGION" \
    --name "$PARAMETER_NAME" \
    --type "SecureString" \
    --value "$OPENAI_API_KEY" \
    --overwrite
  echo "OpenAI API key stored successfully in Parameter Store."
else
  # Check if parameter already exists
  if ! aws ssm get-parameter --region "$REGION" --name "$PARAMETER_NAME" --with-decryption >/dev/null 2>&1; then
    echo "Warning: OpenAI API key not provided and parameter does not exist in Parameter Store."
    echo "You will need to manually create the parameter '$PARAMETER_NAME' in AWS Parameter Store."
  else
    echo "Using existing OpenAI API key from Parameter Store."
  fi
fi

# Deploy or update CloudFormation stack
echo "Deploying CloudFormation stack for OIDC authentication with OpenAI access..."
aws cloudformation deploy \
  --region "$REGION" \
  --stack-name "$STACK_NAME" \
  --template-file "$CLOUDFORMATION_DIR/github_oidc_openai.yaml" \
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
  --query "Stacks[0].Outputs[?OutputKey=='OpenAIRoleARN'].OutputValue" \
  --output text)

echo -e "\nDeployment complete!"
echo "OpenAI IAM Role ARN: $ROLE_ARN"

# Set GitHub repository variable
echo -e "\nSetting GitHub repository variable OPENAI_ROLE_TO_ASSUME..."

# First try to update the variable (if it exists)
UPDATE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X PATCH \
  -H "Accept: application/vnd.github+json" \
  -H "Authorization: token $GITHUB_TOKEN" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "https://api.github.com/repos/$GITHUB_ORG/$REPO_NAME/actions/variables/OPENAI_ROLE_TO_ASSUME" \
  -d "{\"name\":\"OPENAI_ROLE_TO_ASSUME\",\"value\":\"$ROLE_ARN\"}")

# If update fails (variable doesn't exist), create it
if [[ "$UPDATE_RESPONSE" == "404" ]]; then
  echo "Variable does not exist, creating it..."
  CREATE_RESPONSE=$(curl -s -w "%{http_code}" -o /dev/null -X POST \
    -H "Accept: application/vnd.github+json" \
    -H "Authorization: token $GITHUB_TOKEN" \
    -H "X-GitHub-Api-Version: 2022-11-28" \
    "https://api.github.com/repos/$GITHUB_ORG/$REPO_NAME/actions/variables" \
    -d "{\"name\":\"OPENAI_ROLE_TO_ASSUME\",\"value\":\"$ROLE_ARN\"}")
  
  if [[ "$CREATE_RESPONSE" == "201" ]]; then
    echo "Successfully created GitHub variable OPENAI_ROLE_TO_ASSUME"
  else
    echo "Failed to create GitHub variable. HTTP status: $CREATE_RESPONSE"
    echo "Please check your GitHub token has the correct permissions (repo and workflow scopes)."
  fi
elif [[ "$UPDATE_RESPONSE" == "204" ]]; then
  echo "Successfully updated GitHub variable OPENAI_ROLE_TO_ASSUME"
else
  echo "Failed to update GitHub variable. HTTP status: $UPDATE_RESPONSE"
  echo "Please check your GitHub token has the correct permissions (repo and workflow scopes)."
fi

echo -e "\nSetup complete! GitHub Actions workflows can now use OIDC authentication with AWS for OpenAI API access."
echo "Use the following configuration in your GitHub Actions workflow:"
echo ""
echo "jobs:"
echo "  analyze:"
echo "    permissions:"
echo "      id-token: write   # Required for OIDC"
echo "      contents: read"
echo "    steps:"
echo "      - name: Configure AWS credentials"
echo "        uses: aws-actions/configure-aws-credentials@v2"
echo "        with:"
echo "          role-to-assume: \${{ vars.OPENAI_ROLE_TO_ASSUME }}"
echo "          aws-region: $REGION"
echo ""
echo "      - name: Get OpenAI API Key from Parameter Store"
echo "        run: |"
echo "          echo \"OPENAI_API_KEY=\$(aws ssm get-parameter --name $PARAMETER_NAME --with-decryption --query Parameter.Value --output text)\" >> \$GITHUB_ENV"
echo ""
echo "The OPENAI_ROLE_TO_ASSUME variable has been automatically set in your GitHub repository."
echo "Make sure the OpenAI API key is stored in Parameter Store at: $PARAMETER_NAME"
