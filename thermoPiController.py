#!/usr/bin/python

import ConfigParser
import logging
import RPi.GPIO as GPIO  # DEBUG_GPIO
import os.path
import Queue
import socket
import string
import threading
import time

config = ConfigParser.SafeConfigParser()
config.read('config/controller.cfg')

HOST = config.get('network', 'host')  # Symbolic name meaning all available interfaces
MAIN_PORT = config.getint('network', 'port')  # Arbitrary non-privileged port for connection

RUNNER_LOOP_SLEEP = 0.5
RUNOUT_HEAT_TIME = config.getint('main', 'runout_seconds')  # time to run the thermostat after the TEMP has been reached
DEFAULT_TEMP = config.getint('main', 'default_temperature')

BCIM_ID = config.getint('main', 'bcim_id')
GPIO.setmode(GPIO.BCM)  # DEBUG_GPIO
GPIO.setup(BCIM_ID, GPIO.OUT)  # DEBUG_GPIO
GPIO.setwarnings(False)  # DEBUG_GPIO

serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serverSocket.bind((HOST, MAIN_PORT))
logging.basicConfig(filename='controller.log', level=logging.DEBUG, format='%(asctime)s %(message)s')
stringStatus = "STATUS:{0} {1}"

w1_path = "/sys/bus/w1/devices/{0}/w1_slave"  # DEBUG_GPIO
sensor = config.get('main', 'sensor')  # DEBUG_GPIO
# w1_path = "{0}"  # DEBUG_GPIO
# sensor = "./tmp/10-000802b5535b.txt"  # DEBUG_GPIO
threadLock = threading.Lock()


'''
main thermostat logic, including how long to run and keeping track of the
current temperature (passed via Queue)
'''


class thermostatRunner(threading.Thread):

    commandQueue = None
    currentTemp = None
    requestedTemp = None
    requestedTime = 0
    requestedTimeRunning = 0
    # keep track of whether the gpio pin is toggled or not
    running = False
    runningTime = 0

    def __init__(self, mQueue=None, requestedTemp=None):
        threading.Thread.__init__(self)
        if requestedTemp is not None:
            logging.debug("temp")
            self.requestedTemp = int(requestedTemp)
        if mQueue is not None:
            self.commandQueue = mQueue
        else:
            logging.error("cannot run without queue")
            return
        pass

    def run(self):
        if not self.requestedTemp and not self.requestedTime:
            logging.warning("exiting, no time or temperature given")
            return
        logging.debug("Acquire lock")
        locked = threadLock.acquire(False)
        if not locked:
            logging.debug("Lock not acquired, already running")
            return

        while True:
            try:
                while not self.commandQueue.empty():
                    queueValue = self.commandQueue.get(False, 0)
                    # print "checking queue, found something:{0}".format(queueValue)
                    if 'temp' in queueValue:
                        logging.debug("setting temp to " + queueValue['temp'])
                        self.requestedTemp = int(queueValue['temp'])
                    if 'sensor' in queueValue:
                        # logging.debug("setting current temp to {0}".format(queueValue['sensor']))
                        self.currentTemp = int(queueValue['sensor'])
                    if 'time' in queueValue:
                        logging.debug("setting time to " + queueValue['time'])
                        self.requestedTime = int(queueValue['time'])
                    if 'cancel' in queueValue:
                        logging.debug("requested cancel")
                        self.requestedTime = 0
                        self.requestedTimeRunning = 0
                    if 'stop' in queueValue:
                        logging.debug("requested stop")
                        toggle_gpio(BCIM_ID, False, True)
                        return

            except Queue.Empty:
                pass

            if self.requestedTime > 0:
                toggle_gpio(BCIM_ID, True, self.running)
                self.set_running(True)
                if self.requestedTimeRunning <= self.requestedTime:
                    if self.runningTime % (10 / RUNNER_LOOP_SLEEP) == 0:
                        logging.debug("heating while {0} < {1}".format(self.requestedTimeRunning, self.requestedTime))
                    self.requestedTimeRunning = self.requestedTimeRunning + (1 * RUNNER_LOOP_SLEEP)
                    if self.requestedTimeRunning >= self.requestedTime:
                        self.requestedTime = self.requestedTimeRunning = 0
                        if self.currentTemp > self.requestedTemp:
                            # this extra condition is to avoid turning off the switch and then
                            # immediately back on if the requested temperature has not been reached
                            logging.debug("timer expired and requested temperature reached")
                            toggle_gpio(BCIM_ID, False, self.running)
                            self.set_running(False)

            else:
                if self.running is False:
                    if self.currentTemp is not None and self.currentTemp < self.requestedTemp:
                        toggle_gpio(BCIM_ID, True, self.running)
                        self.set_running(True)
                        logging.debug("heating while {0} < {1}".format(self.currentTemp, self.requestedTemp))
                else:
                    if self.currentTemp > self.requestedTemp:
                        # when the requested temperature has been reached, we set the timer
                        # to run the heater for a few more minutes to ensure we reach the temperature
                        logging.debug("setting runout time")
                        self.requestedTime = RUNOUT_HEAT_TIME

            time.sleep(RUNNER_LOOP_SLEEP)
            if self.running is True:
                self.runningTime = self.runningTime + (1 * RUNNER_LOOP_SLEEP)
                # logging.debug("running time {0}".format(self.runningTime))

        toggle_gpio(BCIM_ID, False, self.running)
        self.set_running(False)
        threadLock.release()
        logging.debug("Released Lock")
        pass

    def set_running(self, running):
        if self.running != running:
            logging.debug("set_running: {0}".format(running))
            self.running = running
            self.runningTime = 0

    def get_running(self):
        return self.running

    def get_time_remaining(self):
        return self.requestedTime - self.requestedTimeRunning

    def get_requested_temp(self):
        return self.requestedTemp


