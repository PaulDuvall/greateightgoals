# Security Policy and Compliance Documentation

This document outlines the security practices, potential vulnerabilities, and compliance considerations for the Ovechkin Goal Tracker project.

## Security Assessment

### Identified Security Considerations

#### 1. AWS IAM Permissions

- **Finding**: The Lambda execution role (`WebsiteUpdaterRole`) uses broad resource patterns (`Resource: '*'`) for S3 and CloudFront permissions.
- **Risk Level**: Medium
- **Recommendation**: Implement more restrictive resource patterns by using specific ARNs for S3 buckets and CloudFront distributions rather than wildcards.

```yaml
# Example of more restrictive S3 permissions
- Effect: Allow
  Action:
    - s3:PutObject
    - s3:GetObject
    - s3:ListBucket
  Resource: 
    - !Sub 'arn:aws:s3:::${WebsiteBucketName}'
    - !Sub 'arn:aws:s3:::${WebsiteBucketName}/*'
```

#### 2. Email Configuration Management

- **Finding**: Email configuration is stored in environment variables and potentially in a local `.env` file.
- **Risk Level**: Low
- **Recommendation**: For production environments, ensure all sensitive configuration is stored in AWS Systems Manager Parameter Store with appropriate encryption.

#### 3. Dependency Security

- **Finding**: The project uses several external dependencies (boto3, requests, pytz, etc.)
- **Risk Level**: Low
- **Recommendation**: Implement regular dependency scanning and updates to address potential vulnerabilities in dependencies.

#### 4. GitHub Actions Workflow Secrets

- **Finding**: The GitHub Actions workflow (`deploy_updater_workflow.yml`) uses AWS access keys and secret keys stored as GitHub secrets.
- **Risk Level**: High
- **Recommendation**: Replace direct AWS access keys with OpenID Connect (OIDC) for GitHub Actions to AWS authentication. This eliminates the need to store long-lived AWS credentials as GitHub secrets, reducing the risk of credential exposure or misuse.

```yaml
# Example of OIDC configuration for GitHub Actions
jobs:
  deploy:
    # ...
    permissions:
      id-token: write  # Required for OIDC
      contents: read
    
    steps:
      # ...
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsRole  # REPLACE with your actual AWS account ID
          aws-region: us-east-1
```

> **Note**: Replace `123456789012` with your actual AWS account ID when implementing this workflow.

### Data Privacy Considerations

- The application primarily processes publicly available NHL statistics data.
- Email addresses used for notifications should be handled according to relevant privacy regulations.
- No personally identifiable information (PII) beyond email addresses appears to be collected or processed.

## Security Best Practices Implementation

### Current Security Measures

1. **CloudFront Security Headers**: The project implements security headers via CloudFront ResponseHeadersPolicy.
2. **S3 Bucket Security**: Public access blocking is enabled on S3 buckets.
3. **HTTPS Enforcement**: CloudFront is configured to redirect HTTP to HTTPS.
4. **Least Privilege**: Lambda functions use IAM roles with permissions scoped to required operations.

### Recommended Additional Measures

1. **Automated Dependency Scanning**
   - Implement automated scanning using tools like Bandit for Python-specific vulnerabilities.
   - Consider integrating dependency scanning into CI/CD pipelines.

2. **AWS Resource Security**
   - Implement more specific IAM permissions using resource-level restrictions.
   - Enable AWS CloudTrail for comprehensive logging of API calls.
   - Consider implementing AWS Config rules for continuous compliance monitoring.

3. **Secrets Management**
   - Migrate all configuration to AWS Systems Manager Parameter Store with encryption.
   - Remove any hardcoded credentials or configuration from code.
   - **Replace GitHub Actions AWS credentials with OIDC authentication** to eliminate the need for storing long-lived AWS credentials in GitHub secrets.

4. **Regular Security Reviews**
   - Schedule quarterly security reviews of IAM permissions and dependencies.
   - Update dependencies regularly to address security vulnerabilities.

## Compliance Considerations

### Data Protection

- If collecting email addresses for notifications, ensure compliance with relevant privacy regulations (GDPR, CCPA, etc.).
- Implement appropriate data retention policies for any stored email addresses.
- Consider adding a privacy policy if distributing the application to users.

### AWS Compliance

- Review AWS Shared Responsibility Model to understand security responsibilities.
- Consider using AWS Trusted Advisor for additional security and compliance recommendations.
- Implement resource tagging for better governance and compliance tracking.

## Security Monitoring and Incident Response

### Monitoring Recommendations

1. **CloudWatch Alarms**
   - Set up alarms for unusual Lambda function errors or invocations.
   - Monitor for unauthorized access attempts to AWS resources.

2. **Log Analysis**
   - Centralize and analyze CloudWatch Logs for security events.
   - Consider implementing log retention policies.

### Incident Response

1. **Response Plan**
   - Develop a basic incident response plan for security events.
   - Document contact information for responsible parties.

2. **Recovery Procedures**
   - Document procedures for recovering from potential security incidents.
   - Implement regular backups of configuration and code.

## Security Update Schedule

- **Dependencies**: Review and update monthly
- **IAM Permissions**: Review quarterly
- **Security Documentation**: Update semi-annually or after significant changes
- **Vulnerability Scanning**: Implement as part of CI/CD process

## Reporting Security Issues

If you discover a security vulnerability in this project, please report it responsibly by contacting the project maintainers directly rather than creating a public issue.
