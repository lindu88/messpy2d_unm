import attr
import numpy as np

from qtpy.QtCore import Signal, QObject
from typing import Optional

from Instruments.interfaces import ICam, T
from Instruments.signal_processing import Reading2D, Spectrum, Reading
from Instruments.cam_avaspec.avaspec import MeasurmentSettings, Avaspec


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
    name: str = "AvaSpec"
    line_names: T.List[str] = ['Probe']
    sig_names: T.List[str] = ['Probe']
    std_names: T.List[str] = ['Probe']
    avaspec: Avaspec.Device = attr.field()

    @avaspec.default
    def

    def make_reading(self) -> Reading:
        pass

    def get_spectra(self, frames: int) -> T.Tuple[T.Dict[str, Spectrum], T.Any]:
        pass

    def set_shots(self, shots):
        pass

    def set_background(self, shots):
        pass
