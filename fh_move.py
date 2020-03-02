# -*- coding: utf-8 -*-
"""
Created on Tue Oct 24 14:09:54 2017

@author: 2dir
"""

from __future__ import print_function

import guidata

app = guidata.qapplication() # not required if a QApplication has already been created
#app.exec_()
import threading
import serial, time, random
from collections import namedtuple
import guidata.dataset.dataitems as di
import guidata.dataset.datatypes as dt


from Instruments.faulhaber import XYSingleFaulhaber
import numpy as np

import time

fh = XYSingleFaulhaber()

sq2 = np.sqrt(2)
3#fh = Faulhaber('COM12', 9600)

import json, pickle
import math

class MoveParams(dt.DataSet):
    xm = di.FloatItem('X Max.', 20)
    ym = di.FloatItem('Y Max.  (mm)', 20)
    xfr = di.FloatItem('X Freq', 5)
    yfr = di.FloatItem('Y Freq', 5.1)
    freq = di.FloatItem('CMD Freq',  10)
    vx = di.IntItem('Max x Vel.', 25000, min=0)
    vy = di.IntItem('Max y Vel.', 25000)
    #start = di.Buttcph1 Y176H pump625nm 0p7me probe 1710cm 1740cm pol senkonItem('Start', start_move)

try:
    mp = pickle.load(file('fh_move'))
except:
    mp = MoveParams()

mp.edit()

#pickle.dump(mp, file('fh_move', 'w'))

fh.motor_init()
print(fh.get_pos())
fh.set_home()
print(fh.get_pos())
print(fh.is_moving())

fh.set_pos_mm(y=mp.ym, wait_for_move=True)
fh.set_pos_mm(x=mp.xm, wait_for_move=True)
fh.set_vel(mp.vx, mp.vy)


#win = pg.GraphicsWindow(title="Basic plotting examples")
#win.resize(1000,300)
#win.setWindowTitle('pyqtgraph example: Plotting')

#p1 = win.addPlot().plot()
#win.show()
t0 = time.time()
data = [], []

#def plot(data):
#    p1.setData(*data)


class MoveThread(threading.Thread):
    def __init__(self):
        self.stop = threading.Event()        
        
    def run(self):
        while True:
            try:
                t = time.time() - t0
        #        
         #       while time.time() - t0 < t + 1/float(mp.freq):
          #          app.processEvents()
                
                #pos = fh.get_pos()
                #data[0].append(t)+
                #plot(data)
                
                xpos = mp.xm * math.cos(t*mp.xfr*math.pi*2)
                ypos = mp.ym * math.cos(t*mp.yfr*math.pi*2) +  2*math.cos(t*0.1*math.pi*2)
                #print(xpos, ypos)
                
                fh.set_pos_mm(xpos, ypos, False)

                
                
            except KeyboardInterrupt:
                break

        

print(mp.xfr)
while True:
    try:
        t = time.time() - t0
#        
 #       while time.time() - t0 < t + 1/float(mp.freq):
  #          app.processEvents()
        
        #pos = fh.get_pos()
        #data[0].append(t)+
        #plot(data)
        
        xpos = mp.xm * math.cos(t*mp.xfr*math.pi*2)+   1*math.cos(t*0.2*math.pi*2)
        ypos = mp.ym * math.cos(t*mp.yfr*math.pi*2) +  1*math.cos(t*0.3*math.pi*2)
        #print(xpos, ypos)
        
        fh.set_pos_mm(xpos, ypos, False)
        print(fh.get_pos_mm())
        
        
    except KeyboardInterrupt:
        break

fh.set_pos_mm(0, 0, True)
time.sleep(1)
fh.motor_disable()

