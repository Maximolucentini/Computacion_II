import os
import time


for i in range(3):
    pid = os.fork()
    
    if pid == 0:
        print(f"[HIJO {i+1}] PID: {os.getpid()} | PPID: {os.getppid()}")
        print(f"[HIJO {i+1}] Ejecutando tarea")
        time.sleep(1)
        print(f"[HIJO {i+1}] Tarea finalizada")
        os._exit(0)


for _ in range(3):
    os.wait()

print("[PADRE] Todos los procesos hijos finalizaron.")
