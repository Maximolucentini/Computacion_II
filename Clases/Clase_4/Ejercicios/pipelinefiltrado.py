import os
import random

def generador(w):
    for _ in range(10):
        numero = str(random.randint(1, 100))
        os.write(w, (numero + "\n").encode())
    os.close(w)

def filtro(r, w):
    while True:
        linea = os.read(r, 1024).decode()
        if not linea:
            break
        for num in linea.strip().split('\n'):
            if num and int(num) % 2 == 0:
                os.write(w, (num + "\n").encode())
    os.close(r)
    os.close(w)

def procesador(r):
    while True:
        linea = os.read(r, 1024).decode()
        if not linea:
            break
        for num in linea.strip().split('\n'):
            if num:
                cuadrado = int(num) ** 2
                print(f"{num}^2 = {cuadrado}")
    os.close(r)

def main():
    r1, w1 = os.pipe()
    r2, w2 = os.pipe()

    pid1 = os.fork()
    if pid1 == 0:
        os.close(r1)
        os.close(r2)
        os.close(w2)
        generador(w1)
        exit()

    pid2 = os.fork()
    if pid2 == 0:
        os.close(w1)
        os.close(r2)
        filtro(r1, w2)
        exit()

    os.close(w1)
    os.close(w2)
    os.close(r1)
    procesador(r2)

if __name__ == "__main__":
    main()
