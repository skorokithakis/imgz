"""
Tests for tests?

These are tests of our factories. That these are doing what we think they are
doing is critical to any test that uses them. Let's make sure that they are
doing that.
"""

import datetime

import pytest

from tests.factories import UserFactory


@pytest.mark.django_db
def test_user_factory_admin_trait():
    user = UserFactory(admin=True)
    user.refresh_from_db()
    assert user.is_superuser
    assert user.is_staff


@pytest.mark.django_db
def test_user_factory_with_expired_trial():
    user = UserFactory(with_expired_trial=True)
    user.refresh_from_db()

    assert user.last_payment == datetime.date(1900, 1, 1)
    assert user.upgraded_until == datetime.date.today() - datetime.timedelta(days=31)


@pytest.mark.django_db
def test_user_factory_with_active_subscription():
    user = UserFactory(with_active_subscription=True)
    user.refresh_from_db()

    assert user.is_upgraded


@pytest.mark.django_db
def test_user_factory_with_no_space_left():
    user = UserFactory(with_no_space=True)
    user.refresh_from_db()

    assert not user.storage_space
    assert not user.total_space
