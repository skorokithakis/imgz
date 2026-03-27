---
id: img-d20a
status: closed
deps: [img-ws5a]
links: []
created: 2026-03-27T20:40:36Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Update Dockerfile to use uv instead of Poetry

Replace poetry install steps in Dockerfile with uv. Install uv (e.g. copy from ghcr.io/astral-sh/uv or pip install), copy pyproject.toml + uv.lock, run uv sync --frozen --no-dev. Remove poetry references. Keep the same python:3.8-slim-bullseye base image and all apt-get packages. Keep the collectstatic step and misc/dokku file copies.

## Acceptance Criteria

Dockerfile has no poetry references. docker build . succeeds.

