#!/usr/bin/python

import logging
import RPi.GPIO as GPIO
import os.path
import socket
import string
import threading
import time

HOST = ''  # Symbolic name meaning all available interfaces
MAIN_PORT = 2010  # Arbitrary non-privileged port for connection

MINIMUM_HEAT_TIME = 5 * 60
MAXIMUM_HEAT_TIME = 60 * 60

BCIM_ID = 17
GPIO.setmode(GPIO.BCM)
GPIO.setup(BCIM_ID, GPIO.OUT)
GPIO.setwarnings(False)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))
logging.basicConfig(filename='controller.log', level=logging.DEBUG)
stringStatus = "STATUS:{0} {1}"

w1_path = "/sys/bus/w1/devices/{0}/w1_slave"
sensor = "10-000802b5535b"
# w1_path = "{0}"
# sensor = "10-000802b5535b.txt"
threadLock = threading.Lock()


class thermostatRunner (threading.Thread):

    requestedTemp = None
    requestedTime = None
    timeRunning = 0

    def __init__(self, requestedTemp=None, runTime=None):
        threading.Thread.__init__(self)
        if requestedTemp is not None:
            logging.debug("temp")
            self.requestedTemp = int(requestedTemp)
        if runTime is not None:
            logging.debug("time")
            self.requestedTime = int(runTime)
        pass

    def run(self):
        if not self.requestedTemp and self.requestedTime:
            logging.warning("exiting, no time or temperature given")
        logging.debug("Acquire lock")
        locked = threadLock.acquire(False)
        if not locked:
            logging.debug("Lock not acquired, already running")
            return
        toggle_gpio(BCIM_ID, True)
        try:
            while(self.test_condition() or self.timeRunning <= MINIMUM_HEAT_TIME):
                time.sleep(1)
                self.timeRunning = self.timeRunning + 1
                if self.timeRunning > MAXIMUM_HEAT_TIME:
                    logging.warning("max heating time reached")
                    break
                pass
        except Exception as ex:
            logging.warning(ex)

        toggle_gpio(BCIM_ID, False)
        threadLock.release()
        logging.debug("Released Lock")
        pass

    def test_condition(self):
        if self.requestedTime:
            if self.timeRunning < self.requestedTime:
                logging.debug("heating while {0} < {1}".format(self.timeRunning, self.requestedTime))
                return True
        elif self.requestedTemp:
            temp = get_temp()
            if temp is False:
                logging.warning("cannot read temperature")
                raise Exception(100, "cannot read temperature")
            if temp < self.requestedTemp:
                logging.debug("heating while {0} < {1} : running for {2}".format(temp, self.requestedTemp, self.timeRunning))
                return True
            else:
                return False
        else:
            return False

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
        return False
    wfile = open(w1_path.format(sensor), 'r')
    data = wfile.read()
    wfile.close()
    temp = string.rsplit(data, '=', 1)[1]
    return int(temp)


def toggle_gpio(pinId, inputMode=False):
    GPIO.output(pinId, inputMode)
    # print "GPIO.output({1}, {0})".format(inputMode, pinId)
    pass

'''
main prog loop
'''
# q = Queue.Queue()

while 1:
    conn, addr = init_server_socket()
    logging.debug("processing request from {0} {1}.".format(addr[0], addr[1]))
    data = conn.recv(128)  # receive connection
    logging.debug("data: " + data)

    if data.strip() == "CMD TEMP":  # client wants to connect and perform a command
        conn.send("OK")
        requestedTemp = conn.recv(128)
        runner = thermostatRunner(requestedTemp.strip())
        runner.start()
        conn.send("ACK")
        pass

    elif data.strip() == "CMD TIME":  # client wants to connect and perform a command
        conn.send("OK")
        requestedTime = conn.recv(128)
        runner = thermostatRunner(None, requestedTime.strip())
        runner.start()
        conn.send("ACK")
        pass

    elif data.strip() == "CMD STATUS":  # client wants to connect and perform a command
        conn.send(stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))
        pass

    else:
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
