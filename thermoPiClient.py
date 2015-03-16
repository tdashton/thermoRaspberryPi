#!/usr/bin/python

import ConfigParser
import datetime
import logging
import socket
import string
import sys
import time


config = ConfigParser.SafeConfigParser({'host': '', 'port': 2020})
config.read('config/client.cfg')

HOST = config.get('main', 'host')
PORT = config.getint('main', 'port')

w1_path = "/sys/bus/w1/devices/{0}/w1_slave"
sensors = ["10-000802bcf635", "10-000802b5535b"]

logging.basicConfig(filename='client.log', level=logging.DEBUG)

wsock = None

def open_socket(addr, port):
	if wsock == None:
		print "connecting to {0} port {1}".format(addr, port)
		create_socket(addr, port)
	else:
		print "already connected to {0} port {1}".format(addr, port)

def negotiate_connection(addr, port):
	try:
		#create an AF_INET, STREAM socket (TCP)
		negotiateSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		negotiateSocket.connect((addr, port))
		negotiateSocket.send("CONNECT LOG\n\n")
		data = negotiateSocket.recv(128)
		parsed = string.split(data, "\n")
		logging.debug(parsed)
		portString = string.split(parsed[1], ":")
		port = int(portString[1])
		logging.debug("asked to connect to port {0}".format(port))
		negotiateSocket.close()
		return port

	except socket.error, msg:
		print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
		sys.exit();

def create_socket(addr, port):
	global wsock
	port = negotiate_connection(addr, port)
	# time.sleep(1)
	wsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	wsock.connect((addr, port))

open_socket(HOST, PORT)

while True:
	for sensor in sensors:
		wfile = open(w1_path.format(sensor), 'r')
		data = wfile.read()
		wfile.close()
		temp = string.rsplit(data, '=', 1)[1]
		wsock.send('0|{0}|{1}|{2}'.format(datetime.datetime.now(), sensor, temp))
		# data = wsock.recv(128)

	time.sleep(60)

