import os
import threading

fifo_send = "/tmp/chat_b"
fifo_recv = "/tmp/chat_a"

if not os.path.exists(fifo_send):
    os.mkfifo(fifo_send)
if not os.path.exists(fifo_recv):
    os.mkfifo(fifo_recv)

def recibir():
    with open(fifo_recv, 'r') as f:
        while True:
            msg = f.readline().strip()
            if msg:
                print(f"[Usuario A]: {msg}")

def enviar():
    with open(fifo_send, 'w') as f:
        while True:
            msg = input("Yo (B): ")
            f.write(msg + '\n')
            f.flush()
            if msg.strip().lower() == "exit":
                break

threading.Thread(target=recibir, daemon=True).start()
enviar()

