#!/opt/bin/python

# Echo server program
import hashlib
import logging
import socket
import string
import threading
import collectorMysql
import Queue

HOST = ''                 # Symbolic name meaning all available interfaces
MAIN_PORT = 2020          # Arbitrary non-privileged port for connection negotiation
# (re)use following range of ports for establishing communication channels
PORT_RANGE = [2021, 2022, 2023, 2024, 2025]
serverThreads = []

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
    commandQueue = None
    clientCommand = False  # can the client receive GPIO commands
    h = None

    def __init__(self, listenPort, commandQueue=None):
        threading.Thread.__init__(self)
        if commandQueue is not None:
            self.commandQueue = commandQueue
        self.listenPort = listenPort
        self.h = hashlib.new('md5')
        pass

    def __del__(self):
        print "cowardly dying..."
        # TODO: for some reason the threads are never deallocated until the main
        # process is killed... maybe setDaemon()
        pass

    def initial_setup(self):
        self.serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serverSocket.bind((HOST, self.listenPort))
        self.serverSocket.listen(1)
        logging.info('worker listening on {0}'.format(self.listenPort))
        return self.serverSocket.accept()

    def run(self):
        conn, addr = self.initial_setup()

        #  TODO non blocking: https://docs.python.org/2/howto/sockets.html#non-blocking-sockets
        logging.debug("waiting for mode")
        mode = conn.recv(128)
        if mode.strip() == "CMD":
            self.clientCommand = True

        elif mode.strip() == "LOG":
            pass

        logging.debug("set mode:{0}".format(mode.strip()))
        conn.send("ACK:{0}".format(mode.strip()))

        while True:
            data = conn.recv(1024)
            # logging.debug(data)
            parsed = string.split(data, '|')
            parsed[-1] = parsed[-1].strip()
            if parsed[0] == '0':
                # proto version 0
                timestamp = parsed[1]
                sensorName = parsed[2]
                temp = parsed[3]
            if parsed[0] == '1':
                # proto version 1
                payloadType = parsed[1]
                if payloadType == 'DATA' and len(parsed) == 5:
                    timestamp = parsed[2]
                    sensorName = parsed[3]
                    temp = parsed[4]
                    collectorMysql.connectToDatasource()
                    collectorMysql.writeToDatasource(temp, timestamp, sensorName)
                else:
                    # logging.debug("it is a pass")
                    pass

            else:
                logging.debug("proto not recognized")
                logging.debug(parsed)
                break

            if self.commandQueue is not None:
                # logging.debug("checking queue")
                try:
                    queueValue = self.commandQueue.get(False, 0)
                    logging.debug("got from queue: {0}".format(queueValue))

                except Queue.Empty:
                    pass

            logging.debug("payload")
            self.h.update(data)
            payload = self.h.hexdigest()
            conn.sendall(payload)
            # data = conn.recv(1024)

            # if not data:
            #     logging.debug("nothing received")

        logging.debug("Worker closing port {0}".format(self.listenPort))
        self.serverSocket.close()
        PORT_RANGE.append(self.listenPort)
        self._Thread__stop()
        return

q = Queue.Queue()

while True:
    conn, addr = init_server_socket()
    logging.debug("processing request from {0} {1}.".format(addr[0], addr[1]))
    data = conn.recv(128)  # receive inital connect request
    logging.debug("data: " + data)
    threadNumber = len(serverThreads)

    if len(PORT_RANGE) == 0:
        conn.send("NO_PORTS")  # sorry, no more ports, threads are all running.

    # compatibility
    if data.strip() == "CONNECT CMD":  # client wants to connect and perform a command
        conn.send("CONNECT ACK\nREADY\n\n")
        data = conn.recv(1024)
        q.put(data)
        conn.send("COMMAND ACK\n\n")

    # compatibility
    elif data.strip() == "CONNECT LOG":  # compatibility
        port = PORT_RANGE.pop()
        logging.debug("threadNumber: {1} port: {0}".format(port, threadNumber))
        serverThreads.append(threadedServer(port, q))
        serverThreads[threadNumber].start()
        conn.send("CONNECT ACK\nNEGOTIATE:{0}\n\n".format(port))

    elif data.strip() == "CONNECT":  # connect, send port, and let the client tell threaded server was es kann.
        port = PORT_RANGE.pop()
        logging.debug("threadNumber: {1} port: {0}".format(port, threadNumber))
        serverThreads.append(threadedServer(port, q))
        serverThreads[threadNumber].start()
        conn.send("CONNECT ACK\nNEGOTIATE:{0}\n\n".format(port))

    else:
        conn.send("WHA?")

    # conn.shutdown(socket.SHUT_RDWR)
    conn.close()
