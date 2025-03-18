## Core Functionality

### US-100: Track Ovechkin's Goal Progress
**As a** hockey fan,  
**I want to** see Alex Ovechkin's current goal count and progress toward Wayne Gretzky's record,  
**So that** I can follow his historic chase.

**Acceptance Criteria:**
- Current goal count is displayed  
- Goals needed to break the record (894) is calculated  
- Current season's goal pace is shown  
- Projected record-breaking date is calculated  

**Implementation:**
- [ovechkin_tracker/ovechkin_data.py](/ovechkin_tracker/ovechkin_data.py)  
- [ovechkin_tracker/nhl_api.py](/ovechkin_tracker/nhl_api.py)  
- [ovechkin_tracker/stats.py](/ovechkin_tracker/stats.py)

**Tests:**
- [tests/test_ovechkin_data.py](/tests/test_ovechkin_data.py)  
- [tests/test_nhl_api.py](/tests/test_nhl_api.py)

---

### US-110: Command-Line Interface
**As a** technical user,  
**I want to** access Ovechkin's stats via command line,  
**So that** I can quickly check his progress without opening a browser.

**Acceptance Criteria:**
- Command `./run.sh stats` displays formatted stats in the terminal  
- Output includes current goals, goals needed, and projections  
- Clear formatting makes information easy to read  

**Implementation:**
- [ovechkin_tracker/cli.py](/ovechkin_tracker/cli.py)  
- [run.sh](/run.sh)

**Tests:**
- [tests/test_cli.py](/tests/test_cli.py)

---

### US-120: Email Notifications
**As a** hockey enthusiast,  
**I want to** receive email updates about Ovechkin's progress,  
**So that** I can stay informed without actively checking.

**Acceptance Criteria:**
- Command `./run.sh email` sends stats to configured recipient  
- Command `./run.sh email-to user@example.com` sends to specified address  
- Email contains formatted stats and projections  
- Uses Amazon SES for reliable delivery  

**Implementation:**
- [ovechkin_tracker/email.py](/ovechkin_tracker/email.py)  
- [run.sh](/run.sh)

**Tests:**
- [tests/test_email.py](/tests/test_email.py)

---

## Static Website

### US-200: Static Website Display
**As a** casual fan,  
**I want to** view Ovechkin's stats on a website,  
**So that** I can easily access this information from any device.

**Acceptance Criteria:**
- Website displays current goal count prominently  
- Shows progress toward breaking the record  
- Includes projected record-breaking game details  
- Responsive design works on mobile and desktop  

**Implementation:**
- [aws-static-website/update_website.py](/aws-static-website/update_website.py)  
- [aws-static-website/static/index.html](/aws-static-website/static/index.html)

**Tests:**
- [tests/test_static_website.py](/tests/test_static_website.py)

---

### US-210: Automated Website Updates
**As a** website administrator,  
**I want to** have the website update automatically,  
**So that** fans always see the latest stats without manual intervention.

**Acceptance Criteria:**
- Lambda function updates the website on a schedule  
- Updates occur at least every 30 minutes  
- CloudFront cache is invalidated after updates  
- Update failures are logged and monitored  

**Implementation:**
- [aws-static-website/lambda/update_website_lambda.py](/aws-static-website/lambda/update_website_lambda.py)  
- [aws-static-website/templates/website-updater.yaml](/aws-static-website/templates/website-updater.yaml)  
- [aws-static-website/scripts/deploy_updater.sh](/aws-static-website/scripts/deploy_updater.sh)

**Tests:**
- [tests/test_lambda_function.py](/tests/test_lambda_function.py)

---

### US-220: CloudFront Cache Configuration
**As a** website administrator,  
**I want to** ensure specific files are never cached,  
**So that** users always see the most up-to-date information.

**Acceptance Criteria:**
- CloudFront is configured with a cache behavior for `data/stats.json`  
- The CachingDisabled policy is applied to this path  
- Configuration is automated and repeatable  
- Cache invalidation occurs after content updates  

**Implementation:**
- [aws-static-website/scripts/configure-cloudfront.sh](/aws-static-website/scripts/configure-cloudfront.sh)  
- [aws-static-website/run.sh](/aws-static-website/run.sh)

**Tests:**
- [tests/test_static_website.py](/tests/test_static_website.py)

---

## AWS Infrastructure

### US-300: AWS Infrastructure as Code
**As a** DevOps engineer,  
**I want to** deploy the entire infrastructure using CloudFormation,  
**So that** the environment is consistent, reproducible, and version-controlled.

**Acceptance Criteria:**
- CloudFormation template defines all required resources  
- S3 bucket for static website content  
- CloudFront distribution for content delivery  
- ACM certificate for HTTPS  
- Route 53 configuration for domain management  
- Appropriate IAM roles and policies  

