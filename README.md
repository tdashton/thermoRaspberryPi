# thermoRaspberryPi

A python server / client for sending temperature data between server and client.
The client sends the data via a socket connection and the sever upon receipt
writes it to a a permanent data store.

## Collector
The collector is the server, it implements different collector modules such as
collectorFile or collectorMysql. These collection modules write the received
data to the specified data source.

## Client 
The client is configured and started on the RaspberryPi / server reading the
temperatures and sends the data it collects to the Collector.

## Collector
to be done. To allow two way communication between the client(s) and the server
so the relay to control the thermostat can be toggled.
