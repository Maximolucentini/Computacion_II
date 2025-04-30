"""Como ejecutarlo:Ejecuta desde una terminal
el programa,Copia el PID que aparece en pantalla.
En otra terminal, ejecuta:
kill -TERM <PID>"""

import signal
import os
import time
import atexit


def funcion_finalizacion():
    print("[atexit] El proceso ha terminado. Esto es limpieza general.")

atexit.register(funcion_finalizacion)


def handler_sigterm(signum, frame):
    print(f"[SIGTERM] Señal {signum} recibida. Cerrando proceso...")


signal.signal(signal.SIGTERM, handler_sigterm)


print(f"PID del proceso: {os.getpid()}")
print("Esperando señal SIGTERM... (podés enviarla con: kill -TERM <PID>)")


try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Interrupción con Ctrl+C")

