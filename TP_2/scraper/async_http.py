"""
async_http.py
Cliente HTTP asíncrono usando aiohttp.

Responsable de descargar el HTML sin bloquear el event loop.
"""

import asyncio
from typing import Tuple

import aiohttp


class HttpError(Exception):
    """Error de red o HTTP al hacer la petición."""
    pass


async def fetch_html(url: str, session: aiohttp.ClientSession) -> Tuple[str, str]:
    """
    Descarga el HTML de `url` de forma asíncrona.

    Parámetros:
        url: URL a descargar (http/https)
        session: instancia compartida de aiohttp.ClientSession

    Devuelve:
        (html, url_final) donde url_final es la URL luego de redirecciones.

    Lanza:
        HttpError en caso de problemas de red o HTTP.
    """
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()          # error si status >= 400
            text = await resp.text()         # resp.text() también es asíncrono
            return text, str(resp.url)       # resp.url puede cambiar por redirecciones

    except asyncio.TimeoutError as exc:
        raise HttpError(f"Timeout al acceder a {url}") from exc
    except aiohttp.ClientError as exc:
        raise HttpError(f"Error HTTP al acceder a {url}: {exc}") from exc
