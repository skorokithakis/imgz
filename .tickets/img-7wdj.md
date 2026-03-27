---
id: img-7wdj
status: open
deps: [img-ds8i]
links: []
created: 2026-03-27T20:40:35Z
type: task
priority: 2
assignee: Stavros Korokithakis
---
# Remove upload-page-specific drag-and-drop JS from upload.html

Remove the drag-and-drop JavaScript from templates/upload.html (the script block that handles dragenter/dragover/dragleave/drop on the #drag-drop div). The global drop zone in base.html now handles this. Keep the upload form itself intact — the file input and manual 'choose file' flow should still work. The styled .drag-drop div can remain as a visual hint but no longer needs its own JS event handlers.

## Design

The upload page form still works for manual file selection via the file input. The global handler in base.html intercepts drops on any page including this one.

