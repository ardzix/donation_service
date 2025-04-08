import qrcode
import io
from django.core.files.base import ContentFile
from django_q.tasks import async_task
from campaigns.models import Placement
from common.models import File


def generate_qr_for_placement(placement_id):
    """
    Generate a QR code for a placement and save it as a File instance.
    The file is then linked via ForeignKey to placement.qr_code.
    """
    try:
        placement = Placement.objects.get(id=placement_id)

        default_url = f"https://jadwalshalat.net/donation/{placement.external_id}"
        url = placement.url or default_url

        # Save the default URL to placement if not already set
        if not placement.url:
            placement.url = default_url
            placement.save(update_fields=["url"])

        # Generate QR code
        qr = qrcode.make(url)
        buffer = io.BytesIO()
        qr.save(buffer, format='PNG')

        filename = f"placement_qr_{placement.external_id}.png"
        buffer.seek(0)

        # Save or update File object
        file, created = File.objects.get_or_create(
            name=filename
        )

        # Always update file content
        file.file.save(filename, ContentFile(buffer.getvalue()), save=True)
        buffer.close()

        # Assign to placement
        placement.qr_code = file
        placement.save(update_fields=['qr_code'])

    except Placement.DoesNotExist:
        pass
