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

db = None


def connectToDatasource():
    global db
    if db is None:
        db = MySQLdb.connect(user=username, passwd=password, host=host, db=dbName)
        print "connecting to db"


def writeToDatasource(temp=0, date=datetime.datetime.now(), sensorName='unknown'):
    connectToDatasource()
    try:
        db.query(
            "INSERT INTO logs (value, datetime, fk_sensor) VALUES ({0}, '{1}', '{2}')"
            .format(temp, date, sensorName))

    except MySQLdb.ProgrammingError:
        print "error in query with parameters: {0} {1} {2} ".format(temp, date, sensorName)
        pass


def writeToControlDatasource(value=0, date=datetime.datetime.now(),):
    connectToDatasource()
    try:
        db.query(
            "INSERT INTO logs_control (value, datetime) VALUES ({0}, '{1}')"
            .format(value, date))

    except MySQLdb.ProgrammingError:
        print "error in query with parameters: {0} {1} ".format(value, date)
        pass


def close():
    global db
    db.close()
