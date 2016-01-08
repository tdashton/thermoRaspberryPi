# Latest Status

proof of concept: thread.py
python thread runs in the background even when time.sleep is called

implementation idea:
client runs in its own thread, maintaining open communications with the
server in a nonblocking fashion, i.e. running recv() inside the while True loop
when it receives data from the server it prints it as before (todo: to be sent to
the gpio) and otherwise the python script (non-threaded) also runs in a loop
and sends the readings as before every sixty seconds. This time it sends them
into the separate thread using the Queue class.


24.12.2015:
working as above

still need to add a timer feature and or allow a temperature to be set from 
outside to have the pi act as a thermostat
