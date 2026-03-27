---
id: img-ws5a
status: closed
deps: [img-mtyl]
links: []
created: 2026-03-27T20:40:27Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Generate uv.lock and remove poetry.lock

Run uv lock to generate uv.lock from the converted pyproject.toml. Then delete poetry.lock. Verify the lockfile resolves successfully for Python 3.8.

## Acceptance Criteria

uv.lock exists and is valid. poetry.lock is deleted.

