#!/usr/bin/python

import logging
# import RPi.GPIO as GPIO  # DEBUG_GPIO
import os.path
import Queue
import socket
import string
import threading
import time

HOST = ''  # Symbolic name meaning all available interfaces
MAIN_PORT = 2010  # Arbitrary non-privileged port for connection

MINIMUM_HEAT_TIME = 1 * 60
MAXIMUM_HEAT_TIME = 60 * 60
DEFAULT_TEMP = 17 * 1000

BCIM_ID = 17
# GPIO.setmode(GPIO.BCM)  # DEBUG_GPIO
# GPIO.setup(BCIM_ID, GPIO.OUT)  # DEBUG_GPIO
# GPIO.setwarnings(False)  # DEBUG_GPIO

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))
logging.basicConfig(filename='controller.log', level=logging.DEBUG)
stringStatus = "STATUS:{0} {1}"

# w1_path = "/sys/bus/w1/devices/{0}/w1_slave"  # DEBUG_GPIO
# sensor = "10-000802b5535b"  # DEBUG_GPIO
w1_path = "{0}"  # DEBUG_GPIO
sensor = "10-000802b5535b.txt"  # DEBUG_GPIO
threadLock = threading.Lock()


class thermostatRunner (threading.Thread):

    commandQueue = None
    requestedTemp = None
    requestedTime = 0
    timeRunning = 0
    running = False

    def __init__(self, mQueue=None, requestedTemp=None):
        threading.Thread.__init__(self)
        if requestedTemp is not None:
            logging.debug("temp")
            self.requestedTemp = int(requestedTemp)
        if mQueue is not None:
            self.commandQueue = mQueue
        else:
            logging.error("cannot run without queue")
            return
        pass

    def run(self):
        if not self.requestedTemp and not self.requestedTime:
            logging.warning("exiting, no time or temperature given")
            return
        logging.debug("Acquire lock")
        locked = threadLock.acquire(False)
        if not locked:
            logging.debug("Lock not acquired, already running")
            return

        while True:
            try:
                currentTemp = get_temp()
            except Exception as ex:
                logging.warning(ex)

            try:
                queueValue = self.commandQueue.get(False, 0)
                print "checking queue, found something:{0}".format(queueValue)
                if 'temp' in queueValue:
                    print "setting temp to " + queueValue['temp']
                    self.requestedTemp = int(queueValue['temp'])
                if 'time' in queueValue:
                    print "setting time to " + queueValue['time']
                    self.requestedTime = int(queueValue['time'])
                if 'cancel' in queueValue:
                    print "requested cancel "
                if 'stop' in queueValue:
                    print "requested stop"
                    return

            except Queue.Empty:
                print "nothing in the queue"
                pass

            if self.requestedTime > 0:
                toggle_gpio(BCIM_ID, True, self.running)
                self.running = True
                logging.debug("time set to {0}".format(self.requestedTime))
                if self.timeRunning <= self.requestedTime:
                    logging.debug("heating while {0} < {1}".format(self.timeRunning, self.requestedTime))
                    self.timeRunning = self.timeRunning + 1
                    if self.timeRunning == self.requestedTime:
                        self.requestedTime = 0
                        if currentTemp > xself.requestedTemp:
                            logging.debug("timer expired and requuested temperature not reached")
                            toggle_gpio(BCIM_ID, False, self.running)
                            self.running = False
            else:
                if currentTemp <= self.requestedTemp:
                    toggle_gpio(BCIM_ID, True, self.running)
                    self.running = True
                    logging.debug("heating while {0} < {1} : running for {2}".format(currentTemp, self.requestedTemp, self.timeRunning))
                else:
                    toggle_gpio(BCIM_ID, False, self.running)
                    self.running = False

            time.sleep(1)

        toggle_gpio(BCIM_ID, False, self.running)
        self.running = False
        threadLock.release()
        logging.debug("Released Lock")
        pass


'''
for the main server
'''


def init_server_socket():
    logging.info("server listening on {0}".format(MAIN_PORT))
    serverSocket.listen(2)
    return serverSocket.accept()


'''
get the temperature
'''


def get_temp():
    if os.path.exists(w1_path.format(sensor)) is False:
        logging.warning("cannot read temperature")
        raise Exception(100, "cannot read temperature")
    wfile = open(w1_path.format(sensor), 'r')
    data = wfile.read()
    wfile.close()
    temp = string.rsplit(data, '=', 1)[1]
    return int(temp)


def toggle_gpio(pinId, inputMode=False, currentStatus=False):
    if inputMode == currentStatus:
        return
    # GPIO.output(pinId, inputMode)  # DEBUG_GPIO
    print "GPIO.output({1}, {0})".format(inputMode, pinId)  # DEBUG_GPIO
    pass

'''
main prog loop
'''


q = Queue.Queue()
runner = thermostatRunner(q, DEFAULT_TEMP)
runner.start()

while 1:
    conn, addr = init_server_socket()
    logging.debug("processing request from {0} {1}.".format(addr[0], addr[1]))
    data = conn.recv(128)  # receive connection
    logging.debug("data: " + data)

    if data.strip() == "CMD TEMP":  # client wants to connect and perform a command
        conn.send("READY\n")
        requestedTemp = conn.recv(128)
        q.put({'temp': requestedTemp.strip()})
        conn.send("ACK\n")
        pass

    elif data.strip() == "CMD TIME":  # client wants to connect and perform a command
        conn.send("READY\n")
        requestedTime = conn.recv(128)
        q.put({'time': requestedTime.strip()})
        conn.send("ACK\n")
        pass

    elif data.strip() == "CMD STATUS":  # client wants to connect and perform a command
        # conn.send(stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))  # DEBUG_GPIO
        pass

    else:
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
