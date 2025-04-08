from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django_q.tasks import async_task
from campaigns.models import Placement, Campaign
from campaigns.tasks import generate_qr_for_placement, generate_donation_card
from copy import deepcopy


# ==========================
# Placement Signal
# ==========================

@receiver(pre_save, sender=Placement)
def cache_previous_placement_state(sender, instance, **kwargs):
    """
    Caches relevant fields from the previous Placement instance before saving.
    """
    if not instance.pk:
        instance._previous_url = None
        instance._previous = None
        return

    try:
        previous = Placement.objects.select_related('campaign__featured_image', 'qr_code').get(pk=instance.pk)
        instance._previous_url = previous.url
        instance._previous = deepcopy(previous)
    except Placement.DoesNotExist:
        instance._previous_url = None
        instance._previous = None


@receiver(post_save, sender=Placement)
def run_post_save_tasks_for_placement(sender, instance, created, **kwargs):
    """
    Handles post-save actions for Placement:
    - Generate QR code if missing or URL changed.
    - Generate donation card if created or if relevant field changed.
    """
    url_changed = hasattr(instance, '_previous_url') and instance._previous_url != instance.url
    previous = getattr(instance, '_previous', None)

    if instance.qr_code is None or url_changed:
        async_task(generate_qr_for_placement, instance.id)

    should_generate_card = created
    if not created and previous:
        should_generate_card = (
            previous.qr_code != instance.qr_code or
            previous.campaign.featured_image != instance.campaign.featured_image or 
            url_changed
        )

    if should_generate_card:
        async_task(generate_donation_card, instance.id)


# ==========================
# Campaign Signal
# ==========================

@receiver(pre_save, sender=Campaign)
def cache_previous_campaign_featured_image(sender, instance, **kwargs):
    """
    Cache the previous featured_image of a campaign before save,
    so we can detect if it changed in post_save.
    """
    if not instance.pk:
        instance._previous_featured_image = None
        return

    try:
        previous = Campaign.objects.only('featured_image').get(pk=instance.pk)
        instance._previous_featured_image = previous.featured_image
    except Campaign.DoesNotExist:
        instance._previous_featured_image = None


@receiver(post_save, sender=Campaign)
def trigger_donation_card_on_campaign_change(sender, instance, **kwargs):
    """
    If campaign.featured_image is updated, regenerate donation cards for all placements.
    """
    previous = getattr(instance, '_previous_featured_image', None)
    if previous != instance.featured_image:
        # Featured image changed → trigger donation card regen for each placement
        for placement in instance.placements.all():
            async_task(generate_donation_card, placement.id)


@receiver(post_save, sender=Campaign)
def create_default_placement(sender, instance, created, **kwargs):
    """
    Automatically create a default placement when a new campaign is created.
    """
    if created:
        Placement.objects.create(
            campaign=instance,
            name="Default Placement",
            created_by=instance.organizer
        )