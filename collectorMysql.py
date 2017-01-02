#!/opt/bin/python

import ConfigParser
import MySQLdb
import datetime

config = ConfigParser.RawConfigParser()
config.read('config/collector.cfg')

username = config.get('mysql', 'username')
password = config.get('mysql', 'password')
host = config.get('mysql', 'host')
dbName = config.get('mysql', 'dbName')

db = {}


def connectToDatasource(connectionId):
    global db
    if connectionId not in db.keys():
        db[connectionId] = MySQLdb.connect(user=username, passwd=password, host=host, db=dbName)
        print "connecting to db, connection id:{0}".format(connectionId)
        try:
            db[connectionId].query("SET AUTOCOMMIT=1")
        except MySQLdb.ProgrammingError:
            print "error connecting to the database"
            pass


def writeToDatasource(connectionId, temp=0, date=datetime.datetime.now(), sensorName='unknown'):
    connectToDatasource(connectionId)
    try:
        db[connectionId].query(
            "INSERT INTO logs (value, datetime, fk_sensor) VALUES ({0}, '{1}', '{2}')"
            .format(temp, date, sensorName))

    except MySQLdb.ProgrammingError:
        print "error in query with parameters: {0} {1} {2} ".format(temp, date, sensorName)
        pass


def writeToControlDatasource(connectionId, value=0, date=datetime.datetime.now(),):
    connectToDatasource(connectionId)
    try:
        db[connectionId].query(
            "INSERT INTO logs_control (status, datetime) VALUES ({0}, '{1}')"
            .format(value, date))

    except MySQLdb.ProgrammingError:
        print "error in query with parameters: {0} {1} ".format(value, date)
        pass


def close(connectionId):
    global db
    db[connectionId].close()
    del db[connectionId]
