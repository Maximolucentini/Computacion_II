import os
import time

pid = os.fork()

if pid == 0:
    
    print(f"[HIJO] PID: {os.getpid()} | PPID inicial: {os.getppid()}")
    time.sleep(10)  
    print(f"[HIJO] PID: {os.getpid()} | PPID tras ser huérfano: {os.getppid()}")
    os._exit(0)
else:
    print(f"[PADRE] PID: {os.getpid()} terminó inmediatamente.")
    os._exit(0)  
