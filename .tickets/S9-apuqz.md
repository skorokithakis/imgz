---
id: S9-apuqz
status: open
deps: []
links: []
created: 2026-07-30T18:23:52Z
type: bug
priority: 1
assignee: Stavros Korokithakis
---
# Fix stale Pillow in uv.lock and pin the dev Python version

Ready for implementation.

Problem: uv.lock holds pillow 8.4.0 (October 2021). pyproject.toml only says "pillow>=8.3.1", so there is no pin in pyproject — uv simply kept the old locked version because it still satisfies the range. Pillow 8.4.0 has no cp312+ wheels and its sdist no longer builds with modern setuptools (fails with KeyError: "__version__"). Result: "uv sync" fails, so the test suite cannot run at all, and the Docker build (uv sync --frozen) is at risk for the same reason. The stale entry survived the Poetry-to-uv migration in commit fd48995.

Second problem: there is no .python-version file, so local uv picks whatever is newest on the machine (3.14 here), while the Dockerfile uses python:3.12-slim-bookworm.

Changes:
1. Add a .python-version file containing 3.12, to match the Dockerfile.
2. Raise the floor in pyproject.toml to "pillow>=11".
3. Run "uv lock --upgrade-package pillow". Only the pillow entry in uv.lock should change — verify this with git diff and do not let other packages move.
4. Run "uv sync" and then the full "pytest" suite, and make it pass.

Pillow 8 to 11 API notes: the code uses PILImage.LANCZOS (main/utils.py, main/fancy_ml.py), ImageOps.fit, ImageOps.grayscale, thumbnail, and PILImage.new/putdata. None of these were removed in Pillow 10 or 11 (the removal that usually bites is Image.ANTIALIAS, which is not used here). If something did change, fix the call sites rather than holding Pillow back.

Non-goals: do not upgrade numpy, opencv-python or any other dependency; do not change requires-python in pyproject.toml; do not touch CI workflows; do not change application behaviour.

## Acceptance Criteria

"uv sync" succeeds and the full "pytest" suite passes. The uv.lock diff touches only the pillow package entry. No application code changes, unless a genuine Pillow API break requires one.

