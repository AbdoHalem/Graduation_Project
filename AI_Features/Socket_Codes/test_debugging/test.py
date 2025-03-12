import socket 
 
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
 
# Print the local IP address 
print("Local IP Address:", get_local_ip())