import multiprocessing
import os
import time
import datetime
import random
import statistics
import signal
import sys
import json
import hashlib

# === CONFIGURACIONES ===
VENTANA = 30
MUESTRAS = 60
RUTA_BLOCKCHAIN = os.path.join("TP_1", "blockchain.json")

# === MANEJADOR DE SEÑALES PARA SALIDA LIMPIA ===
def manejador_senal(sig, frame):
    print("\nTerminando ejecución...")
    sys.exit(0)
signal.signal(signal.SIGINT, manejador_senal)

# === FUNCIONES DE ANALISIS ===
def procesar_senal(tipo, conn, queue):
    ventana = []
    while True:
        try:
            paquete = conn.recv()
            if paquete == "FIN":
                break

            timestamp = paquete["timestamp"]
            if tipo == "frecuencia":
                valor = paquete["frecuencia"]
            elif tipo == "presion":
                valor = paquete["presion"][0] 
            elif tipo == "oxigeno":
                valor = paquete["oxigeno"]
            else:
                continue

            ventana.append(valor)
            if len(ventana) > VENTANA:
                ventana.pop(0)

            media = statistics.mean(ventana)
            desv = statistics.stdev(ventana) if len(ventana) > 1 else 0.0

            resultado = {
                "tipo": tipo,
                "timestamp": timestamp,
                "media": round(media, 2),
                "desv": round(desv, 2)
            }
            print(f"[{tipo.upper()}] Resultado: {resultado}")
            queue.put(resultado)
        except EOFError:
            break
        except Exception as e:
            print(f"[{tipo}] Error: {e}")
            break

# === VERIFICADOR ===
def verificador(queue_frec, queue_pres, queue_oxi):
    blockchain = []
    prev_hash = "0" * 64
    for i in range(MUESTRAS):
        try:
            frec = queue_frec.get()
            pres = queue_pres.get()
            oxi = queue_oxi.get()

            alerta = False
            if frec["media"] >= 200 or oxi["media"] < 90 or oxi["media"] > 100 or pres["media"] >= 200:
                alerta = True

            timestamp = frec["timestamp"]
            datos = {
                "frecuencia": {"media": frec["media"], "desv": frec["desv"]},
                "presion": {"media": pres["media"], "desv": pres["desv"]},
                "oxigeno": {"media": oxi["media"], "desv": oxi["desv"]},
            }

            bloque = {
                "timestamp": timestamp,
                "datos": datos,
                "alerta": alerta,
                "prev_hash": prev_hash,
            }
            bloque_str = json.dumps(bloque, sort_keys=True).encode()
            bloque_hash = hashlib.sha256(bloque_str).hexdigest()
            bloque["hash"] = bloque_hash
            prev_hash = bloque_hash

            blockchain.append(bloque)

            print(f"[BLOCKCHAIN] Bloque #{i + 1} | Hash: {bloque_hash[:8]}... | Alerta: {alerta}")

            with open(RUTA_BLOCKCHAIN, "w") as f:
                json.dump(blockchain, f, indent=2)

        except Exception as e:
            print(f"[VERIFICADOR] Error: {e}")
            break

# === PROCESO PRINCIPAL ===
def generar_datos(conns):
    for _ in range(MUESTRAS):
        paquete = {
            "timestamp": datetime.datetime.now().isoformat(),
            "frecuencia": random.randint(60, 210),
            "presion": [random.randint(110, 220), random.randint(70, 110)],
            "oxigeno": random.randint(85, 100)
        }
        print(f"[GENERADOR] Enviando: {paquete}")
        for conn in conns:
            conn.send(paquete)
        time.sleep(1)

    for conn in conns:
        conn.send("FIN")
        conn.close()

# === MAIN ===
def main():
    tipos = ["frecuencia", "presion", "oxigeno"]
    procesos = []
    conns_padre = []
    colas = []

    for tipo in tipos:
        padre_conn, hijo_conn = multiprocessing.Pipe()
        queue = multiprocessing.Queue()
        p = multiprocessing.Process(target=procesar_senal, args=(tipo, hijo_conn, queue))
        procesos.append(p)
        conns_padre.append(padre_conn)
        colas.append(queue)

    verif_proc = multiprocessing.Process(target=verificador, args=tuple(colas))
    verif_proc.start()

    for p in procesos:
        p.start()

    try:
        generar_datos(conns_padre)
    finally:
        for p in procesos:
            p.join()
        verif_proc.join()

if __name__ == "__main__":
    main()

