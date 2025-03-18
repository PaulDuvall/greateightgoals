# Python Class for Ovechkin Data

Develop a fully automated Python solution that replicates and extends the functionality of the existing shell script (`./run.sh stats`) which outputs processed Ovechkin data. Your solution must meet the following requirements:

---

## 1. Encapsulation and API Implementation

- **Python Class:** Create a class named `OvechkinData` to encapsulate the processed data.
- **Getters and Setters:** Provide getter and setter methods for each relevant data field.
- **Python Version & Code Standards:**  
  - Use Python 3.11.  
  - Follow PEP8 style guidelines.  
  - Include detailed inline comments and comprehensive documentation.

---

## 2. Seamless Execution

- Ensure that the solution can be executed using the command `./run.sh stats`.
- The solution must be fully self-contained, with no dependencies on code outside of the scope of this request.

---

## 3. HTML Generation

- **Method:** Develop a method within `OvechkinData` that uses the getter methods to generate a simple yet informative HTML representation of the data.
- **Browser Compatibility:** The generated HTML should be easily rendered by modern web browsers.

---

## 4. Scheduled Upload to AWS S3

- **Automation:** Write a scheduled function (using AWS Lambda, CloudWatch Events, or an equivalent scheduling mechanism) that:
  - Uploads the generated HTML file to an S3 bucket.
  - Ensures reliable, automatic triggering on a defined schedule.

---

## 5. AWS Infrastructure Automation

Automate the provisioning of AWS resources to securely serve a static "Hello World" HTML file. The solution must be self-contained in its own directory and include all necessary files.

### 5.1. Directory Structure
- All files (CloudFormation template, static HTML file, and supporting scripts) should reside in a dedicated directory.

### 5.2. Bash Script
- **Purpose:** Trigger the CloudFormation template to provision the following AWS resources:
  - **ACM (AWS Certificate Manager):** Set up a certificate for HTTPS.
  - **Route 53:** Allow the user to configure the domain name by specifying an existing domain/hosted zone.
  - **CloudFront:** Deploy a CDN distribution that fronts the S3 bucket, including steps for cache invalidation to ensure fresh data.
  - **S3:** Create an S3 bucket to host the HTML file.
- **HTML File:** Include a static `index.html` file containing a simple "Hello World" message for initial testing.
- **S3 Permissions:** Configure the S3 bucket (using a bucket policy or equivalent) to allow public read access, in compliance with default restrictions.
- **Documentation:** Provide clear documentation and inline comments that explain:
  - How each AWS service is configured.
  - The interconnection between services to securely serve the HTML file.
  - How the bash script triggers the CloudFormation deployment.
  - How users can specify the domain/hosted zone in Route 53.
  - How the CloudFront cache invalidation process ensures fresh content.

**Additional AWS Role Variable:**

```
https://github.com/PaulDuvall/thegr8chase/settings/variables/actions
AWS_ROLE_TO_ASSUME
```

---

## 6. Create a New Tag Using Semantic Versioning

- **Tag Format:** `v0.0.0-description` (e.g., `v1.2.3-new-feature`), where:
  - **Major:** Backward-incompatible changes.
  - **Minor:** New functionality in a backward-compatible manner.
  - **Patch:** Backward-compatible bug fixes.
  - **Description:** A brief identifier of the update.
- **Documentation:** Clearly document the tag creation process in your version control system, indicating all changes made in the codebase.

---

## 7. Update the `README.md`

- **Content Update:**  
  - Review the current repository and capture all relevant changes and new functionalities.
  - Update the `README.md` with accurate instructions on setup, usage, and contribution guidelines.
- **Traceability:**  
  - Ensure recent modifications in the codebase are clearly reflected.
  - Include links to user stories, traceability documents, and versioning information where applicable.

---

## 8. Push Changes

1. Stage all changes:
   ```bash
   git add .
   ```
2. Commit with a descriptive message reflecting the updates:
   ```bash
   git commit -m "<Your descriptive commit message here>"
   ```
3. Push to the remote repository:
   ```bash
   git push
   ```

---

## 9. Analyze Code for Security, Privacy, and Compliance

