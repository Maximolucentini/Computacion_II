import os
import time
import random

for cliente in range(1, 6):
    pid = os.fork()
    
    if pid == 0:
        print(f"[HIJO] Atendiendo cliente {cliente} | PID: {os.getpid()}")
        duracion = random.randint(1, 3)
        time.sleep(duracion)
        print(f"[HIJO] Cliente {cliente} atendido en {duracion} segundos")
        os._exit(0)


for _ in range(5):
    os.wait()

print("[SERVIDOR] Todos los clientes fueron atendidos")
