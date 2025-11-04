"""
protocol.py
Protocolo binario simple: [longitud (4 bytes big-endian)] + [payload JSON].

Sirve tanto para el Servidor A (asyncio) como para el B (socketserver).
"""

import asyncio
import socket
import struct
from typing import Any, Dict

from .serialization import dumps, loads

# Unsigned int de 4 bytes big-endian
_HEADER_STRUCT = struct.Struct("!I")


# --------- Versión asíncrona (asyncio) ---------


async def send_message_async(writer: asyncio.StreamWriter, message: Dict[str, Any]) -> None:
    """
    Envía un mensaje (dict) a través de un StreamWriter de asyncio.
    """
    body = dumps(message)
    header = _HEADER_STRUCT.pack(len(body))
    writer.write(header + body)
    await writer.drain()


async def read_message_async(reader: asyncio.StreamReader) -> Dict[str, Any]:
    """
    Lee un mensaje desde un StreamReader de asyncio y lo devuelve como dict.
    """
    header_data = await reader.readexactly(_HEADER_STRUCT.size)
    (length,) = _HEADER_STRUCT.unpack(header_data)
    body = await reader.readexactly(length)
    obj = loads(body)
    if not isinstance(obj, dict):
        raise ValueError("El mensaje recibido no es un dict JSON")
    return obj




def send_message(sock: socket.socket, message: Dict[str, Any]) -> None:
    """
    Envía un mensaje (dict) por un socket bloqueante.
    """
    body = dumps(message)
    header = _HEADER_STRUCT.pack(len(body))
    sock.sendall(header + body)


def read_message(sock: socket.socket) -> Dict[str, Any]:
    """
    Lee un mensaje completo desde un socket bloqueante y lo devuelve como dict.
    """
    header_data = _recv_exact(sock, _HEADER_STRUCT.size)
    if not header_data:
        raise ConnectionError("Conexión cerrada al leer cabecera")

    (length,) = _HEADER_STRUCT.unpack(header_data)
    body = _recv_exact(sock, length)
    if not body:
        raise ConnectionError("Conexión cerrada al leer cuerpo")

    obj = loads(body)
    if not isinstance(obj, dict):
        raise ValueError("El mensaje recibido no es un dict JSON")
    return obj


def _recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """
    Recibe exactamente num_bytes desde el socket (salvo que se cierre).
    """
    data = b""
    while len(data) < num_bytes:
        chunk = sock.recv(num_bytes - len(data))
        if not chunk:
            break
        data += chunk
    return data
