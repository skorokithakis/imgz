---
id: img-2k17
status: closed
deps: []
links: []
created: 2026-03-27T21:11:00Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Bump all dependency pins for Django 4.2 + Python 3.12

Update pyproject.toml: django>=4.2,<4.3. requires-python>=3.12. Relax/bump these pins: django-tokenauth (remove <0.5 cap), djangoql (remove <0.14 cap), sentry-sdk (bump to >=2.0), django-ipware (remove <3 cap), django-stubs (bump to >=5.0), psycopg2-binary (change to >=2.9, remove exact pin), werkzeug (remove <3 pin), pillow (remove <9 cap), numpy (remove <2 cap), django-loginas (remove <0.4 cap). Remove django-simple-blog from dependencies entirely (local fork in simpleblog/ will be used instead). Run uv lock && uv sync --python 3.12 after. Fix any resolution issues.

## Acceptance Criteria

uv sync --python 3.12 succeeds. No poetry-era version caps remain except where genuinely needed.

