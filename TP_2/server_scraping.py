#!/usr/bin/env python3
"""
server_scraping.py

Servidor de Scraping Web Asíncrono (Parte A + Bonus):

- Asyncio + aiohttp.web
- Scraping asíncrono de páginas web
- Comunicación asíncrona con el servidor de procesamiento (Parte B)
- Rate limiting por dominio (Opción 2)
- Caché con TTL de resultados (Opción 2)
- Sistema de cola de tareas con task_id (Opción 1):
    * POST /tasks           -> crea tarea, devuelve task_id
    * GET  /status/{id}     -> estado de la tarea
    * GET  /result/{id}     -> resultado cuando está lista
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

import aiohttp
from aiohttp import web

from scraper.async_http import fetch_html, HttpError
from scraper.html_parser import extract_page_data
from common.protocol import send_message_async, read_message_async

# Dirección del servidor de procesamiento (Parte B)
PROCESSING_SERVER_IP = "127.0.0.1"
PROCESSING_SERVER_PORT = 9000

SCRAPING_TIMEOUT_SECONDS = 30
DEFAULT_CACHE_TTL_SECONDS = 3600  # 1 hora
DEFAULT_MAX_HTML_SIZE_MB = 10.0

class ScrapingError(Exception):
    """Error de alto nivel durante el scraping."""
    pass


@dataclass
class TaskInfo:
    """
    Representa una tarea en la cola (Bonus Opción 1).

    status:
        - pending
        - scraping
        - processing
        - completed
        - failed
    """
    url: str
    status: str = "pending"
    created_at: datetime = field(default_factory=datetime.utcnow)
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ScraperService:
    """
    Servicio de scraping que encapsula:
    - Cliente HTTP asíncrono (aiohttp)
    - Límite de concurrencia (semáforo)
    - Comunicación con el servidor de procesamiento (Parte B)
    - Rate limiting por dominio (Opción 2)
    - Caché de resultados con TTL (Opción 2)
    - Cola de tareas con IDs (Opción 1)
    """

    def __init__(
        self,
        workers: int,
        rate_limit_per_minute: Optional[int] = None,
        cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS,
        max_html_size_mb: float = DEFAULT_MAX_HTML_SIZE_MB,
    ) -> None:
        self._workers = max(1, int(workers))
        self._semaphore = asyncio.Semaphore(self._workers)
        self._session: Optional[aiohttp.ClientSession] = None
        self._max_html_size_mb = max_html_size_mb

        # Rate limiting
        self._rate_limit_per_minute = rate_limit_per_minute if rate_limit_per_minute and rate_limit_per_minute > 0 else None
        # dominio -> lista de timestamps (segundos) de las últimas requests "reales"
        self._domain_requests: Dict[str, list[float]] = {}

        # Caché: url -> (timestamp, resultado_json)
        self._cache_ttl_seconds = max(0, cache_ttl_seconds)
        self._cache: Dict[str, Tuple[float, Dict[str, Any]]] = {}

        # Cola de tareas
        self._tasks: Dict[str, TaskInfo] = {}

    async def start(self) -> None:
        """
        Inicializa el ClientSession con timeout global de scraping.
        Debe llamarse al arrancar el servidor.
        """
        timeout = aiohttp.ClientTimeout(total=SCRAPING_TIMEOUT_SECONDS)
        self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        """
        Cierra el ClientSession al apagar el servidor.
        """
        if self._session is not None:
            await self._session.close()

    # ------------------------------------------------------------------
    #  MODO SIN COLA (endpoint /scrape) - Parte A clásica
    # ------------------------------------------------------------------

    async def handle_url(self, url: str) -> Dict[str, Any]:
        """
        Punto de entrada principal "sin cola": recibe una URL y devuelve
        el JSON completo con scraping_data + processing_data.
        """
        result = await self._run_pipeline(url, job=None)
        return result

    # ------------------------------------------------------------------
    #  MODO CON COLA (Bonus opción 1)
    # ------------------------------------------------------------------

    def create_task(self, url: str) -> str:
        """
        Crea una nueva tarea en estado 'pending' y lanza el procesamiento
        en segundo plano usando asyncio.create_task.

        Devuelve el task_id.
        """
        self._validate_url(url)

        task_id = uuid.uuid4().hex
        task = TaskInfo(url=url)
        self._tasks[task_id] = task

        # Lanzamos la corrutina que hará el trabajo real
        asyncio.create_task(self._run_task(task_id))

        return task_id

    async def _run_task(self, task_id: str) -> None:
        """
        Corrutina que ejecuta el pipeline completo para una tarea, actualizando
        su estado en cada fase.

        Estados: pending -> scraping -> processing -> completed/failed
        """
        task = self._tasks.get(task_id)
        if task is None:
            return  # puede haber sido borrada, etc.

        try:
            await self._run_pipeline(task.url, job=task)
        except (ScrapingError, HttpError) as exc:
            task.status = "failed"
            task.error = str(exc)
        except Exception as exc:  # noqa: BLE001
            logging.exception("Error inesperado procesando tarea %s", task_id)
            task.status = "failed"
            task.error = str(exc)

    def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        return self._tasks.get(task_id)

    # ------------------------------------------------------------------
    #  LÓGICA COMÚN: pipeline scraping + procesamiento (A+B)
    # ------------------------------------------------------------------

    async def _run_pipeline(self, url: str, job: Optional[TaskInfo]) -> Dict[str, Any]:
        """
        Ejecuta todo el pipeline:
            - Cache lookup
            - Rate limiting (si no hay caché)
            - Scraping HTML
            - Parsing
            - Llamada al servidor de procesamiento (Parte B)
        """
        self._validate_url(url)

        if self._session is None:
            raise RuntimeError("ScraperService no inicializado. Falta llamar a start().")

        now_ts = time.time()
        cache_key = url

        # 1) Caché (Opción 2)
        if self._cache_ttl_seconds > 0:
            cached = self._cache.get(cache_key)
            if cached is not None:
                ts, cached_result = cached
                if (now_ts - ts) < self._cache_ttl_seconds:
                    # Resultado cacheado válido
                    if job is not None:
                        job.status = "completed"
                        job.result = cached_result
                    return cached_result

        # 2) Rate limiting (Opción 2) -> solo si NO usamos caché
        self._check_rate_limit(url)

        started_at = datetime.utcnow()

        async with self._semaphore:
            # 3) Scraping HTML
            if job is not None:
                job.status = "scraping"

            html, final_url = await fetch_html(url, session=self._session,max_size_mb=self._max_html_size_mb)

            # 4) Parsing HTML
            scraping_data = extract_page_data(html, base_url=final_url)

            # 5) Procesamiento pesado en Servidor B
            if job is not None:
                job.status = "processing"

            processing_data, processing_status = await self._request_processing_server(
                final_url,
                scraping_data,
                html,
            )

        timestamp = started_at.replace(microsecond=0).isoformat() + "Z"
        status = "success"

        result: Dict[str, Any] = {
            "url": final_url,
            "timestamp": timestamp,
            "scraping_data": scraping_data,
            "processing_data": processing_data,
            "status": status,
            "processing_status": processing_status,
        }

        # Guardar en caché (Opción 2)
        if self._cache_ttl_seconds > 0:
            self._cache[cache_key] = (now_ts, result)

        if job is not None:
            job.status = "completed"
            job.result = result

        return result

    # ------------------------------------------------------------------
    #  Rate limiting y validación URL
    # ------------------------------------------------------------------

    def _validate_url(self, url: str) -> None:
        """
        Valida mínimamente la URL (esquema http/https y host presente).
        """
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            raise ScrapingError(f"URL inválida: {url!r}")

    def _check_rate_limit(self, url: str) -> None:
        """
        Aplica rate limiting por dominio (Opción 2).
        Máximo N requests/minuto al mismo dominio.
        """
        if self._rate_limit_per_minute is None or self._rate_limit_per_minute <= 0:
            return

        parsed = urlparse(url)
        domain = parsed.netloc
        if not domain:
            return

        now = time.time()
        one_minute_ago = now - 60.0

        timestamps = self._domain_requests.setdefault(domain, [])

        # Limpiar timestamps viejos (> 1 minuto)
        while timestamps and timestamps[0] < one_minute_ago:
            timestamps.pop(0)

        if len(timestamps) >= self._rate_limit_per_minute:
            raise ScrapingError(
                f"Rate limit excedido para dominio {domain!r}: "
                f"{len(timestamps)} requests en el último minuto"
            )

        # Registramos la nueva request real (sin caché)
        timestamps.append(now)

    # ------------------------------------------------------------------
    #  Comunicación con Servidor B (asyncio + sockets)
    # ------------------------------------------------------------------

    async def _request_processing_server(
        self,
        url: str,
        scraping_data: Dict[str, Any],
        html: str,
    ) -> tuple[Dict[str, Any], str]:
        """
        Se comunica con el servidor de procesamiento (Parte B) usando
        sockets TCP asíncronos (asyncio.open_connection).

        Envía:
            - url
            - scraping_data
            - html (para análisis avanzado, Bonus Opción 3)

        Devuelve:
            (processing_data, processing_status)
        """
        empty_processing: Dict[str, Any] = {
            "screenshot": None,
            "performance": None,
            "thumbnails": [],
            "advanced": None,
        }

        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(PROCESSING_SERVER_IP, PROCESSING_SERVER_PORT),
                timeout=5,
            )

            request_payload: Dict[str, Any] = {
                "action": "process_page",
                "url": url,
                "scraping_data": scraping_data,
                "html": html,
            }

            await send_message_async(writer, request_payload)
            response = await asyncio.wait_for(
                read_message_async(reader),
                timeout=SCRAPING_TIMEOUT_SECONDS,
            )

            writer.close()
            await writer.wait_closed()

            if isinstance(response, dict) and response.get("status") == "success":
                raw_processing = response.get("processing_data", {}) or {}
                result: Dict[str, Any] = {
                    "screenshot": raw_processing.get("screenshot"),
                    "performance": raw_processing.get("performance"),
                    "thumbnails": raw_processing.get("thumbnails", []),
                    "advanced": raw_processing.get("advanced"),
                }
                return result, "success"

            logging.warning("Respuesta no exitosa del servidor de procesamiento: %r", response)
            return empty_processing, "failed"

        except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as exc:
            logging.error("No se pudo contactar al servidor de procesamiento: %s", exc)
            return empty_processing, "failed"


# ----------------------------------------------------------------------
#  Handlers HTTP (aiohttp.web)
# ----------------------------------------------------------------------


async def scrape_handler(request: web.Request) -> web.Response:
    """
    Handler para el endpoint /scrape

    Ejemplos:
        GET  /scrape?url=https://example.com
        POST /scrape  con JSON: {"url": "https://example.com"}

    Modo clásico: espera el scraping y procesamiento y devuelve todo el JSON.
    """
    service: ScraperService = request.app["scraper_service"]

    url = request.rel_url.query.get("url")
    if not url and request.method == "POST":
        try:
            data = await request.json()
            url = data.get("url")
        except Exception:
            url = None

    if not url:
        return web.json_response(
            {"status": "error", "error": "Parámetro 'url' requerido"},
            status=400,
        )

    try:
        result = await service.handle_url(url)
        return web.json_response(result, status=200)

    except ScrapingError as exc:
        logging.warning("Error de validación de URL: %s", exc)
        return web.json_response(
            {"status": "error", "error": str(exc)},
            status=400,
        )
    except HttpError as exc:
        logging.warning("Error al hacer scraping: %s", exc)
        status_code = 413 if "demasiado grande" in str(exc).lower() else 502
        return web.json_response(
            {"status": "error", "error": str(exc)},
            status=status_code,
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Error inesperado en /scrape")
        return web.json_response(
            {"status": "error", "error": f"Error interno del servidor: {exc}"},
            status=500,
        )


async def enqueue_task_handler(request: web.Request) -> web.Response:
    """
    Bonus Opción 1: crea una tarea en la cola y devuelve un task_id.

    Uso:
        POST /tasks
        body JSON: {"url": "https://example.com"}

        Respuesta:
            {"task_id": "...", "status": "pending"}
    """
    service: ScraperService = request.app["scraper_service"]

    url = None
    try:
        data = await request.json()
        url = data.get("url")
    except Exception:
        url = None

    if not url:
        return web.json_response(
            {"status": "error", "error": "Campo JSON 'url' requerido"},
            status=400,
        )

    try:
        task_id = service.create_task(url)
    except ScrapingError as exc:
        return web.json_response(
            {"status": "error", "error": str(exc)},
            status=400,
        )
    except Exception as exc:  # noqa: BLE001
        logging.exception("Error inesperado al crear tarea")
        return web.json_response(
            {"status": "error", "error": f"Error interno al crear tarea: {exc}"},
            status=500,
        )

    return web.json_response(
        {"task_id": task_id, "status": "pending"},
        status=202,
    )


async def task_status_handler(request: web.Request) -> web.Response:
    """
    Bonus Opción 1: consulta el estado de una tarea.

    GET /status/{task_id}
    """
    service: ScraperService = request.app["scraper_service"]
    task_id = request.match_info.get("task_id", "")

    task = service.get_task_info(task_id)
    if task is None:
        return web.json_response(
            {"status": "error", "error": "Task no encontrada"},
            status=404,
        )

    data: Dict[str, Any] = {
        "task_id": task_id,
        "status": task.status,
        "url": task.url,
        "created_at": task.created_at.replace(microsecond=0).isoformat() + "Z",
    }
    if task.status == "failed" and task.error:
        data["error"] = task.error

    return web.json_response(data, status=200)


async def task_result_handler(request: web.Request) -> web.Response:
    """
    Bonus Opción 1: obtiene el resultado de una tarea.

    GET /result/{task_id}
    """
    service: ScraperService = request.app["scraper_service"]
    task_id = request.match_info.get("task_id", "")

    task = service.get_task_info(task_id)
    if task is None:
        return web.json_response(
            {"status": "error", "error": "Task no encontrada"},
            status=404,
        )

    if task.status != "completed":
        return web.json_response(
            {
                "task_id": task_id,
                "status": task.status,
                "url": task.url,
                "message": "La tarea aún no está completada",
            },
            status=202,
        )

    return web.json_response(
        {
            "task_id": task_id,
            "status": "completed",
            "url": task.url,
            "result": task.result,
        },
        status=200,
    )


async def health_handler(_: web.Request) -> web.Response:
    """
    Endpoint simple de salud: GET /
    """
    return web.json_response({"status": "ok"})


# ----------------------------------------------------------------------
#  Arranque del servidor
# ----------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Servidor de Scraping Web Asíncrono"
    )
    parser.add_argument(
        "-i",
        "--ip",
        required=True,
        help="Dirección de escucha (soporta IPv4/IPv6)",
    )
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        type=int,
        help="Puerto de escucha",
    )
    parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=4,
        help="Número de workers concurrentes (default: 4)",
    )
    parser.add_argument(
        "-r",
        "--rate-limit",
        type=int,
        default=60,
        help="Máximo de requests por minuto por dominio (0 = sin límite, default: 60)",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=DEFAULT_CACHE_TTL_SECONDS,
        help="TTL de la caché en segundos (0 = sin caché, default: 3600)",
    )
    parser.add_argument(
        "--max-html-size",
        type=float,
        default=DEFAULT_MAX_HTML_SIZE_MB,
        help="Tamaño máximo de HTML en MB (default: 10.0)",
    ) 
    return parser.parse_args()


def create_app(
    workers: int,
    rate_limit: int,
    cache_ttl: int,
    max_html_size: float,
) -> web.Application:
    app = web.Application()
    scraper_service = ScraperService(
        workers=workers,
        rate_limit_per_minute=rate_limit,
        cache_ttl_seconds=cache_ttl,
        max_html_size_mb=max_html_size,
    )
    app["scraper_service"] = scraper_service

    # Rutas
    app.router.add_get("/", health_handler)

    # Parte A (modo sin cola)
    app.router.add_get("/scrape", scrape_handler)
    app.router.add_post("/scrape", scrape_handler)

    # Bonus Opción 1 (cola de tareas)
    app.router.add_post("/tasks", enqueue_task_handler)
    app.router.add_get("/status/{task_id}", task_status_handler)
    app.router.add_get("/result/{task_id}", task_result_handler)

    # Hooks de inicio/cierre
    async def on_startup(app: web.Application) -> None:
        service: ScraperService = app["scraper_service"]
        await service.start()
        logging.info("ScraperService inicializado")

    async def on_cleanup(app: web.Application) -> None:
        service: ScraperService = app["scraper_service"]
        await service.close()
        logging.info("ScraperService cerrado")

    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)

    return app


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    app = create_app(
        workers=args.workers,
        rate_limit=args.rate_limit,
        cache_ttl=args.cache_ttl,
        max_html_size=args.max_html_size,
    )

    web.run_app(app, host=args.ip, port=args.port)


if __name__ == "__main__":
    main()
