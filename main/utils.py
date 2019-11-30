import datetime
from typing import Any
from typing import List
from typing import Optional

import requests
from django.conf import settings
from django.utils.timezone import now

import main


class UploadError(Exception):
    """
    A generic upload error exception class.
    """

    pass


def process_upload(
    request_files: Any,
    user: "main.models.User",
    title: Optional[str] = None,
    expires_in: Optional[int] = None,
) -> "main.models.Image":
    """
    Process an uploaded file from request.FILES.
    """
    if not user.is_upgraded:
        raise UploadError("You cannot upload files, you need to pay. PAY!")

    if not user.has_space_left:
        raise UploadError("You've used up all your space. Buy more!")

    if "image" not in request_files:
        raise UploadError("You forgot to give us an image to upload.")

    data = request_files["image"].read()
    title = title if title else request_files["image"].name

    from .models import Image

    expires = (now() + datetime.timedelta(minutes=expires_in)) if expires_in else None

    try:
        image = Image.objects.create(data=data, user=user, title=title, expires=expires)
    except OSError:
        raise UploadError("That file was straight trash, try uploading something else.")
    except ValueError as e:
        raise UploadError(str(e))
    return image


def purge_cloudflare_cache_urls(urls: List[str]) -> None:
    if not settings.CLOUDFLARE_ZONE_ID:
        return

    r = requests.post(
        f"https://api.cloudflare.com/client/v4/zones/{settings.CLOUDFLARE_ZONE_ID}/purge_cache",
        headers={"Authorization": f"Bearer {settings.CLOUDFLARE_CACHE_TOKEN}"},
        json={"files": urls},
    )
    assert r.status_code == 200
