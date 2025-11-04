#!/usr/bin/env python3
"""
server_processing.py

Servidor de Procesamiento Distribuido (Parte B + Bonus Opción 3).

- socketserver + multiprocessing (ProcessPoolExecutor)
- Opera como servidor TCP que recibe requests desde el Servidor A
- Tareas en pool de procesos:
    * Captura de screenshot
    * Análisis de rendimiento
    * Procesamiento de imágenes (thumbnails)
    * Análisis avanzado (tecnologías, SEO, JSON-LD, accesibilidad)
"""

from __future__ import annotations

import argparse
import concurrent.futures
import logging
import multiprocessing
import socket
import socketserver
from typing import Any, Dict

from common.protocol import read_message, send_message
from processor.screenshot import generate_screenshot
from processor.performance import analyze_performance
from processor.image_processor import generate_thumbnails
from processor.advanced_analysis import analyze_advanced


def process_page_task(
    url: str,
    scraping_data: Dict[str, Any],
    html: str = "",
) -> Dict[str, Any]:
    """
    Función que se ejecuta en un PROCESO del pool.

    Hace:
      - screenshot de la página
      - análisis de rendimiento
      - generación de thumbnails de imágenes
      - análisis avanzado (Bonus Opción 3)
    """
    screenshot_b64 = generate_screenshot(url)
    performance_data = analyze_performance(url)
    thumbnails = generate_thumbnails(url, scraping_data)
    advanced_data = analyze_advanced(url, scraping_data, html)

    return {
        "screenshot": screenshot_b64,
        "performance": performance_data,
        "thumbnails": thumbnails,
        "advanced": advanced_data,
    }


class ProcessingRequestHandler(socketserver.BaseRequestHandler):
    """
    Handler para cada conexión entrante desde el Servidor A.
    """

    def handle(self) -> None:  # type: ignore[override]
        logger = logging.getLogger(__name__)

        try:
            request_obj = read_message(self.request)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error leyendo mensaje del servidor A: %s", exc)
            return

        action = request_obj.get("action")
        if action != "process_page":
            response = {
                "status": "error",
                "error": f"Acción desconocida: {action!r}",
                "processing_data": {
                    "screenshot": None,
                    "performance": None,
                    "thumbnails": [],
                    "advanced": None,
                },
            }
            try:
                send_message(self.request, response)
            except Exception:  # noqa: BLE001
                logger.exception("Error enviando respuesta de error al servidor A")
            return

        url = request_obj.get("url")
        scraping_data = request_obj.get("scraping_data", {}) or {}
        if not isinstance(scraping_data, dict):
            scraping_data = {}

        html = request_obj.get("html", "") or ""
        if not isinstance(html, str):
            html = ""

        server = self.server  # type: ignore[attr-defined]
        process_pool: concurrent.futures.ProcessPoolExecutor = getattr(
            server, "process_pool"
        )

        # Enviar el trabajo al POOL de procesos
        future = process_pool.submit(process_page_task, url, scraping_data, html)

        try:
            processing_data = future.result()
            response = {
                "status": "success",
                "processing_data": processing_data,
            }
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error procesando página en el pool: %s", exc)
            response = {
                "status": "error",
                "error": str(exc),
                "processing_data": {
                    "screenshot": None,
                    "performance": None,
                    "thumbnails": [],
                    "advanced": None,
                },
            }

        try:
            send_message(self.request, response)
        except Exception:  # noqa: BLE001
            logger.exception("Error enviando respuesta al servidor A")


class ThreadingTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """
    TCPServer con threads para manejar varias conexiones a la vez.
    Las tareas pesadas igual se mandan al pool de procesos.
    """

    daemon_threads = True
    allow_reuse_address = True


class ProcessingTCPServer(ThreadingTCPServer):
    """
    Servidor base que guarda una referencia al process_pool.
    """

    def __init__(
        self,
        server_address,
        RequestHandlerClass,
        process_pool: concurrent.futures.ProcessPoolExecutor,
        bind_and_activate: bool = True,
    ) -> None:
        self.process_pool = process_pool
        super().__init__(server_address, RequestHandlerClass, bind_and_activate)


class ProcessingTCPServerIPv6(ProcessingTCPServer):
    """
    Variante para IPv6.
    """

    address_family = socket.AF_INET6


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Servidor de Procesamiento Distribuido"
    )
    parser.add_argument(
        "-i",
        "--ip",
        required=True,
        help="Dirección de escucha (IPv4 o IPv6)",
    )
    parser.add_argument(
        "-p",
        "--port",
        required=True,
        type=int,
        help="Puerto de escucha",
    )
    parser.add_argument(
        "-n",
        "--processes",
        type=int,
        default=0,
        help="Número de procesos en el pool (default: CPU count)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    num_procs = args.processes or (multiprocessing.cpu_count() or 1)

    # Elegir clase de servidor según si la IP es IPv4 o IPv6
    if ":" in args.ip:
        ServerClass = ProcessingTCPServerIPv6
    else:
        ServerClass = ProcessingTCPServer

    server_address = (args.ip, args.port)

    logging.info(
        "Iniciando servidor de procesamiento en %s:%s con %d procesos",
        args.ip,
        args.port,
        num_procs,
    )

    with concurrent.futures.ProcessPoolExecutor(max_workers=num_procs) as pool:
        with ServerClass(server_address, ProcessingRequestHandler, process_pool=pool) as server:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                logging.info("Servidor detenido por KeyboardInterrupt")


if __name__ == "__main__":
    main()
