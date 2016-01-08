#!/usr/bin/python

import datetime
import logging
# import RPi.GPIO as GPIO
import socket
import string
import threading
import time

HOST = ''  # Symbolic name meaning all available interfaces
MAIN_PORT = 2010  # Arbitrary non-privileged port for connection

MINIMUM_HEAT_TIME = 1 * 60
MAXIMUM_HEAT_TIME = 60 * 60

BCIM_ID = 17
# GPIO.setmode(GPIO.BCM)
# GPIO.setup(BCIM_ID, GPIO.OUT)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))
logging.basicConfig(filename='controller.log', level=logging.DEBUG)
stringStatus = "STATUS:{0} {1}"

# w1_path = "/sys/bus/w1/devices/{0}/w1_slave"
# sensor = "10-000802b5535b"
w1_path = "{0}"
sensor = "10-000802b5535b.x"
threadLock = threading.Lock()


class thermostatRunner (threading.Thread):

    requestedTemp = 20000
    timeRunning = 0

    def __init__(self, requestedTemp=20000):
        threading.Thread.__init__(self)
        if requestedTemp is not None:
            self.requestedTemp = requestedTemp
        pass

    def run(self):
        logging.debug("Acquire lock")
        locked = threadLock.acquire(False)
        if not locked:
            logging.debug("Lock not acquired, alread running")
            return
        toggle_gpio(17, True)
        temp = get_temp()
        while(temp < self.requestedTemp or self.timeRunning <= MINIMUM_HEAT_TIME):
            temp = get_temp()
            logging.debug("heating while {0} < {1} : running for {2}".format(temp, self.requestedTemp, self.timeRunning))
            time.sleep(1)
            self.timeRunning = self.timeRunning + 1
            if self.timeRunning > MAXIMUM_HEAT_TIME:
                break
            pass

        toggle_gpio(17, False)
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
    wfile = open(w1_path.format(sensor), 'r')
    data = wfile.read()
    wfile.close()
    temp = string.rsplit(data, '=', 1)[1]
    return temp


def toggle_gpio(pinId, inputMode=False):
    print "GPIO.output({1}, {0})".format(inputMode, pinId)
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
        temp = get_temp()
        logging.debug("starting at {0}".format(temp))
        runner = thermostatRunner(requestedTemp.strip())
        runner.start()
        conn.send("ACK")

        # GPIO.output(17, not GPIO.input(17))
        # conn.send(stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))
        # logging.debug(datetime.datetime.now() + " " + stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))
        pass

    elif data.strip() == "CMD TIME":  # client wants to connect and perform a command
        # GPIO.output(17, not GPIO.input(17))
        # conn.send(stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))
        # logging.debug(datetime.datetime.now() + " " + stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))
        pass

    elif data.strip() == "CMD STATUS":  # client wants to connect and perform a command
        # conn.send(stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))
        pass

    else:
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
