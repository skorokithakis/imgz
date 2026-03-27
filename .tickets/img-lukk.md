---
id: img-lukk
status: closed
deps: [img-pufn, img-fw8w, img-t4yl]
links: []
created: 2026-03-27T21:11:20Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Verify: pre-commit, tests, and Docker build pass after Django 4.2 upgrade

Run pre-commit run --all-files (twice if needed), pytest --no-cov, and docker build -t imgz . Fix any issues found.

## Acceptance Criteria

All three pass.

