import socket 
from threading import Thread 


def Sending(s):
    while True : 
        msg = input()
        s.send(bytes(msg,"utf-8"))
def Receving(s):
    while True : 
        msg=s.recv(500)
        print(msg.decode("utf-8"))
SOCKET=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print(str(socket.gethostbyname(socket.gethostname())))
SOCKET.bind(("0.0.0.0",1234))
SOCKET.listen(1)

while True :
    ClientSocket, ClientAddress = SOCKET.accept()
    print("Connected ! ", ClientAddress)
    Thread_1=Thread(target=Sending,args=(ClientSocket, ))
    Thread_2=Thread(target=Receving,args=(ClientSocket, ))
    Thread_1.start()
    Thread_2.start()
