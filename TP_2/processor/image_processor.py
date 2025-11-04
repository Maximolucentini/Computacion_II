"""
processor/image_processor.py

Descarga algunas imágenes de la página y genera thumbnails optimizados.

Devuelve una lista de strings base64 (PNG) para poner en:

    "thumbnails": ["base64_thumb1", "base64_thumb2", ...]
"""

from __future__ import annotations

import base64
import io
import logging
from typing import Any, Dict, List
from urllib.request import Request, urlopen

from PIL import Image

USER_AGENT = "TP2-Scraper-Images/1.0"


def generate_thumbnails(
    url: str,
    scraping_data: Dict[str, Any],
    max_images: int = 3,
    thumb_size: tuple[int, int] = (200, 200),
) -> List[str]:
    """
    Genera thumbnails para algunas imágenes de la página.

    Usa scraping_data.get("images", []) si está disponible.
    Si no hay imágenes, devuelve [].
    """
    logger = logging.getLogger(__name__)

    image_urls = scraping_data.get("images") or []
    if not isinstance(image_urls, list):
        image_urls = []

    thumbs: List[str] = []

    for img_url in image_urls[:max_images]:
        try:
            thumb_b64 = _download_and_resize(img_url, thumb_size)
            if thumb_b64 is not None:
                thumbs.append(thumb_b64)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error generando thumbnail para %s: %s", img_url, exc)

    return thumbs


def _download_and_resize(img_url: str, thumb_size: tuple[int, int]) -> str | None:
    """
    Descarga una imagen y genera un thumbnail PNG en base64.
    """
    req = Request(img_url, headers={"User-Agent": USER_AGENT})

    with urlopen(req, timeout=20.0) as resp:
        data = resp.read()

    image = Image.open(io.BytesIO(data))
    image = image.convert("RGB")
    image.thumbnail(thumb_size)

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("ascii")
