# CI/CD Implementation Plan

This file tracks the CI/CD planning work for the InsureFlow project.

The structure is inspired by the Eigi reference material, but the plan here is
specific to this repository's Docker and deployment setup.

## Goal

Create a clear and maintainable CI/CD flow for the six-service InsureFlow
application.

The CI/CD design should support:

- code validation before deployment
- Docker image build automation
- Docker Hub image publishing
- deployment using pulled images instead of source-code builds on the server

## Confirmed Decisions

- [x] Branch strategy confirmed
  - Repository flow is `main -> development -> feature/*`
  - Feature work is done in task-specific branches
  - Feature branches merge into `development`
  - `development` later merges into `main`

- [x] Current CI target confirmed
  - CI will run on `development`

- [x] Current deployment scope confirmed
  - No server deployment will be implemented in this phase
  - This phase is focused on GitHub Actions only

- [x] Workflow count confirmed
  - Start with one workflow first

- [x] Secrets handling direction confirmed
  - Sensitive values must be stored in GitHub Secrets
  - Secrets must not be hardcoded in workflow files

- [x] EC2 decision confirmed
  - EC2 deployment is out of scope for the current phase

## Current Phase Objective

The immediate objective is not full CI/CD deployment.

The immediate objective is:

```text
create a GitHub Actions-based CI workflow
for the development branch
with safe secret handling
and with room to extend later for Docker Hub push and deployment
```

## Current Docker Baseline

- [x] Dockerfiles exist for all six services
- [x] `docker-compose.yml` builds successfully
- [x] Docker Hub image names are defined in Compose
- [x] Example environment files exist for Docker-related setup
- [x] Local Docker validation completed before CI/CD planning

## Planning Scope

The CI/CD design should cover:

1. `main_backend`
2. `provider_backend`
3. `customer_app_frontend`
4. `provider_app_frontend`
5. `mcp`
6. `bot`

## Phase 1: CI/CD Design

- [x] Confirm target deployment environment
  - No deployment target is needed in the current phase
  - Deployment design is intentionally deferred

- [x] Confirm branch strategy
  - CI will run on `development`
  - `main` remains the final stable branch in the repo flow

- [x] Confirm deployment scope
  - No live deployment in this phase
  - No EC2 rollout in this phase

- [ ] Confirm Docker Hub publishing strategy for the next phase
  - Use `latest`
  - Use versioned tags
  - Or use both

- [ ] Confirm rollback strategy for the future deployment phase
  - Prefer versioned image tags for rollback

## Phase 2: CI Design

- [x] Define repository workflow structure
  - GitHub Actions files will live in `.github/workflows/`
  - Start with one workflow for the `development` branch

- [x] Define validation steps for frontend services
  - dependency install
  - build verification

- [x] Define validation steps for backend services
  - dependency install
  - Docker image build verification in the first CI phase

- [x] Decide whether CI should build all six Docker images on every `development` run
  - Start with all six image builds
  - Revisit path-based filtering later if needed

## Phase 3: CD Design

- [ ] Define Docker Hub login and push process for a later phase

- [ ] Define server deployment flow later if deployment is introduced
  - pull updated images
  - restart services with Docker Compose

- [ ] Define required deployment files later if deployment is introduced
  - production Compose file
  - env files
  - deployment directory layout

- [ ] Define post-deploy verification later if deployment is introduced
  - health endpoints
  - frontend availability

## Phase 4: Secrets And Configuration

- [x] Define initial GitHub Secrets guidance
  - Documented current and next-phase secret expectations

- [ ] Define required GitHub Secrets for Docker Hub push phase
  - Docker Hub username
  - Docker Hub token
  - any build-time frontend variables
  - add server-related secrets only when deployment is introduced

- [ ] Separate build-time frontend variables from runtime backend variables

- [ ] Confirm how CI will consume required variables without exposing secrets

## Phase 5: Implementation

- [x] Create initial `.github/workflows/` file
  - Added first `development` branch CI workflow
  - Scope is validation and Docker builds only

- [ ] Add project-specific deployment workflow later if deployment is introduced

- [ ] Add production deployment documentation

- [ ] Run first CI validation

- [ ] Run first Docker Hub push validation

- [ ] Run first deployment validation

## Notes

- The reference material is useful for workflow shape, secrets, Docker Hub
  login, and EC2 deployment patterns.
- That reference is single-service oriented.
- This project needs a multi-service CI/CD design, so the implementation must
  be adapted carefully rather than copied directly.
- The current implementation phase is CI-first, not deployment-first.
