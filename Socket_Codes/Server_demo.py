import socket 
from threading import Thread 

# Function to send data from server to client
def Sending(s):         # s: server's socket object
    while True : 
        msg = input()
        s.send(bytes(msg,"utf-8"))

# Function to receive data from client to server
def Receving(s):        # s: client's socket object
    while True : 
        msg = s.recv(500)
        print("Received Message:", msg.decode("utf-8"))

SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SOCKET.bind((str(socket.gethostbyname(socket.gethostname())), 1234))
SOCKET.listen(1)

#ClientSocket, ClientAddress = SOCKET.accept()
#Thread_1 = Thread(target=Sending, args=(ClientSocket, ))
#Thread_2 = Thread(target=Receving, args=(ClientSocket, ))
while True :
    ClientSocket, ClientAddress = SOCKET.accept()
    print("Connected with device", ClientAddress)
    Thread_1 = Thread(target=Sending, args=(ClientSocket, ))
    Thread_2 = Thread(target=Receving, args=(ClientSocket, ))
    Thread_1.start()
    Thread_2.start()

