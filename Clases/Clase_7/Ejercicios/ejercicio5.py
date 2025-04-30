import os
import signal
import time
import random
from collections import deque

cola_de_trabajos = deque()  

def handler_SIGUSR1(signum, frame):
    timestamp = time.time()
    print(f"[CONSUMIDOR {os.getpid()}] Recibí señal SIGUSR1 a las {timestamp}")
    cola_de_trabajos.append(timestamp)

def consumidor():
    print(f"[CONSUMIDOR {os.getpid()}] Esperando trabajos...")
    signal.signal(signal.SIGUSR1, handler_SIGUSR1)

    while True:
        if cola_de_trabajos:
            trabajo = cola_de_trabajos.popleft()
            print(f"[CONSUMIDOR {os.getpid()}] Procesando trabajo generado a {trabajo}")
            time.sleep(2)  
        else:
            time.sleep(0.1)  

def productor(pid_consumidor):
    print(f"[PRODUCTOR {os.getpid()}] Enviando trabajos al consumidor PID {pid_consumidor}...")
    for _ in range(5):
        time.sleep(random.uniform(0.5, 1.5))  
        print(f"[PRODUCTOR] Trabajo generado, notificando con SIGUSR1")
        os.kill(pid_consumidor, signal.SIGUSR1)
    print("[PRODUCTOR] Finalizó generación de trabajos.")


pid = os.fork()
if pid == 0:
    consumidor()
else:
    time.sleep(1)  
    productor(pid)
    os.waitpid(pid, 0)
    print("[PADRE] Ejecución finalizada.")
