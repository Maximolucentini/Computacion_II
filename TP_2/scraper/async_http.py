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


class ContentTooLargeError(HttpError):
    """El contenido descargado excede el límite permitido."""
    pass


async def fetch_html(
    url: str, 
    session: aiohttp.ClientSession,
    max_size_mb: float = 10.0  # Límite por defecto: 10 MB
) -> Tuple[str, str]:
    """
    Descarga el HTML de `url` de forma asíncrona.

    Parámetros:
        url: URL a descargar (http/https)
        session: instancia compartida de aiohttp.ClientSession
        max_size_mb: tamaño máximo permitido en MB (default: 10 MB)

    Devuelve:
        (html, url_final) donde url_final es la URL luego de redirecciones.

    Lanza:
        HttpError en caso de problemas de red o HTTP.
        ContentTooLargeError si el contenido excede max_size_mb.
    """
    max_size_bytes = int(max_size_mb * 1024 * 1024)
    
    try:
        async with session.get(url) as resp:
            resp.raise_for_status()
            
            # Verificar Content-Length si está disponible
            content_length = resp.headers.get('Content-Length')
            if content_length:
                try:
                    size = int(content_length)
                    if size > max_size_bytes:
                        raise ContentTooLargeError(
                            f"El contenido es demasiado grande: {size / 1024 / 1024:.2f} MB "
                            f"(límite: {max_size_mb} MB)"
                        )
                except ValueError:
                    pass  # Content-Length no es un número válido
            
            # Descargar con límite de tamaño
            text = await _read_with_limit(resp, max_size_bytes)
            
            return text, str(resp.url)

    except ContentTooLargeError:
        raise  # Re-lanzar sin modificar
    except asyncio.TimeoutError as exc:
        raise HttpError(f"Timeout al acceder a {url}") from exc
    except aiohttp.ClientError as exc:
        raise HttpError(f"Error HTTP al acceder a {url}: {exc}") from exc


async def _read_with_limit(
    response: aiohttp.ClientResponse, 
    max_size: int
) -> str:
    """
    Lee el contenido de la respuesta con un límite de tamaño.
    
    Lanza ContentTooLargeError si se excede el límite.
    """
    chunks = []
    total_size = 0
    
    async for chunk in response.content.iter_chunked(8192):  # 8 KB por chunk
        total_size += len(chunk)
        
        if total_size > max_size:
            raise ContentTooLargeError(
                f"El contenido excede el límite de {max_size / 1024 / 1024:.2f} MB"
            )
        
        chunks.append(chunk)
    
    # Decodificar todo el contenido
    full_content = b''.join(chunks)
    
    # Intentar detectar la codificación
    try:
        encoding = response.get_encoding()
    except RuntimeError:
    # Cuando el cuerpo no fue leído completo, get_encoding()
    # lanza RuntimeError. Usamos utf-8 por defecto y luego
    # aplicamos los fallbacks manuales.
        encoding = 'utf-8'

    try:
        return full_content.decode(encoding)
    except (UnicodeDecodeError, LookupError):
    # Fallback a utf-8 y luego latin-1
        try:
            return full_content.decode('utf-8')
        except UnicodeDecodeError:
            return full_content.decode('latin-1', errors='replace')
