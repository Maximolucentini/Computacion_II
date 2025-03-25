import sys
import getopt


nombre = ""
edad = ""

args = sys.argv[1:]


opts, _ = getopt.getopt(args, "n:e:", ["nombre=", "edad="])


for opt, arg in opts:
    if opt in ("-n", "--nombre"):
        nombre = arg
    elif opt in ("-e", "--edad"):
        edad = arg


print(f"Nombre: {nombre}")
print(f"Edad: {edad}")

