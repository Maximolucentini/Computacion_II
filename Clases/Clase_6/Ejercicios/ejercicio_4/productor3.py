import os, time

fifo_path = "/tmp/fifo_multi"

with open(fifo_path, 'w') as fifo:
    while True:
        fifo.write("Soy productor 3\n")
        fifo.flush()
        time.sleep(2)
