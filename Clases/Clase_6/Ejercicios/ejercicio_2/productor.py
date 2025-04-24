import os
import time

fifo_path = "/tmp/fifo_buffer"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

with open(fifo_path, 'w') as fifo:
    for i in range(1, 101):
        fifo.write(f"{i}\n")
        fifo.flush()
        time.sleep(0.1)
