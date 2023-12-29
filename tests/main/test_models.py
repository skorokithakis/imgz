import datetime

import pytest
from django.conf import settings

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
