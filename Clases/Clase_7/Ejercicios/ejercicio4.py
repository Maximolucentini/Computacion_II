"""Como ejecutarlo:
ejecuta el programa
En otra terminal:
Para pausar:
kill -USR1 <PID>
Para reanudar:
kill -USR2 <PID>"""


import signal
import threading
import time
import os


en_pausa = False
lock = threading.Lock()

def handler_SIGUSR1(signum, frame):
    global en_pausa
    with lock:
        en_pausa = True
        print(f"[{os.getpid()}] Señal SIGUSR1 recibida: contador pausado.")

def handler_SIGUSR2(signum, frame):
    global en_pausa
    with lock:
        en_pausa = False
        print(f"[{os.getpid()}] Señal SIGUSR2 recibida: contador reanudado.")

def contador():
    global en_pausa
    n = 30
    while n >= 0:
        with lock:
            if not en_pausa:
                print(f"Contador: {n}")
                n -= 1
            else:
                print("Contador en pausa...")
        time.sleep(1)


if __name__ == "__main__":
    print(f"[{os.getpid()}] Iniciando programa. Usá 'kill -USR1 {os.getpid()}' para pausar, 'kill -USR2 {os.getpid()}' para reanudar.")
    
   
    signal.signal(signal.SIGUSR1, handler_SIGUSR1)
    signal.signal(signal.SIGUSR2, handler_SIGUSR2)

    
    hilo = threading.Thread(target=contador)
    hilo.start()
    hilo.join()
    print("Contador finalizado.")
