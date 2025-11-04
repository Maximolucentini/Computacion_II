"""
processor/performance.py

Análisis de rendimiento básico:

- Tiempo de carga (ms) del HTML principal
- Tamaño total (KB) del HTML
- Cantidad de requests (aquí contamos sólo el HTML principal = 1)

La idea es cumplir con la estructura:

    "performance": {
        "load_time_ms": ...,
        "total_size_kb": ...,
        "num_requests": ...
    }
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict
from urllib.request import Request, urlopen

USER_AGENT = "TP2-Scraper-Performance/1.0"


def analyze_performance(url: str, timeout: float = 20.0) -> Dict[str, Any]:
    """
    Devuelve un dict con métricas de rendimiento.
    Si algo falla, devuelve valores nulos.
    """
    logger = logging.getLogger(__name__)

    start = time.perf_counter()
    req = Request(url, headers={"User-Agent": USER_AGENT})

    try:
        with urlopen(req, timeout=timeout) as resp:
            data = resp.read()
    except Exception as exc:  # noqa: BLE001
        logger.warning("No se pudo medir rendimiento para %s: %s", url, exc)
        return {
            "load_time_ms": None,
            "total_size_kb": None,
            "num_requests": 0,
        }

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    size_kb = round(len(data) / 1024.0, 2)

    return {
        "load_time_ms": elapsed_ms,
        "total_size_kb": size_kb,
        "num_requests": 1,
    }
