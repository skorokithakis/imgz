import datetime
import imghdr
import os
import subprocess
import tempfile
from io import BytesIO
from typing import Any
from typing import Dict

import shortuuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Sum
from django.urls import reverse
from PIL import Image as PILImage
from PIL import ImageOps

KB = 1024
MB = 1024 * KB
GB = 1024 * MB


def generate_moderate_id() -> str:
    return shortuuid.ShortUUID().random(12)


def generate_image_id() -> str:
    return "i" + shortuuid.ShortUUID().random(7)


class User(AbstractUser):
    upgraded_until = models.DateField(default=datetime.date(1900, 1, 1))
    storage_space = models.PositiveIntegerField(default=500 * MB)
    api_key = models.CharField(
        max_length=200, default=generate_moderate_id, db_index=True
    )

    @property
    def can_upload(self) -> bool:
        """
        Return whether the user can upload new files or not.

        The user might not be able to upload new files if they have not paid or if
        they've reached their storage quota.
        """
        return self.is_paying and self.total_space_left > 0

    @property
    def is_paying(self) -> bool:
        """
        Return whether this is a paying user.
        """
        return self.upgraded_until >= datetime.date.today()

    @property
    def total_space_taken(self) -> int:
        """
        Return the total amount of space this users' images take.
        """
        total_size = self.images.aggregate(Sum("size"))["size__sum"]
        return total_size if total_size else 0

    @property
    def total_space_left(self) -> int:
        """
        Return the total space the user has left on their account.
        """
        return self.storage_space - self.total_space_taken


class ImageManager(models.Manager):  # type: ignore
    def create(self, *args, **kwargs) -> "Image":
        if len(kwargs.get("name", "")) > self.model._meta.get_field("name").max_length:
            raise ValueError(
                "This image's name is huge. Try uploading the abridged version."
            )

        if len(kwargs.get("data", "")) > settings.MAX_IMAGE_SIZE:
            raise ValueError(
                "Whoa there, Ansel Adams, try resizing your photos to a smaller size."
            )

        return super().create(*args, **kwargs)


class Image(models.Model):
    id = models.CharField(
        max_length=30, primary_key=True, default=generate_image_id, editable=False
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="images")
    name = models.CharField(max_length=200, blank=True)
    data = models.BinaryField()
    format = models.CharField(max_length=100, blank=True)
    size = models.IntegerField(default=0)
    uploaded = models.DateTimeField(auto_now_add=True)

    thumbnail_512 = models.BinaryField(default=b"")

    objects = ImageManager()

    @property
    def extension(self) -> str:
        """
        Return the image's extension, based on its format.
        """
        extension = self.format
        if extension == "jpeg":
            extension = "jpg"
        return extension

    @property
    def filename(self) -> str:
        """
        Return the image's filename (i.e. image ID + extension).
        """
        return f"{self.id}.{self.extension}"

    def get_absolute_url(self) -> str:
        """
        Return the URL to the image page.
        """
        return reverse("main:image-page", kwargs={"image_id": self.id})

    def get_image_url(self) -> str:
        """
        Return the URL to the image itself.
        """
        return reverse(
            "main:image-show", kwargs={"image_id": self.id, "extension": self.extension}
        )

    def get_thumbnail_url(self, size: int = 512) -> str:
        return reverse(
            "main:image-show-thumb",
            kwargs={"image_id": self.id, "size": size, "extension": self.extension},
        )

    def generate_thumbnails(self) -> None:
        """
        Generate and store this image's thumbnails.

        It does not save the Image object.
        """
        with BytesIO(self.data) as inp:
            img = PILImage.open(inp)
            thumb = ImageOps.fit(img, (512, 512), method=PILImage.ANTIALIAS)

        with BytesIO() as outp:
            thumb.save(outp, format=img.format)
            outp.seek(0)
            self.thumbnail_512 = outp.read()

    def strip_exif(self) -> None:
        """
        Strip EXIF data from the image and auto-orient it.

        Does not save the Image object.
        """
        fd, filename = tempfile.mkstemp()
        with open(filename, "wb") as f:
            f.write(self.data)

        subprocess.run(["mogrify", "-auto-orient", "-strip", f.name])
        with open(filename, "rb") as f:
            self.data = f.read()

        os.close(fd)
        os.remove(filename)

    def save(self, *args, **kwargs):
        self.strip_exif()

        if not self.format:
            format = imghdr.what(None, h=self.data)
            self.format = format if format else ""

        if not self.size:
            self.size = len(self.data)

        if not bytes(self.thumbnail_512):
            self.generate_thumbnails()

        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        site = Site.objects.get_current()
        return {
            "id": self.id,
            "urls": {
                "page": f"https://{site.domain}{self.get_absolute_url()}",
                "image": f"https://{site.domain}{self.get_image_url()}",
                "thumbnails": {
                    512: f"https://{site.domain}{self.get_thumbnail_url(512)}"
                },
            },
            "size": self.size,
            "name": self.name,
            "format": self.format,
            "uploaded": self.uploaded.strftime("%Y-%m-%d %H:%M:S"),
        }

    def __str__(self) -> str:
        return self.id
