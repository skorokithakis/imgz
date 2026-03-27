---
id: img-ds8i
status: open
deps: [img-340r]
links: []
created: 2026-03-27T20:40:20Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Add global drag-and-drop overlay and upload JS to base.html

In templates/base.html, add: 1) A hidden full-viewport overlay div (only rendered for authenticated users via {% if user.is_authenticated %}). 2) An inline script (also inside the auth guard) that listens for dragenter/dragover/dragleave/drop on document, shows/hides the overlay, and on drop POSTs each dropped file to /upload/ with Accept: application/json header. After all uploads complete, redirect to the URL from the last response. Use vanilla JS, FormData, and fetch(). Handle the dragenter/dragleave counter pattern to avoid flicker from child elements.

## Design

Use a drag enter/leave counter (increment on dragenter, decrement on dragleave, reset on drop) to correctly track when the drag leaves the window vs enters a child element. Upload files sequentially or with Promise.all — parallel is fine since the server handles concurrency. On any upload error, alert the error message and stop.

