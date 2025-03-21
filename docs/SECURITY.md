# Security Policy and Compliance Documentation

This document outlines the security practices, potential vulnerabilities, and compliance considerations for the Ovechkin Goal Tracker project.

## Security Assessment

### Identified Security Considerations

#### 1. AWS IAM Permissions

- **Finding**: The Lambda execution role (`WebsiteUpdaterRole`) now uses properly scoped resource patterns for S3 and CloudFront permissions, following the principle of least privilege.
- **Risk Level**: Low (previously Medium)
- **Recommendation**: Continue to review IAM permissions regularly and further restrict the CloudFront distribution pattern if possible to specific distribution IDs.

```yaml
# Example of current S3 permissions (properly scoped)
- Effect: Allow
  Action:
    - s3:PutObject
    - s3:GetObject
    - s3:ListBucket
  Resource: 
    - !Sub 'arn:aws:s3:::${StackName}-website-${AWS::AccountId}'
    - !Sub 'arn:aws:s3:::${StackName}-website-${AWS::AccountId}/*'
```

#### 2. Email Configuration Management

- **Finding**: Email configuration is stored in AWS Systems Manager Parameter Store with appropriate encryption, which is a secure approach. The application correctly retrieves these parameters at runtime.
- **Risk Level**: Low
- **Recommendation**: Ensure all Parameter Store values are encrypted and implement rotation policies for any sensitive parameters.

#### 3. Dependency Security

- **Finding**: The project uses several external dependencies (boto3, requests, pytz, etc.) which are managed through requirements.txt. The requirements files use a mix of exact version pinning (e.g., `boto3==1.34.7`) and minimum version specifications (e.g., `requests>=2.32.0`).
- **Risk Level**: Low to Medium
- **Recommendation**: Implement regular dependency scanning and updates to address potential vulnerabilities in dependencies. Consider using version pinning with security patches allowed (e.g., `requests~=2.32.0` instead of `requests>=2.32.0`) for all dependencies to balance security and maintainability.

#### 4. GitHub Actions Workflow Security

- **Finding**: The GitHub Actions workflow (`deploy_updater_workflow.yml`) now uses OpenID Connect (OIDC) for AWS authentication, which is a significant security improvement over storing long-lived AWS credentials.
- **Risk Level**: Low (previously High)
- **Recommendation**: Continue using OIDC for authentication and ensure the IAM role used has the minimum necessary permissions.

#### 5. Virtual Environment Management

- **Finding**: The application has improved virtual environment handling in the run.sh script, which now properly validates the Python interpreter and recreates the environment if needed.
- **Risk Level**: Low
- **Recommendation**: Continue with the current approach of validating the virtual environment integrity before use.

#### 6. Input Validation and Error Handling

- **Finding**: The Lambda functions include proper input validation and error handling, with appropriate logging of errors and sanitization of user inputs.
- **Risk Level**: Low
- **Recommendation**: Continue to maintain robust error handling and consider implementing additional input validation for any new features.

#### 7. CORS Configuration

- **Finding**: The Lambda function includes CORS headers that allow requests from any origin (`Access-Control-Allow-Origin: "*"`).
- **Risk Level**: Medium
- **Recommendation**: Restrict CORS to specific domains where possible to reduce the risk of cross-site attacks.

### Data Privacy Considerations

- The application primarily processes publicly available NHL statistics data.
- Email addresses used for notifications are stored securely in AWS Parameter Store.
- No personally identifiable information (PII) beyond email addresses appears to be collected or processed.
- The application correctly implements secure handling of email addresses, using getpass for input and secure parameter storage.

## Security Best Practices Implementation

### Current Security Measures

1. **Secure Configuration Management**: 
   - The application uses AWS Systems Manager Parameter Store for storing configuration values.
   - Parameters are retrieved securely at runtime with proper error handling and fallback mechanisms.
   - The code includes fallback mechanisms when parameters are not available.

2. **Authentication**: 
   - GitHub Actions uses OIDC for AWS authentication, eliminating the need for long-lived credentials.
   - AWS credentials are not hardcoded in the application code.
   - The application uses IAM roles with appropriate permissions for AWS service access.

3. **Input Validation and Error Handling**:
   - The application includes validation for user inputs and API responses.
   - Error handling is implemented to prevent application crashes due to unexpected inputs.
   - Errors are properly logged with appropriate detail levels.

4. **Dependency Management**:
   - Dependencies are managed through requirements.txt with specific versions.
   - The virtual environment setup has been improved to ensure consistent dependency installation.
   - Separate requirements files are maintained for different environments (local development vs. Lambda).

5. **File Operations Security**:
   - The application uses secure file operations with proper error handling.
   - Temporary directories are used appropriately in the Lambda environment.
   - File paths are properly validated before operations.

### Recommended Additional Measures

