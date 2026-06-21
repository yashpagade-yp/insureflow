# Docker Hub Publish

This file explains the current Docker Hub publishing approach for the
InsureFlow project.

## Current Direction

The repository now has two separate GitHub Actions concerns:

- `development-ci.yml`
  CI validation on the `development` branch

- `dockerhub-publish.yml`
  manual Docker Hub publishing for the six project images

This separation is intentional.

It keeps regular CI simple and safe, while still preparing the repository for
Docker Hub publishing.

## Why The Publish Workflow Is Manual

Right now the Docker Hub workflow uses:

```text
workflow_dispatch
```

That means it runs only when triggered manually from GitHub Actions.

This is safer for the current phase because:

- it avoids accidental image pushes
- it lets the team confirm secrets first
- it keeps deployment out of scope
- it limits publishing to `development` and `main`

## Images Covered

The manual publish workflow is prepared for these images:

1. `yashh2000/insureflow-main-backend`
2. `yashh2000/insureflow-provider-backend`
3. `yashh2000/insureflow-customer-frontend`
4. `yashh2000/insureflow-provider-frontend`
5. `yashh2000/insureflow-mcp`
6. `yashh2000/insureflow-bot`

## Tags Used

The workflow pushes:

- `latest`
- custom `image_tag` if provided
- otherwise the commit SHA

This gives one stable tag and one exact version tag per run.

## Secrets Required

This workflow requires:

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

These must be configured in GitHub before the workflow is run.

## Frontend Build Arguments

The frontend images currently use Docker build arguments matching the existing
Docker setup:

- `VITE_MAIN_API_BASE_URL=http://localhost:8000`
- `VITE_BOT_BASE_URL=http://localhost:8002`
- `VITE_PROVIDER_API_BASE_URL=http://localhost:8001`

These values are acceptable for the current preparation phase because the goal
is to align the GitHub workflow with the existing Docker setup.

If environment-specific frontend values are needed later, this workflow can be
updated to use GitHub Variables or Secrets.

## Important Limitation

This workflow only publishes images.

It does not:

- deploy containers
- restart servers
- update EC2
- perform live rollout steps

That is intentional for the current phase.
