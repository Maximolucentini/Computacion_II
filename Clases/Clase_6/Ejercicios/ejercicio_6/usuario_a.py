"""Cómo usarlo
Crear los dos FIFOs:
mkfifo /tmp/chat_a
mkfifo /tmp/chat_b
En una terminal:python3 usuario_a.py
En otra terminal:python3 usuario_b.py"""

import os
import threading

fifo_send = "/tmp/chat_a"
fifo_recv = "/tmp/chat_b"

if not os.path.exists(fifo_send):
    os.mkfifo(fifo_send)
if not os.path.exists(fifo_recv):
    os.mkfifo(fifo_recv)

def recibir():
    with open(fifo_recv, 'r') as f:
        while True:
            msg = f.readline().strip()
            if msg:
                print(f"[Usuario B]: {msg}")

def enviar():
    with open(fifo_send, 'w') as f:
        while True:
            msg = input("Yo (A): ")
            f.write(msg + '\n')
            f.flush()
            if msg.strip().lower() == "exit":
                break

threading.Thread(target=recibir, daemon=True).start()
enviar()
