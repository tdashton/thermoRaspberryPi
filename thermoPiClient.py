#!/usr/bin/python

import datetime
import socket
import string
import sys
import time

w1_path = "/sys/bus/w1/devices/{}/w1_slave"
sensors = ["10-000802bcf635", "10-000802b5535b"]

wsock = None

def open_socket(addr, port):
	if wsock == None:
		print "connecting to {} port {}".format(addr, port)
		create_socket(addr, port)
	else:
		print "already connected to {} port {}".format(addr, port)

def create_socket(addr, port):
	global wsock
	try:
		#create an AF_INET, STREAM socket (TCP)
		wsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		wsock.connect((addr, port))
	except socket.error, msg:
		print 'Failed to create socket. Error code: ' + str(msg[0]) + ' , Error message : ' + msg[1]
		sys.exit();

while True:
	for sensor in sensors:
		wfile = open(w1_path.format(sensor), 'r')
		data = wfile.read()
		wfile.close()
		temp = string.rsplit(data, '=', 1)[1]
		open_socket('192.168.0.200', 2020)
		wsock.send('0|{0}|{1}|{2}'.format(datetime.datetime.now(), sensor, temp))

	time.sleep(10)


