#!/opt/bin/python

# Echo server program
import logging
import socket
import string
import threading
import collectorMysql

HOST = ''                 # Symbolic name meaning all available interfaces
MAIN_PORT = 2020          # Arbitrary non-privileged port for connection negotiation
# (re)use following range of ports for establishing communication channels
PORT_RANGE = [2021, 2022, 2023, 2024, 2025]

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))
logging.basicConfig(filename='collector.log', level=logging.DEBUG)

'''
for the main server
'''
def init_server_socket():
    logging.info("server listening on {0}".format(MAIN_PORT))
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
        logging.info('worker listening on {0}'.format(self.listenPort))
        return self.serverSocket.accept()

    def run(self):
        conn, addr = self.initial_setup()

        while 1:
            data = conn.recv(1024)
            # logging.debug(data)
            parsed = string.split(data, '|')
            parsed[-1] = parsed[-1].strip()
            if parsed[0] == '0':
                # proto version 0
                temp = parsed[3]
                timestamp = parsed[1]
                sensorName = parsed[2]
            else:
                logging.debug("proto not recognized:")
                logging.debug(parsed)
                break

            collectorMysql.connectToDatasource()
            collectorMysql.writeToDatasource(temp, timestamp, sensorName)
            if not data: break
            # conn.sendall(data)

        logging.debug("Worker closing port {0}".format(self.listenPort))
        self.serverSocket.close()
        PORT_RANGE.append(self.listenPort)

while 1:
    conn, addr = init_server_socket()
    logging.debug("processing request from {0} {1}.".format(addr[0], addr[1]))
    data = conn.recv(128) # receive inital connect request
    logging.debug("data: " + data)

    if data.strip() == "CONNECT CMD": # client wants to connect and perform a command
        conn.send("CONNECT ACK\nREADY\n\n")

    elif data.strip() == "CONNECT LOG": # client wants to connect and send logs
        port = PORT_RANGE.pop()
        logging.debug("port: ".format(port))
        server = threadedServer(port)
        server.start()
        conn.send("CONNECT ACK\nNEGOTIATE:{0}\n\n".format(port))

    else:
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
