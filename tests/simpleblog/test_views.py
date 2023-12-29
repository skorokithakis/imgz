import pytest
from django.urls import reverse

from tests.factories import PostFactory


@pytest.mark.django_db
def test_post_list(client):
    PostFactory.create_batch(5)
    response = client.get(reverse("blog_archive"))
    assert response.status_code == 200


@pytest.mark.django_db
def test_post_detail(client):
    post = PostFactory()
    response = client.get(post.get_absolute_url())
    assert response.status_code == 200
