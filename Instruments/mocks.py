import numpy as np
import attr
from Instruments.interfaces import ICam, IDelayLine, IRotationStage, IShutter, Reading

@attr.s(auto_attribs=True)
class MockState:
    wl: float = 0
    t: float = 0
    shutter: bool = False
    rot_stage_angle: float = 45

state = MockState()


@attr.s(auto_attribs=True)
class CamMock(ICam):
    name: str = 'MockCam'
    shots: int = 20
    line_names: list = ['Test1', 'Test2']
    sig_names: list = ['Test1']
    std_names: list = ['Test1', 'Test2']
    channels: int = 200
    ext_channels: int = 3
    background: object = None
    changeable_wavelength: True = True
    center_wl: float = 300

    def set_shots(self, shots):
        self.shots = shots

    def read_cam(self):
        a = np.random.normal(loc=30, size=(self.channels, self.shots)).T
        b = np.random.normal(loc=20, size=(self.channels, self.shots)).T
        ext = np.random.normal(size=(self.ext_channels, self.shots)).T
        chop = np.array([True, False]).repeat(self.shots/2)
        return a, b, chop, ext

    def make_reading(self) -> Reading:
        a, b, chopper, ext = self.read_cam()
        if self.background is not None:
            a -= self.background[0, ...]
            b -= self.background[1, ...]
        tmp = np.stack((a, b))
        tm = tmp.mean(1)
        signal = -np.log10(a[chopper, :].mean(0)/a[~chopper, :].mean(0))
        return Reading(
            lines=tm,
            stds=100*tmp.std(1)/tm,
            signals=signal[None, :],
            valid=True,
        )

    def set_wavelength(self, wl):
        self.center_wl = wl
        state.wl = wl

    def get_wavelength(self):
        return self.center_wl

    def get_wavelength_array(self, center_wl=None):
        if not center_wl:
            center_wl = self.center_wl
        x = (np.arange(self.channels)-self.channels//2)
        return x*0.5 + center_wl


@attr.s(auto_attribs=True)
class DelayLineMock(IDelayLine):
    name: str = 'MockDelayStage'
    pos_mm: float = 0.

    def move_mm(self, mm, do_wait=True):
        self.pos_mm = mm

    def get_pos_mm(self):
        return self.pos_mm

    def is_moving(self):
        return False

    def move_fs(self, fs, do_wait=False):
        super().move_fs(fs, do_wait=do_wait)
        state.t = fs

@attr.s(auto_attribs=True)
class RotStageMock(IRotationStage):
    name: str = 'Rotation Mock'
    deg: float = 0

    def set_degrees(self, deg: float):
        self.deg = deg
        state.rot_stage_angle = deg

    def get_degrees(self) -> float:
        return self.deg

    def is_moving(self):
        return False


@attr.s(auto_attribs=True)
class ShutterMock(IShutter):
    name = 'ShutterMock'
    is_open: bool = True

    def is_open(self):
        return self.is_open

    def toggle(self):
        self.is_open = not self.is_open
        state.shutter = self.is_open


