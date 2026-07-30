---
id: S9-fstnq
status: closed
deps: []
links: []
created: 2026-07-30T21:42:18Z
type: task
priority: 2
assignee: Stavros Korokithakis
external-ref: STA-93
---
# Make the Upload nav button prominent

Ready for implementation.

Objective: the Upload link in the top nav has the same visual weight as FAQ/Blog/Account. Make it the clear primary action on desktop and mobile.

Files: templates/base.html, static/css/style.css.

Changes:
1. Desktop: style the Upload nav item as a SOLID pill button. Reuse the geometry of the existing .discover-btn rule (static/css/style.css ~line 517): same border-radius, padding and Dosis font, but filled with var(--color-1) and white text, and a darker/inverted hover. Add a fa-cloud-upload-alt icon before the label. Give it its own class (e.g. .upload-btn); do not modify .discover-btn, which the anonymous Log in link uses.
2. Mobile: today the whole nav is hidden behind the hamburger, so Upload is invisible until tapped. Add a second copy of the Upload button in templates/base.html placed OUTSIDE the .navbar-collapse div, immediately before the .navbar-toggler button, so it sits next to the hamburger and is always visible. Show the outside copy only below 992px and the in-menu copy only at 992px and above, via CSS display rules. The breakpoint must match the existing navbar-expand-lg / max-width: 991px media query already in style.css.
3. Both copies must render only for authenticated users (the existing {% if request.user.is_authenticated %} branch covers the in-menu one; the outside copy needs its own guard).
4. The compact nav on image pages (body.image rules, style.css ~line 1778) overrides nav link padding; add the equivalent override for the new button class so it does not blow up the compact header.

Non-goals: no change to the drag-and-drop upload overlay, the upload page itself, the order of the other nav items, or the anonymous-user nav. No new CSS framework or JS.

## Acceptance Criteria

Upload renders as a filled button, visually heavier than every other nav item, on both desktop and mobile. On mobile it is visible without opening the hamburger menu, and appears exactly once (no duplicate visible at any width). The nav on image pages (body.image) stays compact. Anonymous users see no change.

