import datetime
from io import BytesIO

import pytest
from django.conf import settings
from PIL import Image as PILImage
from PIL.ExifTags import Base as ExifTag

from main.models import Image
from main.models import User
from tests.factories import ImageFactory
from tests.factories import UserFactory


@pytest.mark.parametrize(
    "creation_kwargs, expected",
    [
        # Rather than test explicitly for the (1900, 1, 1) placeholder, test
        # that whatever default DB value is used for creating new instances
        # is understood to mean "hasn't ever paid".
        [{}, True],
        [{"last_payment": datetime.datetime(2023, 2, 3)}, False],
    ],
)
@pytest.mark.django_db
def test_user_is_on_trial(creation_kwargs, expected):
    user = User.objects.create(**creation_kwargs)
    user.refresh_from_db()
    assert user.is_on_trial is expected


def test_user_str():
    assert str(User(email="imaginary@example.invalid")) == "imaginary@example.invalid"


@pytest.mark.django_db
def test_upgrade_of_trial_user():
    # Try a simple upgrade of a user on trial.
    u = UserFactory()
    assert u.is_upgraded is True
    assert u.has_ever_paid is False
    assert (u.total_space < 1_000_000_000) is True
    assert u.is_on_trial is True

    u.upgrade(1 * settings.GB)

    assert u.is_upgraded is True
    assert u.has_ever_paid is True
    # mypy incorrectly flags the below as unreachable
    assert (u.total_space > 1_000_000_000) is True  # type:ignore
    assert (u.upgraded_until > datetime.date.today() + datetime.timedelta(375)) is True
    assert u.is_on_trial is False


@pytest.mark.django_db
def test_upgrade_of_user_with_space():
    # Upgrade someone who already has lots of space.
    u = UserFactory(bonus_space=(0.5 * settings.GB))
    assert u.is_upgraded is True
    assert u.has_ever_paid is False

    u.upgrade(1 * settings.GB)

    assert u.is_upgraded is True
    assert u.has_ever_paid is True
    # mypy incorrectly flags the below as unreachable
    assert (u.total_space > 1_500_000_000) is True  # type:ignore


@pytest.mark.django_db
def test_image_manager_expired_images():
    user = UserFactory()
    image = ImageFactory(
        user=user,
        expires=datetime.datetime(2003, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc),
    )

    assert user.images.count() == 0
    assert Image.objects.include_expired().filter(pk=image.id).exists()

    image = ImageFactory(user=user)
    assert user.images.count() == 1
    assert Image.objects.filter(id=image.pk).exists()

    image = ImageFactory(
        user=user,
        expires=datetime.datetime(2203, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc),
    )
    assert user.images.count() == 2
    assert Image.objects.filter(id=image.pk).exists()


def test_strip_exif_removes_exif():
    exif = PILImage.Exif()
    exif[ExifTag.ImageDescription] = "private metadata"
    with BytesIO() as output:
        PILImage.new("RGB", (2, 2), color="red").save(output, format="JPEG", exif=exif)
        image = ImageFactory.build(data=output.getvalue())

    with BytesIO(image.data) as input_file:
        source = PILImage.open(input_file)
        assert source.getexif().get(ExifTag.ImageDescription) == "private metadata"
        processed = image.strip_exif(source)

    assert ExifTag.ImageDescription not in processed.getexif()


def test_strip_exif_applies_orientation():
    exif = PILImage.Exif()
    exif[ExifTag.Orientation] = 6
    with BytesIO() as output:
        source = PILImage.new("RGB", (2, 3))
        source.putdata(
            [
                (255, 0, 0),
                (0, 255, 0),
                (0, 0, 255),
                (255, 255, 0),
                (0, 255, 255),
                (255, 0, 255),
            ]
        )
        source.save(output, format="PNG", exif=exif)
        image = ImageFactory.build(data=output.getvalue())

    with BytesIO(image.data) as input_file:
        source = PILImage.open(input_file)
        processed = image.strip_exif(source)

    assert processed.size == (3, 2)
    assert [processed.getpixel((x, y)) for y in range(2) for x in range(3)] == [
        (0, 255, 255),
        (0, 0, 255),
        (255, 0, 0),
        (255, 0, 255),
        (255, 255, 0),
        (0, 255, 0),
    ]


def test_strip_exif_preserves_palette_colours():
    source = PILImage.new("P", (2, 1))
    source.putpalette([255, 0, 0, 0, 255, 0] + [0] * 762)
    source.putdata([0, 1])
    source.info["transparency"] = 1
    image = ImageFactory.build()

    processed = image.strip_exif(source)

    assert [processed.convert("RGB").getpixel((x, 0)) for x in range(2)] == [
        source.convert("RGB").getpixel((x, 0)) for x in range(2)
    ]
    with BytesIO() as output:
        processed.save(output, format="PNG")
        output.seek(0)
        assert PILImage.open(output).info["transparency"] == 1


def test_strip_exif_rotates_and_removes_exif():
    exif = PILImage.Exif()
    exif[ExifTag.Orientation] = 6
    exif[ExifTag.ImageDescription] = "private metadata"
    with BytesIO() as output:
        source = PILImage.new("RGB", (1, 2), color="red")
        source.save(output, format="PNG", exif=exif)
        image = ImageFactory.build(data=output.getvalue())

    with BytesIO(image.data) as input_file:
        processed = image.strip_exif(PILImage.open(input_file))

    assert processed.size == (2, 1)
    assert not processed.getexif()
