"""crear FIFO: mkfifo /tmp/fifo_archivo
Luego ejecutar:
En una terminal:python3 receptor.py
En otra terminal:python3 emisor.py"""

import os

fifo_path = "/tmp/fifo_archivo"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

with open(fifo_path, 'r') as fifo, open("output.txt", 'w') as out:
    for line in fifo:
        if line.strip() == "exit":
            print("Cerrando receptor...")
            break
        out.write(line)
        out.flush()
        print(f"[Guardado] {line.strip()}")
