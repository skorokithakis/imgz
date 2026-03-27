---
id: img-kk5r
status: closed
deps: [img-d20a, img-y0t3]
links: []
created: 2026-03-27T20:40:50Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Verify: pre-commit, tests, and Docker build all pass

Run pre-commit run --all-files (twice if needed), pytest, and docker build . to confirm nothing is broken. Fix any issues found.

## Acceptance Criteria

All three commands succeed.

