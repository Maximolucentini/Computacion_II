import os

def main():
    
    pid = os.fork()
    
    if pid == 0:
        print(f'[Hijo] PID: {os.getpid()} | PPID (padre): {os.getppid()}')
    else:
        print(f'[Padre] PID: {os.getpid()} | PID del hijo: {pid}')
        os.wait()
        
main()

