---
id: img-fw8w
status: closed
deps: [img-2k17]
links: []
created: 2026-03-27T21:11:12Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Fix first-party code for Django 4.2 + Python 3.12

1) simpleblog/views.py: replace request.is_ajax() with request.headers.get('X-Requested-With') == 'XMLHttpRequest'. 2) main/utils.py and main/fancy_ml.py: replace Image.ANTIALIAS with Image.LANCZOS. 3) setup.cfg: update mypy python_version to 3.12. 4) If django-simple-blog was removed from deps, ensure simpleblog/ local app still works without it — check INSTALLED_APPS references and remove any import of the pip package.

## Acceptance Criteria

No references to removed APIs remain in project code.

