import serial, time, random

import os.path
from Config import config
from pathlib import Path
import attr
import numpy as np
from Plans.common_meta import Plan
import typing as T
from collections import namedtuple
from Signal import Signal
from ControlClasses import Cam, Controller
import threading
import scipy.special as spec
import scipy.optimize as opt
from Instruments.interfaces import ILissajousScanner

#faulhaber = XYSingleFaulhaber()


# class faul_sim():
#    def __init__(self):
#        pass
#    def set_pos_mm(self,a,b,c):
#        pass


# faulhaber = faul_sim()


def gauss_int(x, x0, amp, back, sigma):
    return 0.5 * (1 + amp * spec.erf((x - x0) / (sigma * 2))) - back


FitResult = namedtuple('FitResult', ['success', 'params', 'model'])


def fit_curve(pos, val):
    pos = np.array(pos)
    val = np.array(val)
    a = val[np.argmax(pos)]
    b = val[np.argmin(pos)]
    x0 = [pos[np.argmin(np.abs(val - (a - b) / 2))], a - b, b, 0.1]
    def helper(p):
        return np.array(val) - gauss_int(pos, *p)

    res = opt.leastsq(helper, x0)
    fit = gauss_int(pos, *res[0])
    return FitResult(success=res[1], params=res[0], model=fit)



def make_text(name, fr):
    text = '%s\n4*sigma: %2.3f mm \nFWHM %2.3f mm\nPOS %2.2f' % (
    name, 4 * fr.params[-1], 2.355 * fr.params[-1], fr.params[0])
    return text


@attr.s(auto_attribs=True, cmp=False)
class FocusScan():
    """
    x_parameters and y_parameters are List [start, end, step];
    if list empty it is not measured
    """
    name: str
    meta: dict
    cam: Cam
    fh: ILissajousScanner
    x_parameters: list = attr.ib()
    y_parameters: list = attr.ib()
    sigStepDone: Signal = attr.Factory(Signal)
    sigFitDone: Signal = attr.Factory(Signal)

    scan_x: bool = False
    scan_y: bool = False

    # sigXStepDone = attr.ib(attr.Factory(Signal))
    # sigYStepDone = attr.ib(attr.Factory(Signal))

    def __attrs_post_init__(self):
        if self.x_parameters != []:
            self.scan_x = True
            self.pos_x = []
            self.probe_x = []
            self.ref_x = []
        if self.y_parameters != []:
            self.scan_y = True
            self.pos_y = []
            self.probe_y = []
            self.ref_y = []

        self.start_pos = self.fh.get_pos_mm()
        gen = self.make_scan_gen()
        self.make_step = lambda: next(gen)

    def make_scan_gen(self):
        print('start scan focus')
        if self.scan_x:
            scan_axis = 'x'
            self.fh.set_pos_mm(self.x_parameters[0], self.start_pos[1])
            for pos, probe, ref in self.scanner(self.x_parameters, scan_axis):
                if pos is None:
                    yield
                    continue
                self.pos_x.append(pos)
                self.probe_x.append(probe)
                self.ref_x.append(ref)
                self.sigStepDone.emit()
                yield
            self.fit_xprobe = fit_curve(self.pos_x, self.probe_x)
            self.xtext_probe = make_text('x probe', self.fit_xprobe)
            print(self.xtext_probe)
            self.fit_xref = fit_curve(self.pos_x, self.ref_x)
            self.xtext_ref = make_text('x ref', self.fit_xref)
            print(self.xtext_ref)

        if self.scan_y:
            scan_axis = 'y'
            self.fh.set_pos_mm(self.start_pos[0], self.y_parameters[0])
            for pos, probe, ref in self.scanner(self.y_parameters, scan_axis):
                print(pos)
                if pos is None:
                    yield
                    continue
                self.pos_y.append(pos)
                self.probe_y.append(probe)
                self.ref_y.append(ref)
                self.sigStepDone.emit()
                yield
            self.fit_yprobe = fit_curve(self.pos_y, self.probe_y)
            self.ytext_probe = make_text('y probe', self.fit_yprobe)
            print(self.ytext_probe)
            self.fit_yref = fit_curve(self.pos_y, self.ref_y)
            self.ytext_ref = make_text('y ref', self.fit_yref)
            print(self.ytext_ref)
        self.save()
        self.fh.set_pos_mm(0, 0)
        self.sigFitDone.emit()
        yield

    def scanner(self, parameters, axis):
        start_pos = parameters[0]
        end_pos = parameters[1]
        step = parameters[2]

        sign = np.sign(end_pos - start_pos)
        steps = np.arange(start_pos, end_pos, sign * step)
        for i in steps:
            if axis == 'x':
                self.fh.set_pos_mm(i, None)
            if axis == 'y':
                self.fh.set_pos_mm(None, i)

            t = threading.Thread(target=self.cam.read_cam)
            t.start()
            while t.is_alive():
                yield (None, None, None)
            val_probe = np.mean(self.cam.last_read.lines[0, :])
            val_ref = np.mean(self.cam.last_read.lines[1, :])
            yield i, val_probe, val_ref

    def get_name(self, data_path=False):
        if data_path:
            p = Path(config.data_directory)
        else:
            p = Path(r"C:\Users\2dir\messpy2d\data_temps")
        dname = p + f"\{self.name}_focusScan.npz"
        i = 0
        while dname.is_file():
            dname = p +f"\{self.name}{i}_focusScan.npz"
            i = i + 1
        self._name = dname
        #if os.path.exists(dname):
        #    name_exists = True
        #    i = 0
        #    while name_exists == True:
        #        dname = p + f"\{self.name}{i}_focusScan.npz"
        #        i += 1
        #        if os.path.exists(dname) == False:
        #            name_exists = False
        self._name = dname
        return self._name

    def save(self):

        print('save')
        name = self.get_name()
        data = {'cam': self.cam.name}
        # data['meta'] = self.meta
        if self.scan_x:
            data['scan x'] = np.vstack((self.pos_x, self.probe_x, self.ref_x))
        if self.scan_y:
            data['scan y'] = np.vstack((self.pos_y, self.probe_y, self.ref_y))
        try:
            name = self.get_name(data_path=True)
            np.savez(name, **data)
            # fig.savefig(name[:-4] + '.png')
            print('saved in results')
        except:
            name = self.get_name()
            np.savez(name, **data)
            # fig.savefig(name[:-4] + '.png')
            print('saved in local temp')