**Implementation:**
- [aws-static-website/templates/static-website.yaml](/aws-static-website/templates/static-website.yaml)  
- [aws-static-website/scripts/deploy.sh](/aws-static-website/scripts/deploy.sh)

**Tests:**
- [tests/test_static_website.py](/tests/test_static_website.py)

---

### US-310: Scheduled Lambda Updates
**As a** system administrator,  
**I want to** configure automated website updates via Lambda and EventBridge,  
**So that** the website stays current with minimal maintenance.

**Acceptance Criteria:**
- CloudFormation template creates Lambda function and EventBridge rule  
- Schedule is configurable (rate or cron expression)  
- Lambda has appropriate permissions to update S3 and invalidate CloudFront  
- Function execution is logged in CloudWatch  

**Implementation:**
- [aws-static-website/templates/website-updater.yaml](/aws-static-website/templates/website-updater.yaml)  
- [aws-static-website/lambda/update_website_lambda.py](/aws-static-website/lambda/update_website_lambda.py)

**Tests:**
- [tests/test_lambda_function.py](/tests/test_lambda_function.py)

---

### US-320: GitHub Actions Workflow
**As a** developer,  
**I want to** deploy updates through GitHub Actions,  
**So that** changes are automatically deployed when code is pushed.

**Acceptance Criteria:**
- Workflow is triggered by git push and manual dispatch  
- Builds and packages the Lambda function  
- Deploys the CloudFormation stack  
- Updates the Lambda function code  
- Provides informative logs and status updates  

**Implementation:**
- [.github/workflows/deploy_updater_workflow.yml](/.github/workflows/deploy_updater_workflow.yml)

**Tests:**
- Manual verification of workflow execution  

---

### US-330: GitHub Actions OIDC Authentication
**As a** DevOps engineer,  
**I want to** use OIDC authentication for GitHub Actions workflows with AWS,  
**So that** I can eliminate the need for long-lived AWS credentials in GitHub secrets.

**Acceptance Criteria:**
- CloudFormation template for setting up IAM OIDC provider and role
- Automated script to deploy the OIDC infrastructure and configure GitHub repository
- IAM role with appropriate permissions for GitHub Actions workflows
- Example GitHub Actions workflow using OIDC authentication
- Documentation on how to set up and use OIDC authentication

**Implementation:**
- [aws-static-website/cloudformation/github_oidc.yaml](/aws-static-website/cloudformation/github_oidc.yaml)  
- [aws-static-website/scripts/setup_oidc.sh](/aws-static-website/scripts/setup_oidc.sh)  
- [.github/workflows/deploy_updater_workflow.yml](/.github/workflows/deploy_updater_workflow.yml)

**Tests:**
- Manual verification of GitHub Actions workflow execution
- Validation of IAM role assumption via OIDC

---

## Configuration and Management

### US-400: Configuration Management
**As a** system administrator,  
**I want to** manage configuration through environment variables or AWS Parameter Store,  
**So that** sensitive information is securely stored and easily updated.

**Acceptance Criteria:**
- Application reads configuration from `.env` file or Parameter Store  
- Supports configuration for AWS region, sender email, and recipient email  
- Parameter Store values are encrypted when appropriate  
- Configuration changes don't require code changes  

**Implementation:**
- [ovechkin_tracker/cli.py](/ovechkin_tracker/cli.py)  
- [lambda/lambda_function.py](/lambda/lambda_function.py)

**Tests:**
- [tests/test_lambda_function.py](/tests/test_lambda_function.py)

---

### US-410: Comprehensive Testing
**As a** developer,  
**I want to** have automated tests for all components,  
**So that** I can ensure the application works correctly after changes.

**Acceptance Criteria:**
- Unit tests for core functionality  
- Integration tests for AWS services  
- Test script that can run all tests or specific categories  
- Test coverage report generation  

**Implementation:**
- [tests/run_tests.sh](/tests/run_tests.sh)  
- Various test files in the `tests` directory

**Tests:**
- Self-testing via the test suite  

---
Below is an example of how you can insert a new user story (or multiple stories) specifically focused on Blue/Green deployments into the **Future Considerations** section without renumbering any existing stories. Since the numbering jumps by tens (500, 510, 520, etc.), one option is to add **US-515** in between **US-510** and **US-520**. You can rename or add additional user stories similarly (e.g., US-516, US-517, etc.) if needed.

---

## Future Considerations

### US-500: Enhanced Game Projections
**As a** hockey analyst,  
**I want to** see detailed projections about the record-breaking game,  
**So that** I can plan coverage and analysis.

**Acceptance Criteria:**
- Projection includes full game details (date, time, opponent, location)  
- Accounts for schedule changes and game cancellations  
- Provides confidence level for the projection  
- Updates automatically as the season progresses  

**Status:** Partially implemented

---

