from io import BytesIO

import pytest

from tests.helpers import PNG


@pytest.fixture
def png_io():
    return BytesIO(PNG)
