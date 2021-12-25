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
class PumpProbePlan(QObject):
    """Plan used for pump-probe experiments"""
    controller: Controller
    t_list: Iterable[float] 
    name: str
    meta: dict = {} 
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
    time_per_scan: float = 0

    sigStepDone = Signal()

    @property
    def common_mulitple_cwls(self):
        if len(self.center_wl_list) == 1:
            return 1
        else:
            return np.lcm(*map(len, self.center_wl_list))

    def __attrs_post_init__(self):
        QObject.__init__(self)
        self._name = None
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        self.angle_cycle = []
        self.cam_data = []
        for c, cwl in zip(self.controller.cam_list, self.center_wl_list):
            self.cam_data.append(PumpProbeData(cam=c, cwl=cwl, plan=self, t_list=self.t_list))
            c.set_shots(self.shots)

    async def maybe_switch_pol(self):
        rs = self.controller.rot_stage
        do_switch = (self.num_scans % len(self.rot_stage_angles) == 0)
        if do_switch and self.use_rot_stage:
            self.rot_idx = (self.rot_idx+1) % len(self.rot_stage_angles)
            next_pos = self.rot_stage_angles[self.rot_idx]
            await rs.async_set_degrees(next_pos)

    async def post_scan(self):
        self.num_scans += 1
        self.controller.delay_line.set_pos(self.t_list[0], do_wait=False)
        for pp in self.cam_data:
            pp.post_scan()

    async def scan(self):
        c = self.controller
        loop = aio.get_event_loop()
        await self.maybe_switch_pol()

        await c.delay_line.async_set_pos(self.t_list[0]-2000.)
        for self.t_idx, t in enumerate(self.t_list):
            await c.delay_line.async_set_pos(t)
            tasks = []
            for cd in self.cam_data:
                coro = loop.run_in_executor(None, cd.read_point, (self.t_idx,))
                tasks.append(coro)
            if self.use_shutter:
                c.shutter.open()
            await aio.gather(*tasks)
            if self.use_shutter:
                c.shutter.close()
        self.num_scans += 1
        self.controller.delay_line.set_pos(self.t_list[0], do_wait=False)
        for pp in self.cam_data:
            pp.post_scan()

    async def step(self):
        yield self.scan()

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
            while self.controller.delay_line._dl.is_moving():
                yield

            start_t = time.time()

            # -- scan
            for self.t_idx, t in enumerate(self.t_list):
                c.delay_line.set_pos(t*1000., do_wait=False)
                while self.controller.delay_line._dl.is_moving():
                    yield
                if self.use_shutter:
                    self.controller.shutter.open()

                threads = []
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
                yield

            delta_t = time.time() - start_t
            self.time_per_scan = '%d:%02d'%(delta_t // 60, delta_t % 60)

            # --- post scans
            self.num_scans += 1
            self.controller.delay_line.set_pos(self.t_list[0], do_wait=False)
            for pp in self.cam_data:
                pp.post_scan()

            if self.use_rot_stage and (self.num_scans % self.common_mulitple_cwls == 0):
                self.rot_idx = (self.rot_idx + 1) % len(self.rot_stage_angles)
                self.controller.rot_stage.set_degrees(self.rot_stage_angles[self.rot_idx])

    def get_name(self):
        if self._name is None:
            p = Path(config.data_directory)
            dname = p / f"{self.name}_messpy1.npz"
            i = 0
            while dname.is_file():
                dname = p / f"{self.name}{i}_messpy1.npz"
                i = i + 1
            self._name = dname
        return self._name

    def save(self):
        print('save')
        name = self.get_name()
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




