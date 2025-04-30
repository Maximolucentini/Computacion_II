import signal
import time
import os


print(f"[{os.getpid()}] Ignorando Ctrl+C (SIGINT) por 5 segundos...")

signal.signal(signal.SIGINT, signal.SIG_IGN)


for i in range(5):
    print(f"Segundo {i+1}...")
    time.sleep(1)


print("Restaurando comportamiento normal de SIGINT. Ahora Ctrl+C termina el programa.")
signal.signal(signal.SIGINT, signal.default_int_handler)


try:
    while True:
        print("Ejecutando... (presioná Ctrl+C para salir)")
        time.sleep(1)
except KeyboardInterrupt:
    print("\nPrograma interrumpido con Ctrl+C.")
