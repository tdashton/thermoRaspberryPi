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
        mode = conn.recv(128)
        if mode.strip() == "CMD":
            self.clientCommand = True

        elif mode.strip() == "LOG":
            pass

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
                print "done"
                break

            payload = self.h.hexdigest()
            if self.commandQueue is not None:
                print "checking queue"
                try:
                    queueValue = self.commandQueue.get(False, 0)
                    print("got from queue: {0}".format(queueValue))
                    payload += queueValue

                except Queue.Empty:
                    pass

            collectorMysql.connectToDatasource()
            collectorMysql.writeToDatasource(temp, timestamp, sensorName)

            self.h.update(data)
            conn.sendall(payload)

            if not data:
                break

        self.serverSocket.close()
        PORT_RANGE.append(self.listenPort)
        logging.debug("Worker closing port {0}".format(self.listenPort))
        self._Thread__stop()
        return


while 1:
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

    # compatibility
    elif data.strip() == "CONNECT LOG":  # compatibility
        port = PORT_RANGE.pop()
        logging.debug("threadNumber: {1} port: {0}".format(port, threadNumber))
        serverThreads.append(threadedServer(port))
        serverThreads[threadNumber].start()
        conn.send("CONNECT ACK\nNEGOTIATE:{0}\n\n".format(port))

    elif data.strip() == "CONNECT":  # connect, send port, and let the client tell threaded server was es kann.
        port = PORT_RANGE.pop()
        q = Queue.Queue()
        logging.debug("threadNumber: {1} port: {0}".format(port, threadNumber))
        serverThreads.append(threadedServer(port, q))
        serverThreads[threadNumber].start()
        conn.send("CONNECT ACK\nNEGOTIATE:{0}\n\n".format(port))

    else:
        for mThread in serverThreads:
            mThread.commandQueue.put("something in the queue!")
            print "put something in queue"
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
