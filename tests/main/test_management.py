from datetime import date
from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils.timezone import now

from main.models import Image
from tests.factories import ImageFactory
from tests.factories import UserFactory


@pytest.mark.django_db
def test_delete_expired_images():
    """
    Test that "./manage.py delete_expired_images" does what it says it does.
    """

    # An expired image
    expired_image = ImageFactory(expires=now() - timedelta(seconds=10))
    canaries = [
        # Canary: null expiry.
        ImageFactory(),
        # Canary: expires in the future.
        ImageFactory(expires=now() + timedelta(seconds=60)),
    ]

    call_command("delete_expired_images")

    assert Image.objects.include_expired().count() == 2

    for canary in canaries:
        # Will fail with Image.DoesNotExist.
        Image.objects.include_expired().get(id=canary.pk)

    with pytest.raises(Image.DoesNotExist):
        Image.objects.include_expired().get(id=expired_image.pk)


@pytest.mark.django_db
@pytest.mark.xfail  # the management command is broken
def test_delete_inactive_users():
    """
    Test that "./manage.py delete_inactive_users" does what you think it does.

    It doesn't! This test is xfailed because the management command is broken.
    It fails with:

    TypeError: create_reverse_many_to_one_manager.<locals>.RelatedManager.get_queryset() got an unexpected keyword argument 'hide_expired'
    """

    # A user who has never paid, and has been on trial more than 30 days.
    # Delete their stuff.
    expired_trial_user = UserFactory(with_expired_trial=True)

    on_trial = UserFactory(last_payment=date(1900, 1, 1))
    on_trial.upgraded_until == date.today() - timedelta(days=29)
    on_trial.save()

    # A user who has paid recently and has upgrade time remaining.
    paid_user = UserFactory(last_payment=date.today() - timedelta(days=1))
    paid_user.upgraded_until = date.today() + timedelta(days=10)
    paid_user.save()

    # A user who has ever paid, but whose upgrade has expired. Don't delete
    # their stuff; they are granted an indefinite grace period.
    grace_user = UserFactory(last_payment=date.today() - timedelta(days=730))
    grace_user.upgraded_until = date.today() - timedelta(days=365)
    grace_user.save()

    canaries = [paid_user, on_trial, grace_user]

    # Create two images for all of our canaries above.
    for canary in canaries:
        ImageFactory.create_batch(2, user=canary)

    # Create both an expired and unexpired image for the user to ensure both
    # are deleted.
    ImageFactory.create(user=expired_trial_user)
    ImageFactory.create(user=expired_trial_user, expires=now() - timedelta(days=2))

    call_command("delete_inactive_users")

    assert Image.objects.include_expired().count() == len(canaries) * 2
    assert Image.objects.include_expired().filter(user=expired_trial_user).count() == 0


@pytest.mark.django_db
def test_process_images():
    image = ImageFactory(realistic=True)
    # "process" is called on save, so we can't just create an image with
    # processed=False. But we can avoid bypass `save` with `QuerySet.update` :)
    update_count = Image.objects.filter(pk=image.pk).update(
        processed=False, thumbnail_512=b""
    )
    assert update_count == 1

    image.refresh_from_db()
    assert image.processed is False
    assert not image.thumbnail_512

    call_command("process_images")
    image.refresh_from_db()
    assert image.processed is True
    assert image.thumbnail_512  # type:ignore[unreachable]
