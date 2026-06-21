# Branch Testing Notes

This file explains how the current GitHub Actions workflows behave with the
project's branch strategy.

## Branch Strategy

Current repository flow:

```text
main -> development -> feature/*
```

Feature work is done in a feature branch first, then merged into
`development`, and later `development` is merged into `main`.

## Current Workflow Behavior

### `development-ci.yml`

Trigger:

```text
push -> development
workflow_dispatch
```

This means:

- automatic CI runs when code is pushed to `development`
- manual CI runs can still be started from GitHub Actions

### `dockerhub-publish.yml`

Trigger:

```text
workflow_dispatch
```

Restriction:

- publish job is allowed only from `development` or `main`

This means:

- feature branches are used for building and preparing workflow files
- actual manual image publishing should be run only from `development` or
  `main`

## Safe Testing Sequence

Recommended order:

1. create or update workflow files in a feature branch
2. merge the feature branch into `development`
3. verify `development-ci.yml` on `development`
4. configure Docker Hub secrets in GitHub
5. manually run `dockerhub-publish.yml` from `development`
6. verify Docker Hub image output
7. only then consider merging `development` into `main`

## Important Note

If a workflow is present only in a feature branch, that does not automatically
mean `development` has run it yet.

The workflow becomes part of normal `development` automation only after the
feature branch is merged into `development`.
