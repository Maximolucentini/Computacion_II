import os

def main():
    comando1 = input("Primer comando: ").strip().split()
    comando2 = input("Segundo comando: ").strip().split()

    r, w = os.pipe()

    pid1 = os.fork()
    if pid1 == 0:
        os.dup2(w, 1)
        os.close(r)
        os.execvp(comando1[0], comando1)

    pid2 = os.fork()
    if pid2 == 0:
        os.dup2(r, 0)
        os.close(w)
        os.execvp(comando2[0], comando2)

    os.close(r)
    os.close(w)
    os.wait()
    os.wait()

if __name__ == "__main__":
    main()
