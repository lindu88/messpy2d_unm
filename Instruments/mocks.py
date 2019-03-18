import numpy as np
import attr
from Instruments.interfaces import ICam, IDelayLine

@attr.s(auto_attribs=True)
class CamMock(ICam):
    shots: int = 20
    channels: int = 200
    ext_channels: int = 3
    background: tuple = (0., 0.)

    def set_shots(self, shots):
        self.shots = shots

    def read_cam(self):
        a = np.random.normal(loc=30, size=(self.channels, self.shots)).T
        b = np.random.normal(loc=20, size=(self.channels, self.shots)).T
        ext = np.random.normal(size=(self.ext_channels, self.shots)).T
        chop = np.array([True, False]).repeat(self.shots*2)
        return a - self.background[0], b - self.background[0], chop, ext

@attr.s(auto_attribs=True)
class DelayLineMock(IDelayLine):
    pos_mm: float = 0.

    def move_mm(self, mm, do_wait=True):
        self.pos_mm =mm

    def get_pos_mm(self):
        return self.pos_mm

    def is_moving(self):
        return True
