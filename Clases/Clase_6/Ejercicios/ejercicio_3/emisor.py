import os

fifo_path = "/tmp/fifo_archivo"

while not os.path.exists(fifo_path):
    pass

with open(fifo_path, 'w') as fifo:
    while True:
        linea = input("Ingresá texto ('exit' para salir): ")
        fifo.write(linea + '\n')
        fifo.flush()
        if linea.strip() == "exit":
            print("Cerrando emisor...")
            break
