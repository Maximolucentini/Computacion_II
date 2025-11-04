"""
processor/screenshot.py

Generación de screenshot de una página web.

- Intenta usar Selenium (Chrome headless).
- Si falla (no hay driver, error, etc.), genera una imagen placeholder
  con Pillow para no romper el flujo.
"""

from __future__ import annotations

import base64
import io
import logging
import time
from typing import Optional

from PIL import Image, ImageDraw, ImageFont


def generate_screenshot(url: str, width: int = 1280, height: int = 720) -> Optional[str]:
    """
    Devuelve un PNG en base64 con el screenshot de `url`.
    Si Selenium no está disponible o algo falla, devuelve un placeholder.

    La idea es cumplir con:
        "screenshot": "base64_encoded_image"
    """
    logger = logging.getLogger(__name__)

    # Intentar Selenium sólo si está instalado
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.common.exceptions import WebDriverException
    except Exception:  
        webdriver = None
        ChromeOptions = None  
        WebDriverException = Exception  

    if webdriver is not None and ChromeOptions is not None:
        try:
            options = ChromeOptions()
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-gpu")
            options.add_argument(f"--window-size={width},{height}")

            driver = webdriver.Chrome(options=options)
            try:
                driver.set_window_size(width, height)
                driver.get(url)
                # Esperar un poquito para que cargue algo de contenido
                time.sleep(2.0)
                png_bytes = driver.get_screenshot_as_png()
                return base64.b64encode(png_bytes).decode("ascii")
            finally:
                driver.quit()
        except WebDriverException as exc:  # type: ignore[misc]
            logger.warning("Error al usar Selenium, se usará placeholder: %s", exc)
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error inesperado con Selenium, se usará placeholder: %s", exc)

    # Fallback: imagen simple con texto
    return _generate_placeholder_image(url, width, height)


def _generate_placeholder_image(url: str, width: int, height: int) -> str:
    """
    Genera una imagen PNG simple con el texto de la URL.
    Devuelve la imagen en base64 (string).
    """
    img = Image.new("RGB", (width, height), color=(30, 30, 30))
    draw = ImageDraw.Draw(img)
    font = ImageFont.load_default()

    text = f"Screenshot no disponible\n{url}"
    draw.multiline_text((10, 10), text, fill=(220, 220, 220), font=font)

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    data = buffer.getvalue()
    return base64.b64encode(data).decode("ascii")
