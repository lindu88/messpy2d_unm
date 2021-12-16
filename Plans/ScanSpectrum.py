import threading
import typing as T

import attr
import matplotlib.pyplot as plt
import numpy as np
from qtpy.QtCore import QObject, Signal

from ControlClasses import Cam
from Plans.common_meta import Plan


@attr.s(auto_attribs=True, cmp=False, kw_only=True)
class ScanSpectrum(Plan):
    plan_shorthand: T.ClassVar[str] = "scan"
    name: str
    cam: Cam
    wl_list: np.ndarray = attr.ib()
    wl_idx: int = -1
    timeout: float = 3

    sigPointRead: T.ClassVar[Signal] = Signal()


    def __attrs_post_init__(self):
        super(ScanSpectrum, self).__attrs_post_init__()
        n_wl = len(self.wl_list)
        n_lines = self.cam.cam.channels
        self.wls = np.zeros((n_wl, n_lines))
        self.probe = np.zeros((n_wl, n_lines))
        self.ref = np.zeros((n_wl, n_lines))
        self.signal = np.zeros((n_wl, n_lines))

        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)

    def make_step_gen(self):
        self.sigPlanStarted.emit()
        self.cam.set_wavelength(self.wl_list[0])
        for self.wl_idx, wl in enumerate(self.wl_list):

            t = threading.Thread(target=self.cam.set_wavelength, args=(wl, self.timeout))
            t.start()
            while t.is_alive():
                yield False
            wls = self.cam.get_wavelengths(wl)
            t = threading.Thread(target=self.cam.read_cam)
            t.start()
            while t.is_alive():
                yield False

            probe = self.cam.last_read.lines[0, :]
            ref = self.cam.last_read.lines[1, :]
            sig = self.cam.last_read.signals

            self.wls[self.wl_idx, :] = wls
            self.probe[self.wl_idx, :] = probe
            self.ref[self.wl_idx, :] = ref
            self.signal[self.wl_idx, :] = sig
            self.sigPointRead.emit()
            yield False

        self.save()
        self.sigPlanFinished.emit()
        yield True

    def save(self):
        data = {'cam': self.cam.name,
                'wl': self.wls,
                'probe': self.probe,
                'ref': self.ref,
                'signal': self.signal}
        # data['meta'] = self.meta
        self.save_meta()
        fig = plt.figure()
        plt.plot(self.wls[:, 64], self.probe[:, 64], label='Probe')
        plt.plot(self.wls[:, 64], self.ref[:, 64], label='Ref')
        plt.legend()
        fig.show()

        name = self.get_file_name()[0]
        np.savez(name, **data)
        fig.savefig(name.with_suffix('.png'))

