import os
import signal
import time
import random


NOMBRES_SENALES = {
    signal.SIGUSR1: "SIGUSR1",
    signal.SIGUSR2: "SIGUSR2",
    signal.SIGTERM: "SIGTERM"
}


señales_recibidas = []


def handler(signum, frame):
    nombre = NOMBRES_SENALES.get(signum, f"Señal {signum}")
    print(f"[PADRE {os.getpid()}] Recibí {nombre}")
    señales_recibidas.append(nombre)


for sig in [signal.SIGUSR1, signal.SIGUSR2, signal.SIGTERM]:
    signal.signal(sig, handler)


senales = [signal.SIGUSR1, signal.SIGUSR2, signal.SIGTERM]
pids_hijos = []

for senal in senales:
    pid = os.fork()
    if pid == 0:
        
        time.sleep(random.uniform(0.5, 2.0))
        print(f"[HIJO {os.getpid()}] Enviando {NOMBRES_SENALES[senal]} al padre {os.getppid()}")
        os.kill(os.getppid(), senal)
        os._exit(0)
    else:
        
        pids_hijos.append(pid)


print(f"[PADRE {os.getpid()}] Esperando señales de los hijos...\n")

time.sleep(3)


for h in pids_hijos:
    os.waitpid(h, 0)

print("\n[PADRE] Todos los hijos han terminado.")
print(f"[PADRE] Señales recibidas: {señales_recibidas}")
