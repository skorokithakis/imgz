import base64
from io import BytesIO

import pytest
from django.urls import reverse

from main.models import Image
from tests.client import APIClient
from tests.factories import ImageFactory
from tests.factories import UserFactory


@pytest.mark.django_db
def test_image_list():
    url = reverse("main:api-image")
    user = UserFactory()
    ImageFactory.create_batch(5, user=user)
    # Canary for queryset exclusions
    ImageFactory()

    response = APIClient(api_key=user.api_key).get(url)
    assert response.status_code == 200
    assert len(response.json()["images"]) == 5

    # Ensure other users are not seeing the same images.
    response = APIClient(api_key=UserFactory().api_key).get(url)
    assert response.status_code == 200
    assert len(response.json()["images"]) == 0


@pytest.mark.django_db
def test_image_list_without_api_key(client):
    # Get the image list without an API key and with a broken one.
    for use_client in [client, APIClient(api_key="what")]:
        response = use_client.get(reverse("main:api-image"))
        assert response.status_code == 422
        assert b"Invalid API key" in response.content


@pytest.mark.django_db
def test_image_list_with_broken_api_header(client):
    # Fetch the image list with broken headers. This tests the exception
    # handling in _get_auth on APIView.
    for broken_auth in [base64.b64encode(b"asdf"), "f"]:
        response = client.get(
            reverse("main:api-image"),
            HTTP_AUTHORIZATION=f"Basic {broken_auth}",
        )
        assert response.status_code == 422
        print(response.content)


@pytest.mark.django_db
def test_image_detail():
    image = ImageFactory()
    client = APIClient(api_key=image.user.api_key)

    # Get a real image detail page.
    response = client.get(reverse("main:api-image-detail", args=[image.pk]))
    assert response.status_code == 200

    # Get a missing image detail page.
    response = client.get(reverse("main:api-image-detail", args=["ihoooo"]))
    assert response.status_code == 404


@pytest.mark.django_db
def test_image_detail_change_title():
    image = ImageFactory()
    client = APIClient(api_key=image.user.api_key)

    response = client.put(
        reverse("main:api-image-detail", args=[image.id]),
        {"title": "A new title"},
        content_type="application/json",
    )
    assert response.status_code == 200
    image.refresh_from_db()
    assert image.title == "A new title"

    # Check an error handling branch in ImageView.put.
    response = client.put(
        reverse("main:api-image-detail", args=[image.id]),
        {"title": "aa" * Image._meta.get_field("title").max_length},
        content_type="application/json",
    )
    assert response.status_code == 422
    assert b"This image's title is huge." in response.content


@pytest.mark.django_db
def test_image_detail_change_title_with_broken_json():
    """
    Test the error handling branch for receiving broken JSON.
    """
    image = ImageFactory()
    client = APIClient(api_key=image.user.api_key)

    response = client.put(
        reverse("main:api-image-detail", args=[image.id]),
        "!!!",
        HTTP_CONTENT_TYPE="application/json",
    )
    assert response.status_code == 422
    assert b"Error while decoding your JSON content" in response.content


@pytest.mark.django_db
def test_image_detail_delete():
    # Delete the image with the right API key.
    image = ImageFactory()
    response = APIClient(api_key=image.user.api_key).delete(
        reverse("main:api-image-detail", args=[image.id]),
    )
    assert response.status_code == 200
    assert Image.objects.count() == 0


@pytest.mark.django_db
def test_image_detail_delete_without_api_key(client):
    # Delete the image with the wrong API key.
    image = ImageFactory()
    for use_client in [client, APIClient(api_key=UserFactory().api_key)]:
        response = use_client.delete(reverse("main:api-image-detail", args=[image.id]))
        assert response.status_code == 422
    assert Image.objects.count() == 1


@pytest.mark.django_db
def test_image_upload(png_io):
    client = APIClient(api_key=UserFactory().api_key)

    for _ in range(5):
        response = client.post(
            reverse("main:api-image"),
            {"title": "My image", "image": png_io},
        )
        assert response.status_code == 200
        png_io.seek(0)
        image_id = response.json()["id"]

    assert Image.objects.count() == 5

    image = Image.objects.get(pk=image_id)
    assert image.title == "My image"
    assert image.size == len(png_io.getvalue())


@pytest.mark.django_db
def test_image_upload_validation():
    client = APIClient(api_key=UserFactory().api_key)
    response = client.post(reverse("main:api-image"))
    assert response.status_code == 422
    assert b"forgot to give us" in response.content

    response = client.post(
        reverse("main:api-image"),
        {"title": "My image", "image": BytesIO(b"hi")},
    )
    assert response.status_code == 422
    assert b"straight trash" in response.content
    assert Image.objects.count() == 0


@pytest.mark.django_db
def test_image_upload_with_invalid_api_key(client, png_io):
    client = APIClient(api_key="hello")
    response = client.post(
        reverse("main:api-image"),
        {"title": "My image", "image": png_io},
    )
    assert response.status_code == 422
    assert b"Invalid API key" in response.content


@pytest.mark.django_db
def test_image_upload_with_no_space(png_io):
    no_space_user = UserFactory(with_no_space=True)
    response = APIClient(api_key=no_space_user.api_key).post(
        reverse("main:api-image"), {"image": png_io}
    )
    assert response.status_code == 422
    assert b"used up all your space" in response.content