'''
get the temperature, we do this in its own thread because reading the
sensors can introduce a delay into the thermostatRunner. The temperature
must stay constant for at least a minute before it is reported.
'''


class sensorRunner(threading.Thread):

    tempList = []
    queue = None

    def __init__(self, mQueue=None):
        threading.Thread.__init__(self)
        if mQueue is not None:
            self.queue = mQueue
        for i in range(10):
            self.tempList.append(int(self.get_temp()))

        # logging.debug(self.tempList)

        pass

    def run(self):
        while True:
            try:
                self.tempList.append(self.get_temp())
                self.tempList = self.tempList[len(self.tempList)-10:]
                runnerTemp = max(self.tempList)
                self.queue.put({'sensor': runnerTemp})
                # logging.debug("putting temp in queue {0}".format(runnerTemp))
                # logging.debug(self.tempList)
            except Exception as ex:
                logging.warning(ex)
            time.sleep(60/10)

    def get_temp(self):
        if os.path.exists(w1_path.format(sensor)) is False:
            logging.warning("cannot read temperature")
            raise Exception(100, "cannot read temperature")
        wfile = open(w1_path.format(sensor), 'r')
        data = wfile.read()
        wfile.close()
        temp = string.rsplit(data, '=', 1)[1]
        return int(temp)


'''
for the main server
'''


def init_server_socket():
    logging.info("server listening on {0}".format(MAIN_PORT))
    serverSocket.listen(2)
    return serverSocket.accept()


def toggle_gpio(pinId, inputMode=False, currentStatus=False):
    if inputMode == currentStatus:
        return
    GPIO.output(pinId, inputMode)  # DEBUG_GPIO
    # print "GPIO.output({1}, {0})".format(inputMode, pinId)  # DEBUG_GPIO
    pass


'''
main prog loop
'''


q = Queue.Queue()
sensorRunner = sensorRunner(q)
sensorRunner.start()
runner = thermostatRunner(q, DEFAULT_TEMP)
runner.start()

while 1:
    conn, addr = init_server_socket()
    logging.debug("processing request from {0} {1}.".format(addr[0], addr[1]))
    data = conn.recv(128)  # receive connection
    logging.debug("data: " + data)

    if data.strip() == "CMD TEMP":  # client wants to connect and perform a command
        conn.send("READY\n")
        requestedTemp = conn.recv(128)
        q.put({'temp': requestedTemp.strip()})
        conn.send("ACK\n")
        pass

    elif data.strip() == "CMD TIME":  # client wants to connect and perform a command
        conn.send("READY\n")
        requestedTime = conn.recv(128)
        q.put({'time': requestedTime.strip()})
        conn.send("ACK\n")
        pass

    elif data.strip() == "CMD CANCEL":  # client wants to connect and perform a command
        q.put({'cancel': True})
        conn.send("ACK\n")
        pass

    elif data.strip() == "CMD STATUS":  # client wants to connect and perform a command
        conn.send("RUNNING:{0}\nTEMP:{1}\nTIME:{2}\n".format(int(runner.get_running()), runner.get_requested_temp(), runner.get_time_remaining()))
        pass

    elif data.strip() == "CMD STOP":  # client wants to connect and perform a command
        q.put({'stop': True})
        conn.send("ACK\n")
        pass

    else:
        conn.send("WHA?")

    conn.shutdown(socket.SHUT_RDWR)
    conn.close()
