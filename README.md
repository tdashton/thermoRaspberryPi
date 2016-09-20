# thermoRaspberryPi

Control your thermostat with your Raspberry Pi, thermoRaspberryPi is a 
python server / client for sending temperature data between server and client.
The client sends the data via a socket connection and the sever upon receipt
writes it to a a permanent data store.

First steps:

1. setup configuration files
2. create init.d symlinks, see init.d directory in repository
3. run daemons

# thermoRaspberyPi Daemons

## Controller
Allows you to control your Pi / thermostat via a socket connection.

## Collector
The collector is the server, it implements different collector modules such as
collectorFile or collectorMysql. These collection modules write the received
data to the specified data source.

## Client 
The client is configured and started on the RaspberryPi / server reading the
temperatures and sends the data it collects to the Collector.

# What next?
see the accompanying Web and Android project to control your thermoRaspberryPi from your Android.
