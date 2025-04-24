"""Como probarlo
Crear el FIFO:mkfifo /tmp/fifo_condicional
Ejecuta el script:python3 lector_no_bloqueante.py"""

import os
import errno

fifo_path = "/tmp/fifo_condicional"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

try:
    fd = os.open(fifo_path, os.O_RDONLY | os.O_NONBLOCK)
    with os.fdopen(fd, 'r') as fifo:
        print("FIFO abierto exitosamente en modo no bloqueante.")
        for linea in fifo:
            print(f"[Recibido] {linea.strip()}")
except OSError as e:
    if e.errno == errno.ENXIO:
        print("No hay escritores conectados al FIFO. Saliendo sin bloquear.")
    else:
        print(f"Error inesperado: {e}")
