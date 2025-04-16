import os
import sys
import re
import time
import signal

def manejar_salida():
    def salir_gracioso(sig, frame):
        print("\n[Servidor] Cerrando servicio.")
        sys.exit(0)
    signal.signal(signal.SIGINT, salir_gracioso)

def resolver_operacion(expr):
    try:
        if not re.fullmatch(r'[\d\s\.\+\-\*/\(\)]+', expr):
            return "ERROR: Solo se permiten números y operadores válidos"
        return str(eval(expr))
    except ZeroDivisionError:
        return "ERROR: División por cero"
    except Exception:
        return "ERROR: Expresión no válida"

def servidor(entrada, salida):
    manejar_salida()
    print("[Servidor] Activo y esperando operaciones...")

    with os.fdopen(entrada, 'r') as entrada_pipe, os.fdopen(salida, 'w') as salida_pipe:
        while True:
            operacion = entrada_pipe.readline().strip()
            if operacion.lower() == "exit" or not operacion:
                print("[Servidor] Finalizando.")
                break
            print(f"[Servidor] Operación recibida: {operacion}")
            time.sleep(0.3)
            resultado = resolver_operacion(operacion)
            salida_pipe.write(resultado + '\n')
            salida_pipe.flush()

def cliente(salida, entrada):
    print("Cliente de operaciones matemáticas")
    print("Ejemplos válidos: 5 + 3, 10*(2+2), 9 / 0")
    print("Escribí 'exit' para cerrar\n")

    with os.fdopen(salida, 'w') as enviar, os.fdopen(entrada, 'r') as recibir:
        while True:
            op = input("Operación > ")
            if op.lower() == "exit":
                enviar.write("exit\n")
                enviar.flush()
                break
            enviar.write(op + '\n')
            enviar.flush()
            respuesta = recibir.readline().strip()
            print(f"Resultado: {respuesta}")

def main():
    c2s_r, c2s_w = os.pipe()
    s2c_r, s2c_w = os.pipe()

    pid = os.fork()

    if pid == 0:
        os.close(c2s_w)
        os.close(s2c_r)
        servidor(c2s_r, s2c_w)
        sys.exit(0)
    else:
        os.close(c2s_r)
        os.close(s2c_w)
        cliente(c2s_w, s2c_r)
        os.waitpid(pid, 0)

if __name__ == "__main__":
    main()
