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


from instruments.faulhaber import XYSingleFaulhaber
import numpy as np

import time

fh = XYSingleFaulhaber()

sq2 = np.sqrt(2)
3#fh = Faulhaber('COM12', 9600)

import json, pickle
import math

class MoveParams(dt.DataSet):
    outer_r = di.FloatItem('outer r.', 7)
    inner_r = di.FloatItem('inner r.', 5)
    fr1 = di.FloatItem('Freq 1', 0.5)
    fr2 = di.FloatItem('Freq 2', 0.1)
    
    vx = di.IntItem('Max x Vel.', 25000, min=0)
    vy = di.IntItem('Max y Vel.', 25000)
    #start = di.ButtonItem('Start', start_move)

try:
    mp = pickle.load(file('fh_move2'))
except:
    mp = MoveParams()

mp.edit()

pickle.dump(mp, file('fh_move2', 'w'))

fh.motor_init()
print(fh.get_pos())
fh.set_home()
print(fh.get_pos())
print(fh.is_moving())
print(mp.outer_r, mp.inner_r)

#fh.set_pos_mm(y=mp.outer_r, wait_for_move=True)
#fh.set_pos_mm(x=0, wait_for_move=True)
#fh.set_vel(mp.vx, mp.vy)


#win = pg.GraphicsWindow(title="Basic plotting examples")
#win.resize(1000,300)
#win.setWindowTitle('pyqtgraph example: Plotting')

#p1 = win.addPlot().plot()
#win.show()
t0 = time.time()
data = [], []

#def plot(data):
#    p1.setData(*data)


        
dr = mp.outer_r - mp.inner_r
mr = (mp.outer_r + mp.inner_r)/2.

while True:
    try:
        t = time.time() - t0
#        
 #       while time.time() - t0 < t + 1/float(mp.freq):
  #          app.processEvents()
        
        #pos = fh.get_pos()
        #data[0].append(t)+
        #plot(data)
    
        phi = 2*math.pi*mp.fr1 * t
        phi2 = 2*math.pi*mp.fr2 * t
        
        print(mr, dr)
        r = mr + np.sin(phi2)*dr/2.
        
        xpos = r*np.cos(phi)
        ypos = r*np.sin(phi)
        
        fh.set_pos_mm(xpos, ypos, False)
        print(fh.get_pos_mm())
        
        
    except KeyboardInterrupt:
        break

fh.set_pos_mm(0, 0, True)
time.sleep(1)
fh.motor_disable()

