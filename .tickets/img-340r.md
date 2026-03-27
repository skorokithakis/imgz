---
id: img-340r
status: open
deps: []
links: []
created: 2026-03-27T20:40:11Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Add JSON response to image_upload view for AJAX requests

Modify the image_upload view in main/views.py so that when the request includes Accept: application/json, it returns a JSON response with the image's page URL instead of issuing a redirect. The JSON shape should be {"url": "<absolute URL of image page>"}. On error (e.g. no file, validation failure), return a JSON error with an appropriate HTTP status. The existing redirect behavior for normal form submissions must be unchanged. Reuse process_upload() as-is.

## Acceptance Criteria

Normal form POST still redirects. POST with Accept: application/json returns {"url": ...} on success and {"error": ...} on failure.

