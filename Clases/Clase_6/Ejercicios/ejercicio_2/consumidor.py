"""crear FIFO: mkfifo /tmp/fifo_buffer
Luego ejecutar:
En una terminal:python3 consumidor.py
En otra terminal:python3 productor.py"""

import os
from datetime import datetime

fifo_path = "/tmp/fifo_buffer"

with open(fifo_path, 'r') as fifo:
    for line in fifo:
        num = line.strip()
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        print(f"[{timestamp}] Recibido: {num}")