1. **Automated Dependency Scanning**
   - Implement automated scanning using tools like Bandit for Python-specific vulnerabilities.
   - Add a GitHub Actions workflow to regularly scan dependencies for vulnerabilities.
   - Example Bandit integration in GitHub Actions:

```yaml
- name: Run Bandit security scan
  run: |
    pip install bandit
    bandit -r ovechkin_tracker/ -f json -o bandit-results.json
```

2. **AWS Resource Security**
   - Further restrict CloudFront distribution permissions to specific distribution IDs where possible.
   - Enable AWS CloudTrail for comprehensive logging of API calls.
   - Consider implementing AWS Config rules for continuous compliance monitoring.

3. **Secrets Management**
   - Continue using AWS Systems Manager Parameter Store with encryption.
   - Implement parameter rotation policies for any sensitive values.
   - Ensure all environment-specific configurations are stored in Parameter Store rather than in code.

4. **Regular Security Reviews**
   - Schedule quarterly security reviews of IAM permissions and dependencies.
   - Update dependencies regularly to address security vulnerabilities.
   - Implement automated security testing as part of the CI/CD pipeline.

5. **CORS Policy Restriction**
   - Modify the CORS policy to restrict allowed origins to specific domains.
   - Example of more restrictive CORS headers:

```python
"headers": {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "https://greateightgoals.com",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token"
}
```

## Compliance Considerations

### GDPR Compliance

While the application primarily processes public NHL statistics data, it does handle email addresses for notifications, which are considered personal data under GDPR.

**Current Compliance Status**:
- Email addresses are stored securely in AWS Parameter Store.
- The application does not share email addresses with third parties.
- Users can provide their email address directly for notifications.

**Recommendations**:
- Add a privacy policy explaining how email addresses are used and stored.
- Implement a mechanism for users to request deletion of their email address.
- Document the data retention period for email addresses.

### AWS Well-Architected Framework

The application generally follows AWS Well-Architected Framework principles:

1. **Operational Excellence**: 
   - The application uses automation for deployment through GitHub Actions.
   - Error handling and logging are implemented throughout the codebase.
   - The run.sh script provides a consistent interface for various operations.

2. **Security**: 
   - Configuration is stored securely in AWS Parameter Store.
   - The application uses least privilege principles for IAM roles.
   - Authentication is handled securely using OIDC for GitHub Actions.

3. **Reliability**: 
   - The application includes error handling and fallback mechanisms.
   - CloudWatch alarms are configured for monitoring Lambda function errors.
   - Dead Letter Queues are used for handling failed SNS deliveries.

4. **Performance Efficiency**: 
   - The application uses caching to improve performance.
   - Lambda functions are configured with appropriate memory and timeout settings.
   - CloudFront is used for content delivery optimization.

5. **Cost Optimization**: 
   - The application uses serverless components to minimize costs.
   - Resources are properly sized for the workload.
   - Caching is implemented to reduce API calls and improve efficiency.

## Monitoring Recommendations

1. **CloudWatch Alarms**
   - Set up alarms for unusual Lambda function errors or invocations.
   - Monitor for unauthorized access attempts to AWS resources.
   - Configure alarms for API Gateway 4xx and 5xx errors.

2. **CloudTrail Logging**
   - Enable CloudTrail logging for all API calls.
   - Set up alerts for sensitive API calls (e.g., IAM changes, parameter modifications).
   - Implement log retention policies to balance cost and compliance requirements.

3. **Regular Security Scans**
   - Implement regular security scans using tools like Bandit, Prowler, or AWS Inspector.
   - Schedule quarterly manual security reviews.
   - Integrate security scanning into the CI/CD pipeline.

## Security Response Plan

1. **Vulnerability Reporting**
   - Create a security.md file with instructions for reporting vulnerabilities.
   - Set up a dedicated email address for security reports.
   - Define a process for acknowledging and responding to vulnerability reports.

2. **Incident Response**
   - Document the steps to take in case of a security incident.
   - Identify the team members responsible for security incident response.
   - Establish communication channels for security incidents.
   - Define severity levels and corresponding response times.

3. **Remediation Process**
   - Document the process for addressing security vulnerabilities.
   - Establish SLAs for addressing different types of vulnerabilities based on severity.
   - Implement a process for communicating security updates to users.
   - Document post-incident review procedures to prevent similar issues in the future.

## Conclusion

The Ovechkin Goal Tracker application has implemented several security best practices, particularly in the areas of configuration management, authentication, and dependency management. The recent improvements to virtual environment handling, IAM permissions, and the use of OIDC for GitHub Actions authentication have significantly enhanced the security posture.

The application now follows the principle of least privilege for IAM permissions, with properly scoped resource patterns for S3 and CloudFront permissions. Email configuration is securely stored in AWS Systems Manager Parameter Store, and the application includes proper input validation and error handling.

By implementing the recommended additional measures, particularly automated dependency scanning, further restriction of CORS policies, and regular security reviews, the application can further improve its security posture and ensure compliance with relevant regulations and best practices.
