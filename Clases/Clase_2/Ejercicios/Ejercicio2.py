import os

def main():
    for i in range(2):
        pid = os.fork()
        if pid == 0:
            
            print(f"[Hijo {i+1}] PID: {os.getpid()} | PPID: {os.getppid()}")
            os._exit(0)
        

    
    for _ in range(2):
     os.wait()


main()
