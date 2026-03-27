from io import BytesIO

import pytest
from django.contrib.messages import ERROR
from django.urls import reverse

from main.models import Image
from tests.factories import ImageFactory
from tests.factories import UserFactory
from tests.helpers import pil_from_response


@pytest.mark.django_db
def test_set_image_title(client):
    image = ImageFactory()
    client.force_login(image.user)

    response = client.post(image.get_absolute_url(), data={"title": "New title"})
    assert response.status_code == 302
    assert response["Location"] == image.get_absolute_url()

    image.refresh_from_db()
    assert image.title == "New title"


@pytest.mark.django_db
def test_set_someone_elses_image_title(client):
    """
    Ensure someone can't change the title on someone else's image.
    """
    client.force_login(UserFactory())
    image = ImageFactory()
    old_title = image.title

    response = client.post(image.get_absolute_url())
    assert response.status_code == 302

    response = client.get(response["Location"])
    assert response.status_code == 200
    messages = list(response.context["messages"])
    assert len(response.context["messages"]) == 1
    assert messages[0].level == ERROR
    assert messages[0].message == "No."

    # Ensure the title hasn't changed.
    image.refresh_from_db()
    assert image.title == old_title


@pytest.mark.django_db
@pytest.mark.parametrize(
    "post_data, expected_message",
    [
        ({}, "A man needs a name."),
        ({"title": ""}, "A man needs a name."),
        ({"title": "a" * 201}, "This image's title is huge."),
    ],
)
def test_set_bad_image_titles(client, post_data, expected_message):
    """
    Test various bad paths for setting the title of an image.
    """
    user = UserFactory()
    image = ImageFactory(user=user)
    client.force_login(user)
    old_title = image.title

    response = client.post(image.get_absolute_url(), data=post_data)
    assert response.status_code == 302

    response = client.get(response["Location"])
    assert response.status_code == 200
    messages = list(response.context["messages"])
    assert len(response.context["messages"]) == 1
    assert messages[0].level == ERROR
    assert expected_message in messages[0].message

    # Ensure the title hasn't changed.
    image.refresh_from_db()
    assert image.title == old_title


@pytest.mark.django_db
def test_get_api_doc_view(client):
    response = client.get(reverse("main:api-docs"))
    assert response.status_code == 200
    assert b"curl https://:y0uRAP1k3y" in response.content

    client.force_login(UserFactory(api_key="samplekey"))
    response = client.get(reverse("main:api-docs"))
    assert response.status_code == 200
    assert b"curl https://:samplekey" in response.content


@pytest.mark.django_db
def test_latest_view(client):
    ImageFactory.create_batch(101)
    url = reverse("main:latest")
    # Unauthed users must not be able to see the latest image list.
    response = client.get(url)
    assert response.status_code == 404

    user = UserFactory()
    # Nor may non-superusers see the latest image list.
    response = client.get(url)
    assert response.status_code == 404

    user.is_superuser = True
    user.save()
    client.force_login(user)

    # From here, it is a superuser, which means they have permission to view
    # the image list.
    #
    # Check that the default of 100 is shown.
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.context["images"]) == 100

    # The default of 100 will be shown even if we give a nonsense value for
    # `items`.
    response = client.get(url, data={"items": "whargbl"})
    assert response.status_code == 200
    assert len(response.context["images"]) == 100

    # The item count in
    response = client.get(url, data={"items": "5"})
    assert response.status_code == 200
    assert len(response.context["images"]) == 5


@pytest.mark.django_db
def test_account_delete_all_their_shit(client):
    user = UserFactory(with_active_subscription=True)
    ImageFactory.create_batch(3, user=user)

    # Canary images, don't delete the wrong shit
    ImageFactory.create_batch(5)

    # silly paranoia test
    assert user.images.count() == 3

    client.force_login(user)
    response = client.post(f"{reverse('main:account')}?delete=allmyshit")
    assert response.status_code == 302
    assert user.images.count() == 0
    assert Image.objects.count() == 5

    user.refresh_from_db()
    assert user.is_upgraded is False
    assert user.total_space_left == 0


@pytest.mark.django_db
def test_image_resize_view(client):
    image = ImageFactory(realistic=True)
    response = client.get(
        reverse(
            "main:image-show-resized",
            kwargs={
                "image_id": image.id,
                "size": 666,
                "extension": "png",
            },
        )
    )
    assert response.status_code == 404
    assert response.content == b"Size not found."

    response = client.get(
        reverse(
            "main:image-show-resized",
            kwargs={
                "image_id": image.id,
                "size": 1280,
                "extension": "png",
            },
        )
    )
    assert response.status_code == 200

    pil_image = pil_from_response(response)
    assert pil_image.size == (1280, 720)


@pytest.mark.django_db
@pytest.mark.parametrize(
    "view_name, query_data, expected_string",
    [
        ("main:index", {}, "bullshit social network"),
        ("main:index", {"v": "c"}, "Supercharge your visual pipeline"),
        ("main:index", {"v": "s"}, "We don't fuck you over"),
        ("main:faq", {}, "Here are the answers to all your questions"),
        ("main:terms", {}, "This is my project"),
        ("main:money", {}, "Let's talk money."),
        ("main:money-safe", {}, "Here you can purchase our services."),
        ("main:payment-return", {}, "Oh wow, you paid."),
    ],
)
def test_unauthed_views(client, view_name, query_data, expected_string):
    """
    Tests the various views which are available to all users.
    """
    response = client.get(reverse(view_name), data=query_data)
    assert response.status_code == 200
    assert expected_string.encode("utf8") in response.content


