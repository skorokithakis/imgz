# AGENTS.md - Coding agent instructions for imgz

This is a Django 2.2 image hosting application. The main app is `main/` with a
custom User model at `main.models.User`.

## Build/lint/test commands

Package manager: **Poetry**

```bash
# Install dependencies
poetry install

# Run all pre-commit hooks (linting, formatting, type checking, migrations check)
pre-commit run --all-files

# Run all tests with coverage
pytest

# Run a single test file
pytest tests/main/test_views.py

# Run a single test function
pytest tests/main/test_views.py::test_set_image_title

# Run tests matching a keyword
pytest -k "test_upload"

# Run tests with verbose output
pytest -v

# Run tests without coverage (faster)
pytest --no-cov

# Check for uncreated migrations
./manage.py makemigrations --check --dry-run
```

## Pre-commit hooks

The project uses these pre-commit hooks (run `pre-commit run --all-files` after changes):

1. **ruff** - Linting with auto-fix
2. **ruff-format** - Code formatting
3. **mypy** - Type checking (strict mode)
4. **migrations-check** - Ensures no uncreated migrations

## Code style

### Formatting and linting

- Use **ruff** for linting and formatting (configured in pyproject.toml)
- Line length is not strictly enforced (E501 ignored)
- Run `pre-commit run --all-files` after each change, twice if needed

### Imports

- All imports at the top of the file, never inside functions
- One import per line for `from` imports
- Order: stdlib, third-party, local (ruff handles this)

```python
# Good
from typing import Any
from typing import Optional

from django.http import JsonResponse
from django.views.generic import View

from .models import Image
from .models import User
```

### Type hints

- All function signatures must be statically typed (parameters and return)
- Use built-in types: `list`, `dict`, `tuple` (not `typing.List`, `typing.Dict`)
- Import from `typing` only for: `Any`, `Optional`, `Tuple`, `Dict` when needed

```python
# Good
def process_image(data: bytes, width: int) -> Optional[bytes]:
    ...

def get_items() -> list[str]:
    ...

# Bad - missing types
def process_image(data, width):
    ...
```

### Naming conventions

- Use full words, not abbreviations: `number` not `num`, `greater_than` not `gt`
- Snake_case for functions and variables
- PascalCase for classes
- Some naming conventions are relaxed (N802, N803, N806 ignored)

### Comments

- Comments explain the **why**, not the **what**
- Remove comments that just describe what the next few lines do
- Comments should be full sentences with proper capitalization and full stops

```python
# Good - explains why
# We need to refresh from DB because the signal handler modifies the object.
image.refresh_from_db()

# Bad - just describes what
# Refresh the image from database.
image.refresh_from_db()
```

### Error handling

- Do NOT write defensive try/catch blocks
- Let exceptions propagate unless there's a specific reason to catch them
- The codebase uses exceptions to signal errors, not return values

```python
# Good - let it fail
user = User.objects.get(id=user_id)

# Bad - defensive
try:
    user = User.objects.get(id=user_id)
except User.DoesNotExist:
    return None  # Don't do this unless explicitly needed
```

### String fields in models

- String fields should NOT be nullable
- Use `blank=True` with an empty string default, not `null=True`
- This avoids confusion where falsy could be either "" or None

```python
# Good
title = models.CharField(max_length=200, blank=True)

# Bad
title = models.CharField(max_length=200, null=True, blank=True)
```

### Django admin

- All model fields must be exposed in the admin
- Use `list_display`, `search_fields`, `list_filter` appropriately
- Register all models with `@admin.register(Model)`

## Testing

### Test structure

- Tests are in `tests/` directory, mirroring the app structure
- Use pytest with `@pytest.mark.django_db` for database access
- Use `@pytest.mark.parametrize` for multiple test cases
- Use plain `assert` statements

### Factories

Use factory_boy factories from `tests/factories.py`:

```python
from tests.factories import UserFactory, ImageFactory

# Basic usage
user = UserFactory()
image = ImageFactory()

# With traits
admin_user = UserFactory(admin=True)
user_no_space = UserFactory(with_no_space=True)
user_expired = UserFactory(with_expired_trial=True)
user_paying = UserFactory(with_active_subscription=True)

# Realistic image data (for resize/processing tests)
image = ImageFactory(realistic=True)

# With specific attributes
image = ImageFactory(user=user, title="My Image")
```

### Test patterns

```python
import pytest
from tests.factories import UserFactory, ImageFactory

@pytest.mark.django_db
def test_user_can_edit_own_image(client):
    image = ImageFactory()
    client.force_login(image.user)

    response = client.post(image.get_absolute_url(), data={"title": "New"})
    assert response.status_code == 302

    image.refresh_from_db()
    assert image.title == "New"

@pytest.mark.django_db
@pytest.mark.parametrize("input,expected", [
    ("", "error message"),
    ("valid", None),
])
def test_validation(client, input, expected):
    ...
```

## Project structure

```
imgz/
├── imgz/           # Django project settings
│   ├── settings.py # Single settings file (uses env vars)
│   └── urls.py     # Root URL config
├── main/           # Primary app
│   ├── models.py   # User, Image models
│   ├── views.py    # Web views
│   ├── api.py      # REST API (class-based views)
│   ├── admin.py    # Admin configuration
│   └── utils.py    # Helper functions
├── simpleblog/     # Blog app
├── templates/      # HTML templates
├── tests/          # Test suite
│   ├── factories.py
│   ├── conftest.py
│   └── main/
└── manage.py
```

## Important notes

- Custom User model: `main.models.User` (AUTH_USER_MODEL = "main.User")
- IDs use shortuuid (e.g., "i" + 7 random chars for images)
- Never run `manage.py runserver` to test - use pytest
- The project uses Stripe for payments, Sentry for error tracking
