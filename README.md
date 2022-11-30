# Using a low-cost Raspberry pi enabled Gnss reflectometer to log and upload NMEA messages

[Instructions for building together the casing](doc/README.md)

# Using the NMEA logger
---

### Install this python module from the repository root directory
```
pip install .
```

### Copy and Change the yaml config file

The file ``nmeaconfig.yml`` is the file used for configuration. Copy the file to the user's home and open it with a text editor and change the value.

* ``file_base`` *ex: myfile*, the basename used for naming the  output (date and increment will be appended to this e.g. providing `testname` will result in `testname_2022-01-01_00.gz`
* ``data_dir`` *ex: /home/user*, the path where the data logs will be stored
* ``device`` *ex: /dev/ttyAMA0*, the linux serial device path which produces the nmea output   
* ``baudrate`` *ex: 9600*, the baudrate of the serial port   
* ``serialsleep`` *ex: 20*, set the amount of microseconds to sleep between serial reads (this time will be made available to do other tasks such as uploading)
* ``webdav`` 
	* ``url`` Webdav upload address
	* ``user``
	* ``password``

### How to setup a service file

If you want your raspberry to automatically launch the logger on boot, you need to create a service file (see the example file [nmealogger.service](nmealogger.service). This allows to simply plug your raspberry and directly execute a program without having to open a terminal. This is very useful for field survey where the raspberry boots and runs without interactive user input, or where a power failure will result in a reboot.


Now to create the service, copy the modified [nmealogger.service file](nmealogger.service) into the right directory:  
```
sudo cp nmealogger.service /etc/systemd/system/nmealogger.service
```

Make sure to replace *User* with a user who can access the serial port and the *data_dir* provided in the [configuration file](nmeaconfig.yml)
Before starting the service, execute the following line. It reloads to take the change into account
```
sudo systemctl daemon-reload
```
You can then start the service, if the service file is installed in the right directory (``/etc/systemd/system/``)
```
sudo systemctl start nmealogger.service
```
You can see if your service file is properly running by executing
```
sudo systemctl status nmealogger.service
```
You can also of course stop the service
```
sudo systemctl stop nmealogger.service
```
Your service file is now running on your raspberry until the board is shutdown. If you want to start it on boot *enable* it:

```
sudo systemctl enable nmealogger.service
```





## Authors

**Lubin Roineau, Roelof Rietbroek**


