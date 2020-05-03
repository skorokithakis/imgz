import base64
import datetime
import json
import os
from io import BytesIO

from django.conf import settings
from django.template import Template
from django.test import Client
from django.test import TestCase
from django.urls import reverse
from shortuuid import ShortUUID as SU

from .models import Image
from .models import User


# A valid PNG image, the smallest possible PNG.
# From https://garethrees.org/2007/11/14/pngcrush/.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQAAAAA3bvkkAAAACklEQVR4nGNgAAAAAgABSK+kcQAAAABJRU5ErkJggg=="
)


def http_auth(username: str, password: str) -> str:
    """
    Encode a username/password pair to Basic auth.
    """
    data = f"{username}:{password}"
    credentials = base64.b64encode(data.encode("utf-8")).strip()
    auth_string = f'Basic {credentials.decode("utf-8")}'
    return auth_string


class ViewTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            username="hi", email="hi@hi.com", password="hi"
        )
        self.assertTrue(self.user1.is_upgraded)
        self.assertFalse(self.user1.has_ever_paid)

        self.expired = User.objects.create(
            username="hi2", email="hi@hi.com", password="hi"
        )
        self.expired.upgraded_until = datetime.date(1900, 1, 1)
        self.expired.save()

        self.assertFalse(self.expired.is_upgraded)
        self.assertFalse(self.expired.has_ever_paid)

        self.no_space = User.objects.create(
            username="hi3", email="hi@hi.com", password="hi"
        )
        self.no_space.storage_space = 0
        self.no_space.save()

        self.assertTrue(self.no_space.is_upgraded)
        self.assertFalse(self.no_space.has_ever_paid)
        self.assertEqual(self.no_space.total_space_left, 0)

        self.superuser = User.objects.create(
            username="super", email="hi@hi.com", password="hi"
        )
        self.superuser.is_superuser = self.superuser.is_staff = True
        self.superuser.save()

    def test_compile_templates(self):
        for template_dir in settings.TEMPLATES[0]["DIRS"]:  # type: ignore
            for basepath, dirs, filenames in os.walk(template_dir):
                for filename in filenames:
                    path = os.path.join(basepath, filename)
                    with open(path, "r") as f:
                        # This will fail if the template cannot compile
                        Template(f.read())

    def test_views(self):
        for name in ("main:index", "main:faq", "main:terms", "main:money"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

        for name in ("main:account", "main:image-upload"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302)

        self.client.force_login(self.user1)  # type: ignore

        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.expired)  # type: ignore

        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)

        for name in ("main:account", "main:image-upload"):
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("main:logout"))
        self.assertEqual(response.status_code, 302)

    def test_expired_images(self):
        i = Image.objects.create(
            title="Horatio, I am expired. Thou livest.",
            user=self.user1,
            data=PNG,
            expires=datetime.datetime(
                2003, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.assertEqual(self.user1.images.count(), 0)
        self.assertTrue(Image.objects.include_expired().filter(pk=i.id).exists())

        i = Image.objects.create(
            title="Horatio, I am expired. Thou livest.", user=self.user1, data=PNG
        )
        self.assertEqual(self.user1.images.count(), 1)
        self.assertTrue(Image.objects.filter(pk=i.id).exists())

        i = Image.objects.create(
            title="Horatio, I am expired. Thou livest.",
            user=self.user1,
            data=PNG,
            expires=datetime.datetime(
                2203, 1, 2, 0, 0, 0, tzinfo=datetime.timezone.utc
            ),
        )
        self.assertEqual(self.user1.images.count(), 2)
        self.assertTrue(Image.objects.filter(pk=i.id).exists())

    def test_invalid_user(self):
        self.client.force_login(self.expired)  # type: ignore

        # Try to upload a valid image.
        png = BytesIO(PNG)
        response = self.client.post(
            reverse("main:image-upload"), {"title": "My image", "image": png}
        )
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Image.objects.count(), 0)

    def test_valid_user(self):
        self.client.force_login(self.user1)  # type: ignore

        # Load the upload page.
        response = self.client.get(reverse("main:image-upload"))
        self.assertEqual(response.status_code, 200)

        # Upload an invalid image.
        self.assertEqual(Image.objects.count(), 0)

        response = self.client.post(
            reverse("main:image-upload"),
            {"title": "My image", "image": BytesIO(b"haha")},
        )
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Image.objects.count(), 0)

        # Upload a valid image.
        png = BytesIO(PNG)
        response = self.client.post(
            reverse("main:image-upload"), {"title": "My image", "image": png}
        )
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Image.objects.count(), 1)

        image = Image.objects.all().order_by("uploaded").first()
        assert image

        self.assertEqual(image.title, "My image")
        self.assertEqual(image.size, len(PNG))

        # Upload another valid image.
        png = BytesIO(PNG)
        response = self.client.post(reverse("main:image-upload"), {"image": png})
        self.assertEqual(response.status_code, 302)

        self.assertEqual(Image.objects.count(), 2)

        image = Image.objects.all().order_by("uploaded").last()
        assert image

        self.assertEqual(image.title, "image")
        self.assertEqual(image.size, len(PNG))

        # Test the image page.
        image.refresh_from_db()
        self.assertEqual(image.views, 0)

        response = self.client.get(image.get_absolute_url())
        self.assertEqual(response.status_code, 200)

        image.refresh_from_db()
        self.assertEqual(image.views, 1)

        response = self.client.get(image.get_image_url())
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.content), len(PNG))

        response = self.client.get(image.get_thumbnail_url(512))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(image.get_thumbnail_url(100))
        self.assertEqual(response.status_code, 404)

        # Let expired try to delete user1's image.
        c2 = Client()
        c2.force_login(self.expired)  # type: ignore
        response = c2.post(reverse("main:image-delete", args=[image.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Image.objects.count(), 2)

        # Delete the image.
        response = self.client.post(reverse("main:image-delete", args=[image.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Image.objects.count(), 1)

        # Check that superuser can delete another user's image.
        image = Image.objects.all().order_by("uploaded").first()
        assert image
        c3 = Client()
        c3.force_login(self.superuser)  # type: ignore
        response = c3.post(reverse("main:image-delete", args=[image.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Image.objects.count(), 0)

    def test_account_deletion(self):
        self.user1.bonus_space = 1024 ** 3
        self.user1.save()

        for _ in range(5):
            png = BytesIO(PNG)
            response = self.client.post(
                reverse("main:api-image"),
                {"title": "My image", "image": png},
                HTTP_AUTHORIZATION=http_auth("", self.user1.api_key),
            )
            self.assertEqual(response.status_code, 200)

        self.assertEqual(Image.objects.count(), 5)

        self.client.force_login(self.user1)  # type: ignore

        response = self.client.post(reverse("main:account") + "?delete=allmyshit")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Image.objects.count(), 0)

        self.user1.refresh_from_db()

        self.assertFalse(self.user1.is_upgraded)
        self.assertEqual(self.user1.total_space_left, 0)

    def test_api(self):
        # Upload an image with an invalid API key.
        png = BytesIO(PNG)
        response = self.client.post(
            reverse("main:api-image"),
            {"title": "My image", "image": png},
            HTTP_AUTHORIZATION=http_auth("", "hello"),
        )
        self.assertEqual(response.status_code, 422)

        # Upload an image with a valid API key.
        for _ in range(5):
            png = BytesIO(PNG)
            response = self.client.post(
                reverse("main:api-image"),
                {"title": "My image", "image": png},
                HTTP_AUTHORIZATION=http_auth("", self.user1.api_key),
            )
            self.assertEqual(response.status_code, 200)
            image_id = json.loads(response.content)["id"]

        self.assertEqual(Image.objects.count(), 5)

        image = Image.objects.get(pk=image_id)

        self.assertEqual(image.title, "My image")
        self.assertEqual(image.size, len(PNG))

        # Get the image list without an API key.
        response = self.client.get(reverse("main:api-image"))
        self.assertEqual(response.status_code, 422)

        # Get the image list with an API key.
        response = self.client.get(
            reverse("main:api-image"),
            HTTP_AUTHORIZATION=http_auth("", self.user1.api_key),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()["images"]), 5)

        # Get the image list for another user.
        response = self.client.get(
            reverse("main:api-image"),
            HTTP_AUTHORIZATION=http_auth("", self.superuser.api_key),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"images": []})

        # Get the image detail page.
        response = self.client.get(reverse("main:api-image-detail", args=[image.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My image", response.content)

        # Get a missing image detail page.
        response = self.client.get(reverse("main:api-image-detail", args=["ihoooo"]))
        self.assertEqual(response.status_code, 404)

        # Change the title.
        response = self.client.put(
            reverse("main:api-image-detail", args=[image.id]),
            {"title": "A new title"},
            content_type="application/json",
            HTTP_AUTHORIZATION=http_auth("", self.user1.api_key),
        )
        self.assertEqual(response.status_code, 200)
        image.refresh_from_db()
        self.assertEqual(image.title, "A new title")

        # Delete the image with the wrong API key.
        response = self.client.delete(
            reverse("main:api-image-detail", args=[image.id]),
            HTTP_AUTHORIZATION=http_auth("", "heyo"),
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Image.objects.count(), 5)

        # Delete the image with another user's API key.
        response = self.client.delete(
            reverse("main:api-image-detail", args=[image.id]),
            HTTP_AUTHORIZATION=http_auth("", self.expired.api_key),
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Image.objects.count(), 5)

        # Delete the image with the right API key.
        response = self.client.delete(
            reverse("main:api-image-detail", args=[image.id]),
            HTTP_AUTHORIZATION=http_auth("", self.user1.api_key),
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Image.objects.count(), 4)

    def test_failure_modes(self):
        # Upload an image when there's no space left.
        png = BytesIO(PNG)
        response = self.client.post(
            reverse("main:api-image"),
            {"title": "My image", "image": png},
            HTTP_AUTHORIZATION=http_auth("", self.no_space.api_key),
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn(b"used up all your space", response.content)

        response = self.client.post(
            reverse("main:api-image"),
            HTTP_AUTHORIZATION=http_auth("", self.user1.api_key),
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn(b"forgot to give us", response.content)

        response = self.client.post(
            reverse("main:api-image"),
            {"title": "My image", "image": BytesIO(b"hi")},
            HTTP_AUTHORIZATION=http_auth("", self.user1.api_key),
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn(b"straight trash", response.content)

        self.assertEqual(Image.objects.count(), 0)

    def test_upgrade(self):
        # Try a simple upgrade of a user on trial.
        u = User.objects.create(username=SU(), email="hi@hi.com", password="hi")
        self.assertTrue(u.is_upgraded)
        self.assertFalse(u.has_ever_paid)
        self.assertTrue(u.total_space < 1_000_000_000)

        u.upgrade()

        self.assertTrue(u.is_upgraded)
        self.assertTrue(u.has_ever_paid)
        self.assertTrue(u.total_space > 1_000_000_000)
        self.assertTrue(
            u.upgraded_until > datetime.date.today() + datetime.timedelta(385)
        )

        # Upgrade someone who already has lots of space.
        u = User.objects.create(username=SU(), email="hi@hi.com", password="hi")
        u.bonus_space = 0.5 * settings.GB
        self.assertTrue(u.is_upgraded)
        self.assertFalse(u.has_ever_paid)

        u.upgrade()

        self.assertTrue(u.is_upgraded)
        self.assertTrue(u.has_ever_paid)
        self.assertTrue(u.total_space > 1_500_000_000)

    def test_size_tag(self):
        from main.templatetags.human_size import size

        for num, display in (
            (100, "100 bytes"),
            (1_992_294, "1.9 MB"),
            (10_048_577, "9.58 MB"),
            (10_048_577_000, "9.36 GB"),
            (1024 ** 3, "1 GB"),
        ):
            self.assertEqual(size(num), display)
