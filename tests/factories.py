import datetime

import factory
import shortuuid
from django.contrib.auth import get_user_model
from django.utils.text import slugify

from main.models import Image
from simpleblog.models import Post
from tests.helpers import data_file_path
from tests.helpers import PNG


class UserFactory(factory.django.DjangoModelFactory):
    email = factory.Sequence(lambda i: f"imaginary{i}@example.invalid")
    username = factory.LazyFunction(shortuuid.uuid)

    class Meta:
        model = get_user_model()
        skip_postgeneration_save = True

    class Params:
        admin = factory.Trait(
            is_staff=True,
            is_superuser=True,
        )

    @factory.post_generation  # type:ignore
    def with_expired_trial(obj, create, extracted: bool, **kwargs):
        """
        Creates this instance with an expired trial; last_payment set to the
        default of 1900-01-01 and a "upgraded until" of more than 30 days
        ago.

        This cannot be implemented as a trait because "upgraded_until" is
        set to a future date on save.
        """
        if create and extracted:
            obj.last_payment = datetime.date(1900, 1, 1)
            obj.upgraded_until = datetime.date.today() - datetime.timedelta(days=31)
            obj.save()

    @factory.post_generation  # type:ignore
    def with_active_subscription(obj, create, extracted: bool, **kwargs):
        """
        Creates this instance with a currently active subscription.

        As above, this cannot be implemented as a trait because
        "upgraded_until" is set to a future date on save.
        """
        if create and extracted:
            obj.last_payment = datetime.date.today() - datetime.timedelta(days=10)
            obj.upgraded_until = datetime.date.today() + datetime.timedelta(days=365)
            obj.storage_space = 1024**3
            obj.save()

    @factory.post_generation  # type:ignore
    def with_no_space(obj, create, extracted: bool, **kwargs):
        """
        Create a user with no storage space left; use this for tests where you
        want to test the "out of storage space" behaviour.
        """
        if create and extracted:
            obj.storage_space = 0
            obj.save()


class ImageFactory(factory.django.DjangoModelFactory):
    """
    Generates an image for tests.

    Ordinarily, the `data` field (the image itself) will be the minimum viable
    PNG, because not all tests require working on real image data. If your
    tests require working on real image data (for example, they do resizing),
    instantiate with the `realistic=True` keyword argument. This will give you
    a 1920x1080 PNG as the image data.
    """

    user = factory.SubFactory(UserFactory)
    title = factory.Sequence(lambda i: f"Masterpiece #{i}")
    data = PNG

    class Meta:
        model = Image

    class Params:
        realistic = factory.Trait(
            data=factory.LazyAttribute(
                lambda obj: data_file_path("image-1920x1080.png").read_bytes()
            ),
        )


class PostFactory(factory.django.DjangoModelFactory):
    title = factory.Sequence(lambda i: f"War and Peace chapter {i}")
    slug = factory.LazyAttribute(lambda obj: slugify(obj.title))
    bodytext = factory.Sequence(lambda i: " ".join(["spam"] * i))

    class Meta:
        model = Post
