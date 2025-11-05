"""
client.py

Cliente de prueba - Sistema de Scraping y Análisis Web Distribuido.

- El cliente SOLO se comunica con el Servidor A (asyncio, HTTP).
- El Servidor A internamente coordina con el Servidor B de procesamiento.
- Desde la perspectiva del cliente, todo ocurre en un único servidor.

Uso:

    # Ayuda
    python client.py -h

    # Ejemplo IPv4
    python client.py -i 127.0.0.1 -p 8000 https://example.com

    # Ejemplo IPv6 (localhost)
    python client.py -i ::1 -p 8000 https://example.com https://www.python.org

El cliente:
    - Recibe una lista de URLs a scrapear.
    - Hace requests HTTP al endpoint /scrape del Servidor A usando aiohttp.
    - Muestra un resumen de la respuesta por cada URL (estado, título, métricas).
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Dict, List, Tuple

import aiohttp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cliente de prueba para el Servidor de Scraping (Parte C)"
    )
    parser.add_argument(
        "-i",
        "--ip",
        required=True,
        help="IP o hostname del Servidor A (soporta IPv4/IPv6)",
    )
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        type=int,
        help="Puerto del Servidor A",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=30.0,
        help="Timeout total por request en segundos (default: 30)",
    )
    parser.add_argument(
        "-c",
        "--concurrency",
        type=int,
        default=4,
        help="Máximo de requests concurrentes hacia el Servidor A (default: 4)",
    )
    parser.add_argument(
        "urls",
        nargs="+",
        help="URLs de páginas web a scrapear",
    )
    return parser.parse_args()


def build_base_url(ip: str, port: int, scheme: str = "http") -> str:
    """
    Construye la URL base del servidor A, manejando IPv4 e IPv6.

    Ej:
        ip='127.0.0.1', port=8000 -> 'http://127.0.0.1:8000'
        ip='::1',       port=8000 -> 'http://[::1]:8000'
    """
    # Si tiene ':' asumimos IPv6 y la envolvemos en corchetes
    if ":" in ip and not ip.startswith("["):
        host = f"[{ip}]"
    else:
        host = ip
    return f"{scheme}://{host}:{port}"


async def fetch_scrape(
    session: aiohttp.ClientSession,
    base_url: str,
    target_url: str,
) -> Tuple[str, int | None, Dict[str, Any] | None, str | None]:
    """
    Hace una request al Servidor A:

        GET {base_url}/scrape?url={target_url}

    Devuelve:
        (target_url, status_http, data_json, error_str)

    Donde:
        - data_json es el JSON que devuelve el servidor A
        - error_str tiene el mensaje de error si algo falla
    """
    scrape_endpoint = f"{base_url}/scrape"
    params = {"url": target_url}

    try:
        async with session.get(scrape_endpoint, params=params) as resp:
            status = resp.status
            # Intentamos leer JSON siempre; si falla lo manejamos abajo
            try:
                data = await resp.json()
            except Exception as exc:  # noqa: BLE001
                return target_url, status, None, f"Error parseando JSON: {exc}"
            return target_url, status, data, None

    except asyncio.TimeoutError:
        return target_url, None, None, "Timeout al esperar respuesta del Servidor A"
    except aiohttp.ClientError as exc:
        return target_url, None, None, f"Error de red al hablar con el Servidor A: {exc}"


def print_result(
    target_url: str,
    status_http: int | None,
    data: Dict[str, Any] | None,
    error: str | None,
) -> None:
    """
    Imprime un resumen legible del resultado para una URL.
    No muestra nada del Servidor B: todo se ve como si fuera un solo servicio.
    """
    print("=" * 80)
    print(f"URL objetivo: {target_url}")

    if error is not None:
        print(f"Resultado: ERROR")
        print(f"Detalle: {error}")
        return

    if data is None:
        print("Resultado: ERROR (sin datos y sin mensaje específico)")
        return

    print(f"HTTP status: {status_http}")
    status_global = data.get("status")
    print(f"Estado del sistema: {status_global}")

    if status_global != "success":
        # Mostramos el error devuelto por el servidor si existe
        error_msg = data.get("error", "Error desconocido")
        print(f"Mensaje de error del servidor: {error_msg}")
        return

    # --- Scraping data ---
    scraping = data.get("scraping_data", {}) or {}
    processing = data.get("processing_data", {}) or {}

    title = scraping.get("title", "")
    num_links = len(scraping.get("links", []) or [])
    images_count = scraping.get("images_count")

    print("\n[SCRAPING]")
    print(f"- Título de la página: {title!r}")
    print(f"- Cantidad de links encontrados: {num_links}")
    if images_count is not None:
        print(f"- Cantidad de imágenes (images_count): {images_count}")

    # --- Meta tags (solo algunas claves importantes) ---
    meta = scraping.get("meta_tags", {}) or {}
    if meta:
        desc = meta.get("description", "")
        keywords = meta.get("keywords", "")
        og_title = meta.get("og:title", "")
        print("\n[Meta tags principales]")
        if desc:
            print(f"  description: {desc!r}")
        if keywords:
            print(f"  keywords: {keywords!r}")
        if og_title:
            print(f"  og:title: {og_title!r}")

    # --- Performance ---
    performance = processing.get("performance") or {}
    load_time = performance.get("load_time_ms")
    total_size = performance.get("total_size_kb")
    num_requests = performance.get("num_requests")

    print("\n[Procesamiento / Rendimiento]")
    print(f"- Tiempo de carga (ms): {load_time}")
    print(f"- Tamaño total HTML (KB): {total_size}")
    print(f"- Cantidad de requests (aprox.): {num_requests}")

    # --- Screenshot / Thumbnails (solo resumen, no imprimimos el base64) ---
    screenshot_b64 = processing.get("screenshot")
    thumbs = processing.get("thumbnails", []) or []

    print("\n[Imágenes procesadas]")
    print(f"- Screenshot disponible: {'sí' if screenshot_b64 else 'no'}")
    print(f"- Cantidad de thumbnails: {len(thumbs)}")

    
    # print("\n[JSON completo]")
    # print(json.dumps(data, indent=2, ensure_ascii=False))


async def main_async() -> None:
    args = parse_args()

    base_url = build_base_url(args.ip, args.port, scheme="http")

    timeout = aiohttp.ClientTimeout(total=args.timeout)
    connector = aiohttp.TCPConnector(limit=args.concurrency)

    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
        
        tasks = [
            fetch_scrape(session, base_url, url)
            for url in args.urls
        ]

        
        for coro in asyncio.as_completed(tasks):
            target_url, status_http, data, error = await coro
            print_result(target_url, status_http, data, error)

    print("=" * 80)
    print("Fin de la ejecución del cliente.")


def main() -> None:
    # Wrapper para poder llamar parse_args() dentro de main_async de forma limpia
    asyncio.run(main_async())


if __name__ == "__main__":
    main()