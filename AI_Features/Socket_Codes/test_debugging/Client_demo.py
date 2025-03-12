import socket 
from threading import Thread 

# Function to send data from client to server
def Sending(s):
    while True : 
        msg = input()
        s.send(bytes(msg,"utf-8"))

# Function to receive data from server to client
def Receving(s):
    while True : 
        msg = s.recv(500)
        print(msg.decode("utf-8"))

SOCKET = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_IP = socket.gethostbyname("Halem-Lab")
SOCKET.connect((server_IP, 1234))
print(socket.gethostbyname(socket.gethostname()))

while True :
    Thread_1 = Thread(target=Sending, args=(SOCKET, ))
    Thread_2 = Thread(target=Receving, args=(SOCKET, ))
    Thread_1.start()
    Thread_2.start()

