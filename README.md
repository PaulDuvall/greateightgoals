# Ovechkin Goal Tracker

A Python application to track Alex Ovechkin's progress toward breaking Wayne Gretzky's NHL goal record, display real-time projections on a static website, and send email notifications with projections. Supports both standalone execution and AWS Lambda deployment with automated updates.

## Overview

This application fetches Alex Ovechkin's current stats from the NHL API, calculates his progress toward breaking Wayne Gretzky's all-time goal record (894 goals), and provides multiple ways to view and share this information:

1. Command-line interface for direct stats viewing
2. Static website that updates automatically via AWS Lambda
3. Email notifications with the latest stats and projections

## Features

- Fetches real-time stats from the NHL API
- Calculates goals needed to break Gretzky's record (894 goals)
- Projects when Ovechkin might break the record based on his current scoring pace
- Identifies the specific game where the record might be broken, including date, time, opponent, and location
- Displays a formatted projection string: "Projected Record-Breaking Game: Saturday, April 12, 2025, 12:30 PM ET vs Columbus Blue Jackets (Away)"
- Hosts a static website that updates automatically on a configurable schedule
- Sends email notifications with stats and projections using Amazon SES
- Configurable through AWS Systems Manager Parameter Store
- Supports AWS Lambda deployment with API Gateway integration
- Implements CloudFront cache invalidation to ensure fresh content
- Includes comprehensive automated testing for all components

## Architecture

The application follows the twelve-factor app methodology and is organized into a modular structure. For detailed architecture diagrams including data flow, AWS infrastructure, and Lambda deployment, see [Architecture Diagrams](docs/architecture_diagrams.md).

```
ovechkin_tracker/         # Core Python package
├── __init__.py        # Package initialization
├── ovechkin_data.py   # OvechkinData class for stats calculation
├── nhl_api.py         # NHL API interaction functions
├── stats.py           # Stats calculation and projections
├── email.py           # Email formatting and sending
└── cli.py             # Command-line interface

aws-static-website/       # Static website infrastructure
├── update_website.py  # Script to generate and update the website
├── run.sh             # Main entry point script
├── scripts/           # Supporting scripts
│   ├── deploy_updater.sh  # Script to deploy the Lambda updater
│   └── configure-cloudfront.sh # Script to configure CloudFront cache
├── static/            # Static website content
├── lambda/            # Lambda function for website updates
│   ├── update_website_lambda.py # Lambda handler
│   └── requirements-lambda.txt # Lambda dependencies
└── cloudformation/    # CloudFormation templates
    └── website-updater.yaml # CloudFormation template for Lambda updater

tests/                    # Test directory
├── test_cli.py           # CLI tests
├── test_email.py         # Email functionality tests
├── test_lambda_function.py # Lambda function tests
├── test_lambda_local.py  # Local Lambda function test script
├── test_nhl_api.py       # NHL API interaction tests
├── test_ovechkin_data.py # Stats calculation tests
├── test_static_website.py # AWS infrastructure tests
└── run_tests.sh          # Test runner script

lambda_function.py     # AWS Lambda handler
requirements.txt       # Core dependencies
requirements-lambda.txt # Lambda-specific dependencies

## Requirements

- Python 3.11+
- AWS account with SES access (for email functionality)
- AWS CLI installed and configured (for infrastructure deployment)
- A domain name registered in Route 53 (for static website)
- Dependencies listed in requirements.txt and requirements-lambda.txt

## Installation

1. Clone the repository
2. Run the setup command to create a virtual environment and install dependencies:

```bash
./run.sh setup            # For standard application
./run.sh setup-lambda     # For Lambda development (includes all dependencies)
```

## Configuration

The application uses AWS Systems Manager Parameter Store for configuration by default.

## AWS Parameter Store Configuration

The application uses AWS Systems Manager Parameter Store to securely store configuration values. Set up the following parameters:

- `/ovechkin-tracker/sender_email` - Email address to send notifications from (must be verified in SES)
- `/ovechkin-tracker/recipient_email` - Email address to send notifications to
- `/ovechkin-tracker/aws_region` - AWS region for SES and other AWS services (e.g., us-east-1)

### Setting Up Parameters

Use the AWS CLI to set up the required parameters:

```bash
# Set up sender email (must be verified in SES)
aws ssm put-parameter --name "/ovechkin-tracker/sender_email" --value "your-verified-email@example.com" --type "SecureString" --overwrite

