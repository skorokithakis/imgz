import datetime

from django.core.management.base import BaseCommand

from main.models import User


class Command(BaseCommand):
    help = "Delete everything about users whose trial expired and they haven't paid."

    def handle(self, *args, **options):
        counter = 0

        # Find users whose trial expired a month ago and haven't paid.
        for user in User.objects.filter(
            last_payment=datetime.date(1900, 1, 1),
            upgraded_until__lt=datetime.date.today() - datetime.timedelta(days=30),
        ):
            images, _ = user.images.all().delete()
            print(
                f"Deleted {images} images for user {user.email} (trial ended on {user.upgraded_until})..."
            )
            counter += 1

        print(f"Processed {counter} users.")
