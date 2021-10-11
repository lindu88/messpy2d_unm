# MessPy

## Device Control

_What is device control?_ 

Reading and controling hardware. Examples are beamshutters, cameras, mechanical stages, spectrometers and so on.

_How to do that?_

Before using it in MessPy, we have to be able do it from python. How, depends on the hardware, what kind of interface it uses?

*  Python Module --> Use directly. Quite common today. Look at Github.
*  Serial --> Use PySerial or PyVisa, latter removes some Boilerplate 
* Network --> Write directly to an socket, easily done in python
* dll --> Multiple options: ctypes, cffi, nicelib, cppyy, dragonffi 
* other --> Net libaries

### Serial device

Either real serial devices or virtual serial devices. Can send and recive bytes. 

Idea: Live-coding of an device module using a Serial Port.

***SC10*** from Thorlabs, controller for Beamshutter.



1. Find the correct connection settings in the manual. Create a connection.
2. Find the command structure in the manual, especially line-endings. Latter likley `'\n'`, `'\r'` or `'\r\n`. Remember: pyserial accpets bytes only. 
3. If the command structure is regular, write an helper function. 