import os
import sys
import json
import random
import time
from collections import defaultdict

class Transaccion:
    def __init__(self, tid=None, tipo=None, monto=None):
        self.tid = tid or random.randint(1000, 9999)
        self.tipo = tipo or random.choice(["deposito", "retiro", "pago", "transferencia"])
        self.monto = monto or round(random.uniform(20, 1200), 2)

    def serializar(self):
        return json.dumps({"tid": self.tid, "tipo": self.tipo, "monto": self.monto})

    @staticmethod
    def deserializar(cadena):
        try:
            datos = json.loads(cadena)
            return Transaccion(datos["tid"], datos["tipo"], datos["monto"])
        except:
            return None

def generador(nombre, pipe_w, cantidad):
    with os.fdopen(pipe_w, 'w') as salida:
        for _ in range(cantidad):
            t = Transaccion()
            salida.write(t.serializar() + '\n')
            salida.flush()
            print(f"[{nombre}] Generó transacción #{t.tid}")
            time.sleep(random.uniform(0.2, 0.5))
        salida.write("FIN\n")
        salida.flush()

def validador(pipes_lectura, pipe_salida):
    entradas = [os.fdopen(p, 'r') for p in pipes_lectura]
    salida = os.fdopen(pipe_salida, 'w')
    activos = len(entradas)

    while activos > 0:
        for i, entrada in enumerate(entradas):
            if entrada is None:
                continue
            linea = entrada.readline().strip()
            if not linea:
                continue
            if linea == "FIN":
                print(f"[Validador] Generador {i+1} finalizó")
                entradas[i] = None
                activos -= 1
                continue

            t = Transaccion.deserializar(linea)
            if not t:
                continue
            valido = t.monto > 0 and not (t.tipo == "retiro" and t.monto > 500)
            error = None if valido else "Monto inválido"
            salida.write(json.dumps({
                "t": t.__dict__,
                "ok": valido,
                "err": error
            }) + '\n')
            salida.flush()
            estado = "válida" if valido else f"inválida ({error})"
            print(f"[Validador] Transacción #{t.tid} {estado}")
        time.sleep(0.1)

    salida.write("FIN\n")
    salida.flush()

def registrador(pipe_lectura):
    entrada = os.fdopen(pipe_lectura, 'r')
    total = 0
    validas = 0
    invalidas = 0
    tipos = defaultdict(int)
    montos = defaultdict(float)
    top = []

    while True:
        linea = entrada.readline().strip()
        if not linea:
            continue
        if linea == "FIN":
            break
        info = json.loads(linea)
        t = info["t"]
        if info["ok"]:
            validas += 1
            tipos[t["tipo"]] += 1
            montos[t["tipo"]] += t["monto"]
            top.append(t)
        else:
            invalidas += 1
        total += 1
        if total % 5 == 0:
            print(f"[Registrador] Procesadas {total} transacciones")

    print("\n===== RESUMEN =====")
    print(f"Total válidas: {validas}")
    print(f"Total inválidas: {invalidas}")
    print("\nPor tipo:")
    for tipo in tipos:
        print(f"- {tipo}: {tipos[tipo]} transacciones, ${montos[tipo]:.2f}")

    print("\nTop 3 montos:")
    top_ordenado = sorted(top, key=lambda x: x["monto"], reverse=True)[:3]
    for i, t in enumerate(top_ordenado, 1):
        print(f"{i}. #{t['tid']} - {t['tipo']} ${t['monto']:.2f}")
    print("====================")

def main():
    cant_gen = 2
    pipes_g2v = []
    for _ in range(cant_gen):
        r, w = os.pipe()
        pipes_g2v.append((r, w))
    r_val_log, w_val_log = os.pipe()

    pids = []

    for i, (r, w) in enumerate(pipes_g2v):
        pid = os.fork()
        if pid == 0:
            for j, (rx, wx) in enumerate(pipes_g2v):
                if j != i:
                    os.close(rx)
                    os.close(wx)
                else:
                    os.close(rx)
            os.close(r_val_log)
            os.close(w_val_log)
            generador(f"GEN{i+1}", w, random.randint(6, 10))
            sys.exit(0)
        pids.append(pid)

    pid_val = os.fork()
    if pid_val == 0:
        for _, w in pipes_g2v:
            os.close(w)
        os.close(r_val_log)
        validador([r for r, _ in pipes_g2v], w_val_log)
        sys.exit(0)

    pid_log = os.fork()
    if pid_log == 0:
        for r, w in pipes_g2v:
            os.close(r)
            os.close(w)
        os.close(w_val_log)
        registrador(r_val_log)
        sys.exit(0)

    for r, w in pipes_g2v:
        os.close(r)
        os.close(w)
    os.close(r_val_log)
    os.close(w_val_log)

    for pid in pids:
        os.waitpid(pid, 0)
    os.waitpid(pid_val, 0)
    os.waitpid(pid_log, 0)
    print("Todo finalizado correctamente.")

if __name__ == "__main__":
    main()
