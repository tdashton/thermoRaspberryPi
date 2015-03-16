#!/opt/bin/python

import ConfigParser
import datetime

config = ConfigParser.RawConfigParser()
config.read('config/collector.cfg')

FILENAME = config.get('file', 'filename')

fileHandle = None

def connectToDatasource():
    global fileHandle
    if fileHandle == None:
        fileHandle = open(FILENAME, 'a', 1)
        print "opening file"

def writeToDatasource(temp = 0, date = datetime.datetime.now(), sensorName = 'unknown'):
    connectToDatasource()
    fileHandle.write("INSERT INTO log (value, datetime, fk_sensor) VALUES ({0}, '{1}', '{2}')"
        .format(temp, date, sensorName))

def close():
    global fileHandle
    fileHandle.close()