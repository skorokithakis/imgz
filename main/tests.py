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

from .models import Image
from .models import User

# Create your tests here.

# A valid PNG image, the smallest possible PNG.
# From https://garethrees.org/2007/11/14/pngcrush/.
PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABAQAAAAA3bvkkAAAACklEQVR4nGNgAAAAAgABSK+kcQAAAABJRU5ErkJggg=="
)


class ViewTests(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            username="hi", email="hi@hi.com", password="hi"
        )
        self.assertTrue(self.user1.is_paying)
        self.assertFalse(self.user1.has_ever_paid)

        self.user2 = User.objects.create(
            username="hi2", email="hi@hi.com", password="hi"
        )
        self.user2.upgraded_until = datetime.date(1900, 1, 1)
        self.user2.save()

        self.assertFalse(self.user2.is_paying)
        self.assertFalse(self.user2.has_ever_paid)

    def test_compile_templates(self):
        for template_dir in settings.TEMPLATES[0]["DIRS"]:  # type: ignore
            for basepath, dirs, filenames in os.walk(template_dir):
                for filename in filenames:
                    path = os.path.join(basepath, filename)
                    with open(path, "r") as f:
                        # This will fail if the template cannot compile
                        Template(f.read())

    def test_views(self):
        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user1)  # type: ignore

        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)

        self.client.force_login(self.user2)  # type: ignore

        response = self.client.get(reverse("main:index"))
        self.assertEqual(response.status_code, 200)

        response = self.client.get(reverse("main:logout"))
        self.assertEqual(response.status_code, 302)

        response = self.client.get(reverse("main:faq"))
        self.assertEqual(response.status_code, 200)

    def test_invalid_user(self):
        self.client.force_login(self.user2)  # type: ignore

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

        response = self.client.get(image.get_thumbnail_url(513))
        self.assertEqual(response.status_code, 404)

        # Let user2 try to delete user1's image.
        c2 = Client()
        c2.force_login(self.user2)  # type: ignore
        response = c2.post(reverse("main:image-delete", args=[image.id]))
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Image.objects.count(), 2)

        # Delete the image.
        response = self.client.post(reverse("main:image-delete", args=[image.id]))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Image.objects.count(), 1)

    def test_api(self):
        # Upload an image with an invalid API key.
        png = BytesIO(PNG)
        response = self.client.post(
            reverse("main:api-image-upload") + f"?api_key=hello",
            {"title": "My image", "image": png},
        )
        self.assertEqual(response.status_code, 422)

        # Upload an image with a valid API key.
        png = BytesIO(PNG)
        response = self.client.post(
            reverse("main:api-image-upload") + f"?api_key={self.user1.api_key}",
            {"title": "My image", "image": png},
        )
        self.assertEqual(response.status_code, 200)
        image_id = json.loads(response.content)["id"]

        self.assertEqual(Image.objects.count(), 1)

        image = Image.objects.get(pk=image_id)

        self.assertEqual(image.title, "My image")
        self.assertEqual(image.size, len(PNG))

        # Get the image detail page.
        response = self.client.get(reverse("main:api-image-detail", args=[image.id]))
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"My image", response.content)

        # Get a missing image detail page.
        response = self.client.get(reverse("main:api-image-detail", args=["ihoooo"]))
        self.assertEqual(response.status_code, 404)

        # Delete the image with the wrong API key.
        response = self.client.delete(
            reverse("main:api-image-detail", args=[image.id])
            + f"?api_key={self.user2.api_key}"
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(Image.objects.count(), 1)

        # Delete the image with the right API key.
        response = self.client.delete(
            reverse("main:api-image-detail", args=[image.id])
            + f"?api_key={self.user1.api_key}"
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Image.objects.count(), 0)
