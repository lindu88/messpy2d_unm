import attr
import numpy as np
from Plans.common_meta import  Plan
import typing as T
from Signal import Signal

if T.TYPE_CHECKING:
    from ControlClasses import Cam, Controller


@attr.s(auto_attribs=True)
class ScanSpectrum(Plan):
    cam: Cam
    wl_list: T.Iterable[float]
    amplitudes: np.ndarray = attr.ib(init=False)
    signals: np.ndarray = attr.ib(init=False)

    sigPointRead: Signal = attr.Factor(Signal)

    def __attrs_post_init__(self):
        gen = self.make_step_gen()
        self.make_step = lambda: next(gen)
        N = self.cam.channels
        L = self.cam.lines
        Ls = self.cam.sig_lines
        n_wl = len(self.wl_list)
        self.amplitudes = np.zeros((L, n_wl, N))
        self.signals = np.zeros((Ls, n_wl, N))

    def make_step_gen(self):
        cam = self.cam
        for wl_idx, wl in enumerate(self.wl_list):
            cam.set_wavelength(wl)
            cam.last_read.update()
            self.amplitudes[:, wl_idx, :] = cam.last_read.spec
            self.signals[:, wl_idx, :] = cam.last_read.probe_signal




