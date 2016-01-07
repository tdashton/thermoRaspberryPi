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
sensor = "10-000802b5535b.txt"
threadLock = threading.Lock()


class thermostatRunner (threading.Thread):

    requestedTemp = 20000

    def __init__(self, requestedTemp=20000):
        threading.Thread.__init__(self)
        if requestedTemp is not None:
            self.requestedTemp = requestedTemp
        pass

    def run(self):
        logging.debug("acquire")
        logging.debug(self.requestedTemp)
        threadLock.acquire()
        toggle_gpio(17)
        temp = get_temp()
        logging.debug(temp)
        while(temp < self.requestedTemp):
            temp = get_temp()
            logging.debug("heating while {0} < {1}".format(temp, self.requestedTemp))
            time.sleep(1)
            pass

        toggle_gpio(17)
        threadLock.release()
        logging.debug("released")
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


def toggle_gpio(pinId):
    print "GPIO.output(17, not GPIO.input(17))"
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
        runner = thermostatRunner(requestedTemp)
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
