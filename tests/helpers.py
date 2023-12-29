import base64
from io import BytesIO
from pathlib import Path

from PIL import Image as PILImage


# A valid PNG image, the smallest possible PNG.
# From https://garethrees.org/2007/11/14/pngcrush/.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQAAAAA3bvkkAAAACklEQVR4nGNgAAAAAgABSK+kcQAAAABJRU5ErkJggg=="
)


def pil_from_response(response) -> PILImage:
    """
    Returns a PIL Image from the content of the given Django response
    `response`.
    """
    return PILImage.open(BytesIO(response.content))


def data_file_path(filename) -> Path:
    """
    Returns a Path object for the given `filename` within the test data
    directory.
    """
    return Path(__file__).parent / "data" / filename
