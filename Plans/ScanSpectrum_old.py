import attr
import numpy as np
from Plans.common_meta import Plan
import typing as T
from Signal import Signal


from ControlClasses import Cam, Controller


@attr.s(auto_attribs=True)
class ScanSpectrum:
    name: str
    meta: dict
    cam: Cam
    wl_list: T.Iterable[float]
    amplitudes: np.ndarray = attr.ib(init=False)
    signals: np.ndarray = attr.ib(init=False)
    wl_idx: int = 0
    sigPointRead: Signal = attr.Factory(Signal)

    def __attrs_post_init__(self):
        self.wl_list = np.array(self.wl_list)
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        N = self.cam.channels
        n_lines = self.cam.lines
        n_sig = self.cam.sig_lines
        n_wl = len(self.wl_list)
        self.amplitudes = np.zeros((n_lines, n_wl, N))
        self.signals = np.zeros((n_sig, n_wl, N))

    def make_step_gen(self):
        cam = self.cam
        for self.wl_idx, wl in enumerate(self.wl_list):
            cam.set_wavelength(wl)
            cam.last_read.update()
            self.amplitudes[:, self.wl_idx, :] = cam.last_read.spec
            self.signals[:, self.wl_idx, :] = cam.last_read.probe_signal
            self.sigPointRead.emit()
            yield





