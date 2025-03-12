import socket
from threading import Thread

# Function to send data from server to client
def Sending(client_socket):
    while True:
        msg = input("Server: ")
        client_socket.send(bytes(msg, "utf-8"))
        

# Function to receive data from client to server
def Receiving(client_socket):
    while True:
            msg = client_socket.recv(500)     
            print("Received Message:", msg.decode("utf-8"))
        
def get_local_ip(): 
    try: 
        # Create a socket object and connect to an external server 
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
        s.connect(("8.8.8.8", 80)) 
        local_ip = s.getsockname()[0]  # Get the local IP address 
        s.close() 
        return local_ip 
    except Exception as e: 
        return f"Error: {e}" 

SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# server_ip = socket.gethostbyname(socket.gethostname())
# server_ip = str(get_local_ip())
server_ip = socket.gethostbyname("Halem-Lab")
port = 1234

SOCKET.bind((server_ip, port))
SOCKET.listen(1)
print(f"Server running on {server_ip}:{port}")

while True:
    try:
        client_socket, client_address = SOCKET.accept()
        print(f"Connected with device: {client_address}")
        send_thread = Thread(target=Sending, args=(client_socket,))
        recv_thread = Thread(target=Receiving, args=(client_socket,))
        send_thread.start()
        recv_thread.start()

    except KeyboardInterrupt:
        print("\nShutting down the server.")
        SOCKET.close()
        break
   
