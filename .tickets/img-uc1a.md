---
id: img-uc1a
status: closed
deps: []
links: []
created: 2026-03-27T20:40:28Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Add CSS for the full-viewport drop overlay

In static/css/style.css, add styles for the drop overlay: fixed position covering the full viewport, high z-index, semi-transparent background, centered text indicating 'Drop to upload'. Include a visible/active state class that the JS toggles. Should look reasonable with the existing site design (use existing CSS custom properties like --color-1, --color-2 if appropriate).

