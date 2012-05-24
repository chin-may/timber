# Echo client program
import sys
import socket
HOST = sys.argv[1] if len(sys.argv) >= 2 else ''
PORT = 8033
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.send("hello\r")
print s.recv(1024)
s.close()
