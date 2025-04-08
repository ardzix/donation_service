from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from campaigns.models import Placement
from campaigns.tasks import generate_qr_for_placement


@receiver(pre_save, sender=Placement)
def store_previous_url(sender, instance, **kwargs):
    """
    Store the previous URL before saving to compare in post_save.
    """
    if instance.pk:
        try:
            previous = Placement.objects.get(pk=instance.pk)
            instance._previous_url = previous.url
        except Placement.DoesNotExist:
            instance._previous_url = None

@receiver(post_save, sender=Placement)
def generate_qr_after_placement_saved(sender, instance, **kwargs):
    """
    Generate QR code if:
    - qr_code is not yet assigned
    - or URL has changed from its previous value
    """
    url_changed = (
        hasattr(instance, '_previous_url') and instance._previous_url != instance.url
    )
    if instance.qr_code is None or url_changed:
        async_task(generate_qr_for_placement, instance.id)
