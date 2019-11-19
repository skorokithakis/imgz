import datetime
import imghdr
from typing import Any
from typing import Dict

import shortuuid
from django.contrib.auth.models import AbstractUser
from django.contrib.sites.models import Site
from django.db import models
from django.db.models import Sum
from django.urls import reverse


def generate_moderate_id() -> str:
    return shortuuid.ShortUUID().random(12)


def generate_image_id() -> str:
    return "i" + shortuuid.ShortUUID().random(7)


class User(AbstractUser):
    upgraded_until = models.DateField(default=datetime.date(1900, 1, 1))
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
        return self.is_paying

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

    def get_absolute_url(self) -> str:
        return reverse("main:image-show", kwargs={"image_id": self.id})

    def save(self, *args, **kwargs):
        format = imghdr.what(None, h=self.data)
        self.format = format if format else ""
        self.size = len(self.data)
        super().save(*args, **kwargs)

    def as_dict(self) -> Dict[str, Any]:
        site = Site.objects.get_current()
        return {
            "id": self.id,
            "url": f"https://{site.domain}{self.get_absolute_url()}",
            "size": self.size,
            "name": self.name,
            "format": self.format,
            "uploaded": self.uploaded.strftime("%Y-%m-%d %H:%M:S"),
        }

    def __str__(self) -> str:
        return self.id
