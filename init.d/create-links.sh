sudo ln -s /home/pi/thermoRaspberryPi/init.d/thermopi-client.sh  /etc/init.d/thermopi-03-client.sh
sudo ln -s /home/pi/thermoRaspberryPi/init.d/thermopi-controller.sh  /etc/init.d/thermopi-02-controller.sh
sudo ln -s /home/pi/thermoRaspberryPi/init.d/thermopi-collector.sh  /etc/init.d/thermopi-01-collector.sh

sudo update-rc.d thermopi-03-client.sh defaults
sudo update-rc.d thermopi-02-controller.sh defaults
sudo update-rc.d thermopi-01-collector.sh defaults
