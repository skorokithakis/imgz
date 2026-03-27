---
id: img-isll
status: closed
deps: []
links: []
created: 2026-03-27T19:50:05Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Create GitHub Actions workflows and delete GitLab CI

Create .github/workflows/pre-commit.yml and .github/workflows/deploy.yml, delete .gitlab-ci.yml. Pre-commit workflow: runs on push to master and PRs, uses actions/checkout@v3, actions/setup-python@v3, pre-commit/action@v3.0.1 with extra_args '--all-files --hook-stage=manual'. Deploy workflow: triggers after pre-commit workflow succeeds on master, checks out with fetch-depth 0, sets up SSH with DOKKU_SSH_KEY secret, configures SSH for projects.stavros.io port 16022, pushes to dokku@projects.stavros.io:imgz. Use deadmansswitch-v3 workflows as reference (at /home/stavros/Code/Django/deadmansswitch-v3/.github/workflows/). Do NOT create a claude.yml workflow.

