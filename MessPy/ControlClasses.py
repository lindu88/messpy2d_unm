import asyncio as aio
import asyncio
from asyncio import Task

import numpy as np
from attr import attrs, attrib, Factory, define
import os
from loguru import logger

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer, QObject, Signal
from qasync import Slot
from MessPy.Config import config
import threading
import time
import typing as T
from MessPy.HwRegistry import (
    _cam,
    _cam2,
    _dl,
    _dl2,
    _rot_stage,
    _shutter,
    _sh,
    _shaper,
    _power_meter,
)
import MessPy.Instruments.interfaces as I

if T.TYPE_CHECKING:
    from MessPy.Plans.PlanBase import Plan


Reading = I.Reading


@attrs(cmp=False)
class Cam(QObject):
    cam: I.ICam = attrib(_cam)
    shots: int = attrib(config.shots)

    back: T.Any = attrib((0, 0))
    has_ref: bool = attrib(init=False)
    last_read: T.Optional[I.Reading] = attrib(init=False)

    wavelengths: np.ndarray = attrib(init=False)
    wavenumbers: np.ndarray = attrib(init=False)
    disp_axis: np.ndarray = attrib(init=False)
    disp_wavelengths: bool = attrib(True)

    sigShotsChanged: Signal = Signal(int)
    sigReadCompleted: Signal = Signal()
    sigRefCalibrationFinished = Signal(object, object)

    def __attrs_post_init__(self):
        QObject.__init__(self)
        if self.shots > 1000:
            self.set_shots(20)
        self.read_cam()
        c = self.cam
        self.channels = c.channels
        self.lines = c.lines
        self.sig_lines = c.sig_lines
        self.name = c.name
        self.has_ref = c.has_ref

        if c.spectrograph is not None:
            self.changeable_wavelength = c.spectrograph.changeable_wavelength
            c.spectrograph.sigWavelengthChanged.connect(self._update_wl_arrays)

        else:
            self.changeable_wavelength = False

        self.wavelengths = self.get_wavelengths()
        self.wavenumbers = 1e7 / self.wavelengths
        self.disp_axis = self.wavelengths.copy()

    def _update_wl_arrays(self, cwl=None):
        self.wavelengths[:] = self.get_wavelengths(cwl)
        self.wavenumbers[:] = 1e7 / self.wavelengths
        if self.disp_wavelengths:
            self.disp_axis[:] = self.wavelengths
        else:
            self.disp_axis[:] = self.wavenumbers

    def set_disp_wavelengths(self, use_wl):
        self.disp_wavelengths = not use_wl
        self._update_wl_arrays()

    def set_shots(self, shots):
        """Sets the number of shots recorded"""
        try:
            self.shots = int(shots)
            self.cam.set_shots(self.shots)
            config.shots = shots
            self.sigShotsChanged.emit(self.shots)
        except ValueError:
            pass

    def read_cam(self, two_dim=False):
        rd = self.cam.make_reading()
        self.last_read = rd
        # self.sigReadCompleted.emit()
        return rd

    def start_two_reading(self):
        pass

    def set_wavelength(self, wl, timeout=5):
        assert self.cam.spectrograph is not None
        self.cam.spectrograph.set_wavelength(wl, timeout=timeout)
        self.cam.spectrograph.sigWavelengthChanged.emit(wl)

    def get_wavelength(self):
        assert self.cam.spectrograph is not None
        return self.cam.spectrograph.get_wavelength()

    def get_wavelengths(self, center_wl=None):
        return self.cam.get_wavelength_array(center_wl)

    def get_bg(self):
        self.cam.set_background(self.shots)

    def remove_bg(self):
        self.cam.remove_background()

    def set_slit(self, slit):
        if self.cam.spectrograph is not None:
            self.cam.spectrograph.set_slit(slit)
            slit = self.cam.spectrograph.get_slit()
            self.cam.spectrograph.sigSlitChanged.emit(slit)
        else:
            raise AttributeError("No slit installed")

    def get_slit(self):
        return self.cam.spectrograph.get_slit()

    def calibrate_ref(self):
        self.cam.calibrate_ref()
        self.sigRefCalibrationFinished.emit(self.cam.deltaK1, self.cam.deltaK2)