1. Review the codebase and associated libraries for known vulnerabilities and potential privacy or compliance violations.  
2. Consider the use of automated scanning tools such as [Bandit](https://bandit.readthedocs.io/en/latest/), [Prowler](https://github.com/prowler-cloud/prowler), or [AWS CodeGuru Reviewer](https://aws.amazon.com/codeguru/) to identify common security issues.  
3. Ensure that data handling follows relevant regulations (e.g., GDPR, CCPA) and that any personal or sensitive data is appropriately masked, encrypted, or secured.  
4. Document findings in a dedicated `SECURITY.md` or integrate them into existing documentation, detailing remediation steps and best practices.  
5. Schedule regular reviews and scans to maintain ongoing compliance, especially in high-risk areas where data flows or access controls may change frequently.

---

## 10. Analyze the Codebase for Unused Files and Opportunities for Consolidation

1. **Conduct a Comprehensive File Audit:**  
   - Use static analysis tools and custom scripts to identify files that are no longer referenced in the codebase.  
   - Check for orphaned modules, outdated libraries, and redundant configurations.

2. **Evaluate File Usage and Dependencies:**  
   - Map out the dependency graph of your code to see which files are central and which are rarely or never invoked.  
   - Prioritize files with low or no usage for consolidation or removal.

3. **Perform Code Coverage Analysis:**  
   - Leverage code coverage tools to verify if tests are executing all files, highlighting those that might be obsolete.  
   - Identify files that have little to no test coverage as potential candidates for deletion.

4. **Review Version Control History:**  
   - Examine commit histories to understand the purpose and evolution of files that appear redundant.  
   - Ensure that any deletion or consolidation does not remove functionality important for historical context or future reference.

5. **Collaborate with Stakeholders:**  
   - Discuss proposed file removals or consolidations with your development team and key stakeholders.  
   - Validate that these changes align with the project’s strategic goals and do not disrupt the overall functionality.

6. **Plan and Execute Refactorings:**  
   - Develop a clear plan for refactoring the codebase, including file consolidation and cleanup tasks.  
   - Document all changes in a dedicated changelog or update section in your documentation; follow semantic versioning for significant modifications.

7. **Test Thoroughly Post-Cleanup:**  
   - Run all unit, integration, and end-to-end tests to ensure that file consolidation or deletion has not impacted system behavior.  
   - Use continuous integration (CI) pipelines to automatically verify that the refactored codebase maintains the expected functionality.

8. **Document the Process:**  
   - Update the project documentation to include the rationale behind consolidations or deletions.  
   - Ensure the documentation reflects any new module structure or file organization for future maintenance.

---

## 11. Documentation Standards

### 11.1. User Stories
- Clear ID format: `US-XXX`
- Acceptance criteria for each story
- Links to implementation and test files

### 11.2. Code Comments
- Reference user story IDs
- Document configuration requirements
- Explain complex logic or business rules

### 11.3. Version Control
- Semantic versioning for documentation changes
- Descriptive commit messages
- Tag major documentation updates

### 11.4. Testing Documentation
- Test file location: `./tests/`
- Test execution: `./tests/run_tests.sh`
- Test coverage requirements

---

## 12. User Story Updates

### 12.1. Review Existing User Stories
1. Examine the current codebase in detail.  
2. Identify all implemented features and functionalities.  
3. Compare these with the existing stories in `docs/user_stories.md`.  
4. Update any outdated or inaccurate stories to match the latest code.

### 12.2. Add New User Stories
1. Identify any new features or changes in the code that are not yet documented.  
2. Create new user stories that capture both technical details and user-centric perspectives.  
3. Ensure each story is clear and comprehensive.

### 12.3. Ensure Accuracy and Completeness
1. Verify that every user story provides clear insights into the intended functionality.  
2. Include acceptance criteria where applicable to define the expected behavior.  
3. Maintain consistency in language and structure throughout the document.

### 12.4. Recommendations for Future Alignment
1. Note any discrepancies between the current code and the documented user stories.  
2. Suggest best practices for keeping documentation synchronized with future code changes.  
3. Recommend periodic reviews to ensure ongoing alignment between the codebase and documentation.

### 12.5. Establish End-to-End Traceability
1. Ensure traceability between user stories, automated tests, and implementation details.  
2. Update `docs/traceability_matrix.md` so that each User Story ID (e.g., `US-300`) includes a hyperlink to its corresponding section in `docs/user_stories.md` (e.g., `user_stories.md#us-300-aws-resources-cleanup`).  
3. Document these relationships for seamless accountability and streamlined maintenance.

---

## 13. Generate Diagrams


Create a file named docs/architecture_diagrams_prompt.md containing the following text. This file is used to request generation of architecture diagrams in the same style/format used throughout your documentation.

# Architecture Diagrams Prompt

We need updated architecture diagrams for the following components:

1. **Ovechkin Data Processing Architecture**  
   - Flow of data from acquisition to HTML generation.  
   - AWS services used for storage and hosting (e.g., S3, CloudFront).  

2. **AWS Infrastructure for Static Site**  
   - Components: ACM, Route 53, CloudFront, and S3.  
   - Security and access flows (certificate management, DNS, CDN).  

3. **Scheduled Lambda for HTML Upload**  
   - Execution cycle (CloudWatch Events / EventBridge).  
   - High-level overview of data pipeline.

Please provide diagrams in a format that can be referenced in our markdown documentation. Use neutral background colors for easy embedding in various documents.
By placing this file in the docs/ folder, anyone can quickly reference and execute a request (for instance, via a generative AI tool or specialized diagramming system) to produce updated diagrams.


Below is the updated, fully automated prompt that leverages GitHub repository variables. The one-step script deploys the CloudFormation stack, retrieves the IAM Role ARN, and automatically sets the GitHub repository variable (`AWS_ROLE_TO_ASSUME`) via the GitHub API.

---

## 14. Fully Automated AWS OIDC Authentication for GitHub Actions

This guide provides a one-step solution for configuring OpenID Connect (OIDC) authentication between GitHub Actions and AWS. With a single command, the solution deploys the necessary CloudFormation stack, retrieves the IAM Role ARN, and automatically sets the GitHub repository variable—all while eliminating the need to store long-lived AWS credentials in GitHub Secrets.

---

## Why Use OIDC?

- **Enhanced Security:** No long-term credentials are stored in GitHub.
- **Temporary Credentials:** Uses short-lived tokens to reduce risk.
- **Fine-Grained Access:** Precisely control permissions.
- **Auditability:** Monitor usage via AWS CloudTrail.

---

## Fully Automated Setup

An all-in-one script and CloudFormation template work together to automate the entire setup process. This solution will:

- **Deploy/Update the CloudFormation Stack:** Automatically create an IAM OIDC Identity Provider for GitHub Actions, an IAM Role with a trust policy scoped to your GitHub organization, repository, and branch, and a managed IAM Policy with the minimum required permissions.
- **Wait for Deployment Completion:** Monitor the CloudFormation stack until deployment is finished.
- **Retrieve the IAM Role ARN:** Extract the ARN from the stack outputs.
- **Automatically Set the GitHub Repository Variable:** Use the GitHub API to set `AWS_ROLE_TO_ASSUME` in your repository’s variables.

### Usage

Run the following command with your GitHub Personal Access Token (which must have `repo` and `workflow` scopes) along with any optional parameters. The script handles everything for you.

```bash
# Navigate to your project root
cd /path/to/project

# Make the setup script executable (if needed)
chmod +x scripts/setup-oidc.sh

# Run the fully automated setup with default settings
./scripts/setup-oidc.sh --github-token YOUR_GITHUB_TOKEN

# Or customize the deployment:
./scripts/setup-oidc.sh \
  --region us-east-1 \
  --stack-name my-github-oidc-stack \
  --github-org YourGitHubOrg \
  --repo-name YourRepoName \
  --branch-name main \
  --github-token YOUR_GITHUB_TOKEN
```

**What the Script Does:**
- **Deploys/Updates the CloudFormation Stack:** Creates the necessary IAM OIDC provider, role, and policy.
- **Waits for Completion:** Monitors the stack until the deployment is finished.
- **Retrieves the IAM Role ARN:** Extracts and prints the role ARN.
- **Sets the GitHub Repository Variable:** Automatically configures `AWS_ROLE_TO_ASSUME` in your GitHub repository using the provided GitHub token.

---

## GitHub Actions Workflow Example

After the setup, your GitHub Actions workflow (e.g., `.github/workflows/deploy.yml`) can reference the repository variable. This example shows how to authenticate with AWS using the variable:

```yaml
jobs:
  deploy:
    permissions:
      id-token: write   # Required for OIDC
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: ${{ vars.AWS_ROLE_TO_ASSUME }}
          aws-region: us-east-1
      
      # Additional deployment steps...
```

---

## CloudFormation Template

The accompanying `cloudformation/github-oidc.yaml` template automatically creates:
- **GitHub OIDC Provider:** Establishes the provider for GitHub Actions.
- **IAM Role for GitHub Actions:** Configured with a trust policy tied to your GitHub organization, repository, and branch.
- **Managed IAM Policy:** Provides the minimal permissions necessary for required AWS operations.

*(The full template code is available in your repository for review and customization.)*

---

## References

- [AWS OIDC Documentation](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_roles_providers_create_oidc.html) 
- [GitHub Actions OIDC Documentation](https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect) 

---


