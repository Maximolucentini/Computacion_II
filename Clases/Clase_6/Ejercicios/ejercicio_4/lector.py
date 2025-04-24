"""Como probarlo
crear el FIFO:mkfifo /tmp/fifo_multi
En una terminal, ejecuta:
python3 lector.py
En tres terminales separadas, ejecuta cada uno de:
python3 productor1.py
python3 productor2.py
python3 productor3.py
"""

import os

fifo_path = "/tmp/fifo_multi"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

print("Lector activo. Esperando mensajes...\n")
with open(fifo_path, 'r') as fifo:
    for linea in fifo:
        print(f"[Recibido] {linea.strip()}")
