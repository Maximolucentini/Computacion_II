"""Cómo ejecutarlo
Crear el FIFO:
mkfifo /tmp/fifo_temp
En una terminal:python3 monitor.py
En otra terminal:python3 sensor.py"""

import os

fifo_path = "/tmp/fifo_temp"

if not os.path.exists(fifo_path):
    os.mkfifo(fifo_path)

print(" Monitor de Temperatura Activo...\n")
with open(fifo_path, 'r') as fifo:
    for line in fifo:
        try:
            temp = float(line.strip())
            msg = f"{temp} °C"
            if temp > 28:
                msg += " ⚠️ ALERTA: Temperatura elevada"
            print(msg)
        except ValueError:
            print("Dato no válido recibido")
