# CI/CD Validation Checklist

This file defines what should be verified before the current CI/CD phase is
considered complete.

## Current Phase Scope

Current scope includes:

- `development` branch CI workflow
- manual Docker Hub publish workflow
- GitHub Secrets documentation
- GitHub Actions runbook

Current scope does not include:

- EC2 deployment
- server rollout
- production restart automation

## Validation Steps

### 1. Workflow Files Exist

- [ ] `.github/workflows/development-ci.yml` exists
- [ ] `.github/workflows/dockerhub-publish.yml` exists

### 2. CI Workflow Validation

- [ ] `development-ci.yml` is visible in the GitHub Actions tab
- [ ] CI workflow runs successfully on `development`
- [ ] customer frontend build passes
- [ ] provider frontend build passes
- [ ] Python syntax checks pass for:
  - [ ] `main_backend`
  - [ ] `provider_backend`
  - [ ] `mcp`
  - [ ] `bot`
- [ ] Docker image builds pass for all six services

### 3. Docker Hub Publish Validation

- [ ] `dockerhub-publish.yml` is visible in the GitHub Actions tab
- [ ] `DOCKERHUB_USERNAME` is configured in GitHub Secrets
- [ ] `DOCKERHUB_TOKEN` is configured in GitHub Secrets
- [ ] Manual publish workflow runs successfully from `development`
- [ ] All 6 images are pushed successfully
- [ ] `latest` tags appear in Docker Hub
- [ ] commit-specific tags appear in Docker Hub

### 4. Documentation Validation

- [ ] `deployment/ci_cd/README.md` is up to date
- [ ] `implementation_plan.md` reflects the actual workflow state
- [ ] `github_secrets.md` reflects the real required secrets
- [ ] `dockerhub_publish.md` reflects the real publish behavior
- [ ] `github_actions_runbook.md` reflects the real GitHub-side steps

## Recommended Completion Rule

This CI/CD phase should be treated as complete only when:

1. CI validation is passing on `development`
2. Docker Hub publish works successfully
3. the project documentation matches the real workflow behavior

Only after that should the completed work move from `development` to `main`.
