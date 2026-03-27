---
id: img-m8vp
status: closed
deps: []
links: []
created: 2026-03-27T19:40:45Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Remove outdated custom nginx sigil template

Delete misc/dokku/nginx.conf.sigil. The only customization it contained (client_max_body_size 42M) will be set via dokku nginx:set instead. The custom template was based on an old Dokku version and references deprecated variables (DOKKU_APP_LISTENERS, NGINX_LOG_ROOT, etc) that cause it to fail silently on newer Dokku, falling back to the default 1M body size limit.

## Acceptance Criteria

The file misc/dokku/nginx.conf.sigil is deleted. Pre-commit hooks pass.

