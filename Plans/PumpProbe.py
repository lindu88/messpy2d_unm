import time

import numpy as np
from attr import attrs, attrib, Factory

from ControlClasses import Controller, Signal


@attrs
class PumpProbePlan:
    """Plan used for pump-probe experiments"""
    controller = attrib(Factory(Controller))
    name = attrib('')
    shots = attrib(1000)
    num_scans = attrib(0)
    wl_idx = attrib(0)
    t_idx = attrib(0)
    center_wl_list = attrib(Factory(list))
    t_list = attrib(Factory(list))
    signal_data = attrib(None)
    rot_stage_angles = attrib(None)
    sigStepDone = attrib(Factory(Signal))
    sigWavelengthChanged = attrib(Factory(Signal))
    time_per_scan = attrib(0)
    cur_scan = attrib(None)
    old_scans = attrib(None)
    mean_scans = attrib(None)
    wl = attrib(None)

    def __attrs_post_init__(self):
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        self.angle_cycle = []

    def make_step_gen(self):
        c = self.controller
        c.cam.set_shots(self.shots)
        N, M = len(self.center_wl_list), len(self.t_list)
        self.wl = np.zeros((N, c.cam.num_ch))
        self.wl += np.arange(16)[None, :]
        self.old_scans = np.zeros((N, M, self.controller.cam.num_ch, 0))

        while True:
            self.pre_scan()


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

    def read_point(self):
        lr = self.controller.last_read
        lr.update()
        self.signal_data = lr.probe_signal
        self.cur_scan[self.wl_idx, self.t_idx, :] = lr.probe_signal

    def pre_scan(self):
        N, M = len(self.center_wl_list), len(self.t_list)
        self.cur_scan = np.zeros((N, M, self.controller.cam.num_ch))
        self.num_scans += 1
        self.wl_idx += 1
        self.t_idx = 0
