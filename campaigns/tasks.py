import qrcode
import io
import os
from django.conf import settings
from django.core.files.base import ContentFile
from campaigns.models import Placement
from common.models import File
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO

import time
from PIL import UnidentifiedImageError
import logging

logger = logging.getLogger(__name__)


def wait_for_file_access(file_field, retries=5, delay=0.5):
    """
    Wait until the FileField's underlying file is ready for access.

    Args:
        file_field: Django FileField (e.g. model.qr_code or model.featured_image)
        retries: number of attempts before giving up
        delay: seconds between retries
    Returns:
        PIL Image object if successful, None if failed
    """
    for attempt in range(retries):
        try:
            if not file_field or not file_field.file:
                raise FileNotFoundError("File field is empty.")
            return Image.open(file_field.file).convert("RGBA" if file_field.name.endswith(".png") else "RGB")
        except (FileNotFoundError, UnidentifiedImageError, ValueError):
            time.sleep(delay)
    return None


def generate_donation_card(placement_id):
    """
    Generate a donation card with a styled layout.

    - Resize campaign's featured image to HD (1920px width)
    - Place QR code centered in the last third of the image
    - Draw "Scan untuk donasi" above QR code inside a rounded white box
    - Compress final image as JPEG and save to File model
    """

    try:
        placement = Placement.objects.select_related("campaign__featured_image", "qr_code").get(pk=placement_id)
        if not placement.campaign.featured_image or not placement.qr_code:
            return

        # Resize featured image to HD
        featured = wait_for_file_access(placement.campaign.featured_image)
        target_width = 1920
        aspect_ratio = featured.height / featured.width
        target_height = int(target_width * aspect_ratio)
        featured = featured.resize((target_width, target_height), Image.LANCZOS)

        # Load QR
        qr = wait_for_file_access(placement.qr_code)

        # Prepare canvas
        canvas = Image.new("RGB", featured.size, "white")
        canvas.paste(featured, (0, 0))
        draw = ImageDraw.Draw(canvas)

        # Layout and size definitions
        col_w = target_width // 3
        margin = int(target_height * 0.15)
        qr_max = target_height - 2 * margin
        qr.thumbnail((col_w, qr_max), Image.LANCZOS)

        # Font
        try:
            font_path = os.path.join(settings.BASE_DIR, "assets", "fonts", "dejavu-sans-boldttf")
            font_size = int(target_height * 0.04)
            font = ImageFont.truetype(font_path, font_size)
        except IOError:
            font = ImageFont.load_default()

        text = "Scan untuk donasi"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]

        # Calculate box position
        block_w = max(text_w, qr.width) + 60
        block_h = text_h + qr.height + 40
        block_x = 2 * col_w + (col_w - block_w) // 2
        block_y = (target_height - block_h) // 2

        # shadow config
        radius = 25
        shadow_offset = (8, 8)
        shadow_blur = 6
        shadow_alpha = 80  # softer transparency

        # Create larger canvas for shadow to allow blur
        expanded_w = block_w + shadow_blur * 5
        expanded_h = block_h + shadow_blur * 5

        shadow = Image.new("RGBA", (expanded_w, expanded_h), (0, 0, 0, 0))
        shadow_mask = Image.new("L", (expanded_w, expanded_h), 0)
        draw_shadow = ImageDraw.Draw(shadow_mask)
        draw_shadow.rounded_rectangle(
            [shadow_blur, shadow_blur, shadow_blur + block_w, shadow_blur + block_h],
            radius=radius,
            fill=shadow_alpha  # softer alpha mask
        )
        shadow.putalpha(shadow_mask)
        shadow = shadow.filter(ImageFilter.GaussianBlur(shadow_blur))

        # Paste shadow
        shadow_x = block_x + shadow_offset[0] - shadow_blur
        shadow_y = block_y + shadow_offset[1] - shadow_blur
        canvas.paste(shadow, (shadow_x, shadow_y), shadow)

        # White box on top
        box = Image.new("RGBA", (block_w, block_h), (255, 255, 255, 255))
        box_mask = Image.new("L", (block_w, block_h), 0)
        draw_box = ImageDraw.Draw(box_mask)
        draw_box.rounded_rectangle([0, 0, block_w, block_h], radius, fill=255)
        canvas.paste(box, (block_x, block_y), box_mask)

        # Draw text
        text_x = block_x + (block_w - text_w) // 2
        text_y = block_y + 20
        draw.text((text_x, text_y), text, fill="black", font=font)

        # Paste QR
        qr_x = block_x + (block_w - qr.width) // 2
        qr_y = text_y + text_h + 20
        canvas.paste(qr, (qr_x, qr_y), mask=qr)

        # Save to JPEG
        buffer = BytesIO()
        canvas.save(buffer, format="JPEG", quality=85, optimize=True)
        buffer.seek(0)

        filename = f"donation_card_{placement.external_id}.jpg"
        file = File.objects.create(name=filename)
        file.file.save(filename, ContentFile(buffer.getvalue()), save=True)
        buffer.close()

        placement.donation_card = file
        placement.save(update_fields=["donation_card"])

        logger.info(f"Donation card created: {placement.donation_card.file.url}")
        return placement.donation_card.file.url


    except Placement.DoesNotExist:
        pass


def generate_qr_for_placement(placement_id):
    """
    Generate a QR code for a placement and save it as a File instance.
    The file is then linked via ForeignKey to placement.qr_code.

    Also checks if donation card image should be regenerated.
    """
    try:
        placement = Placement.objects.select_related('campaign__featured_image', 'qr_code').get(id=placement_id)

        # Build URL for QR code
        default_url = f"https://jadwalshalat.net/donation/{placement.external_id}"
        url = placement.url or default_url

        if not placement.url:
            placement.url = default_url
            placement.save(update_fields=["url"])

        # Generate QR code
        qr = qrcode.make(url)
        buffer = io.BytesIO()
        qr.save(buffer, format='PNG')
        buffer.seek(0)

        filename = f"placement_qr_{placement.external_id}.png"

        file = File.objects.create(name=filename)
        file.file.save(filename, ContentFile(buffer.getvalue()), save=True)
        buffer.close()

        placement.qr_code = file
        placement.save(update_fields=['qr_code'])

        logger.info(f"QR Code created: {placement.qr_code.file.url}")
        return placement.donation_card.file.url


    except Placement.DoesNotExist:
        pass

