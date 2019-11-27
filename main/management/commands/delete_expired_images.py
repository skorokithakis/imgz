import datetime

from django.core.management.base import BaseCommand

from main.models import Image


class Command(BaseCommand):
    help = "Delete expired images."

    def handle(self, *args, **options):
        counter = 0

        for image in Image.objects.include_expired().filter(
            expires__lt=datetime.datetime.utcnow()
        ):
            print(f"Deleting {image.id}...")
            image.delete()
            counter += 1

        print(f"Deleted {counter} images.")
