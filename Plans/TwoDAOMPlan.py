import time, threading
from typing import Optional, List, Iterable, TYPE_CHECKING
import numpy as np
from attr import attrs, attrib, Factory
from .common_meta import Plan
from ControlClasses import Controller, Cam
from Signal import Signal

from datetime import datetime
import asyncio as aio

if TYPE_CHECKING:
    from Instruments.interfaces import ICam, IRotationStage, IShutter
from Instruments.dac_px import AOM

from qtpy.QtWidgets import QApplication
import h5py

@attrs(auto_attribs=True)
class PulseShaperTwoDPlan(Plan):
    """Plan used for pump-probe experiments"""
    controller: Controller
    shaper: AOM
    t3_list: Iterable[float]
    date: datetime = Factory(datetime.now)
    max_t2: float = 4
    step_t2: float = 0.05
    rot_frame_freq: float = 0
    time_per_scan: float = 0
    sigStepDone: Signal = Factory(Signal)

    def setup_shaper(self):
        self.shaper.double_pulse(self.max_t2, self.step_t2, self.rot_frame_freq)

    def make_step_gen(self):
        c = self.controller
        self.setup_shaper()
        for t3 in self.t3_list:
            c.delay_line.set_pos(t3, do_wait=False)
            while c.delay_line.moving:
                yield
            yield from self.measure_point()

    def measure_point(self):
        c.cam.read_cam()

    def save_data(self):