### US-510: Mobile Application
**As a** mobile user,  
**I want to** have a dedicated mobile app for tracking Ovechkin's progress,  
**So that** I can receive push notifications and have a native experience.

**Acceptance Criteria:**
- Native iOS and Android applications  
- Push notifications for milestones and updates  
- Offline capability for viewing latest cached stats  
- Same core functionality as the website  

**Status:** Not implemented

---

### US-515: Blue/Green Deployment Strategy
**As a** DevOps engineer,  
**I want to** implement a Blue/Green deployment approach for website updates,  
**So that** I can minimize downtime and risk when rolling out new versions.

**Acceptance Criteria:**
- Two production environments (Blue and Green) are maintained  
- Infrastructure-as-Code (IaC) ensures both environments mirror each other  
- Traffic can be switched from Blue to Green with near-zero downtime  
- Rollback process is documented and can be executed quickly if needed  
- Monitoring and health checks confirm environment stability before switching

**Implementation:**
- Create a duplicate environment stack (CloudFormation or Terraform)  
- Incorporate scripts (e.g., AWS CodeDeploy, Route 53 weighted routing)  
- Document rollback procedure and test it regularly  
- Reference Martin Fowler’s [BlueGreenDeployment article](https://martinfowler.com/bliki/BlueGreenDeployment.html) for best practices  
- Include automation tests to verify environment switchover and rollback

**Tests:**
- Automated integration tests to confirm the correct environment is active  
- Load testing to validate performance on both environments  
- Failover simulation to ensure rollback process works  
- Monitoring checks in Amazon CloudWatch or other APM tools

**Status:** Not implemented

---

### US-520: Historical Comparisons
**As a** hockey historian,  
**I want to** compare Ovechkin's pace with other great goal scorers,  
**So that** I can put his achievement in historical context.

**Acceptance Criteria:**
- Compare with Gretzky, Hull, Howe, and other top goal scorers  
- Show goals by age and season number  
- Visualize pace through interactive charts  
- Include contextual statistics (era-adjusted goals, etc.)  

**Status:** Not implemented

---

### US-530: Game-Aware Website Updates
**As a** website administrator,  
**I want to** optimize the website update schedule based on the Capitals' game schedule,  
**So that** I can reduce unnecessary API calls while ensuring timely updates after games.

**Acceptance Criteria:**
- Website updates every 6 hours on non-game days  
- Website updates every hour before games  
- Website updates every 15 minutes for 3 hours after games  
- No updates during games when the NHL API doesn't update  
- Automatic adjustment of schedules based on the Capitals' upcoming games  

**Implementation:**
- [aws-static-website/game_schedule_manager.py](/aws-static-website/game_schedule_manager.py)  
- [aws-static-website/cloudformation/game-aware-scheduler.yaml](/aws-static-website/cloudformation/game-aware-scheduler.yaml)  
- [aws-static-website/scripts/deploy_game_aware_scheduler.sh](/aws-static-website/scripts/deploy_game_aware_scheduler.sh)

**Tests:**
- Manual verification of EventBridge rule creation  
- Validation of update frequency during and after games  

**Status:** Not implemented

---

### US-540: Efficient Resource Utilization
**As a** system operator,  
**I want to** minimize unnecessary API calls and Lambda executions,  
**So that** I can reduce costs and system load.

**Acceptance Criteria:**
- Reduced number of Lambda executions on non-game days  
- Elimination of updates during games when they provide no value  
- Automatic disabling of the default fixed-interval schedule  
- CloudWatch metrics showing reduced execution frequency  

**Implementation:**
- [aws-static-website/game_schedule_manager.py](/aws-static-website/game_schedule_manager.py)  
- [aws-static-website/cloudformation/game-aware-scheduler.yaml](/aws-static-website/cloudformation/game-aware-scheduler.yaml)

**Tests:**
- CloudWatch logs analysis to verify execution patterns  
- Cost comparison before and after implementation  

---

### US-550: Timely Goal Updates
**As a** hockey fan,  
**I want to** see Ovechkin's goal updates shortly after they happen,  
**So that** I can stay current with his progress toward Gretzky's record.

**Acceptance Criteria:**
- More frequent updates (every 15 minutes) for 3 hours after games  
- Updates reflect Ovechkin's goals within 15-30 minutes of NHL API updates  
- Website shows accurate, up-to-date statistics after Capitals games  

**Implementation:**
- [aws-static-website/game_schedule_manager.py](/aws-static-website/game_schedule_manager.py)  
- [aws-static-website/update_website.py](/aws-static-website/update_website.py)

**Tests:**
- Manual verification after Capitals games  
- Timestamp validation of website updates  

---

## Recommendations for Future Alignment

1. **Automated Documentation Updates**  
2. **Story-Driven Development**  
3. **Quarterly Documentation Reviews**  
4. **Integration with Issue Tracking**  
5. **Documentation Testing**  
