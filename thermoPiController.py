#!/usr/bin/python

import logging
import RPi.GPIO as GPIO
import socket

HOST = ''                 # Symbolic name meaning all available interfaces
MAIN_PORT = 2010          # Arbitrary non-privileged port for connection 

BCIM_ID = 17;
GPIO.setmode(GPIO.BCM)
GPIO.setup(BCIM_ID, GPIO.OUT)

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))
logging.basicConfig(filename='controller.log', level=logging.DEBUG)
stringStatus = "STATUS:{0} {1}"


'''
for the main server
'''
def init_server_socket():
    logging.info("server listening on {0}".format(MAIN_PORT))
    serverSocket.listen(2)
    return serverSocket.accept()

'''
main prog loop
'''
while 1:
    conn, addr = init_server_socket()
    logging.debug("processing request from {0} {1}.".format(addr[0], addr[1]))
    data = conn.recv(128) # receive connection
    logging.debug("data: " + data)

    if data.strip() == "CMD TOGGLE": # client wants to connect and perform a command
        GPIO.output(17, not GPIO.input(BCIM_ID))
        conn.send(stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))

    elif data.strip() == "CMD STATUS": # client wants to connect and perform a command
        conn.send(stringStatus.format(BCIM_ID, GPIO.input(BCIM_ID)))

    else:
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()


# setup the GPIO Communcation

