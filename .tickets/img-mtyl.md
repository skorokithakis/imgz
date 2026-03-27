---
id: img-mtyl
status: closed
deps: []
links: []
created: 2026-03-27T20:40:24Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Convert pyproject.toml from Poetry to PEP 621 / uv format

Convert the pyproject.toml from Poetry format to PEP 621 standard format with uv as the build backend. Move [tool.poetry.dependencies] to [project] dependencies. Move [tool.poetry.dev-dependencies] to [dependency-groups] dev group. Update [build-system] to use hatchling or remove it (uv doesn't need one for non-publishable projects). Keep all existing dependency version bounds equivalent. Keep the [tool.ruff] section unchanged. Set requires-python to >=3.8.

## Acceptance Criteria

pyproject.toml has no [tool.poetry] sections. Has [project] with name/version/dependencies and [dependency-groups] for dev deps. All original deps preserved with equivalent bounds.