# Set up recipient email
aws ssm put-parameter --name "/ovechkin-tracker/recipient_email" --value "recipient@example.com" --type "SecureString" --overwrite

# Set up AWS region (used by all components of the application)
aws ssm put-parameter --name "/ovechkin-tracker/aws_region" --value "us-east-1" --type "SecureString" --overwrite
```

### Verifying Parameters

Verify that your parameters are correctly set:

```bash
aws ssm get-parameter --name "/ovechkin-tracker/aws_region" --with-decryption
```

> **Note**: The AWS region parameter is used throughout the application to ensure consistency across all AWS service calls. While default fallbacks are in place, it's recommended to set this parameter explicitly.

## Usage

The application provides several commands through the `run.sh` script:

### Display Stats

To display current Ovechkin stats:

```bash
./run.sh stats
```

### Send Email

To send an email with Ovechkin stats to the configured recipient:

```bash
./run.sh email
```

To send to a specific email address:

```bash
./run.sh email-to user@example.com
```

### Test Lambda Function

To test the Lambda function locally:

```bash
./run.sh test-lambda                        # Test with default settings
./run.sh test-lambda --format=flat          # Test with flat format response
./run.sh test-lambda --method=POST --email=user@example.com  # Test email sending
./run.sh test-lambda --config-source=event  # Test with event-based configuration
```

## AWS Static Website Infrastructure

The project includes a complete infrastructure solution for hosting a static website on AWS that follows the twelve-factor app methodology and uses AWS CloudFormation for infrastructure as code.

### Key Features

- **Infrastructure as Code**: Uses AWS CloudFormation to declare and manage all infrastructure
- **HTTPS Support**: Automatically sets up ACM certificates for secure connections
- **Content Delivery**: Configures CloudFront CDN for fast global content delivery
- **Domain Management**: Integrates with Route 53 for custom domain configuration
- **Cache Management**: Includes tools for CloudFront cache invalidation
- **Secure by Default**: Implements S3 bucket policies with least privilege access
- **Automatic Hosted Zone Detection**: Automatically detects the Route 53 hosted zone ID based on the domain name
- **Existing DNS Handling**: Automatically detects and handles existing DNS records
- **DNS Record Updates**: Updates existing DNS records to point to the new CloudFront distribution
- **Resource Management**: Provides options for handling existing resources during deployment
- **Automated Updates**: Scheduled Lambda function updates the website on a configurable schedule
- **Cache Control**: Implements CloudFront cache invalidation to ensure fresh content

### Directory Structure

```
aws-static-website/
├── run.sh                  # Main entry point script
├── scripts/                # Supporting scripts
│   ├── deploy.sh           # CloudFormation deployment script
│   ├── update_content.sh   # Content update script
│   ├── deploy_updater.sh   # Script to deploy the Lambda updater
│   ├── configure-cloudfront.sh # CloudFront cache configuration script
│   └── invalidate_cache.sh # CloudFront cache invalidation script
├── static/                 # Static website content
│   └── index.html          # Sample "Hello World" page
├── lambda/                 # Lambda function for website updates
│   ├── update_website_lambda.py # Lambda handler
│   └── requirements-lambda.txt # Lambda dependencies
└── cloudformation/        # CloudFormation templates
    ├── static-website.yaml # Main infrastructure template
    └── website-updater.yaml # CloudFormation template for Lambda updater
