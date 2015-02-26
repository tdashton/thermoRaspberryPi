#!/opt/bin/python

# Echo server program
import logging
import socket
import string
import threading
import collectorMysql

HOST = ''                 # Symbolic name meaning all available interfaces
MAIN_PORT = 3030          # Arbitrary non-privileged port for connection negotiation
# (re)use following range of ports for establishing communication channels
PORT_RANGE = [2021, 2022, 2023, 2024, 2025]

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))

def init_server_socket():
    serverSocket.listen(2)
    return serverSocket.accept()

'''
the server logic, does the actual work
'''
class threadedServer (threading.Thread):

    serverSocket = None
    listenPort = None

    def __init__(self, listenPort):
        threading.Thread.__init__(self)
        self.listenPort = listenPort
        pass

    def initial_setup(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((HOST, self.listenPort))
        self.serverSocket.listen(1)
        conn, addr = self.serverSocket.accept()
        print 'worker listening on {0}'.format(self.listenPort)

    def run(self):
        self.initial_setup()

        # data = conn.recv(1024)
        # parsed = string.split(data, '|')
        # parsed[-1] = parsed[-1].strip()
        # if parsed[0] == '0':
        #     # proto version 0
        #     temp = parsed[3]
        #     timestamp = parsed[1]
        #     sensorName = parsed[2]
        # else:
        #     print "proto not recognized:"
        #     print parsed
        #     break

        # collectorMysql.connectToDatasource()
        # collectorMysql.writeToDatasource(temp, timestamp, sensorName)

        data = self.serverSocket.recv(128) # receive inital connect request
        print data

        print "closing {0}".format(self.listenPort)
        self.serverSocket.close()
        # if not data: break
        #conn.sendall(data)

while 1:
    conn, addr = init_server_socket()
    logging.debug(addr)
    logging.debug(conn)
    data = conn.recv(128) # receive inital connect request
    print "data: " + data
    if data.strip() == "CONNECT": # client wants to connect
        port = PORT_RANGE.pop()
        logging.debug(port)
        conn.send("CONNECT ACK\nNEGOTIATE:{0}\n\n".format(port))
        server = threadedServer(port)
        server.start()

    else:
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
