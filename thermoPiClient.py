#!/usr/bin/python

import ConfigParser
import datetime
import logging
import Queue
import socket
import string
import sys
import threading
import time


config = ConfigParser.RawConfigParser()
config.read('config/client.cfg')

HOST = config.get('network', 'host')
PORT = config.getint('network', 'port')

w1_path = "/sys/bus/w1/devices/{0}/w1_slave"
sensorsConfig = config.items('sensors')

sensors = []
for sensor in sensorsConfig:
    sensors.append(sensor[1])

logging.basicConfig(filename='client.log', level=logging.DEBUG)


class threadedClient (threading.Thread):

    wsock = None
    commandQueue = None
    port = None

    def __init__(self, commandQueue=None):
        threading.Thread.__init__(self)
        if commandQueue is not None:
            self.commandQueue = commandQueue
        pass

    def __del__(self):
        print "cowardly dying..."
        # TODO: for some reason the threads are never deallocated until the main
        # process is killed... maybe setDaemon()
        pass

    def run(self):
        self.open_socket(HOST, PORT)
        # sends that i am a logger
        self.wsock.send("LOG")

        data = self.wsock.recv(128)

        while True:
            # print "checking queue"
            if self.commandQueue is not None:
                try:
                    queueValue = self.commandQueue.get(False, 0)
                    # print "checking queue, found something:{0}".format(queueValue)
                    self.wsock.send(queueValue)
                    data = self.wsock.recv(128)
                    print data

                except Queue.Empty:
                    # print "nothing in the queue"
                    pass
            time.sleep(1)

    def open_socket(self, addr, port):
        if self.wsock is None:
            print "connecting to {0} port {1}".format(addr, port)
            self.wsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.wsock.connect((addr, port))
        else:
            print "already connected to {0} port {1}".format(addr, port)

q = Queue.Queue()
client = threadedClient(q)
client.start()

i = 0
while True:
    if i == 0:
        i = 0
        for sensor in sensors:
            # 24 00 4b 46 ff ff 0e 10 3d : crc=3d YES
            # 24 00 4b 46 ff ff 0e 10 3d t=17875
            # data = "24 00 4b 46 ff ff 0e 10 3d t=17875"
            wfile = open(w1_path.format(sensor), 'r')
            data = wfile.read()
            wfile.close()
            temp = string.rsplit(data, '=', 1)[1]
            q.put('3|SENSOR|{0}|{1}'.format(sensor, temp))
    else:
        # q.put("1|PASS")
        pass
    i = i + 1
    if i == 60:
        i = 0

    time.sleep(1)
