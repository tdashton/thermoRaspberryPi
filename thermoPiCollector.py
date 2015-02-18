#!/opt/bin/python

# Echo server program
import socket
import string

f = open('log.txt', 'w', 1)

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 2020               # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print 'Connected to ', addr

while 1:
    data = conn.recv(1024)
    parsed = string.split(data, '\00')
    parsed[-1] = parsed[-1].strip()
    f.write(data)
    if not data: break
    conn.sendall(data)

conn.close()
f.close()

