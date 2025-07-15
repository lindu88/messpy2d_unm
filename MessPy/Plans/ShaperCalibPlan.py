from MessPy.Plans.PlanBase import AsyncPlan
from MessPy.ControlClasses import Cam
from MessPy.Instruments.dac_px import AOM
import numpy as np
from pyqtgraph.parametertree import Parameter, ParameterTree
import pyqtgraph as pg
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import *
from qasync import QEventLoop, asyncSlot
from typing import List, Callable, Tuple, ClassVar
from MessPy.Instruments.interfaces import ICam
import asyncio
import asyncio as aio
import sys

import attr

sys.path.append("../")


@attr.s(auto_attribs=True, cmp=False, kw_only=True)
class CalibPlan(AsyncPlan):
    cam: Cam
    dac: AOM
    points: List[float]
    amps: List[List[float]] = attr.Factory(list)
    single_spectra: np.ndarray = attr.ib(init=False)
    num_shots: int = 100
    separation: int = 500
    width: int = 50
    single: int = 6000
    start_pos: Tuple[float, float] = 0
    check_zero_order: bool = True
    channel: int = 67
    is_async: bool = True

    sigStepDone = pyqtSignal()
    plan_shorthand: ClassVar[str] = "Calibration"

    def __attrs_post_init__(self):
        super(CalibPlan, self).__attrs_post_init__()
        self.single_spectra = np.zeros((self.cam.channels, len(self.points)))

    async def plan(self):
        self.sigPlanStarted.emit()
        self.cam.set_shots(self.num_shots)
        loop = asyncio.get_running_loop()
        initial_wl = self.cam.get_wavelength()
        initial_shots = self.cam.shots
        if self.check_zero_order:
            await loop.run_in_executor(
                None, self.cam.cam.spectrograph.set_wavelength, 0, 10
            )
            reading, ch = await loop.run_in_executor(None, self.cam.cam.get_spectra, 3)
            pump_spec = reading["Probe2"]
            self.channel = np.argmax(pump_spec.mean)  # typing: ignore

        self.single_spectra = np.zeros((self.cam.channels, len(self.points)))
        self.dac.load_mask(
            self.dac.make_calib_mask(
                width=self.width, separation=self.separation, single=self.single
            )
        )
        for i, p in enumerate(self.points):
            await self.read_point(i, p)
            self.sigStepDone.emit()
        self.cam.set_wavelength(initial_wl)
        self.cam.set_shots(initial_shots)
        self.sigPlanFinished.emit()

    async def read_point(self, i, p):
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None, self.cam.cam.spectrograph.set_wavelength, p, 10
        )
        spectra, ch = await loop.run_in_executor(None, self.cam.cam.get_spectra, 3)
        self.amps.append(spectra["Probe2"].frame_data[self.channel, :])
        self.single_spectra[:, i] = spectra["Probe2"].frame_data[:, 1]
