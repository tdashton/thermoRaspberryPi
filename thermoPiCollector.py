#!/usr/bin/python

# Echo server program
import datetime
import hashlib
import logging
import socket
import string
import threading
import collectorMysql
import Queue

HOST = ''                 # Symbolic name meaning all available interfaces
MAIN_PORT = 2020          # Arbitrary non-privileged port for connection negotiation
serverThreads = []

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))
logging.basicConfig(filename='collector.log', level=logging.DEBUG, format='%(asctime)s %(message)s')

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
    addr = None
    threadNumber = None

    def __init__(self, socket, addr, threadNumber=None):
        threading.Thread.__init__(self)
        self.serverSocket = socket
        self.addr = addr
        if threadNumber is not None:
            self.threadNumber = threadNumber
        pass

    def tear_down(self):
        logging.debug("Worker closing {0}".format(self.addr))
        self.serverSocket.close()
        serverThreads.remove(self)

    def run(self):
        logging.debug("running for connection {0}".format(self.addr))
        self.serverSocket.send("CONNECT ACK\n\n")

        #  TODO non blocking: https://docs.python.org/2/howto/sockets.html#non-blocking-sockets
        logging.debug("waiting for mode")
        mode = self.serverSocket.recv(128)

        logging.debug("set mode:{0}".format(mode.strip()))
        self.serverSocket.send("ACK:{0}".format(mode.strip()))

        while True:
            data = self.serverSocket.recv(1024)
            # logging.debug(data)
            parsed = string.split(data, '|')
            parsed[-1] = parsed[-1].strip()
            if parsed[0] == '1':
                # proto version 1
                payloadType = parsed[1]
                if payloadType == 'DATA' and len(parsed) == 5:
                    timestamp = parsed[2]
                    sensorName = parsed[3]
                    temp = parsed[4]
                    collectorMysql.connectToDatasource(self.addr[1])
                    collectorMysql.writeToDatasource(self.addr[1], temp, timestamp, sensorName)
                else:
                    # logging.debug("it is a pass")
                    pass
            elif parsed[0] == '2':
                # proto version 2
                payloadType = parsed[1]
                if payloadType == 'SENSOR':
                    timestamp = parsed[2]
                    sensorName = parsed[3]
                    temp = parsed[4]
                    collectorMysql.writeToDatasource(self.addr[1], temp, timestamp, sensorName)
                else:
                    pass
            elif parsed[0] == '3':
                # proto version 3
                payloadType = parsed[1]
                if payloadType == 'SENSOR':
                    timestamp = datetime.datetime.now()
                    sensorName = parsed[2]
                    temp = parsed[3]
                    collectorMysql.writeToDatasource(self.addr[1], temp, timestamp, sensorName)
                else:
                    pass

            else:
                logging.debug("proto not recognized")
                logging.debug(parsed)
                break

            payload = hashlib.md5(data).hexdigest()
            self.serverSocket.sendall(payload)
            # data = self.serverSocket.recv(1024)

            # if not data:
            #     logging.debug("nothing received")

        self.tear_down()
        pass

q = Queue.Queue()

while True:
    conn, addr = init_server_socket()
    threadNumber = len(serverThreads)
    logging.debug("addr: {1} port: {0}".format(addr, threadNumber))
    serverThreads.append(threadedServer(conn, addr, threadNumber + 1))
    serverThreads[threadNumber].setDaemon(True)
    serverThreads[threadNumber].start()
