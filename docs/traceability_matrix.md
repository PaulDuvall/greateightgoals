# Ovechkin Goal Tracker - Traceability Matrix

This document provides traceability between user stories, implementation files, and test files for the Ovechkin Goal Tracker project. It helps maintain alignment between requirements, code, and testing.

## User Story Traceability

| User Story ID | Description | Implementation Files | Test Files |
|--------------|-------------|----------------------|------------|
| [US-100](user_stories.md#us-100-track-ovechkins-goal-progress) | Track Ovechkin's Goal Progress | [ovechkin_tracker/ovechkin_data.py](/ovechkin_tracker/ovechkin_data.py)<br>[ovechkin_tracker/nhl_api.py](/ovechkin_tracker/nhl_api.py)<br>[ovechkin_tracker/stats.py](/ovechkin_tracker/stats.py) | [tests/test_ovechkin_data.py](/tests/test_ovechkin_data.py)<br>[tests/test_nhl_api.py](/tests/test_nhl_api.py) |
| [US-110](user_stories.md#us-110-command-line-interface) | Command-Line Interface | [ovechkin_tracker/cli.py](/ovechkin_tracker/cli.py)<br>[run.sh](/run.sh) | [tests/test_cli.py](/tests/test_cli.py) |
| [US-120](user_stories.md#us-120-email-notifications) | Email Notifications | [ovechkin_tracker/email.py](/ovechkin_tracker/email.py)<br>[run.sh](/run.sh) | [tests/test_email.py](/tests/test_email.py) |
| [US-200](user_stories.md#us-200-static-website-display) | Static Website Display | [aws-static-website/update_website.py](/aws-static-website/update_website.py)<br>[aws-static-website/static/index.html](/aws-static-website/static/index.html) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [US-210](user_stories.md#us-210-automated-website-updates) | Automated Website Updates | [aws-static-website/lambda/update_website_lambda.py](/aws-static-website/lambda/update_website_lambda.py)<br>[aws-static-website/templates/website-updater.yaml](/aws-static-website/templates/website-updater.yaml)<br>[aws-static-website/scripts/deploy_updater.sh](/aws-static-website/scripts/deploy_updater.sh) | [tests/test_lambda_function.py](/tests/test_lambda_function.py) |
| [US-220](user_stories.md#us-220-cloudfront-cache-configuration) | CloudFront Cache Configuration | [aws-static-website/scripts/configure-cloudfront.sh](/aws-static-website/scripts/configure-cloudfront.sh)<br>[aws-static-website/run.sh](/aws-static-website/run.sh) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [US-300](user_stories.md#us-300-aws-infrastructure-as-code) | AWS Infrastructure as Code | [aws-static-website/templates/static-website.yaml](/aws-static-website/templates/static-website.yaml)<br>[aws-static-website/scripts/deploy.sh](/aws-static-website/scripts/deploy.sh) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [US-310](user_stories.md#us-310-scheduled-lambda-updates) | Scheduled Lambda Updates | [aws-static-website/templates/website-updater.yaml](/aws-static-website/templates/website-updater.yaml)<br>[aws-static-website/lambda/update_website_lambda.py](/aws-static-website/lambda/update_website_lambda.py) | [tests/test_lambda_function.py](/tests/test_lambda_function.py) |
| [US-320](user_stories.md#us-320-github-actions-workflow) | GitHub Actions Workflow | [.github/workflows/deploy_updater_workflow.yml](/.github/workflows/deploy_updater_workflow.yml) | Manual verification |
| [US-330](user_stories.md#us-330-github-actions-oidc-authentication) | GitHub Actions OIDC Authentication | [aws-static-website/cloudformation/github_oidc.yaml](/aws-static-website/cloudformation/github_oidc.yaml)<br>[aws-static-website/scripts/setup_oidc.sh](/aws-static-website/scripts/setup_oidc.sh)<br>[.github/workflows/deploy_updater_workflow.yml](/.github/workflows/deploy_updater_workflow.yml) | Manual verification |
| [US-400](user_stories.md#us-400-configuration-management) | Configuration Management | [ovechkin_tracker/cli.py](/ovechkin_tracker/cli.py)<br>[lambda/lambda_function.py](/lambda/lambda_function.py) | [tests/test_lambda_function.py](/tests/test_lambda_function.py) |
| [US-410](user_stories.md#us-410-comprehensive-testing) | Comprehensive Testing | [tests/run_tests.sh](/tests/run_tests.sh)<br>Various test files | Self-testing |
| [US-500](user_stories.md#us-500-enhanced-game-projections) | Enhanced Game Projections | Partially implemented | N/A |
| [US-520](user_stories.md#us-520-historical-comparisons) | Historical Comparisons | Not implemented | N/A |
| [US-530](user_stories.md#us-530-game-aware-scheduling) | Game-Aware Scheduling | Not implemented | N/A |

## Implementation Coverage

| Implementation File | Associated User Stories | Test Coverage |
|---------------------|--------------------------|---------------|
| [ovechkin_tracker/ovechkin_data.py](/ovechkin_tracker/ovechkin_data.py) | [US-100](user_stories.md#us-100-track-ovechkins-goal-progress) | [tests/test_ovechkin_data.py](/tests/test_ovechkin_data.py) |
| [ovechkin_tracker/nhl_api.py](/ovechkin_tracker/nhl_api.py) | [US-100](user_stories.md#us-100-track-ovechkins-goal-progress) | [tests/test_nhl_api.py](/tests/test_nhl_api.py) |
| [ovechkin_tracker/stats.py](/ovechkin_tracker/stats.py) | [US-100](user_stories.md#us-100-track-ovechkins-goal-progress) | [tests/test_ovechkin_data.py](/tests/test_ovechkin_data.py) |
| [ovechkin_tracker/cli.py](/ovechkin_tracker/cli.py) | [US-110](user_stories.md#us-110-command-line-interface), [US-400](user_stories.md#us-400-configuration-management) | [tests/test_cli.py](/tests/test_cli.py) |
| [ovechkin_tracker/email.py](/ovechkin_tracker/email.py) | [US-120](user_stories.md#us-120-email-notifications) | [tests/test_email.py](/tests/test_email.py) |
| [run.sh](/run.sh) | [US-110](user_stories.md#us-110-command-line-interface), [US-120](user_stories.md#us-120-email-notifications) | [tests/test_cli.py](/tests/test_cli.py) |
| [aws-static-website/update_website.py](/aws-static-website/update_website.py) | [US-200](user_stories.md#us-200-static-website-display) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [aws-static-website/static/index.html](/aws-static-website/static/index.html) | [US-200](user_stories.md#us-200-static-website-display) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [aws-static-website/lambda/update_website_lambda.py](/aws-static-website/lambda/update_website_lambda.py) | [US-210](user_stories.md#us-210-automated-website-updates), [US-310](user_stories.md#us-310-scheduled-lambda-updates) | [tests/test_lambda_function.py](/tests/test_lambda_function.py) |
| [aws-static-website/templates/website-updater.yaml](/aws-static-website/templates/website-updater.yaml) | [US-210](user_stories.md#us-210-automated-website-updates), [US-310](user_stories.md#us-310-scheduled-lambda-updates) | [tests/test_lambda_function.py](/tests/test_lambda_function.py) |
| [aws-static-website/scripts/deploy_updater.sh](/aws-static-website/scripts/deploy_updater.sh) | [US-210](user_stories.md#us-210-automated-website-updates) | [tests/test_lambda_function.py](/tests/test_lambda_function.py) |
| [aws-static-website/scripts/configure-cloudfront.sh](/aws-static-website/scripts/configure-cloudfront.sh) | [US-220](user_stories.md#us-220-cloudfront-cache-configuration) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [aws-static-website/run.sh](/aws-static-website/run.sh) | [US-220](user_stories.md#us-220-cloudfront-cache-configuration) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [aws-static-website/templates/static-website.yaml](/aws-static-website/templates/static-website.yaml) | [US-300](user_stories.md#us-300-aws-infrastructure-as-code) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [aws-static-website/scripts/deploy.sh](/aws-static-website/scripts/deploy.sh) | [US-300](user_stories.md#us-300-aws-infrastructure-as-code) | [tests/test_static_website.py](/tests/test_static_website.py) |
| [.github/workflows/deploy_updater_workflow.yml](/.github/workflows/deploy_updater_workflow.yml) | [US-320](user_stories.md#us-320-github-actions-workflow) | Manual verification |
| [lambda/lambda_function.py](/lambda/lambda_function.py) | [US-400](user_stories.md#us-400-configuration-management) | [tests/test_lambda_function.py](/tests/test_lambda_function.py) |
| [tests/run_tests.sh](/tests/run_tests.sh) | [US-410](user_stories.md#us-410-comprehensive-testing) | Self-testing |
| [aws-static-website/cloudformation/github_oidc.yaml](/aws-static-website/cloudformation/github_oidc.yaml) | [US-330](user_stories.md#us-330-github-actions-oidc-authentication) | Manual verification |
| [aws-static-website/scripts/setup_oidc.sh](/aws-static-website/scripts/setup_oidc.sh) | [US-330](user_stories.md#us-330-github-actions-oidc-authentication) | Manual verification |

## Test Coverage

| Test File | Implementation Files Covered | User Stories Verified |
|-----------|-------------------------------|------------------------|
| [tests/test_ovechkin_data.py](/tests/test_ovechkin_data.py) | [ovechkin_tracker/ovechkin_data.py](/ovechkin_tracker/ovechkin_data.py)<br>[ovechkin_tracker/stats.py](/ovechkin_tracker/stats.py) | [US-100](user_stories.md#us-100-track-ovechkins-goal-progress) |
| [tests/test_nhl_api.py](/tests/test_nhl_api.py) | [ovechkin_tracker/nhl_api.py](/ovechkin_tracker/nhl_api.py) | [US-100](user_stories.md#us-100-track-ovechkins-goal-progress) |
| [tests/test_cli.py](/tests/test_cli.py) | [ovechkin_tracker/cli.py](/ovechkin_tracker/cli.py)<br>[run.sh](/run.sh) | [US-110](user_stories.md#us-110-command-line-interface) |
| [tests/test_email.py](/tests/test_email.py) | [ovechkin_tracker/email.py](/ovechkin_tracker/email.py) | [US-120](user_stories.md#us-120-email-notifications) |
| [tests/test_static_website.py](/tests/test_static_website.py) | [aws-static-website/update_website.py](/aws-static-website/update_website.py)<br>[aws-static-website/static/index.html](/aws-static-website/static/index.html)<br>[aws-static-website/scripts/configure-cloudfront.sh](/aws-static-website/scripts/configure-cloudfront.sh)<br>[aws-static-website/templates/static-website.yaml](/aws-static-website/templates/static-website.yaml) | [US-200](user_stories.md#us-200-static-website-display)<br>[US-220](user_stories.md#us-220-cloudfront-cache-configuration)<br>[US-300](user_stories.md#us-300-aws-infrastructure-as-code) |
| [tests/test_lambda_function.py](/tests/test_lambda_function.py) | [aws-static-website/lambda/update_website_lambda.py](/aws-static-website/lambda/update_website_lambda.py)<br>[lambda/lambda_function.py](/lambda/lambda_function.py) | [US-210](user_stories.md#us-210-automated-website-updates)<br>[US-310](user_stories.md#us-310-scheduled-lambda-updates)<br>[US-400](user_stories.md#us-400-configuration-management) |
| [tests/test_lambda_local.py](/tests/test_lambda_local.py) | [lambda/lambda_function.py](/lambda/lambda_function.py) | [US-210](user_stories.md#us-210-automated-website-updates)<br>[US-310](user_stories.md#us-310-scheduled-lambda-updates) |

## Maintenance Guidelines

1. **Adding New User Stories**:
   - Create a new entry in user_stories.md with a unique ID (US-XXX)
   - Add the story to this traceability matrix
   - Link implementation and test files once developed

2. **Modifying Existing Features**:
   - Update the corresponding user story in user_stories.md
   - Update this matrix if implementation or test files change

3. **Removing Features**:
   - Mark the user story as deprecated rather than removing it
   - Update the implementation and test status accordingly

4. **Periodic Review**:
   - Review this matrix quarterly to ensure it remains accurate
   - Verify that all new code has corresponding user stories and tests
