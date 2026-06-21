# CI/CD

This folder contains the CI/CD planning material for the InsureFlow project.

It is inspired by the reference structure from:

```text
https://github.com/eigi-ai/FDE/tree/main/deployment/ci_cd
```

but is adapted for this repository's multi-service Docker setup.

## Purpose

Docker is already prepared for the project. The next step is to define a clean,
project-specific CI/CD flow that can:

- validate code changes
- build Docker images
- push images to Docker Hub
- deploy the updated images to the target server

## Current Project Scope

This project currently has six Dockerized services:

1. `main_backend`
2. `provider_backend`
3. `customer_app_frontend`
4. `provider_app_frontend`
5. `mcp`
6. `bot`

These services are mapped to Docker Hub image names through
`docker-compose.yml`.

## Planned CI/CD Direction

The expected high-level flow is:

```text
developer pushes code to GitHub
   |
   v
GitHub Actions starts CI
   |
   v
service checks/build validation runs
   |
   v
Docker images are built
   |
   v
images are pushed to Docker Hub
   |
   v
deployment server pulls updated images
   |
   v
Docker Compose restarts the application
```

## What Will Live In This Folder

- `README.md`
  Overview of CI/CD structure for this repo.

- `implementation_plan.md`
  Step-by-step plan for introducing CI/CD safely.

- `github_secrets.md`
  Project-specific guide for which GitHub Secrets are needed now and later.

## Important Notes

- This folder is documentation and planning only for now.
- Real GitHub Actions workflow files must eventually live in:

```text
.github/workflows/
```

- The workflow design must be adapted for a six-service application, not a
  single frontend service.

## Next Expected Topics

The next CI/CD implementation work will likely define:

- branch trigger strategy
- CI checks per service
- Docker Hub push flow for all six images
- required GitHub secrets
- target deployment environment
- deployment and rollback approach
