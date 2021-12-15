import numpy as np
from attr import attrs, attrib, Factory
from Config import config
import threading, time
import typing as T
from HwRegistry import _cam, _cam2, _dl, _dl2, _rot_stage, _shutter, _sh, _shaper
import Instruments.interfaces as I


Reading = I.Reading

from qtpy.QtWidgets import QApplication
from qtpy.QtCore import QThread, QTimer, QObject, Signal
import asyncio as aio


@attrs(cmp=False)
class Cam(QObject):
    cam: I.ICam = attrib(_cam)
    shots: int = attrib(config.shots)

    back: T.Any = attrib((0, 0))
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
        self.read_cam()
        c = self.cam
        self.channels = c.channels
        self.lines = c.lines
        self.sig_lines = c.sig_lines
        self.name = c.name
        if c.spectrograph is not None:
            self.changeable_wavelength = c.spectrograph.changeable_wavelength
            c.spectrograph.sigWavelengthChanged.connect(self._update_wl_arrays)
        else:
            self.changeable_wavelength = False

        self.wavelengths = self.get_wavelengths()
        self.wavenumbers = 1e7 / self.wavelengths
        self.disp_axis = self.wavelengths.copy()

    def _update_wl_arrays(self, cwl=None):
        self.wavelengths[:] = self.get_wavelengths()
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
        self.shots = shots
        self.cam.set_shots(int(shots))
        config.shots = shots
        self.sigShotsChanged.emit(shots)

    def read_cam(self, two_dim=False):
        rd = self.cam.make_reading()
        self.last_read = rd
        # self.sigReadCompleted.emit()
        return rd

    def start_two_reading(self):
        pass

    def set_wavelength(self, wl, timeout=5):
        self.cam.spectrograph.set_wavelength(wl, timeout=timeout)
        self.cam.spectrograph.sigWavelengthChanged.emit(wl)

    def get_wavelength(self):
        return self.cam.spectrograph.get_wavelength()

    def get_wavelengths(self, center_wl=None):
        return self.cam.get_wavelength_array(center_wl)

    def get_bg(self):
        self.cam.set_background(self.shots)

    def remove_bg(self):
        self.cam.remove_background()

    def set_slit(self, slit):
        self.cam.spectrograph.set_slit(slit)
        slit = self.cam.spectrograph.get_slit()
        self.sigSlitChanged.emit(slit)

    def get_slit(self):
        return self.cam.spectrograph.get_slit()

    def calibrate_ref(self):
        self.cam.calibrate_ref()
        self.sigRefCalibrationFinished.emit(self.cam.deltaK1, self.cam.deltaK2)


@attrs(cmp=False)
class Delayline(QObject):
    pos = attrib(0)
    moving = attrib(False)
    _dl = attrib(I.IDelayLine)
    _thread = attrib(None)
    sigPosChanged = Signal(float)

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
            QTimer.singleShot(100, self.wait_and_update)
        else:
            self.moving = False

    def get_pos(self) -> float:
        return self._dl.get_pos_fs()

    async def async_set_pos(self):
        self._dl.move_fs(pos_fs, do_wait=False)
        while _dl.is_moving():
            aio.sleep(0.1)

    def set_speed(self, ps_per_sec: float):
        self._dl.set_speed(ps_per_sec)

    def set_home(self):
        self._dl.home_pos = self._dl.get_pos_mm()
        self._dl.def_home()
        config.__dict__['Delay 1 Home Pos.'] = self._dl.get_pos_mm()
        config.save()
        self.sigPosChanged.emit(self.get_pos())


arr_factory = Factory(lambda: np.zeros(16))


class Controller(QObject):
    """Class which controls the main loop."""
    cam: Cam
    cam2: T.Optional[Cam]
    cam_list: T.List[Cam]
    shutter: T.Optional[I.IShutter]
    delay_line: Delayline
    rot_stage: T.Optional[I.IRotationStage]
    sample_holder: T.Optional[I.ILissajousScanner]
    shaper: T.Optional[object] = None
    loop_finnished = Signal()

    def __init__(self):
        super(Controller, self).__init__()
        self.cam = Cam()
        self.cam.read_cam()
        self.shutter = _shutter
        self.cam_list = [self.cam]



        if _cam2 is not None:
            self.cam2 = Cam(cam=_cam2)
            self.cam2.read_cam()
            self.cam.sigShotsChanged.connect(self.cam2.set_shots)
            self.cam_list.append(self.cam2)
        else:
            self.cam2 = None

        self.delay_line = Delayline(dl=_dl)
        self.rot_stage = _rot_stage

        if _dl2:
            self.delay_line_second = Delayline(dl=_dl2)
        else:
            self.delay_line_second = None

        if _sh:
            self.sample_holder = _sh
        else:
            self.sample_holder = None

        self.shaper = _shaper
        self.async_plan = False
        self.plan = None
        self.pause_plan = False
        self.running_step = False
        self.thread = None


        # self.loop = lambda: next(self.loop_gen())

    def loop(self):
        if self.plan is None or self.pause_plan:
            t1 = threading.Thread(target=self.cam.read_cam)
            t1.start()
            t2 = threading.Thread()
            if self.cam2:
                t2 = threading.Thread(target=self.cam2.read_cam)
                t2.start()

            while t1.is_alive() or t2.is_alive():
                QApplication.instance().processEvents()
            self.cam.sigReadCompleted.emit()
            if self.cam2:
                self.cam2.sigReadCompleted.emit()
            t1.join()
            if self.cam2:
                t2.join()

        else:
            try:
                self.plan.make_step()
            except StopIteration:
                self.pause_plan = True
        self.loop_finnished.emit()

        # print(time.time() - t)

    def shutdown(self):
        if _dl2 is not None:
            _dl2.shutdown()
        _dl.shutdown()
        _cam.shutdown()
        if _cam2 is not None:
            _cam2.shutdown()
