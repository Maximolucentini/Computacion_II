import os
import time

fifo_path = "/tmp/test_fifo"

print("Esperando 3 segundos antes de escribir...")
time.sleep(3)

with open(fifo_path, 'w') as fifo:
    fifo.write("Primera línea\n")
    fifo.write("Segunda línea\n")
    fifo.write("Tercera línea\n")
    fifo.flush()
    print("Mensajes enviados.")
