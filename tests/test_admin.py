import pytest
from django.urls import reverse

from tests.factories import ImageFactory
from tests.factories import PostFactory
from tests.factories import UserFactory


@pytest.mark.django_db
@pytest.mark.parametrize("model_factory", [ImageFactory, PostFactory, UserFactory])
def test_admin_smoke(client, model_factory):
    """
    Basic tests to make sure the admin isn't broken. It is easy to get
    code coverage of these things, because it is all declarative; it is just
    as easy to break the admin.
    """
    client.force_login(UserFactory(admin=True))

    app_label = model_factory._meta.model._meta.app_label
    model_name = model_factory._meta.model._meta.model_name

    for action in ["add", "changelist"]:
        response = client.get(reverse(f"admin:{app_label}_{model_name}_{action}"))
        assert response.status_code == 200

    instances = model_factory.create_batch(10)
    response = client.get(reverse(f"admin:{app_label}_{model_name}_changelist"))
    assert response.status_code == 200

    response = client.get(
        reverse(f"admin:{app_label}_{model_name}_change", args=[instances[0].pk])
    )
    assert response.status_code == 200
