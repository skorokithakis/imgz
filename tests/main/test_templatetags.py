import pytest

from main.templatetags.human_size import human_size
from main.templatetags.human_size import size


@pytest.mark.parametrize(
    "num, display",
    [
        (0, "0 bytes"),
        ("", "0 bytes"),
        (100, "100 bytes"),
        (1_992_294, "1.9 MB"),
        (10_048_577, "9.58 MB"),
        (10_245_161, "9.77 MB"),
        (10_048_577_000, "9.36 GB"),
        (1024**3, "1 GB"),
    ],
)
@pytest.mark.parametrize("func", [human_size, size])
def test_size_tag(func, num, display):
    assert func(num) == display
