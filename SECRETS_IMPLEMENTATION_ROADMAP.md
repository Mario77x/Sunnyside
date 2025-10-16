# Secrets Management Implementation Roadmap

## 1. Introduction

This document provides a step-by-step guide for migrating the Sunnyside application's secrets management from `.env` files to Doppler. This roadmap is a practical companion to the [SECRETS_MANAGEMENT_PLAN.md](SECRETS_MANAGEMENT_PLAN.md) and is intended for developers to follow during the migration process.

### 1.1. Prerequisites

Before starting the migration, ensure the following prerequisites are met:

- **Doppler Account:** A Doppler account has been created and is accessible.
- **Project Access:** All team members have been invited to the Doppler project.
- **Familiarity with Doppler:** Team members should have a basic understanding of Doppler's concepts, such as projects, environments, and the Doppler CLI.

### 1.2. Roadmap Overview

The migration is divided into four phases:

- **Phase 1: Setup and Initial Configuration:** Configure the Doppler project and import the existing secrets.
- **Phase 2: Local Development Integration:** Integrate the Doppler CLI into the local development workflow.
- **Phase 3: CI/CD Integration:** Integrate Doppler with the CI/CD pipeline for automated secret injection.
- **Phase 4: Production Deployment and Validation:** Deploy the new secrets management workflow to production and validate its functionality.

---

## 2. Phase 1: Setup and Initial Configuration

This phase focuses on setting up the Doppler project and importing the existing secrets from the `.env` file.

### 2.1. Create Doppler Project and Environments

1. **Create a Doppler Project:**
   - Log in to your Doppler account.
   - Create a new project named `sunnyside`.

2. **Configure Environments:**
   - Within the `sunnyside` project, create three environments:
     - `development`
     - `staging`
     - `production`

### 2.2. Import Secrets from `.env`

1. **Retrieve Secrets:**
   - Open the existing `.env` file and identify all the secrets that need to be migrated.

2. **Import into Doppler:**
   - In the Doppler dashboard, navigate to the `development` environment of the `sunnyside` project.
   - Manually add each secret from the `.env` file to the `development` environment.

### 2.3. Invite Team Members

1. **Invite Team:**
   - In the Doppler dashboard, invite all team members to the `sunnyside` project.

2. **Assign Roles:**
   - Assign the appropriate roles to each team member based on the access control policies defined in the architectural plan.

### 2.4. Validation Checklist

- [ ] A Doppler project named `sunnyside` has been created.
- [ ] Three environments (`development`, `staging`, `production`) have been configured.
- [ ] All secrets from the `.env` file have been imported into the `development` environment.
- [ ] All team members have been invited to the project and assigned the correct roles.

---

## 3. Phase 2: Local Development Integration

This phase focuses on integrating the Doppler CLI into the local development workflow.

### 3.1. Install Doppler CLI

1. **Installation:**
   - Follow the official Doppler documentation to install the Doppler CLI on your local machine.

2. **Authentication:**
   - Authenticate the Doppler CLI with your Doppler account by running the following command:
     ```bash
     doppler login
     ```

### 3.2. Update Development Workflow

1. **Run Application with Doppler:**
   - To run the application with the secrets from the `development` environment, use the `doppler run` command:
     ```bash
     doppler run -- python -m uvicorn backend.main:app --reload --port 8000
     ```

2. **Update `package.json` (Frontend):**
   - For the frontend, update the `dev` script in `frontend/package.json` to use `doppler run`:
     ```json
     "scripts": {
       "dev": "doppler run -- vite"
     }
     ```

### 3.3. Remove `.env` File

1. **Backup and Remove:**
   - Create a backup of the `.env` file and then remove it from the project's root directory.

2. **Update `.gitignore`:**
   - Ensure that `.env` is listed in the `.gitignore` file to prevent it from being accidentally committed.

### 3.4. Validation Checklist

- [ ] The Doppler CLI is installed and authenticated on all developer machines.
- [ ] The application can be successfully started using the `doppler run` command.
- [ ] The `.env` file has been removed from the project.
- [ ] The `.gitignore` file includes `.env`.

---

## 4. Phase 3: CI/CD Integration

This phase focuses on integrating Doppler with the CI/CD pipeline to automate the injection of secrets.

### 4.1. Configure CI/CD Pipeline

1. **Create a Doppler Service Token:**
   - In the Doppler dashboard, create a service token for the CI/CD pipeline with "Viewer" access to the `staging` and `production` environments.

2. **Add Service Token to CI/CD:**
   - Add the Doppler service token as a secret in your CI/CD provider's settings.

### 4.2. Update Deployment Scripts

1. **Fetch Secrets:**
   - In your deployment scripts, use the Doppler CLI to fetch the secrets for the target environment:
     ```bash
     doppler secrets download --no-file --format=json > secrets.json
     ```

2. **Inject Secrets:**
   - Update your deployment scripts to read the secrets from `secrets.json` and inject them as environment variables into the application.

### 4.3. Validation Checklist

- [ ] A Doppler service token has been created for the CI/CD pipeline.
- [ ] The service token has been added as a secret to the CI/CD provider.
- [ ] The deployment scripts have been updated to fetch and inject secrets from Doppler.
- [ ] The CI/CD pipeline can successfully deploy the application to the staging environment with the correct secrets.

---

## 5. Phase 4: Production Deployment and Validation

This phase focuses on deploying the new secrets management workflow to the production environment and validating its functionality.

### 5.1. Deploy to Production

1. **Run Production Deployment:**
   - Trigger the CI/CD pipeline to deploy the application to the production environment.

2. **Monitor Deployment:**
   - Monitor the deployment process to ensure that it completes successfully.

### 5.2. Validate Production Environment

1. **Verify Application Functionality:**
   - Perform a full suite of tests on the production environment to ensure that the application is functioning correctly with the new secrets management workflow.

2. **Check Logs:**
   - Check the application logs for any errors related to secrets management.

### 5.3. Validation Checklist

- [ ] The application has been successfully deployed to the production environment.
- [ ] All application functionality is working as expected in the production environment.
- [ ] There are no errors in the application logs related to secrets management.

---

## 6. Rollback Procedures

In the event of a critical issue, the following rollback procedures can be executed for each phase.

### 6.1. Phase 2 Rollback

- **Restore `.env` File:** Restore the `.env` file from the backup.
- **Revert `package.json`:** Revert the changes to the `dev` script in `frontend/package.json`.
- **Update Workflow:** Instruct developers to stop using `doppler run` and revert to using the `.env` file.

### 6.2. Phase 3 Rollback

- **Revert Deployment Scripts:** Revert the changes to the deployment scripts to remove the Doppler integration.
- **Restore Manual Secret Configuration:** Manually configure the secrets in the CI/CD provider's settings.

### 6.3. Phase 4 Rollback

- **Redeploy Previous Version:** Redeploy the previous version of the application that does not use the Doppler integration.
- **Investigate and Resolve:** Investigate the root cause of the issue before attempting the migration again.