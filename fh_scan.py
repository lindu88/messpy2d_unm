# -*- coding: utf-8 -*-
"""
Created on Mon Jul 29 16:34:17 2013

@author: Femtos
"""
from __future__ import print_function

import guidata

app = guidata.qapplication() # not required if a QApplication has already been created
#app.exec_()

import serial, time, random
from collections import namedtuple
import guidata.dataset.dataitems as di
import guidata.dataset.datatypes as dt

from Instruments.cam_phasetec import _ircam
cam = _ircam
from Instruments.faulhaber import XYSingleFaulhaber
fh = XYSingleFaulhaber()

import numpy as np
import scipy.special as spec
import scipy.optimize as opt
import os
import matplotlib
import pyqtgraph as pg
import time

#matplotlib.use('qt4agg')
#from matplotlib import pyplot as plt

sq2 = np.sqrt(2)
#fh = Faulhaber('COM2')

import json

tmp_dic = {'sc': False,
           'sp': 0,
           'spx': 0,
           'epx': 1,
           'ep': 1,
           'step':0.1,
           'do_y': True,
           'shots': 50,
           'do_x': True}

try:
    tmp_dic2 = json.load('fh_scan')
    tmp_dic.update(tmp_dic2)
except:
    pass

fh.get_pos() 

class ScanParams(dt.DataSet):
    do_y = di.BoolItem('Scan y', default=tmp_dic['do_y'] )
    start_pos_y = di.FloatItem('Starting pos y (mm)', tmp_dic['sp'])
    end_pos_y = di.FloatItem('End Pos (mm)',  tmp_dic['ep'])
    
    do_x = di.BoolItem('Scan x', default=tmp_dic['do_x'] )    
    start_pos_x = di.FloatItem('Starting pos x (mm)', tmp_dic['spx'])
    end_pos_x = di.FloatItem('End Pos (mm)',  tmp_dic['epx'])
    
    step = di.FloatItem('Step (mm)', tmp_dic['step'], min=0)
    cam_shots = di.IntItem('Shots', tmp_dic['shots'])
    


sp = ScanParams()



def gauss_int(x, x0, amp, back, sigma):
    return 0.5*(1+amp*spec.erf((x-x0)/(sigma*2)))-back

FitResult = namedtuple('FitResult', ['success', 'params', 'model'])

def fit_curve(pos, val):
    try:
        pos = np.array(pos)
        val = np.array(val)
        a = val[np.argmax(pos)]
        b = val[np.argmin(pos)]
        x0 = [pos[np.argmin(np.abs(val-(a-b)/2))], a-b, b, 0.1]
        print(x0)
        def f(p):
            return np.array(val)-gauss_int(pos, *p)

        res = opt.leastsq(f, x0)
        fit = gauss_int(pos, *res[0])
        return FitResult(success=res[1], params=res[0], model=fit)
    except:
        raise



def make_window():
    win = pg.GraphicsLayoutWidget()
    win.resize(1000,700)
    win.setWindowTitle('pyqtgraph example: Plotting')
    
    
    pg.setConfigOptions(antialias=True)
    p1 = win.addPlot(title="Gruen (Array A)")
    l1 = p1.plot([], pen='y')
    p2 = win.addPlot(title="Rot(Array B)")
    l2 = p2.plot([], pen='y')
    p3 = win.addPlot(title="Pump")
    l3 = p3.plot([], pen='y')    
    p4 = win.addPlot(title="Spectra")
    
    win.nextRow()
    p11 = win.addPlot(title="Gruen (Array A)")
    l11 = p11.plot([], pen='y')
    l12 = p11.plot([], pen='r')
    p22 = win.addPlot(title="Rot(Array B)")
    l22 = p22.plot([], pen='y')
    p33 = win.addPlot(title="Pump")
    l33 = p33.plot([], pen='y')
    p44 = win.addPlot(title="Spectra")
    

    return win, [l1, l2, l3, p1, p2, p3, p4], [l11, l22, l33, p11, p22, p33,p44]


while sp.edit():
    win, [l1, l2, l3, p1, p2, p3, p4], [l11, l22, l33, p11, p22, p33,p44]  = make_window()
    fh.motor_init()
    fh.set_home()
    tmp_dic = {'sp': sp.start_pos_y,
               'ep': sp.end_pos_y,
               'epx': sp.end_pos_x,
               'spx': sp.start_pos_x,
               'step': sp.step,
               'shots': sp.cam_shots,
               'do_x': sp.do_x,
               'do_y': sp.do_y}
    win.show()
    try:
        json.dump( tmp_dic, 'fh_scan')
    except:
        print('fucking json')

    cam.set_shots(sp.cam_shots)
    print(cam.shots)
    #sl3 = p3.plot([])
