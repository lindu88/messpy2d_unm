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

### Python module

Nowadays it gets more common of hardware manufactures to offer python modules. 
Note that these sometimes are not that well written, since these are quite often
written of C-programmers with no python experience. If you are comfortable,
feel free to write you own wrapper.

### Serial device

Either real serial devices or virtual serial devices. Can send and recive bytes.
This can be done by using the pyserial module. There is also pyvisa, which offers
a lot of additional useful helper functions. 

Idea: Live-coding of an device module using a Serial Port.

***SC10*** from Thorlabs, controller for Beamshutter.

1. Find the correct connection settings in the manual. Create a connection.
2. Find the command structure in the manual, especially line-endings. 
   Latter likely is one of `'\n'`, `'\r'` or `'\r\n`. Remember: pyserial accepts bytes only, use `b'commandstring'`. 
3. If the command structure is regular, write a helper function to send and receive commands. 

### Network

Python includes everything to communicate over
