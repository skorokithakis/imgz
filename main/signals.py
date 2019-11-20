import datetime

from django.conf import settings
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import User


@receiver(pre_save, sender=User, dispatch_uid="user_signup")
def user_creation_signal(sender, instance, **kwargs):
    user = instance
    if user.id:
        # This user was already created and is just being saved, there's nothing to do.
        return

    user.upgraded_until = datetime.date.today() + datetime.timedelta(days=30)
    user.storage_space = 100 * settings.MB
