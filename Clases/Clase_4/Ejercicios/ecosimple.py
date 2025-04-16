import os

def main():
    padre_a_hijo_r, padre_a_hijo_w = os.pipe()
    hijo_a_padre_r, hijo_a_padre_w = os.pipe()

    pid = os.fork()

    if pid == 0:
        
        os.close(padre_a_hijo_w)  
        os.close(hijo_a_padre_r)  

        
        mensaje = os.read(padre_a_hijo_r, 1024).decode()
        print(f"[Hijo] Mensaje recibido: {mensaje}")

        
        os.write(hijo_a_padre_w, mensaje.encode())

        os.close(padre_a_hijo_r)
        os.close(hijo_a_padre_w)

    else:
        
        os.close(padre_a_hijo_r)  
        os.close(hijo_a_padre_w)  

        mensaje = "Hola desde el padre"
        os.write(padre_a_hijo_w, mensaje.encode())

        
        eco = os.read(hijo_a_padre_r, 1024).decode()
        print(f"[Padre] Eco recibido: {eco}")

        os.close(padre_a_hijo_w)
        os.close(hijo_a_padre_r)

if __name__ == "__main__":
    main()
