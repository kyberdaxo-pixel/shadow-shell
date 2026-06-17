from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import CyberProfile


@receiver(post_save, sender=User)
def create_cyber_profile(sender, instance, created, **kwargs):
    if created:
        CyberProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_cyber_profile(sender, instance, **kwargs):
    try:
        instance.cyber_profile.save()
    except CyberProfile.DoesNotExist:
        CyberProfile.objects.create(user=instance)