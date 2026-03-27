---
id: img-t4yl
status: closed
deps: [img-2k17]
links: []
created: 2026-03-27T21:11:16Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Update Dockerfile to Python 3.12

Change base image from python:3.8-slim-bullseye to python:3.12-slim-bookworm. Everything else should stay the same (uv install, collectstatic, etc).

## Acceptance Criteria

docker build succeeds.

