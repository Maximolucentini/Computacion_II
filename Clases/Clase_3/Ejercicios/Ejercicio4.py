import os
import time

def ejecutar_hijo(nombre, tarea):
    pid = os.fork()
    
    if pid == 0:
        print(f"[HIJO {nombre}] PID: {os.getpid()} | PPID: {os.getppid()}")
        print(f"[HIJO {nombre}] Ejecutando tarea: {tarea}")
        time.sleep(1)
        print(f"[HIJO {nombre}] Tarea '{tarea}' finalizada.\n")
        os._exit(0)
    
    
    os.wait()
# Tarea ilustrativa
ejecutar_hijo("1", "Calcular suma")
ejecutar_hijo("2", "Escribir en archivo")

print("[PADRE] Ambos hijos han finalizado.")
