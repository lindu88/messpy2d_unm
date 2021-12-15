import time, threading
from typing import Optional, List, Iterable, TYPE_CHECKING, ClassVar, Callable
import numpy as np
from attr import attrs, attrib, Factory
from .common_meta import Plan
from ControlClasses import Controller, Cam


from datetime import datetime
import asyncio as aio

if TYPE_CHECKING:
    from Instruments.interfaces import ICam, IRotationStage, IShutter
from Instruments.dac_px import AOM

#from qtpy.QtWidgets import QApplication
from qtpy.QtCore import Signal
import h5py


@attrs(auto_attribs=True, kw_only=True)
class PulseShaperTwoDPlan(Plan):
    """Plan used for pump-probe experiments"""
    controller: Controller
    shaper: AOM
    t3_list: np.ndarray
    max_t2: float = 4
    step_t2: float = 0.05
    t2: np.ndarray = attrib()
    rot_frame_freq: float = 0
    time_per_scan: float = 0
    plan_shorthand: ClassVar[str] = "2D"
    data_file: h5py.File = attrib()

    sigStepDone: ClassVar[Signal] = Signal()
    make_step: Callable = attrib()

    @t2.default
    def _t2_default(self):
        return np.arange(0, self.max_t2 + 1e-3, self.step_t2)


    @data_file.default
    def _default_file(self):
        name = self.get_file_name()[0]
        f = h5py.File(name, mode='w')
        f.create_dataset("t2", data=self.t2)
        f.create_dataset("t3", data=self.t3_list)
        f['t2'].attrs['rot_frame'] = self.rot_frame_freq
        return f

    @make_step.default
    def make_step_gen(self):
        c = self.controller
        self.setup_shaper()
        for t3 in self.t3_list:
            c.delay_line.set_pos(t3, do_wait=False)
            while c.delay_line.moving:
                yield
            yield from self.measure_point()

    def setup_shaper(self):
        self.shaper.double_pulse(self.max_t2, self.step_t2, self.rot_frame_freq)

    def measure_point(self):
        self.controller.cam.read_cam()
        self.controller.cam.cam.make_2D_reading()

    def save_data(self):
        name, meta_name = self.get_file_name()
        f =y.File(name)