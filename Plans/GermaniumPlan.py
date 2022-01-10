import time, threading
from typing import Optional, List, Iterable, TYPE_CHECKING
import numpy as np
from attr import attrs, attrib, Factory
from collections import namedtuple
from ControlClasses import Controller, Cam
import attr
from PlanBase import Plan
import scipy.special as spec
import scipy.optimize as opt

from qtpy.QtCore import Signal
from typing import ClassVar

if TYPE_CHECKING:
    from Instruments.interfaces import ICam, IRotationStage, IShutter
from qtpy.QtWidgets import QApplication

FitResult = namedtuple('FitResult', ['success', 'params', 'model'])


def gauss_int(x, x0, amp, back, sigma):
    return 0.5 * (1 + amp * spec.erf((x - x0) / (sigma * 2))) - back


def fitter(t, data):
    a = data[np.argmax(t)]
    b = data[np.argmin(t)]
    x0 = [t[np.argmin(np.abs(data - (a - b) / 2))], a - b, b, 0.1]

    def helper(p):
        return np.array(data) - gauss_int(t, *p)

    res = opt.leastsq(helper, x0)
    fit = gauss_int(t, *res[0])
    return FitResult(success=res[1], params=res[0], model=fit)


@attr.s(auto_attribs=True, cmp=False)
class GermaniumPlan(Plan):
    controller: Controller
    name: str
    cam: Cam
    t_list: np.ndarray
    t_idx: int = 0
    sigStepDone: ClassVar[Signal] = Signal()
    sigGerDone: ClassVar[Signal] = Signal()

    def __attrs_post_init__(self):
        super(GermaniumPlan, self).__attrs_post_init__()
        self.t = self.t_list * 1000
        self.wls = []
        self.germaniumData = np.zeros((len(self.t_list), 128))
        self.germaniumSignal = np.zeros(len(self.t_list))
        gen = self.make_scan_gen()
        self.make_step = lambda: next(gen)

    def make_scan_gen(self):
        self.controller.delay_line.set_pos(self.t_list[0] - 2000., do_wait=False)  # why -2000??!!
        while self.controller.delay_line._dl.is_moving():
            yield
        self.wls = self.cam.get_wavelengths(self.cam.get_wavelength())
        for self.t_idx, t in enumerate(self.t):
            self.controller.delay_line.set_pos(t, do_wait=False)
            while self.controller.delay_line._dl.is_moving():
                yield
            t = threading.Thread(target=self.cam.read_cam)
            t.start()
            while t.is_alive():
                yield
            self.germaniumData[self.t_idx, :] = self.cam.last_read.signals
            self.germaniumSignal[self.t_idx] = np.sum(self.germaniumData[self.t_idx, :])
            self.sigStepDone.emit()
            yield

        self.controller.delay_line.set_pos(self.t_list[0] - 2000., do_wait=False)  # why -2000??!!
        while self.controller.delay_line._dl.is_moving():
            yield

        self.save()
        self.fit = fitter(self.t, self.germaniumSignal)
        self.sigGerDone.emit()
        yield

    def make_zero(self):
        print(f'New time Zero: {self.fit.params[0]}')
        self.controller.delay_line.set_pos(self.fit.params[0], do_wait=False)
        self.controller.delay_line.set_home()

