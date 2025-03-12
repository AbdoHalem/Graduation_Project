import os
import platform
import threading
import ipaddress
import socket

# Function to ping an IP and check if it is alive
def ping_ip(ip, results):
    """Ping an IP address, check if reachable, and get the hostname."""
    try:
        # Construct the ping command based on the OS
        param = "-n 1" if platform.system().lower() == "windows" else "-c 1"
        command = f"ping {param} -w 1000 {ip}"
        # Run the ping command
        response = os.system(command)
        
        # If the ping is successful (exit code 0), resolve the hostname
        if response == 0:
            try:
                hostname = socket.gethostbyaddr(str(ip))[0]
            except socket.herror:
                hostname = "Unknown"
            #print(f"[+] Active IP: {ip}, Hostname: {hostname}")
            results.append((ip, hostname))
    except Exception as e:
        pass

def scan_network(network):
    """Scan the entire network for active IPs and hostnames."""
    results = []  # List to store active IPs and hostnames
    threads = []  # List to store threads
    
    # Generate all IPs in the given network
    for ip in ipaddress.IPv4Network(network, strict=False):
        # Create a thread for each IP
        thread = threading.Thread(target=ping_ip, args=(str(ip), results))
        threads.append(thread)
        thread.start()
    # Wait for all threads to finish
    for thread in threads:
        thread.join()
    # Return the IPs with their hostnames
    return results

if __name__ == "__main__":
    # Specify the network range (e.g., 192.168.1.0/24)
    network = "192.168.1.0/24"
    active_ips = scan_network(network)
    print("\n[+] Active IPs and Hostnames in the network:")
    for ip, hostname in active_ips:
        print(f"{ip} - {hostname}")
