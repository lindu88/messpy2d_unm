import time
from typing import Optional, List, Iterable, Any
import numpy as np
from attr import attrs, attrib, Factory
from .common_meta import Plan
from ControlClasses import Controller, Signal
from pathlib import Path
from Config import config

@attrs(auto_attribs=True)
class PumpProbePlan:
    """Plan used for pump-probe experiments"""
    controller: Controller
    t_list: Iterable[float] 
    name: str
    meta: dict = {} 
    shots: int = 1000
    num_scans: int = 0
    wl_idx: int = 0
    t_idx: int = 0
    rot_idx: int = 0
    center_wl_list : Iterable[float] = Factory(list)
    use_shutter: bool = False

    signal_data: Any = None
    rot_stage_angles: Optional[list] =  None
    time_per_scan: float = 0
    cur_scan: int = -1
    old_scans: Any = None
    mean_scans: Any = None
    wl_arrays: Any = None

    sigStepDone: Signal = Factory(Signal)
    sigWavelengthChanged: Signal = Factory(Signal)

    def __attrs_post_init__(self):
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        self.angle_cycle = []

    def make_step_gen(self):
        c = self.controller
        c.cam.set_shots(self.shots)
        n_pixel = c.cam.cam.channels
        N, M = len(self.center_wl_list), len(self.t_list)
        self.wl = np.zeros((N, n_pixel))
        self.wl += np.arange(n_pixel)[None, :]
        self.old_scans = np.zeros((N, M, n_pixel, 0))

                
        if c.cam2 is not None:
            c.cam2.set_shots(self.shots)
            self.old_scans2 = np.zeros((N, M, self.controller.cam2.cam.num_ch, 0))
            self.wl2 = np.zeros((N, c.cam2.num_ch))

        while True:
            self.pre_scan()
            yield
            start_t = time.time()
            for self.wl_idx, wl in enumerate(self.center_wl_list):
                c.spectrometer.set_wavelength(wl)
                self.sigWavelengthChanged.emit()

                for self.t_idx, t in enumerate(self.t_list):
                    c.delay_line.set_pos(t*1000.)
                    self.read_point()
                    self.sigStepDone.emit()
                    yield
            delta_t = time.time() - start_t
            self.time_per_scan = '%d:%02d'%(delta_t // 60, delta_t % 60)
            self.post_scan()

    def post_scan(self):
        self.old_scans = np.concatenate((self.old_scans, self.cur_scan[..., None]), 3)
        self.old_scans2 = np.concatenate((self.old_scans2, self.cur_scan2[..., None]), 3)

    def read_point(self):
        if self.use_shutter:
            self.controller.shutter.open()
        lr = self.controller.last_read
        lr.update()
        self.signal_data = lr.probe_signal
        self.cur_scan[self.wl_idx, self.t_idx, :] = lr.probe_signal

        if self.controller.cam2 is not None:
            lr = self.controller.last_read2 
            lr.update()
            self.signal_data2 = lr.probe_signal
            self.cur_scan2[self.wl_idx, self.t_idx, :] = lr.probe_signal

        if self.use_shutter:
            self.controller.shutter.close()

    def save(self):
        p = Path(config.data_directory)
        dname = p + f"{self.name}.messpy1"
        if (p + f"{self.name}.messpy1").is_file():
            dname = dname + '1'
        np.savez(dname)

    def pre_scan(self):
        N, M = len(self.center_wl_list), len(self.t_list)
        self.cur_scan = np.zeros((N, M, self.controller.cam.cam.channels))
        self.num_scans += 1
        self.wl_idx += 1
        self.t_idx = 0
        if self.controller.cam2 is not None:
            self.cur_scan2 = np.zeros((N, M, self.controller.cam2.cam.channels))
        if self.rot_stage_angles is not None:
            pos = self.rot_stage_angles[self.rot_idx]
            self.rot_idx = (self.rot_idx + 1) % len(self.rot_stage_angles)
            self.controller.rot_stage.set_pos()

