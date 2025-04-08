import time
import os

pid = os.fork()

if pid == 0:
    print(f"[Hijo] PID= {os.getpid()} termino")
    os._exit(0)
else:
     print(f"[PADRE]  PID = {os.getpid()} No llama a wait().Observa el zombi con 'ps -el'")
     time.sleep(15)
     os.wait()
     