@pytest.mark.django_db
@pytest.mark.parametrize("view_name", ["main:account", "main:image-upload"])
def test_authenticated_views_when_unauthenticated(client, view_name):
    url = reverse(view_name)
    response = client.get(url)
    assert response.status_code == 302
    assert response["Location"] == f"{reverse('main:index')}?next={url}"


@pytest.mark.django_db
def test_authenticated_home(client):
    user = UserFactory()
    ImageFactory.create_batch(3, user=user)
    # canary to test queryset exclusions
    ImageFactory.create_batch(5)
    client.force_login(user)
    response = client.get(reverse("main:index"))
    assert response.status_code == 200
    assert len(response.context["images"]) == 3


@pytest.mark.django_db
def test_image_delete_with_wrong_user(client):
    image = ImageFactory()

    # A user should not be allowed to delete someone else's image.
    client.force_login(UserFactory())
    response = client.post(reverse("main:image-delete", args=[image.id]))
    assert response.status_code == 404
    assert Image.objects.count() == 1


@pytest.mark.django_db
def test_image_delete(client):
    owner = UserFactory()
    admin = UserFactory(admin=True)
    # A user should be able to delete their own image.
    for user in [owner, admin]:
        image = ImageFactory(user=owner)
        client.force_login(user)
        response = client.post(reverse("main:image-delete", args=[image.id]))
        assert response.status_code == 302
        assert response["Location"] == reverse("main:index")
        assert Image.objects.count() == 0


@pytest.mark.django_db
def test_image_detail_pages(client):
    image = ImageFactory()
    assert image.views == 0

    response = client.get(image.get_absolute_url())
    assert response.status_code == 200
    image.refresh_from_db()
    assert image.views == 1

    response = client.get(image.get_image_url())
    assert response.status_code == 200
    assert len(response.content) == len(image.data)

    response = client.get(image.get_thumbnail_url(512))
    assert response.status_code == 200

    response = client.get(image.get_thumbnail_url(100))
    assert response.status_code == 404


@pytest.mark.django_db
def test_image_upload(client, png_io):
    client.force_login(UserFactory(with_active_subscription=True))

    # Load the upload page.
    response = client.get(reverse("main:image-upload"))
    assert response.status_code == 200

    assert Image.objects.count() == 0

    # Upload an invalid image.
    response = client.post(
        reverse("main:image-upload"),
        {"title": "My image", "image": BytesIO(b"haha")},
    )
    assert response.status_code == 302
    assert response["Location"] == reverse("main:image-upload")
    assert Image.objects.count() == 0

    # Upload an valid image.
    response = client.post(
        reverse("main:image-upload"),
        {"title": "My image", "image": png_io},
    )
    assert response.status_code == 302
    image = Image.objects.get()
    assert response["Location"] == image.get_absolute_url()
    assert image.title == "My image"
    assert image.size == len(png_io.getvalue())


@pytest.mark.django_db
def test_image_upload_with_expired_trial(client, png_io):
    client.force_login(UserFactory(with_expired_trial=True))
    response = client.post(reverse("main:image-upload"), data={"image": png_io})
    assert response.status_code == 302
    assert response["Location"] == reverse("main:image-upload")

    response = client.get(response["Location"])
    assert response.status_code == 200
    assert "you need to pay" in list(response.context["messages"])[0].message
    assert Image.objects.count() == 0


@pytest.mark.django_db
def test_various_views_with_expired_trial(client):
    client.force_login(UserFactory(with_expired_trial=True))
    response = client.get(reverse("main:index"))
    assert response.status_code == 200
    assert b"your trial expired" in response.content

    for name in ("main:account", "main:image-upload"):
        response = client.get(reverse(name))
        assert response.status_code == 200


@pytest.mark.django_db
def test_logout(client):
    client.force_login(UserFactory())
    response = client.get(reverse("main:logout"))
    assert response.status_code == 302
    assert response["Location"] == reverse("main:index")


@pytest.mark.django_db
def test_image_upload_json_success(client, png_io):
    """
    A POST with Accept: application/json should return JSON with the image URL
    instead of a redirect.
    """
    client.force_login(UserFactory(with_active_subscription=True))

    response = client.post(
        reverse("main:image-upload"),
        {"title": "My image", "image": png_io},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 200
    data = response.json()
    image = Image.objects.get()
    assert data == {"url": f"http://testserver{image.get_absolute_url()}"}


@pytest.mark.django_db
def test_image_upload_json_upload_error(client, png_io):
    """
    An UploadError (e.g. unpaid user) should return a JSON error with status 400.
    """
    client.force_login(UserFactory(with_expired_trial=True))

    response = client.post(
        reverse("main:image-upload"),
        {"image": png_io},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert "pay" in data["error"]
    assert Image.objects.count() == 0


@pytest.mark.django_db
def test_image_upload_json_invalid_form(client):
    """
    A POST with Accept: application/json and no file should return a JSON error
    with status 400 (form validation failure, not UploadError).
    """
    client.force_login(UserFactory(with_active_subscription=True))

    response = client.post(
        reverse("main:image-upload"),
        {},
        HTTP_ACCEPT="application/json",
    )
    assert response.status_code == 400
    data = response.json()
    assert "error" in data
    assert Image.objects.count() == 0


@pytest.mark.django_db
def test_image_upload_normal_post_still_redirects(client, png_io):
    """
    A normal POST without Accept: application/json must still redirect.
    """
    client.force_login(UserFactory(with_active_subscription=True))

    response = client.post(
        reverse("main:image-upload"),
        {"title": "My image", "image": png_io},
    )
    assert response.status_code == 302
    image = Image.objects.get()
    assert response["Location"] == image.get_absolute_url()
