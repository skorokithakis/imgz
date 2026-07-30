---
id: S9-npkkj
status: closed
deps: []
links: []
created: 2026-07-30T22:21:28Z
type: chore
priority: 2
assignee: Stavros Korokithakis
external-ref: STA-93
---
# Unify border radius across the site

Ready for implementation.

Objective: static/css/style.css uses five different corner radii (3px, 5px, 8px, 10px, plus Bootstrap's 4px default on the hamburger). Unify them on 8px behind a single CSS variable.

Scope: static/css/style.css only.

Changes:
1. Add a --radius: 8px custom property to the existing :root block at the top of the file, alongside the colour variables.
2. Replace every pixel border-radius value in the file with var(--radius). Preserve which corners are rounded: a rule like '8px 8px 0 0' becomes 'var(--radius) var(--radius) 0 0'. Two-value shorthands like '8px 8px' can collapse to a single var(--radius).
3. Leave all 50% radii alone. Those are deliberate circles for avatars and round icons.
4. Drop the -webkit- and -moz- border-radius prefixes wherever you touch a rule. Every browser that supports CSS custom properties supports unprefixed border-radius, so the prefixed copies would silently stop matching the unprefixed one and are dead weight.
5. Override Bootstrap's default radius for the components actually rendered in our templates: the .navbar-toggler (currently 4px from bootstrap.min.css, visibly mismatched next to the Upload button) and the form inputs. Put the overrides in style.css.

Non-goals: do not edit bootstrap.min.css or all.min.css, they are vendored. Do not change any other property while sweeping (no padding, colour or border tweaks). Do not delete rules that look like dead theme code; only change their radius.

## Acceptance Criteria

No pixel border-radius literal remains in static/css/style.css; all are var(--radius). 50% radii are untouched. The hamburger toggler and the Upload button have visibly identical corners. Partial-corner rules keep the same corners rounded as before.

