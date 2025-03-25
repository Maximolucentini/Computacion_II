import argparse

parser = argparse.ArgumentParser(description="Recibe nombre, edad y ciudad opcional.")

parser.add_argument("-n", "--nombre", required=True, help="Nombre del usuario")
parser.add_argument("-e", "--edad", required=True, type=int, help="Edad del usuario")

parser.add_argument("-c", "--ciudad", default="Desconocida", help="Ciudad del usuario")

args = parser.parse_args()

print(f"Nombre: {args.nombre}")
print(f"Edad: {args.edad}")
print(f"Ciudad: {args.ciudad}")
