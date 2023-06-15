import os
import socket

def get_ip_address():
    git_hostname = os.getenv('GITHUB_SERVER_HOST')
    ip_address = socket.gethostbyname(git_hostname)
    open("get_ip_address.txt", "w").write(ip_address)
    print(ip_address)
    return ip_address

if __name__ == "__main__":
    get_ip_address()
