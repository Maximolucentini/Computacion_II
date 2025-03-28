import os
import time

pid = os.fork()

if pid == 0:
    
    print(f"[HIJO] PID: {os.getpid()} | PPID inicial: {os.getppid()}")
    time.sleep(5)  
    print(f"[HIJO] Soy huerfano. Mi nuevo padre es: {os.getppid()}")
    
    # Ejecuta un comando externo sin supervisión del padre
    # Esto simula una acción potencialmente riesgosa si no hay control
    os.execvp("bash", ["bash", "-c", "echo 'Comando externo ejecutado sin control del padre' > huerfano.log"])

else:
    
    print(f"[PADRE] PID: {os.getpid()} termino sin esperar al hijo.")
    os._exit(0)  
