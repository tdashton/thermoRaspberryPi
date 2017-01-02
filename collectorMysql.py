#!/opt/bin/python

import ConfigParser
import MySQLdb
import datetime
import os

config = ConfigParser.RawConfigParser()
config.read('config/collector.cfg')

username = config.get('mysql', 'username')
password = config.get('mysql', 'password')
host = config.get('mysql', 'host')
dbName = config.get('mysql', 'dbName')

db = {os.getpid(): None}


def connectToDatasource():
    global db
    if db[os.getpid()] is None:
        db[os.getpid()] = MySQLdb.connect(user=username, passwd=password, host=host, db=dbName)
        print "connecting to db, for pid {0}".format(os.getpid())
        try:
            db[os.getpid()].query("SET AUTOCOMMIT=1")
        except MySQLdb.ProgrammingError:
            print "error connecting to the database"
            pass


def writeToDatasource(temp=0, date=datetime.datetime.now(), sensorName='unknown'):
    connectToDatasource()
    try:
        db[os.getpid()].query(
            "INSERT INTO logs (value, datetime, fk_sensor) VALUES ({0}, '{1}', '{2}')"
            .format(temp, date, sensorName))

    except MySQLdb.ProgrammingError:
        print "error in query with parameters: {0} {1} {2} ".format(temp, date, sensorName)
        pass


def writeToControlDatasource(value=0, date=datetime.datetime.now(),):
    connectToDatasource()
    try:
        db[os.getpid()].query(
            "INSERT INTO logs_control (status, datetime) VALUES ({0}, '{1}')"
            .format(value, date))

    except MySQLdb.ProgrammingError:
        print "error in query with parameters: {0} {1} ".format(value, date)
        pass


def close():
    global db
    db[os.getpid()].close()
