---
id: S9-dmnps
status: open
deps: []
links: []
created: 2026-07-30T18:46:33Z
type: chore
priority: 1
assignee: Stavros Korokithakis
---
# Run the test suite in CI

Ready for implementation.

Problem: nothing in CI runs the tests. .github/workflows/pre-commit.yml runs pre-commit with --hook-stage=manual, which skips the migrations-check hook (it declares stages: [pre-commit]). That hook is the only one that runs "uv run", so no CI job ever installs the dependencies either. A dependency broken since the Python 3.12 migration went unnoticed for months because of this.

Changes:
1. Rename .github/workflows/pre-commit.yml to .github/workflows/ci.yml and change the workflow "name" to CI. Keep the existing pre-commit job as it is.
2. Add a second job to the same workflow that installs dependencies and runs the tests: checkout, astral-sh/setup-uv, "uv sync", "uv run pytest", and "uv run ./manage.py makemigrations --check --dry-run". The migrations check belongs here because this is the only job with dependencies installed.
3. Update .github/workflows/deploy.yml: its workflow_run trigger matches on the workflow NAME, so "workflows: [\"pre-commit\"]" must become "workflows: [\"CI\"]". Get this right — if the name does not match, deploys stop silently.

Notes:
- Both jobs must be in the same workflow, so that a workflow_run conclusion of success means both passed and deploys stay gated on the tests.
- No services are needed. imgz/settings.py falls back to sqlite when neither IN_DOCKER nor DATABASE_URL is set.
- uv reads .python-version (3.12) and will fetch that interpreter, so do not hardcode a Python version.
- Known risk: opencv-python (not the headless build) links against libGL, and "import cv2" can fail on a GitHub runner with "libGL.so.1: cannot open shared object file". If that happens, add an apt-get install of libgl1 to the test job. Do NOT switch the dependency to opencv-python-headless as part of this ticket.

Non-goals: do not change the pre-commit hook configuration, do not add coverage reporting or upload artifacts, do not add a matrix of Python versions, do not touch application code.

## Acceptance Criteria

A single CI workflow named CI contains both the pre-commit job and a test job that runs pytest and the makemigrations check. deploy.yml triggers on the renamed workflow. Verified by a real run on GitHub after the push: both jobs pass and the deploy workflow still triggers.

