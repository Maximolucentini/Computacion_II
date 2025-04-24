import os
import time
import random

fifo_path = "/tmp/fifo_temp"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

with open(fifo_path, 'w') as fifo:
    while True:
        temp = round(random.uniform(20, 30), 2)
        fifo.write(f"{temp}\n")
        fifo.flush()
        print(f"[Sensor] Temperatura enviada: {temp} °C")
        time.sleep(1)
