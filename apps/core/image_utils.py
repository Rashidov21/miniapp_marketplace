"""Resize and compress uploaded raster images for web (WebP preferred)."""
from __future__ import annotations

from io import BytesIO

from django.core.files.base import ContentFile

try:
    from PIL import Image, ImageOps
except ImportError:  # pragma: no cover
    Image = None
    ImageOps = None

# Product hero: mobile-friendly width, low-end devices
PRODUCT_MAX_SIDE = 800
SHOP_LOGO_MAX_SIDE = 400
WEBP_QUALITY = 78
JPEG_QUALITY_FALLBACK = 80


def _to_rgb(img: Image.Image) -> Image.Image:
    if img.mode == "LA":
        img = img.convert("RGBA")
    if img.mode == "P":
        img = img.convert("RGBA")
    if img.mode == "RGBA":
        background = Image.new("RGB", img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        return background
    if img.mode != "RGB":
        return img.convert("RGB")
    return img


def optimize_image_bytes(
    raw: bytes,
    *,
    max_side: int = PRODUCT_MAX_SIDE,
    webp_quality: int = WEBP_QUALITY,
) -> tuple[bytes, str]:
    """
    Resize (max side), strip EXIF by re-encoding, output WebP or JPEG.

    Returns (bytes, filename_suffix) where suffix is 'webp' or 'jpg'.
    """
    if not Image:
        return raw, "jpg"
    buf = BytesIO(raw)
    try:
        img = Image.open(buf)
    except OSError:
        return raw, "jpg"

    img = ImageOps.exif_transpose(img)
    img = _to_rgb(img)

    w, h = img.size
    if max(w, h) > max_side:
        ratio = max_side / float(max(w, h))
        img = img.resize((int(w * ratio), int(h * ratio)), Image.Resampling.LANCZOS)

    out = BytesIO()
    try:
        img.save(
            out,
            format="WEBP",
            quality=webp_quality,
            method=6,
        )
        return out.getvalue(), "webp"
    except Exception:
        out = BytesIO()
        img.save(out, format="JPEG", quality=JPEG_QUALITY_FALLBACK, optimize=True)
        return out.getvalue(), "jpg"


def file_to_optimized_content(
    django_file,
    *,
    basename: str,
    max_side: int = PRODUCT_MAX_SIDE,
) -> tuple[ContentFile, str]:
    """
    Read uploaded file, return ContentFile and storage name (basename + ext).
    """
    django_file.open("rb")
    try:
        raw = django_file.read()
    finally:
        django_file.close()

    data, ext = optimize_image_bytes(raw, max_side=max_side)
    name = f"{basename}.{ext}"
    return ContentFile(data, name=name), name
