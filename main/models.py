import datetime
import imghdr

import shortuuid
from django.contrib.auth.models import AbstractUser
from django.db import models  # noqa
from django.db.models import Sum
from django.urls import reverse


def generate_short_id() -> str:
    """
    Return a random string of length 7.
    """
    return shortuuid.ShortUUID().random(7)


class User(AbstractUser):
    upgraded_until = models.DateField(default=datetime.date(1900, 1, 1))

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
        return total_size


class Image(models.Model):
    id = models.CharField(
        max_length=30, primary_key=True, default=generate_short_id, editable=False
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

    def __str__(self) -> str:
        return self.id
