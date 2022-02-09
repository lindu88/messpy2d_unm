import typing
from typing import Dict, Optional

import numpy as np
import attr
from Instruments.interfaces import ICam, IDelayLine, IRotationStage, \
    IShutter, Reading, Spectrum, ISpectrograph, ILissajousScanner
import time
import threading

@attr.s(auto_attribs=True)
class MockState:
    wl: float = 0
    t: float = 0
    t2: float = 0
    shaper_amp: float = 0
    shaper_running: bool = True
    shutter: bool = False
    rot_stage_angle: float = 45
    stage_pos: list[float] = [0, 0, 0]

state = MockState()


@attr.s(auto_attribs=True)
class MockSpectrograph(ISpectrograph):
    name: str = 'MockSpec'
    changeable_wavelength: bool = True
    center_wl: float = 300
    _cur_grating: int = 0

    def get_state(self) -> dict:
        return {
            'grating': self.gratings[self._cur_grating],
            'current wavelength': self.center_wl,
        }

    def set_wavelength(self, wl: float, timeout=3):
        self.center_wl = wl
        state.wl = wl
        self.sigWavelengthChanged.emit(wl)

    def get_wavelength(self):
        return self.center_wl

    @property
    def gratings(self) -> Dict[int, str]:
        return {0: "0", 1: "1"}

    def set_grating(self, idx: int):
        self._cur_grating = idx
        self.sigGratingChanged.emit(idx)

    def get_grating(self) -> int:
        return self._cur_grating


@attr.s(auto_attribs=True)
class CamMock(ICam):
    name: str = 'MockCam'
    shots: int = 20
    line_names: list = ['Probe', 'Ref']
    sig_names: list = ['Probe Normed', 'Probe' ]
    std_names: list = ['Probe', 'Ref', 'Normed']
    channels: int = 200
    ext_channels: int = 3
    background: object = None
    spectrograph: Optional[ISpectrograph] = attr.Factory(MockSpectrograph)

    def get_state(self) -> dict:
        return {'shots': self.shots}

    def set_shots(self, shots):
        self.shots = shots

    def read_cam(self):
        t0 = time.time()
        x = self.get_wavelength_array()
        y = 300*np.exp(-(x-250)**2/50**2/2)
        from math import erfc, sqrt
        knife_amp = 2-erfc(sqrt(2)*(-state.stage_pos[0]+0.5) / 0.25)
        knife_amp *= 2 - erfc(sqrt(2) * (-state.stage_pos[1]+0.5) / 0.25)
        y = y*(knife_amp/4)

        a = np.random.normal(loc=y, scale=3, size=(self.shots, self.channels))
        b = np.random.normal(loc=y/2, scale=3, size=(self.shots, self.channels))
        common_noise = np.random.normal(loc=1, scale=0.15, size=(self.shots, 1))

        a *= common_noise
        b *= common_noise
        ext = np.random.normal(size=(self.shots, self.ext_channels))
        chop = np.zeros(self.shots, 'bool')
        chop[::2] = True
        signal = 0.1*np.exp(-state.t/3000) if state.t > 0 else 0.1*np.exp(state.t/100)
        y_sig = 300 * np.exp(-(x - 250) ** 2 / 30 ** 2 / 2)
        y_sig -= 300 * np.exp(-(x - 310) ** 2 / 30 ** 2 / 2)
        a[::2, :] *= 1 + signal * y_sig/300
        dt = time.time() - t0
        time.sleep(self.shots/1000.-dt)
        return a, b, chop, ext

    def make_reading(self) -> Reading:
        a, b, chopper, ext = self.read_cam()
        if self.background is not None:
            a -= self.background[0, ...]
            b -= self.background[1, ...]
        tmp = np.stack((a, b, a/b))
        tm = tmp.mean(1)
        ts = 100 * tmp.std(1)/tm

        with np.errstate(all="ignore"):
            signal = -1000*np.log10(np.nanmean(a[chopper, :], 0)/np.nanmean(a[~chopper, :], 0))
            signal2 = -1000 * np.log10(np.nanmean((a/b)[chopper, :], 0) / np.nanmean((a/b)[~chopper, :], 0))
        return Reading(
            lines=tm[:2, :],
            stds=ts,
            signals=np.stack((signal2, signal)),
            valid=True,
        )

    def get_spectra(self, frames):
        pass

    def set_background(self, shots):
        pass

    def get_wavelength_array(self, center_wl=None):
        if not center_wl:
            center_wl = self.spectrograph.center_wl
        x = (np.arange(self.channels)-self.channels//2)
        return x*0.5 + center_wl


@attr.s(auto_attribs=True)
class DelayLineMock(IDelayLine):
    name: str = 'MockDelayStage'
    pos_mm: float = 0.
    mock_speed: float = 6.
    moving: bool = False
    current_move: tuple = None

    def move_mm(self, mm, do_wait=True):
        distance = mm - self.pos_mm
        duration = distance / self.mock_speed
        self.current_move = (time.time(), mm)
        self.moving = True
        self.pos_mm = mm

    def get_pos_mm(self):
        if self.moving:
            time_passed = self.current_move[0] - time.time()
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


@attr.s(auto_attribs=True)
class StageMock(ILissajousScanner):
    name: str = 'MockSampleStage'
    has_zaxis: bool = True
    _pos: list[float] = [0, 0, 0]
    pos_home: tuple[float] = (0, 0)

    def is_moving(self) -> typing.Tuple[bool, bool]:
        return False, False

    def set_home(self):
        pass

    def set_zpos_mm(self, mm: float):
        state.stage_pos[2] = mm

    def get_zpos_mm(self) -> float:
        return state.stage_pos[2]

    def is_zmoving(self) -> bool:
        return False

    def get_pos_mm(self) -> typing.Tuple[float, float]:
        return tuple(state.stage_pos[:2])

    def set_pos_mm(self, x=None, y=None):
        print(f"{x=} {y=}")
        if x is not None:
            state.stage_pos[0] = x
        if y is not None:
            state.stage_pos[1] = y


