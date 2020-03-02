# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 16:34:17 2013

@author: Femtos
"""

import serial, time, random


try:
    s
except NameError:
    s = serial.Serial(1, 19200)
s.timeout = .5

s.write('1sp13000\r\n')
s.write('2sp13000\r\n')
#print "1 ", s.read(4)
s.write('1en\r\n')
s.write('2en\r\n')
print "2 ", s.read(4)

pos = range(-200000, 200001, 50000)
ypos = range(-200000, 200000, 10000)
i = 0
y = 0#
s.write('1la0\rm\r')
s.write('2la0\rm\r')
while True:
    #####time.sleep(1)
    #####print '1la'+str(pos[i])+'\r'
    if i%2==0:
        y = (y+1) % len(ypos)
        print ypos[y]
        s.write('1la'+str(random.randint(-150000, 150000))+'\r')

    s.write('2la'+str(pos[i])+'\r')
    ##print s.read(4)
    #s.readline()
    #####print s.read(4L)
    s.write('m\r')
    #
    ##print s.readline()
    ####
    i = (i + 1) % len(pos)
##
    print i
    time.sleep(0.1)
