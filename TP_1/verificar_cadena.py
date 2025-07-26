import json
import hashlib
import os


def calcular_hash(bloque):
    bloque_sin_hash = bloque.copy()
    bloque_sin_hash.pop("hash", None)
    bloque_str = json.dumps(bloque_sin_hash, sort_keys=True).encode()
    return hashlib.sha256(bloque_str).hexdigest()


def verificar_cadena():
    ruta_blockchain = os.path.join("TP_1", "blockchain.json")
    ruta_reporte = os.path.join("TP_1", "reporte.txt")

    try:
        with open(ruta_blockchain, "r") as f:
            blockchain = json.load(f)
    except FileNotFoundError:
        print("[ERROR] No se encontró el archivo TP_1/blockchain.json")
        return

    bloques_corruptos = 0
    alertas = 0
    suma_frec = suma_pres = suma_oxi = 0
    total_bloques = len(blockchain)

    for i, bloque in enumerate(blockchain):
        hash_calculado = calcular_hash(bloque)
        if bloque["hash"] != hash_calculado:
            print(f"[CORRUPTO] Bloque #{i+1}: hash no coincide")
            bloques_corruptos += 1

        if i > 0 and bloque["prev_hash"] != blockchain[i-1]["hash"]:
            print(f"[CORRUPTO] Bloque #{i+1}: prev_hash no coincide")
            bloques_corruptos += 1

        if bloque.get("alerta"):
            alertas += 1

        suma_frec += bloque["datos"]["frecuencia"]["media"]
        suma_pres += bloque["datos"]["presion"]["media"]
        suma_oxi += bloque["datos"]["oxigeno"]["media"]

    prom_frec = round(suma_frec / total_bloques, 2) if total_bloques else 0
    prom_pres = round(suma_pres / total_bloques, 2) if total_bloques else 0
    prom_oxi = round(suma_oxi / total_bloques, 2) if total_bloques else 0

    with open(ruta_reporte, "w") as rep:
        rep.write(f"Bloques totales: {total_bloques}\n")
        rep.write(f"Bloques con alerta: {alertas}\n")
        rep.write(f"Bloques corruptos: {bloques_corruptos}\n")
        rep.write(f"Promedio frecuencia: {prom_frec}\n")
        rep.write(f"Promedio presion: {prom_pres}\n")
        rep.write(f"Promedio oxigeno: {prom_oxi}\n")

    print("\n[✔] Verificación completa. Resultado guardado en TP_1/reporte.txt")


if __name__ == "__main__":
    verificar_cadena()