```

### Prerequisites

- AWS CLI installed and configured with appropriate permissions
- A domain name registered in Route 53 with a hosted zone
- Python 3.11 (for running tests)

### Deploying the Website

To deploy the static website infrastructure, run:

```bash
./aws-static-website/run.sh deploy --domain-name example.com--force-bucket-recreation
```

This will:
1. Create an S3 bucket for website content
2. Set up CloudFront distribution with HTTPS
3. Configure Route 53 DNS records
4. Upload initial content

### Deploying the Website Updater

To deploy the Lambda function that automatically updates the website, run:

```bash
cd aws-static-website
./scripts/deploy_updater.sh --schedule 'rate(30 minutes)'
```

This will:
1. Package the Lambda function with dependencies
2. Deploy the CloudFormation stack with the Lambda function and EventBridge rule
3. Configure the Lambda function to update the website on the specified schedule

#### Schedule Expression Options

You can customize the update frequency using various schedule expressions:

- `rate(30 minutes)` - Run every 30 minutes
- `rate(1 hour)` - Run every hour
- `cron(0 * * * ? *)` - Run at the top of every hour (00:00)
- `cron(0,30 * * * ? *)` - Run at the top and half of every hour (00:00, 00:30)

### Updating Website Content

To update the website content manually, run:

```bash
cd aws-static-website
./run.sh update-content
```

## CI/CD with GitHub Actions

The project includes a GitHub Actions workflow for automated deployment of the website updater. The workflow is triggered manually via the GitHub Actions UI or automatically on pushes to the repository that modify relevant files.

### Workflow Features

- **On-demand Deployment**: Manually trigger deployments with customizable parameters
- **Automatic Updates**: Automatically deploys when code changes are pushed
- **Configurable Schedule**: Customize the update frequency using schedule expressions
- **Lambda Code Updates**: Option to update only the Lambda function code without redeploying the CloudFormation stack

### AWS OIDC Authentication for GitHub Actions

This project implements OpenID Connect (OIDC) authentication between GitHub Actions and AWS, eliminating the need for storing long-lived AWS credentials in GitHub Secrets.

#### Benefits of OIDC Authentication

- **Enhanced Security:** No long-term credentials are stored in GitHub
- **Temporary Credentials:** Uses short-lived tokens to reduce risk
- **Fine-Grained Access:** Precisely control permissions based on repository and branch
- **Auditability:** Monitor usage via AWS CloudTrail

#### Setting Up OIDC Authentication

1. **Deploy the CloudFormation Stack**

   ```bash
   # Navigate to the aws-static-website directory
   cd aws-static-website

   # Make the setup script executable (if needed)
   chmod +x scripts/setup_oidc.sh

   # Run the automated setup
   ./scripts/setup_oidc.sh
   ```

   This script will:
   - Deploy a CloudFormation stack with the IAM OIDC provider and role
   - Configure the necessary IAM permissions for GitHub Actions workflows
   - Set up the trust relationship between AWS and GitHub

2. **Update GitHub Repository Settings**

   After running the setup script, you'll need to add the IAM Role ARN to your GitHub repository:
   - Go to your GitHub repository
   - Navigate to Settings > Secrets and variables > Variables
   - Add a new repository variable named `AWS_ROLE_TO_ASSUME` with the value of the IAM Role ARN

3. **Use OIDC in GitHub Actions Workflows**

   Your GitHub Actions workflows can now use OIDC authentication with AWS:

   ```yaml
   jobs:
     deploy:
       permissions:
         id-token: write   # Required for OIDC
         contents: read
       steps:
         - name: Configure AWS credentials
           uses: aws-actions/configure-aws-credentials@v2
           with:
             role-to-assume: ${{ vars.AWS_ROLE_TO_ASSUME }}
             aws-region: us-east-1
   ```

#### Troubleshooting OIDC Authentication

- **Permission Errors**: If you encounter permission errors, check the IAM policy attached to the role
- **Trust Relationship**: Ensure the trust relationship is correctly configured for your GitHub repository
- **CloudFormation Stack**: If you need to update the permissions, you can rerun the setup script

## Optimizing Update Frequency

The website updater can be configured to run on a schedule that aligns with the Washington Capitals' game schedule, rather than running at fixed intervals. This optimization is useful because the NHL API updates anywhere from 30 minutes to 3 hours after a game ends.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
