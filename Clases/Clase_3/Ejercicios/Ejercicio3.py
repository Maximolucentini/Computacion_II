import os

def main():
   
   pid = os.fork()
   
   if pid == 0:
       os.execvp("ls", ["ls", "-l"])
   else:
       os.wait()
       
main()