from typing import Any
from typing import List

import requests
from django.conf import settings
from django.http import JsonResponse

from .models import Image
from .models import User


class UploadError(Exception):
    """
    A generic upload error exception class.
    """

    pass


def process_upload(request_files: Any, user: User) -> Image:
    """
    Process an uploaded file from request.FILES.
    """
    if not user.is_paying:
        raise UploadError("You cannot upload files, you need to pay. PAY!")

    if not user.has_space_left:
        raise UploadError("You've used up all your space. Buy more!")

    if "data" not in request_files:
        raise UploadError("You forgot to give us an image to upload.")

    data = request_files["data"].read()
    name = request_files["data"].name
    try:
        image = Image.objects.create(data=data, user=user, name=name)
    except OSError:
        raise UploadError("That file was straight trash, try uploading something else.")
    except ValueError as e:
        raise UploadError(str(e))
    return image


def construct_error_response(
    error_code: int, error_message: str, status_code: int = 422
) -> JsonResponse:
    """
    Construct a JsonResponse error message.

    This is just a boilerplate-saving class.
    """
    response = JsonResponse({"error_code": error_code, "error_message": error_message})
    response.status_code = status_code
    return response


def purge_cloudflare_cache_urls(urls: List[str]) -> None:
    if not settings.CLOUDFLARE_ZONE_ID:
        return

    r = requests.post(
        f"https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_ZONE_ID}/purge_cache",
        headers={"Authorization": f"Bearer {settings.CLOUDFLARE_CACHE_TOKEN}"},
        json={"files": urls},
    )
    assert r.status_code == 200
