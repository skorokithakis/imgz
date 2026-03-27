---
id: img-pufn
status: closed
deps: [img-2k17]
links: []
created: 2026-03-27T21:11:06Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Update settings.py for Django 4.2

In imgz/settings.py: 1) Add DEFAULT_AUTO_FIELD = 'django.db.models.AutoField' (preserves existing behavior). 2) Replace STATICFILES_STORAGE with STORAGES dict. 3) Update sentry-sdk initialization if needed (modern sentry-sdk 2.x auto-detects Django, but explicit DjangoIntegration() import should still work — verify the import path). 4) Remove USE_L10N if present (deprecated in 4.0).

## Acceptance Criteria

manage.py check produces no errors related to these settings.

