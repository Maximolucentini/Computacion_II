"""Crear el FIFO: 
mkfifo /tmp/test_fifo
luejo ejecutar lector.py y escritor.py"""


import os

fifo_path = "/tmp/test_fifo"

print("Abriendo FIFO para lectura (bloqueará si no hay escritor)...")
with open(fifo_path, 'r') as fifo:
    print("FIFO abierto. Esperando datos...")
    for linea in fifo:
        print(f"[LEÍDO] {linea.strip()}")