@define(auto_attribs=True, slots=False)
class DelayLine(QObject):
    pos: float = 0
    moving: bool = False
    _dl: I.IDelayLine = _dl
    _thread: T.Optional[object] = None

    sigPosChanged: T.ClassVar[Signal] = Signal(float)

    def __attrs_post_init__(self):
        QObject.__init__(self)
        self.pos = self._dl.get_pos_fs()
        self.sigPosChanged.emit(self.pos)

    def set_pos(self, pos_fs: float, do_wait=True):
        "Set pos in femtoseconds"
        try:
            pos_fs = float(pos_fs)
        except ValueError:
            raise
        self.moving = True
        self._dl.move_fs(pos_fs, do_wait=do_wait)
        if not do_wait:
            self.wait_and_update()
        else:
            while _dl.is_moving():
                time.sleep(0.1)
            self.moving = False
        self.pos = self._dl.get_pos_fs()
        self.sigPosChanged.emit(self.pos)

    def wait_and_update(self):
        "Wait until not moving. Do update position while moving"
        self.pos = self._dl.get_pos_fs()
        self.sigPosChanged.emit(self.pos)
        if self._dl.is_moving():
            QTimer.singleShot(30, self.wait_and_update)
        else:
            self.moving = False

    def get_pos(self) -> float:
        return self._dl.get_pos_fs()

    def set_speed(self, ps_per_sec: float):
        self._dl.set_speed(ps_per_sec)

    def set_home(self):
        self._dl.home_pos = self._dl.get_pos_mm()
        self._dl.def_home()
        config.__dict__["Delay 1 Home Pos."] = self._dl.get_pos_mm()
        config.save()
        self.sigPosChanged.emit(self.get_pos())


arr_factory = Factory(lambda: np.zeros(16))


@define(slots=False, auto_attribs=True)
class Controller(QObject):
    """Class which controls the main loop."""

    cam: Cam = attrib(init=False)
    delay_line: DelayLine = Factory(lambda: DelayLine(dl=_dl))
    delay_line_second: T.Optional[DelayLine] = None
    cam2: T.Optional[Cam] = attrib(init=False)
    cam_list: T.List[Cam] = Factory(list)
    shutter: T.List[I.IShutter] = _shutter
    rot_stage: T.Optional[I.IRotationStage] = _rot_stage
    sample_holder: T.Optional[I.ILissajousScanner] = _sh
    shaper: T.Optional[object] = _shaper
    power_meter: T.Optional[I.IPowerMeter] = _power_meter
    async_tasks: list = Factory(list)
    plan: T.Optional[object] = None
    pause_plan: bool = False

    loop_finished: T.ClassVar[Signal] = Signal()
    stopping_plan: T.ClassVar[Signal] = Signal(bool)
    starting_plan: T.ClassVar[Signal] = Signal(bool)

    def __attrs_post_init__(self):
        super().__init__()
        self.cam = Cam()
        self.shutter = _shutter
        self.cam_list = [self.cam]
        if _cam2 is not None:
            self.cam2 = Cam(_cam2)
            self.cam.sigShotsChanged.connect(self.cam2.set_shots)
            self.cam_list.append(self.cam2)
        else:
            self.cam2 = None
        self.t1 = None

    @Slot()
    def start_standard_read(self):
        # t0 = time.time()
        self.t1 = threading.Thread(target=self.cam.read_cam)
        self.t1.start()
        if self.cam2:
            self.t2 = threading.Thread(target=self.cam2.read_cam)
            self.t2.start()

    def standard_read_running(self):
        return self.t1.is_alive()

    def standard_read(self):
        self.t1.join()
        self.cam.sigReadCompleted.emit()
        # print((time.time()-t0)*1000)

        if self.cam2:
            self.t2.join()
            self.cam2.sigReadCompleted.emit()
        self.t1 = None

    @Slot()
    def loop(self):
        if self.plan is None or self.pause_plan:
            if self.t1 is None:
                self.start_standard_read()
            elif not self.standard_read_running():
                self.standard_read()
        elif getattr(self.plan, "is_async", False) and self.plan.task:
            t = self.plan.task
            t: aio.Task
            # print(t)
            if t.done():
                if t.exception():
                    t.cancel()
                    self.plan = None
                    raise t.exception()
                else:
                    self.plan.task = None
        elif hasattr(self.plan, "make_step"):
            try:
                self.plan.make_step()
            except StopIteration:
                self.pause_plan = True
        self.loop_finished.emit()

    @Slot(object)
    def start_plan(self, plan):
        self.plan = plan
        self.pause_plan = False
        self.plan.sigPlanFinished.connect(self.stop_plan)
        self.starting_plan.emit(True)

    def add_task(self, task: Task):
        self.async_tasks.append(task)

    @Slot()
    def stop_plan(self):
        if self.plan:
            self.plan.stop_plan()
            self.plan = None
            self.stopping_plan.emit(True)


if __name__ == "__main__":
    c = Controller()
    print(c)
