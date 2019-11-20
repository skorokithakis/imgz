from django.core.management.base import BaseCommand

from main.models import Image


class Command(BaseCommand):
    help = "Process all unprocessed images (generate thumbnails, rotate, etc)."

    def handle(self, *args, **options):
        counter = 0
        for image in Image.objects.filter(processed=False):
            print(f"Processing {image.id}...")
            image.process()
            image.save()
            counter += 1

        print(f"Processed {counter} images.")
