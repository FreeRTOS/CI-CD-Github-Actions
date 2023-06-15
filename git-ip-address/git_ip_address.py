import os
import socket

def get_ip_address():
    git_hostname =  socket.gethostname()
    ip_address = socket.gethostbyname(git_hostname).split('.')
    with open("git_ip_address.txt", "w") as file:
        count = 0
        for part in ip_address:
            file.write("#define configECHO_SERVER_ADDR" + str(count) + " " + str(part) + "\n")
            count += 1
    
    echo_address = ""
    with open('git_ip_address.txt', 'r') as f:
        echo_address = f.read()
        print(echo_address)
    return echo_address

if __name__ == "__main__":
    get_ip_address()
