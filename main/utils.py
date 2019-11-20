from typing import Any

from .models import Image
from .models import User


def process_upload(request_files: Any, user: User) -> Image:
    """
    Process an uploaded file from request.FILES.
    """
    if "data" not in request_files:
        raise ValueError("You forgot to give us an image to upload.")

    data = request_files["data"].read()
    name = request_files["data"].name
    try:
        image = Image.objects.create(data=data, user=user, name=name)
    except OSError:
        raise ValueError("That file was straight trash, try uploading something else.")
    except ValueError:
        raise
    return image
