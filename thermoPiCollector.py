#!/opt/bin/python

# Echo server program
import socket
import string
import collectorMysql

HOST = ''                 # Symbolic name meaning all available interfaces
PORT = 2020               # Arbitrary non-privileged port
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind((HOST, PORT))
s.listen(1)
conn, addr = s.accept()
print 'Connected to ', addr

while 1:
    data = conn.recv(1024)
    parsed = string.split(data, '|')
    parsed[-1] = parsed[-1].strip()
    if parsed[0] == '0':
        # proto version 0
        temp = parsed[3]
        timestamp = parsed[1]
        sensorName = parsed[2]
    else:
        print "proto not recognized:"
        print parsed
        break

    collectorMysql.connectToDatasource()
    collectorMysql.writeToDatasource(temp, timestamp, sensorName)

    if not data: break
    #conn.sendall(data)

collectorMysql.close()
conn.close()
