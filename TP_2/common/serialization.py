"""
serialization.py
Funciones de serialización para comunicación entre servidores.
"""

import json
from typing import Any


def dumps(obj: Any) -> bytes:
    """
    Serializa un objeto Python a bytes usando JSON (UTF-8).
    """
    text = json.dumps(obj, ensure_ascii=False)
    return text.encode("utf-8")


def loads(data: bytes) -> Any:
    """
    Deserializa bytes (JSON UTF-8) a objeto Python.
    """
    text = data.decode("utf-8")
    return json.loads(text)
