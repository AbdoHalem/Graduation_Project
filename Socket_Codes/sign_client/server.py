import socket
from threading import Thread

# Function to receive data from client to server
def Receiving(client_socket, stop_flag):
    while not stop_flag["stop"]:
        try:
            msg = client_socket.recv(500)
            if not msg or msg.decode("utf-8").lower() == 'exit':
                print("Client disconnected.")
                # client_socket.close()
                stop_flag["stop"] = True
                break
            # Receive the message from the client
            print("Received Message:", msg.decode("utf-8"))
        except Exception as e:
            print("Error receiving message:", e)
            stop_flag["stop"] = True
            break

# Create and bind socket
SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
device_name = "Halem-Lab"
server_ip = socket.gethostbyname(device_name)
port = 1234
SOCKET.bind((server_ip, port))
SOCKET.listen(1)
print(f"Server running on {server_ip}:{port}")

try:
    while True:
        client_socket, client_address = SOCKET.accept()
        print(f"Connected with device: {client_address}")
        stop_flag = {"stop": False}     # Shared flag to coordinate thread shutdown
        Receiving(client_socket, stop_flag)
        client_socket.close()           # Ensure socket is closed after threads finish
        if stop_flag["stop"]:           # Exit server loop if stop_flag is set
            break

except KeyboardInterrupt:
    print("\nShutting down the server.")
finally:
    SOCKET.close()