#!/opt/bin/python

import MySQLdb
import datetime

username = "temp"
password = "temp"
host = "localhost"
dbName = "temperature"

db = None

def connectToDatasource():
    global db
    if db == None:
        db = MySQLdb.connect(user = username, passwd = password, host = host, db = dbName)
        print "connecting to db"

def writeToDatasource(temp = 0, date = datetime.datetime.now(), sensorName = 'unknown'):
    connectToDatasource()
    try:
        db.query("INSERT INTO logs (value, datetime, fk_sensor) VALUES ({0}, '{1}', '{2}')"
            .format(temp, date, sensorName))
    except _mysql_exceptions.ProgrammingError:
        print "error in query with parameters: {} {} {} ".format(temp, date, sensorName)
        pass

def close():
    global db
    db.close()