"""
tests/test_scraper.py

Tests básicos del Servidor A (asyncio + aiohttp).

Estos tests asumen que:
    - server_processing.py está corriendo en 127.0.0.1:9000
    - server_scraping.py está corriendo en 127.0.0.1:8000

Ejemplo para levantar los servidores:

    # Terminal 1
    python server_processing.py -i 127.0.0.1 -p 9000 -n 4

    # Terminal 2
    python server_scraping.py -i 127.0.0.1 -p 8000 -w 4

Para ejecutar estos tests:

    python -m tests.test_scraper
"""

from __future__ import annotations

import asyncio
import unittest
from typing import Any, Dict, Tuple

import aiohttp

SERVER_BASE_URL = "http://127.0.0.1:8000"


async def _call_scrape(target_url: str) -> Tuple[int, Dict[str, Any]]:
    """
    Llama al endpoint /scrape del Servidor A y devuelve (status_http, data_json).
    """
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{SERVER_BASE_URL}/scrape",
            params={"url": target_url},
        ) as resp:
            data = await resp.json()
            return resp.status, data


async def _create_task(target_url: str) -> Tuple[int, Dict[str, Any]]:
    """
    Envía una tarea a la cola del Servidor A (Bonus opción 1).
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SERVER_BASE_URL}/tasks",
            json={"url": target_url},
        ) as resp:
            data = await resp.json()
            return resp.status, data


async def _get_task_status(task_id: str) -> Tuple[int, Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_BASE_URL}/status/{task_id}") as resp:
            data = await resp.json()
            return resp.status, data


async def _get_task_result(task_id: str) -> Tuple[int, Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_BASE_URL}/result/{task_id}") as resp:
            data = await resp.json()
            return resp.status, data


class ScraperServerTests(unittest.TestCase):
    """
    Tests de integración simples para el Servidor A.
    """

    def test_scrape_example_success(self) -> None:
        """
        Caso feliz: /scrape sobre https://example.com debería devolver
        un JSON con 'scraping_data' y status 'success'.
        """
        status_http, data = asyncio.run(
            _call_scrape("https://example.com")
        )

        self.assertEqual(status_http, 200)
        self.assertIn("scraping_data", data)
        self.assertIn("processing_data", data)
        self.assertEqual(data.get("status"), "success")

        scraping = data.get("scraping_data") or {}
        self.assertIn("title", scraping)
        self.assertIn("links", scraping)
        self.assertIn("meta_tags", scraping)
        self.assertIn("images_count", scraping)
        self.assertIn("structure", scraping)

    def test_scrape_invalid_url(self) -> None:
        """
        Si la URL es inválida, el servidor debería devolver HTTP 400 y status 'error'.
        """
        status_http, data = asyncio.run(
            _call_scrape("esto_no_es_una_url")
        )

        self.assertEqual(status_http, 400)
        self.assertEqual(data.get("status"), "error")
        self.assertIn("error", data)

    def test_queue_task_flow(self) -> None:
        """
        Bonus: prueba básica del flujo de cola de tareas:

            POST /tasks           -> devuelve task_id
            GET  /status/{id}     -> va cambiando de estado
            GET  /result/{id}     -> devuelve resultado cuando está completed
        """
        async def _flow() -> None:
            # 1) Crear la tarea
            status_http, data = await _create_task("https://example.com")
            self.assertIn(status_http, (200, 202))
            self.assertIn("task_id", data)

            task_id = data["task_id"]

            # 2) Consultar estado hasta que sea completed o failed
            final_status = None
            for _ in range(30):  # máx ~30 segundos
                await asyncio.sleep(1.0)
                st_http, st_data = await _get_task_status(task_id)
                self.assertEqual(st_http, 200)
                final_status = st_data.get("status")
                if final_status in ("completed", "failed"):
                    break

            self.assertIn(final_status, ("completed", "failed"))

            # 3) Si completó bien, pedimos el resultado
            if final_status == "completed":
                res_http, res_data = await _get_task_result(task_id)
                self.assertEqual(res_http, 200)
                self.assertEqual(res_data.get("status"), "completed")
                self.assertIn("result", res_data)
                result = res_data["result"]
                self.assertIn("scraping_data", result)
                self.assertIn("processing_data", result)

        asyncio.run(_flow())


if __name__ == "__main__":
    unittest.main()
