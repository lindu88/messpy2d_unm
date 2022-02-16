import time

import attr
import numpy as np

from qtpy.QtCore import Signal, QObject
from typing import Optional

from Instruments.interfaces import ICam, T
from Instruments.signal_processing import Spectrum, Reading
from Instruments.cam_avaspec.avaspec import AvantesSpec


class Reader(QObject):
    dataReady = Signal()

    def __init__(self, device, parent: Optional['QObject'] = None) -> None:
        super().__init__(parent)
        self.device = device
        self.tmpdata = np.zeros((2048, 1000))
        self.cnt = 0
        self.t0 = 0
        self.shots = 1000

        @self.device._ffi.callback("void(long*, int*)")
        def cb(handle, para):
            self.tmpdata[:, self.cnt] = self.device.GetScopeData()[1]
            self.cnt += 1
            if self.cnt == self.shots:
                self.data = self.tmpdata
                self.tmpdata = np.zeros((2048, 1000))
                self.cnt = 0
                self.dataReady.emit()
        self.callback = cb


@attr.define
class AvaCam(ICam):
    _spec: AvantesSpec
    name: str = "AvaSpec"
    line_names: T.List[str] = ['Probe']
    sig_names: T.List[str] = ['Probe']
    std_names: T.List[str] = ['Probe']

    def make_reading(self) -> Reading:
        spec = self.get_spectra()[0]['Probe']
        return Reading(lines=spec.mean[None, :],
                       stds=spec.std[None, :],
                       signals=spec.signal[:, None],
                       valid=True)

    def get_spectra(self, frames: int) -> T.Tuple[T.Dict[str, Spectrum], T.Any]:
        self._spec.start_reading(self.shots, self._spec.callback_factory())
        while not self._spec.is_reading:
            time.sleep(0.010)
        if self.background is not None:
            self._spec.data -= self.background[:, None]
        spec = Spectrum.create(self._spec.data, name='Probe', frames=frames, first_frame=0)
        return {"Probe": spec}, None

    def set_shots(self, shots):
        self.shots = shots

    def set_background(self, shots):
        tmp = self.shots
        self.set_shots(shots)
        spec = self.get_spectra()[0]
        self.background = spec['Probe'].mean
        self.set_shots(tmp)
