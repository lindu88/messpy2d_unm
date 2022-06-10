import time, threading
from typing import Optional, List, Iterable, TYPE_CHECKING
import numpy as np
from attr import attrs, attrib, Factory
from .PlanBase import Plan
from ControlClasses import Controller, Cam
from qtpy.QtCore import QObject, Signal
from pathlib import Path
from Config import config
import datetime
import asyncio as aio

if TYPE_CHECKING:
    from Instruments.interfaces import ICam, IRotationStage, IShutter
from qtpy.QtWidgets import QApplication

@attrs(auto_attribs=True)
class PumpProbePlan(Plan):
    """Plan used for pump-probe experiments"""
    controller: Controller
    t_list: Iterable[float]
    shots: int = 1000
    num_scans: int = 0
    t_idx: int = 0
    rot_idx: int = 0

    center_wl_list : List[List[float]] = [[0]]
    use_shutter: bool = False
    cam_data: List['PumpProbeData'] = attrib(init=False)
    use_rot_stage: bool = False
    rot_stage_angles: Optional[list] = None
    rot_at_scan: List[float] = Factory(list)
    time_per_scan: str = ""

    sigStepDone = Signal()
    plan_shorthand = "PumpProbe"

    @property
    def common_mulitple_cwls(self):
        if len(self.center_wl_list) == 1:
            return 1
        else:
            return np.lcm(*map(len, self.center_wl_list))

    def __attrs_post_init__(self):
        super(PumpProbePlan, self).__attrs_post_init__()
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        self.angle_cycle = []
        self.cam_data = []
        for c, cwl in zip(self.controller.cam_list, self.center_wl_list):
            self.cam_data.append(PumpProbeData(cam=c, cwl=cwl, plan=self, t_list=self.t_list))
            c.set_shots(self.shots)

    def make_step_gen(self):
        c = self.controller
        rs = self.controller.rot_stage
        if rs and self.use_rot_stage:
            rs.set_degrees(self.rot_stage_angles[self.rot_idx])
            while rs.is_moving():
                rs.sigDegreesChanged.emit(rs.get_degrees())
                yield
        while True:

            # --- Pre Scan
            if rs and self.use_rot_stage:
                while rs.is_moving():
                    rs.sigDegreesChanged.emit(rs.get_degrees())
                    yield
                self.rot_at_scan.append(rs.get_degrees())
            self.controller.delay_line.set_pos(self.t_list[0] - 2000., do_wait=False)
            while self.controller.delay_line.moving:
                yield

            start_t = time.time()
            self.time_tracker.scan_starting()
            # -- scan
            for self.t_idx, t in enumerate(self.t_list):
                c.delay_line.set_pos(t*1000., do_wait=False)
                while self.controller.delay_line.moving:
                    yield
                if self.use_shutter:
                    self.controller.shutter.open()
                threads = []
                self.time_tracker.point_starting()
                for pp in self.cam_data:
                    t = threading.Thread(target=pp.read_point, args=(self.t_idx,))
                    t.start()
                    threads.append(t)
                while any([t.is_alive() for t in threads]):
                    yield
                for pp in self.cam_data:
                    pp.sigStepDone.emit()
                if self.use_shutter:
                    self.controller.shutter.close()
                self.sigStepDone.emit()
                self.time_tracker.point_ending()
                yield

            delta_t = time.time() - start_t
            self.time_per_scan = '%d:%02d'%(delta_t // 60, delta_t % 60)
            self.time_tracker.scan_ending()
            # --- post scans
            self.num_scans += 1
            self.controller.delay_line.set_pos(self.t_list[0], do_wait=False)
            for pp in self.cam_data:
                pp.post_scan()

            if self.use_rot_stage and (self.num_scans % self.common_mulitple_cwls == 0):
                self.rot_idx = (self.rot_idx + 1) % len(self.rot_stage_angles)
                self.controller.rot_stage.set_degrees(self.rot_stage_angles[self.rot_idx])

    def save(self):
        name = self.get_file_name()[0]
        self.save_meta()
        data = {"data_" + ppd.cam.name: np.float32(ppd.completed_scans)
                for ppd in self.cam_data}
        wls = {"wl_" + ppd.cam.name: ppd.wavelengths for ppd in self.cam_data}
        data.update(wls)
        data['meta'] = self.meta
        data['t'] = np.array(self.t_list)
        data['rot'] = self.rot_at_scan
        np.savez(name, **data)



@attrs(auto_attribs=True, cmp=False)
class PumpProbeData(QObject):
    """Class holding the pump-probe data for a single cam"""
    cam: Cam
    plan: PumpProbePlan
    cwl: List[float] = attrib()
    t_list: Iterable[float]
    scan: int = 0
    delay_scans : int  = 0
    wl_idx: int = 0
    t_idx: int = 0

    last_signal: Optional[np.ndarray] = None
    mean_signal: Optional[np.ndarray] = None
    current_scan: np.ndarray = attrib(init=False)
    mean_scans: Optional[np.ndarray] = None
    completed_scans: Optional[np.ndarray] = None
    wavelengths: np.ndarray = attrib(init=False)

    sigWavelengthChanged = Signal()
    sigStepDone = Signal()

    def __attrs_post_init__(self):
        super(PumpProbeData, self).__init__()
        num_sig = self.cam.sig_lines
        num_wl = len(self.cwl)
        num_t = len(self.t_list)
        num_ch = self.cam.channels
        self.wavelengths = np.zeros((num_wl, num_ch))
        for i, wl in enumerate(self.cwl):
            self.wavelengths[i, :] = self.cam.get_wavelengths(wl)
        self.current_scan = np.zeros((num_wl, num_t, num_sig, num_ch))
        self.mean_scans = None
        if self.cam.changeable_wavelength:
            self.cam.set_wavelength(self.cwl[0])

    def post_scan(self):
        'Called when a scan through the delay-line has finished'
        self.delay_scans += 1
        self.wl_idx = self.delay_scans % len(self.cwl)
        if self.delay_scans % len(self.cwl) == 0:
            self.scan += 1
            if self.completed_scans is None:
                self.completed_scans = self.current_scan[None, ...]
            else:
                self.completed_scans = np.concatenate((self.completed_scans, self.current_scan[None, ...]))
            self.mean_scans = self.completed_scans.mean(0)
            self.plan.save()
        next_wl = self.cwl[self.wl_idx]
        if len(self.cwl) > 1:
            self.cam.set_wavelength(next_wl)
        self.sigWavelengthChanged.emit()

    def read_point(self, t_idx):
        self.t_idx = t_idx
        self.cam.read_cam()
        lr = self.cam.last_read
        self.current_scan[self.wl_idx, t_idx, :, :] = lr.signals[...]
        if self.mean_scans is not None:
            self.mean_signal = self.mean_scans[self.wl_idx, t_idx, 0, :]
        self.last_signal = lr.signals[0, :]
