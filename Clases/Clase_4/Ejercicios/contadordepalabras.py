import os

def main():
    padre_a_hijo_r, padre_a_hijo_w = os.pipe()
    hijo_a_padre_r, hijo_a_padre_w = os.pipe()

    pid = os.fork()

    if pid == 0:
        os.close(padre_a_hijo_w)
        os.close(hijo_a_padre_r)

        while True:
            linea = os.read(padre_a_hijo_r, 1024).decode()
            if linea == "FIN":
                break
            cantidad = str(len(linea.strip().split()))
            os.write(hijo_a_padre_w, cantidad.encode())

        os.close(padre_a_hijo_r)
        os.close(hijo_a_padre_w)

    else:
        os.close(padre_a_hijo_r)
        os.close(hijo_a_padre_w)

        with open("contadordepalabras.txt", "r") as f:
            for linea in f:
                os.write(padre_a_hijo_w, linea.encode())
                resultado = os.read(hijo_a_padre_r, 1024).decode()
                print(f"Palabras: {resultado}")

        os.write(padre_a_hijo_w, "FIN".encode())

        os.close(padre_a_hijo_w)
        os.close(hijo_a_padre_r)

if __name__ == "__main__":
    main()
