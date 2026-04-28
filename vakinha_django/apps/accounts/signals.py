from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile


@receiver(post_save, sender=User)
def user_profile_handler(sender, instance, created, **kwargs):
    """Create or save user profile when user is saved."""
    if created:
        UserProfile.objects.create(user=instance)
    else:
        # Save profile if it exists
        if hasattr(instance, "profile"):
            instance.profile.save()
