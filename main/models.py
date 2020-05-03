import datetime
import imghdr
import os
import subprocess
import tempfile
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

import shortuuid
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Sum
from django.db.models.query import QuerySet
from django.urls import reverse
from django.utils import timezone

from .utils import generate_thumbnail
from .utils import purge_cloudflare_cache_urls


def generate_moderate_id() -> str:
    return shortuuid.ShortUUID().random(12)


def generate_image_id() -> str:
    return "i" + shortuuid.ShortUUID().random(7)


class User(AbstractUser):
    upgraded_until = models.DateField(default=datetime.date(1900, 1, 1))
    last_payment = models.DateField(default=datetime.date(1900, 1, 1))
    storage_space = models.BigIntegerField(
        default=0, help_text="The user's base storage space (from their payment plan)."
    )
    bonus_space = models.BigIntegerField(
        default=0,
        help_text="The user's bonus space (persistent, won or given by admins.",
    )
    api_key = models.CharField(
        max_length=200, default=generate_moderate_id, unique=True
    )

    def __str__(self) -> str:
        return self.email

    @property
    def can_upload(self) -> bool:
        """
        Return whether the user can upload new files or not.

        The user might not be able to upload new files if they have not paid or if
        they've reached their storage quota.
        """
        return self.is_upgraded and self.has_space_left

    @property
    def has_ever_paid(self) -> bool:
        """
        Return whether this user has ever paid or if they've only ever been on the trial.
        """
        return self.last_payment != datetime.date(1900, 1, 1)

    @property
    def has_space_left(self) -> bool:
        """
        Return whether the user has space left.
        """
        return self.total_space_left > 0

    @property
    def is_upgraded(self) -> bool:
        """
        Return whether this is a paying user.
        """
        return self.upgraded_until >= datetime.date.today()

    @property
    def is_paying(self) -> bool:
        """
        Return whether the user is currently paying, i.e. is upgraded and not on trial.
        """
        return self.is_upgraded and self.has_ever_paid

    @property
    def total_space(self) -> int:
        """
        The total space this user has access to (base and bonus).
        """
        return self.storage_space + self.bonus_space

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
        return self.total_space - self.total_space_taken

    def upgrade(self, space=settings.GB) -> None:
        """
        Upgrade the user's account for a year.
        """
        self.storage_space = space
        self.upgraded_until = max(
            datetime.date.today(), self.upgraded_until
        ) + datetime.timedelta(366)
        self.last_payment = datetime.date.today()
        self.save()


class ImageManager(models.Manager):  # type: ignore
    def get_queryset(self, hide_expired=True) -> QuerySet:  # type: ignore
        qs = super().get_queryset()
        if hide_expired:
            qs = qs.exclude(expires__lt=timezone.now())
        return qs

    def include_expired(self) -> QuerySet:  # type: ignore
        return self.get_queryset(hide_expired=False)

    def create(self, *args, **kwargs) -> "Image":
        if (
            len(kwargs.get("title", ""))
            > self.model._meta.get_field("title").max_length
        ):
            raise ValueError(
                "This image's title is huge. Try uploading the abridged version."
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
    title = models.CharField(max_length=200, blank=True)
    data = models.BinaryField()
    format = models.CharField(max_length=100, blank=True)
    size = models.IntegerField(default=0)
    uploaded = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(blank=True, null=True)
    views = models.PositiveIntegerField(default=0)

    processed = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Indicate whether this image has been processed (gone through "
        "thumbnail generation, rotation, etc) after upload.",
    )

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
        """
        Return the URL to the image thumbnail.
        """
        return reverse(
            "main:image-show-thumb",
            kwargs={"image_id": self.id, "size": size, "extension": self.extension},
        )

    def set_title(self, title: Optional[str]) -> None:
        """
        Set the image's title.

        Raises ValueError if the title is too short or too long. Does not save the image.
        """
        if not title:
            raise ValueError("A man needs a name.")
        elif len(title) > self._meta.get_field("title").max_length:
            raise ValueError(
                "This image's title is huge. Try uploading the abridged version."
            )
        else:
            self.title = title.replace("\n", " ").strip()

    def generate_thumbnails(self) -> None:
        """
        Generate and store this image's thumbnails.

        It does not save the Image object.
        """
        self.thumbnail_512 = generate_thumbnail(self.data)

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

    def increment_views(self) -> None:
        """
        Increment the image's views by one.

        Saves the Image object.
        """
        self.views += 1
        self.save()

    def process(self) -> None:
        """
        Run various computationally-heavy processes, such as rotation,
        thumbnail generation, etc.
        """
        if self.processed:
            return

        self.strip_exif()

        format = imghdr.what(None, h=self.data)
        self.format = format if format else ""

        self.size = len(self.data)
        self.generate_thumbnails()
        self.processed = True

    def purge_cache(self) -> None:
        """
        Purge this image's URL and all thumbnails from all caches.
        """
        image_dict = self.as_dict()
        image_urls = [
            image_dict["urls"]["image"],
            *image_dict["urls"]["thumbnails"].values(),
        ]
        purge_cloudflare_cache_urls(image_urls)

    def delete(self, *args, **kwargs) -> Tuple[int, Dict[str, int]]:
        self.purge_cache()
        return super().delete(*args, **kwargs)

    def save(self, *args, **kwargs) -> None:
        self.process()
        return super().save(*args, **kwargs)

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
            "title": self.title,
            "format": self.format,
            "uploaded": self.uploaded.strftime("%Y-%m-%d %H:%M:S"),
        }

    def __str__(self) -> str:
        return self.id
