#!/opt/bin/python

import ConfigParser
import sqlite3
import datetime

config = ConfigParser.RawConfigParser()
config.read('config/collector.cfg')

dbName = config.get('sqlite3', 'dbName')

db = {}


def connectToDatasource(connectionId):
    global db
    if connectionId not in db.keys():
        db[connectionId] = sqlite3.connect(database=dbName, isolation_level="IMMEDIATE")
        print "connecting to db, connection id:{0}".format(connectionId)
        try:
            db[connectionId].execute("SELECT 1")
        except sqlite3.Error:
            print "error connecting to the database"
            pass


def writeToDatasource(connectionId, temp=0, date=datetime.datetime.now(), sensorName='unknown'):
    connectToDatasource(connectionId)
    try:
        db[connectionId].execute(
            "INSERT INTO logs (value, datetime, fk_sensor) VALUES ({0}, '{1}', '{2}')"
            .format(temp, date, sensorName))
        db[connectionId].commit()

        print "INSERT INTO logs (value, datetime, fk_sensor) VALUES ({0}, '{1}', '{2}')".format(temp, date, sensorName)

    except sqlite3.Error:
        print "error in query with parameters: {0} {1} {2} ".format(temp, date, sensorName)
        pass


def writeToControlDatasource(connectionId, value=0, date=datetime.datetime.now(),):
    connectToDatasource(connectionId)
    try:
        db[connectionId].execute(
            "INSERT INTO logs_control (status, datetime) VALUES ({0}, '{1}')"
            .format(value, date))

    except sqlite3.Error:
        print "error in query with parameters: {0} {1} ".format(value, date)
        pass


def close(connectionId):
    global db
    db[connectionId].close()
    del db[connectionId]
