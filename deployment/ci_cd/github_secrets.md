# GitHub Secrets

This file lists the GitHub Secrets that are relevant for the InsureFlow CI/CD
setup.

For the current phase, the workflow does not require secrets yet because it only
does build validation on the `development` branch.

These secret names are documented now so the next CI/CD phase is easier to set
up.

## What GitHub Secrets Are

GitHub Secrets are private values stored securely inside the repository or
environment settings in GitHub.

They are used in GitHub Actions so sensitive values do not need to be hardcoded
inside workflow files.

Examples of sensitive values:

- Docker Hub username
- Docker Hub access token
- API keys
- SSH private keys
- production-only environment values

## Current Phase

Current workflow scope:

- branch: `development`
- purpose: CI validation only
- Docker Hub push: not enabled yet
- deployment: not enabled yet

Because of that, no secrets are required by the current
`.github/workflows/development-ci.yml` workflow.

## Expected Secrets For Next Phase

If the next phase adds Docker Hub image publishing, these are the most likely
secrets we will need:

- `DOCKERHUB_USERNAME`
  Docker Hub account username

- `DOCKERHUB_TOKEN`
  Docker Hub access token

## Possible Future Build-Time Frontend Variables

If frontend builds later need production-specific values from GitHub Actions,
they may be stored as secrets or variables depending on sensitivity.

Examples:

- `VITE_MAIN_API_BASE_URL`
- `VITE_PROVIDER_API_BASE_URL`
- `VITE_BOT_BASE_URL`

If a value is public and non-sensitive, GitHub Variables may be enough.
If a value is sensitive, GitHub Secrets should be used.

## Not Needed In The Current Phase

These are not needed right now because we are not deploying anywhere yet:

- SSH private key
- EC2 host
- server username
- production server env files

## Important Rule

Never hardcode real secrets inside:

- workflow `.yml` files
- committed `.env` files
- README examples

Use placeholders in documentation and keep real values only in GitHub Secrets.
