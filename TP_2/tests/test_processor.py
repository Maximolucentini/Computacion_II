"""
tests/test_processor.py

Tests de funciones del Servidor B (processor/*).

No hace falta que el servidor B esté corriendo: probamos directamente
las funciones puras de los módulos:

- analyze_performance (performance.py)
- generate_thumbnails (image_processor.py)
- analyze_advanced (advanced_analysis.py)
"""

from __future__ import annotations

import unittest

from processor.performance import analyze_performance
from processor.image_processor import generate_thumbnails
from processor.advanced_analysis import analyze_advanced


class ProcessorTests(unittest.TestCase):
    """
    Tests unitarios básicos para las funciones de procesamiento.
    """

    def test_analyze_performance_keys(self) -> None:
        """
        analyze_performance siempre debe devolver un dict con las 3 claves
        principales, aunque los valores puedan ser None si falla la red.
        """
        url = "https://example.com"
        result = analyze_performance(url, timeout=3.0)

        self.assertIsInstance(result, dict)
        self.assertIn("load_time_ms", result)
        self.assertIn("total_size_kb", result)
        self.assertIn("num_requests", result)

        # Si vienen valores, chequeamos tipos básicos
        if result["load_time_ms"] is not None:
            self.assertIsInstance(result["load_time_ms"], int)
        if result["total_size_kb"] is not None:
            self.assertIsInstance(result["total_size_kb"], float)
        if result["num_requests"] is not None:
            self.assertIsInstance(result["num_requests"], int)

    def test_generate_thumbnails_empty_list(self) -> None:
        """
        Si scraping_data no tiene imágenes, generate_thumbnails debe retornar [].
        """
        scraping_data = {
            "images": [],
            "images_count": 0,
        }
        thumbs = generate_thumbnails("https://example.com", scraping_data)
        self.assertIsInstance(thumbs, list)
        self.assertEqual(len(thumbs), 0)

    def test_analyze_advanced_with_sample_html(self) -> None:
        """
        Probamos analyze_advanced con un HTML sintético que incluye:
        - meta description/keywords
        - un H1
        - JSON-LD con schema.org
        - imágenes con y sin alt
        - un script que sugiere React
        """
        sample_html = """
        <!doctype html>
        <html>
        <head>
            <title>Example page</title>
            <meta name="description" content="Pagina de ejemplo para pruebas">
            <meta name="keywords" content="python, asyncio, scraping">
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "WebSite",
                "name": "Example Site"
            }
            </script>
            <script src="https://cdn.example.com/react.production.min.js"></script>
        </head>
        <body>
            <h1>Hola mundo</h1>
            <img src="foto1.jpg" alt="Foto con alt">
            <img src="foto2.jpg">
        </body>
        </html>
        """

        scraping_data = {
            "title": "Example page",
            "meta_tags": {
                "description": "Pagina de ejemplo para pruebas",
                "keywords": "python, asyncio, scraping",
            },
            "structure": {"h1": 1},
            "images_count": 2,
        }

        result = analyze_advanced(
            "https://example.com",
            scraping_data,
            sample_html,
        )

        # Chequeamos estructura general
        self.assertIsInstance(result, dict)
        self.assertIn("technologies", result)
        self.assertIn("seo", result)
        self.assertIn("structured_data", result)
        self.assertIn("accessibility", result)

        # Tecnologías: debería detectar al menos algo de JS
        tech = result["technologies"]
        self.assertIsInstance(tech, dict)
        self.assertIn("frameworks_js", tech)
        self.assertIsInstance(tech["frameworks_js"], list)

        # SEO: score en rango 0-100
        seo = result["seo"]
        self.assertGreaterEqual(seo["score"], 0)
        self.assertLessEqual(seo["score"], 100)
        self.assertTrue(seo["has_meta_description"])

        # Datos estructurados: debería haber al menos un JSON-LD
        sd = result["structured_data"]
        self.assertGreaterEqual(sd["json_ld_count"], 1)

        # Accesibilidad: 2 imágenes, 1 con alt
        acc = result["accessibility"]
        self.assertEqual(acc["total_images"], 2)
        self.assertEqual(acc["images_with_alt"], 1)

    # Podrías agregar más tests si querés (por ejemplo, otro HTML sin metas)
    # para ver cómo se comporta el score de SEO.


if __name__ == "__main__":
    unittest.main()
