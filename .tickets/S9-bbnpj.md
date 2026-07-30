---
id: S9-bbnpj
status: closed
deps: []
links: []
created: 2026-07-30T18:13:47Z
type: feature
priority: 2
assignee: Stavros Korokithakis
---
# Add a 'Take a photo' control to the upload page

Ready for implementation.

Objective: on mobile, let the user open the camera directly from the upload page, in one tap, instead of going through the OS file picker.

Scope: templates/upload.html and static/css/style.css only. No changes to main/views.py or ImageUploadForm.

Approach (agreed): keep the single existing <input type="file" ... required id="id_image"> exactly as it is. Add a "Take a photo" button next to it. On click, the button sets capture="environment" on that input, opens it, then removes the attribute again so a later normal click still shows the full picker. One input means no name/required conflicts and no server-side change.

Visibility: show the button only on touch devices, using a CSS media query on (pointer: coarse). No user-agent sniffing.

Caveats:
- Do NOT add a second file input. A second input named "image" would force us to drop client-side required validation, and the template does not render form.image.errors, so a fileless submit would fail silently.
- Removing the capture attribute after .click() is the fragile part. Browsers open the picker synchronously inside the click call, so removing it straight after is normally fine, but restoring on the change/cancel event is also acceptable if that proves more reliable.
- Style the button consistently with the existing markup (there is a .btn .btn-blue pattern in this template).

Non-goals: no image preview, no crop or rotate, no client-side resize, no multi-shot capture, no changes to the global drag-and-drop uploader in base.html, no changes to the title/expires fields.

## Acceptance Criteria

Tapping "Take a photo" on a mobile browser opens the rear camera directly, and the captured photo uploads through the normal form submit. The existing "click to select" flow still opens the full file picker, including for existing gallery photos. The button is not visible on a desktop pointer device. Change is around 15 lines.

