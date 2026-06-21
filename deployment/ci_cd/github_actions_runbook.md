# GitHub Actions Runbook

This file explains the practical GitHub-side setup for the current InsureFlow
CI/CD workflows.

## Current Workflows

The repository currently has:

- `development-ci.yml`
  Runs CI validation on pushes to `development`

- `dockerhub-publish.yml`
  Runs manually and publishes Docker images to Docker Hub

## What To Configure In GitHub

For the current CI-only workflow:

- no secrets are required

For the manual Docker Hub publish workflow:

- add `DOCKERHUB_USERNAME`
- add `DOCKERHUB_TOKEN`

## Where To Add Secrets

In the GitHub repository:

```text
Settings -> Secrets and variables -> Actions
```

Add these as repository secrets:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

## How To Run The Manual Docker Hub Workflow

1. Open the GitHub repository
2. Go to the `Actions` tab
3. Select `Docker Hub Publish`
4. Click `Run workflow`
5. Choose branch:
   - `development` or `main`
6. Optionally enter `image_tag`
   - leave empty to use the commit SHA
7. Start the workflow

## Why The Workflow Is Restricted

The publish job is intentionally limited to:

- `development`
- `main`

This reduces accidental image publishing from temporary feature branches.

## Recommended First Use

For the first real run:

1. confirm `DOCKERHUB_USERNAME` is correct
2. confirm `DOCKERHUB_TOKEN` is valid
3. run the workflow from `development`
4. verify all 6 images appear in Docker Hub

## Current Limitation

This runbook is for CI and Docker Hub publishing only.

It does not include:

- server deployment
- EC2 rollout
- production restart steps