#    xfig, axs = plt.subplots(4, 1, figsize=(6, 3), dpi=100)
    #l, = axs[0].plot([1,2,3], [1,2,3], color="r")


    sign = np.sign(sp.end_pos_x - sp.start_pos_x)
    r = np.arange(sp.start_pos_x, sp.end_pos_x, sign*sp.step)    
    #win.set_window_title('Scan ' + str_ax)
    abort = False
    def handle_close(*args):
        global abort
        abort = True
    win.closeEvent = handle_close
    #xfig.canvas.mpl_connect('close_event', handle_close)


    fh.set_pos(0, 0, 1)





    #l1, = axs[0].plot(pos, val_a)
    #l2, = axs[1].plot(pos, val_b)
    #l3, = axs[2].plot(pos, val_pump)

    #axs[0].set_xlabel('A')
    #axs[1].set_xlabel('B')
    #axs[2].set_xlabel('Pump')

    

    def make_text(name, fr):
        text = '%s\n4*sigma: %2.3f mm \nFWHM %2.3f mm\nPOS %2.2f'% (name, 4*fr.params[-1], 2.355 * fr.params[-1], fr.params[0])
        text = pg.TextItem(text,  anchor=(0, 1.0))
        return text


    if sp.do_y:
        pos = []
        val_a = []
        val_b = []
        val_pump = []
    
        sign = np.sign(sp.end_pos_y - sp.start_pos_y)
        r = np.arange(sp.start_pos_y, sp.end_pos_y, sign*sp.step) 
        fh.set_pos_mm(0, r[0], True)  # y first
        for i in r:        
            fh.set_pos_mm(None, i, False)

            lines = cam.make_reading().lines
            val_a.append(np.mean(np.array(lines[0, :])))
            val_b.append(np.mean(np.array(lines[1, :])))
            
            #val_a.append(a.mean())
            #val_b.append(b.mean())
            
            #val_pump.append(-d[1, ~c].mean())
            val_pump.append(0)
            pos.append(i)
            l1.setData(pos, val_a)
            l2.setData(pos, val_b)
            l3.setData(pos, val_pump)
            p4.plot(lines[0, :])
            p44.plot(lines[1, :])
            if abort:
                fh.set_pos_mm(0, 0, 1)                
                break
        
        if not abort:
            fr = fit_curve(pos, val_a)
            if fr.success:
                p1.plot(pos, fr.model, pen='r')
                text2 = make_text('DetA', fr)
                text2.setPos(pos[int(len(pos)/2)], (val_a[0]+val_a[-1])/3.)
                p1.addItem(text2)
    
            fr = fit_curve(pos, val_b)
            if fr.success:
                p2.plot(pos, fr.model, pen='r')
                text2 = make_text('DetB', fr)
                text2.setPos(pos[int(len(pos)/2)], (val_b[0]+val_b[-1])/3.)
                p2.addItem(text2)
    
    
            fr = fit_curve(pos, val_pump)
            if fr.success:
                p3.plot(pos, fr.model, pen='r')
                text2 = make_text('Pump', fr)
                text2.setPos(pos[int(len(pos)/2)], (np.max(val_pump) + np.min(val_pump))/2.)
                p3.addItem(text2)
        
    if sp.do_x:
        
        posx = []    
        val_a_x = []
        val_b_x = []
        val_pump_x = []

        sign = np.sign(sp.end_pos_x - sp.start_pos_x)
        print(sp.start_pos_x, sp.end_pos_x)
        r = np.arange(sp.start_pos_x, sp.end_pos_x, sign*sp.step)
        print(r)
        fh.set_pos_mm(r[0], 0, True)
        for i in r:    
            print('move to', i)
            fh.set_pos_mm(i, None, False)

            lines = cam.make_reading().lines
            val_a_x.append(np.mean(np.array(lines[0, :])))
            val_b_x.append(np.mean(np.array(lines[1, :])))
            
            #val_pump_x.append(-d[1, ~c].mean())
            val_pump_x.append(0)
            posx.append(i)
            l11.setData(posx, val_a_x)
            l22.setData(posx, val_b_x)
            l33.setData(posx, val_pump_x)
            p4.plot(lines[0, :])
            p44.plot(lines[1, :])
            if abort:
                fh.set_pos_mm(0, 0, 1)                
                break
        if not abort:
            fr = fit_curve(posx, val_a_x)
            if fr.success:                
                fit11 = p11.plot(posx, fr.model, pen='r')
                text2 = make_text('DetA', fr)
                text2.setPos(posx[int(len(posx)/2)], (val_a_x[0]+val_a_x[-1])/3.)
                p11.addItem(text2)
    
            fr = fit_curve(posx, val_b_x)
            if fr.success:
                
                fit22 = p22.plot(posx, fr.model, pen='r')
                text2 = make_text('DetB', fr)
                text2.setPos(posx[int(len(posx)/2)], (val_b_x[0]+val_b_x[-1])/3.)
                p22.addItem(text2)
    
    
            fr = fit_curve(posx, val_pump_x)
            if fr.success:
                p33.plot(posx, fr.model, pen='r')
                text2 = make_text('Pump', fr)
                text2.setPos(posx[int(len(posx)/2)], (val_pump_x[0]+val_pump_x[-1])/3.)
                p33.addItem(text2)
        



    

    fh.set_pos_mm(0, 0, 1)
    fh.motor_disable()

 




