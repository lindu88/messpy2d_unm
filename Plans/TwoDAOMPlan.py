import time, threading
from typing import Optional, List, Iterable, TYPE_CHECKING
import numpy as np
from attr import attrs, attrib, Factory
from .common_meta import Plan
from ControlClasses import Controller, Cam
from Signal import Signal
from pathlib import Path
from Config import config
from datetime import datetime
import asyncio as aio

if TYPE_CHECKING:
    from Instruments.interfaces import ICam, IRotationStage, IShutter
from qtpy.QtWidgets import QApplication

@attrs(auto_attribs=True)
class PulseShaperTwoDPlan:
    """Plan used for pump-probe experiments"""
    controller: Controller
    t3_list: Iterable[float]
    name: str
    meta: dict
    date: datetime = Factory(datetime.now)
    max_t2: float = 4
    step_t2: float = 0.05
    rot_frame_freq: float = 0


    time_per_scan: float = 0

    sigStepDone: Signal = Factory(Signal)

    def setup_shaper(self):
        pass

    def make_step_gen(self):
        c = self.controller
        self.setup_shaper()
        for t3 in self.t3_list:
            c.delay_line.set_pos(t3)
            while c.delay_line._dl.is_moving():
                yield
            c.cam.read_cam()

    def measure_point(self):
        pass
