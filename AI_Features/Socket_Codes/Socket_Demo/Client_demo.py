import socket 
from threading import Thread 

# Function to send data from client to server
def Sending(s):
    while True : 
        try:
            msg = input()
            if msg.lower() == 'exit':  # Exit condition
                s.send(bytes("exit", "utf-8"))  # Notify server
                s.close()
                break
            s.send(bytes(msg, "utf-8"))
        except Exception as e:
            print("Error sending message:", e)
            s.close()
            break

# Function to receive data from server to client
def Receiving(s):
    while True : 
        try:
            msg = s.recv(500)
            if not msg or msg.decode("utf-8").lower() == 'exit':  # Exit condition
                print("Server disconnected.")
                s.close()
                break
            print("Received Message:", msg.decode("utf-8"))
        except Exception as e:
            print("Error receiving message:", e)
            break

SOCKET = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
server_IP = socket.gethostbyname("Halem-Lab")
port = 1234
SOCKET.connect((server_IP, port))
print("Connected to server.")

try:
    send_thread = Thread(target=Sending, args=(SOCKET,))
    recv_thread = Thread(target=Receiving, args=(SOCKET,))
    send_thread.start()
    recv_thread.start()
    send_thread.join()
    recv_thread.join()
except KeyboardInterrupt:
    print("\nShutting down the client.")
finally:
    SOCKET.close()