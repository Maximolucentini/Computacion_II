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
from unittest.mock import AsyncMock, MagicMock, patch

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
        
    def test_scrape_content_too_large_mock(self) -> None:
        """
        Test para verificar que el límite de tamaño de HTML funciona.
        
        Usa mocking para simular una respuesta muy grande sin necesidad
        de descargar contenido real.
        """
        async def _test() -> None:
            from scraper.async_http import fetch_html, ContentTooLargeError
            
            # Mock de la respuesta HTTP
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Length': '20971520'}  # 20 MB
            mock_response.url = "https://example.com"
            mock_response.raise_for_status = MagicMock()
            
            # Mock del ClientSession
            mock_session = MagicMock()
            mock_session.get = MagicMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Intentar descargar con límite de 10 MB
            with self.assertRaises(ContentTooLargeError) as context:
                await fetch_html(
                    "https://example.com",
                    session=mock_session,
                    max_size_mb=10.0
                )
            
            error_msg = str(context.exception)
            self.assertIn("demasiado grande", error_msg.lower())
            self.assertIn("20", error_msg)  # Debería mencionar 20 MB
            self.assertIn("10", error_msg)  # Debería mencionar el límite de 10 MB
        
        asyncio.run(_test())

    def test_scrape_content_within_limit_mock(self) -> None:
        """
        Test para verificar que contenido dentro del límite se descarga bien.
        """
        async def _test() -> None:
            from scraper.async_http import fetch_html
            
            # Mock de la respuesta HTTP con contenido pequeño
            mock_response = MagicMock()
            mock_response.status = 200
            mock_response.headers = {'Content-Length': '5000'}  # 5 KB
            mock_response.url = "https://example.com"
            mock_response.raise_for_status = MagicMock()
            mock_response.get_encoding = MagicMock(return_value='utf-8')
            
            # Mock del content.iter_chunked
            small_html = b"<html><body>Test content</body></html>"
            async def async_iter():
                yield small_html
            
            mock_response.content.iter_chunked = MagicMock(return_value=async_iter())
            
            # Mock del ClientSession
            mock_session = MagicMock()
            mock_session.get = MagicMock()
            mock_session.get.return_value.__aenter__ = AsyncMock(return_value=mock_response)
            mock_session.get.return_value.__aexit__ = AsyncMock(return_value=None)
            
            # Descargar con límite de 10 MB (debe funcionar)
            html, final_url = await fetch_html(
                "https://example.com",
                session=mock_session,
                max_size_mb=10.0
            )
            
            self.assertIsInstance(html, str)
            self.assertIn("Test content", html)
            self.assertEqual(final_url, "https://example.com")
        
        asyncio.run(_test())



if __name__ == "__main__":
    unittest.main()
