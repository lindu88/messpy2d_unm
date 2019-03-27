import time, threading
from typing import Optional, List, Iterable, TYPE_CHECKING
import numpy as np
from attr import attrs, attrib, Factory
from .common_meta import Plan
from ControlClasses import Controller, Cam
from Signal import Signal
from pathlib import Path
from Config import config
if TYPE_CHECKING:
    from Instruments.interfaces import ICam, IRotationStage, IShutter

@attrs(auto_attribs=True, cmp=False)
class PumpProbeData:
    """Class holding the pump-probe data for a single cam"""
    cam: Cam
    cwl: List[float] = attrib()
    t_list: Iterable[float]
    scan: int = 0
    delay_scans = 0
    wl_idx: int = 0
    t_idx: int = 0

    last_signal: Optional[np.ndarray] = None
    mean_signal: Optional[np.ndarray] = None
    current_scan: np.ndarray = attrib(init=False)
    mean_scans: Optional[np.ndarray] = None
    completed_scans: Optional[np.ndarray] = None
    wavelengths: np.ndarray = attrib(init=False)

    sigWavelengthChanged: Signal = Factory(Signal)
    sigStepDone: Signal = Factory(Signal)

    def __attrs_post_init__(self):
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
        next_wl = self.cwl[self.wl_idx]
        self.cam.set_wavelength(next_wl)
        self.sigWavelengthChanged.emit()

    def read_point(self, t_idx):
        self.t_idx = t_idx
        lr = self.cam.last_read
        lr.update()
        self.current_scan[self.wl_idx, t_idx, :] = lr.probe_signal
        self.last_signal = lr.probe_signal[0, :]
        self.sigStepDone.emit()

@attrs(auto_attribs=True)
class PumpProbePlan:
    """Plan used for pump-probe experiments"""
    controller: Controller
    t_list: Iterable[float] 
    name: str
    meta: dict = {} 
    shots: int = 1000
    num_scans: int = 0
    t_idx: int = 0
    rot_idx: int = 0

    center_wl_list : List[Iterable[float]] = [[0]]
    use_shutter: bool = False
    cam_data: List[PumpProbeData] = attrib(init=False)
    use_rot_stage: bool = False
    rot_stage_angles: Optional[list] = None
    time_per_scan: float = 0

    sigStepDone: Signal = Factory(Signal)


    def __attrs_post_init__(self):
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        self.angle_cycle = []
        self.cam_data = []
        for c, cwl in zip(self.controller.cam_list, self.center_wl_list):
            self.cam_data.append(PumpProbeData(cam=c, cwl=cwl, t_list=self.t_list))

    def make_step_gen(self):
        c = self.controller
        while True:
            self.pre_scan()
            yield
            start_t = time.time()

            for self.t_idx, t in enumerate(self.t_list):
                c.delay_line.set_pos(t*1000., do_wait=True)
                self.read_point()
                self.sigStepDone.emit()
                yield

            delta_t = time.time() - start_t
            self.time_per_scan = '%d:%02d'%(delta_t // 60, delta_t % 60)
            self.post_scan()

    def post_scan(self):
        self.controller.delay_line.set_pos(self.t_list[0], do_wait=False)
        for pp in self.cam_data:
            pp.post_scan()
        if self.use_rot_stage:
            self.rot_idx += (self.rot_idx+1) % len(self.rot_stage_angles)

    def read_point(self):
        if self.use_shutter:
            self.controller.shutter.open()
        threads = []
        for pp in self.cam_data:
            t = threading.Thread(target=pp.read_point, args=(self.t_idx,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()
        if self.use_shutter:
            self.controller.shutter.close()

    def save(self):
        p = Path(config.data_directory)
        dname = p + f"{self.name}.messpy1"
        if (p + f"{self.name}.messpy1").is_file():
            dname = dname + '1'
        np.savez(dname)

    def pre_scan(self):
        rs = self.controller.rot_stage
        if rs and self.use_rot_stage:
            rs.set_degrees(self.rot_stage_angles[self.rot_idx])
        self.controller.delay_line.set_pos(self.t_list[0]-2000.)
