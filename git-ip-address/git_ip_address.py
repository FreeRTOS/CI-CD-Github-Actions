import os
import socket

def get_ip_address():
    git_hostname =  socket.gethostname()
    # ip_address = socket.gethostbyname(git_hostname)
    # open("get_ip_address.txt", "w").write(ip_address)
    print(git_hostname)
    # print(ip_address)
    return git_hostname

if __name__ == "__main__":
    get_ip_address()
