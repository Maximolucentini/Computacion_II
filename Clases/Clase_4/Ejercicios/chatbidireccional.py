import os
import sys
import signal
import threading
import select

def manejar_ctrl_c():
    def salir_gracioso(signum, frame):
        print("\n[!] Saliendo del chat.")
        sys.exit(0)
    signal.signal(signal.SIGINT, salir_gracioso)

def escuchar(entrada, nombre_otro, cerrar):
    lector = os.fdopen(entrada, 'r', buffering=1)
    while not cerrar[0]:
        listo, _, _ = select.select([lector], [], [], 0.3)
        if listo:
            mensaje = lector.readline()
            if mensaje:
                print(f"\n{nombre_otro}: {mensaje.strip()}")
                print("Tú > ", end='', flush=True)
            else:
                print(f"\n[{nombre_otro} salió del chat]")
                cerrar[0] = True
                break

def iniciar_chat(entrada, salida, mi_nombre, otro_nombre):
    manejar_ctrl_c()
    cerrar = [False]
    hilo = threading.Thread(target=escuchar, args=(entrada, otro_nombre, cerrar), daemon=True)
    hilo.start()

    escritor = os.fdopen(salida, 'w', buffering=1)

    print(f"Conectado como {mi_nombre}. Escribí 'salir' para cerrar el chat.\n")

    try:
        while not cerrar[0]:
            msg = input("Tú > ")
            if msg.lower() == "salir":
                cerrar[0] = True
                break
            escritor.write(msg + '\n')
            escritor.flush()
    except (EOFError, KeyboardInterrupt):
        cerrar[0] = True
    finally:
        try:
            escritor.close()
        except:
            pass

def main():
    r1, w1 = os.pipe()
    r2, w2 = os.pipe()

    pid = os.fork()

    if pid == 0:
        os.close(w1)
        os.close(r2)
        iniciar_chat(r1, w2, "Usuario B", "Usuario A")
        sys.exit(0)
    else:
        os.close(r1)
        os.close(w2)
        iniciar_chat(r2, w1, "Usuario A", "Usuario B")
        os.waitpid(pid, 0)

if __name__ == "__main__":
    main()
