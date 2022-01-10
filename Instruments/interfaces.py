import abc
import asyncio
import atexit
import contextlib
import json
import multiprocessing
import threading
import time
import typing
import warnings
import xmlrpc.server as rpc

import attr
import numpy as np
from qtpy.QtCore import Signal, QObject
from scipy.constants import c

from .signal_processing import Reading, Reading2D, Spectrum

QObjectType = type(QObject)

T = typing

class QABCMeta(QObjectType, abc.ABCMeta):
    pass

@attr.s(auto_attribs=True)
class IDevice(QObject, metaclass=QABCMeta):
    name: str

    registered_devices: T.ClassVar[T.List['IDevice']] = []

    def __attrs_post_init__(self):
        QObject.__init__(self)
        self.registered_devices.append(self)
        self.load_state()
        atexit.register(self.save_state)

    def shutdown(self):
        pass

    @classmethod
    def create_remote(cls, addr, type='process', *args, **kwargs):
        '''Creates an instance and puts it into a
        xmlrpc server which is started in a separated thread.

        Returns (obj, server, thread)'''
        def create_obj():
            obj = cls(*args, **kwargs)
            server = rpc.SimpleXMLRPCServer(addr, allow_none=True)
            server.register_instance(obj)
            server.register_introspection_functions()
            server.serve_forever()

        if type == 'process':
            thr = multiprocessing.Process(target=create_obj)
        else:
            thr = threading.Thread(target=create_obj)

        return thr

    def get_state(self) -> dict:
        return dict()

    def save_state(self):
        d = self.get_state()
        if d:
            with open(self.name + '.cfg', 'w') as f:
                json.dump(d, f)

    def load_state(self, exclude: T.Optional[T.List[str]] = None):
        """
        Looks for a .cfg file. If found, uses all values in the json
        as attributes.
        """
        if exclude is None:
            exclude = []
        try:
            with open(self.name + '.cfg', 'r') as f:
                d = json.load(f)
            for key, val in d.items():
                if not hasattr(self, key):
                    warnings.warn(f"Config file for {self.name} has value for {key}, which is not "
                                  f"an attribute of the class.")
                if key not in exclude:
                    setattr(self, key, val)
        except FileNotFoundError:
            return


@attr.s(auto_attribs=True, cmp=False)
class ISpectrograph(IDevice):
    changeable_wavelength: bool = False
    changeable_slit: bool = False
    center_wl: typing.Optional[float] = None

    sigWavelengthChanged = Signal(float)
    sigSlitChanged = Signal(float)
    sigGratingChanged = Signal(int)

    @property
    def gratings(self):
        return [0]

    @abc.abstractmethod
    def set_wavelength(self, wl: float, timeout=3):
        pass

    @abc.abstractmethod
    def get_wavelength(self) -> float:
        pass

    def get_slit(self) -> float:
        pass

    def set_slit(self, slit: float):
        pass

    def set_grating(self, idx):
        pass

    def get_grating(self) -> int:
        pass


# Defining a minimal interface for each hardware
@attr.s(auto_attribs=True, cmp=False)
class ICam(IDevice):
    shots: int
    line_names: T.List[str]
    sig_names: T.List[str]
    std_names: T.List[str]
    channels: int
    ext_channels: int
    background: object = None
    spectrograph: T.Optional[ISpectrograph] = None

    can_validate_pixel: bool = None

    @property
    def sig_lines(self):
        return len(self.sig_names)

    @property
    def std_lines(self):
        return len(self.std_names)

    @property
    def lines(self):
        return len(self.line_names)

    @abc.abstractmethod
    def read_cam(self):
        pass

    @abc.abstractmethod
    def make_reading(self) -> Reading:
        pass

    @abc.abstractmethod
    def get_spectra(self, frames: int) -> T.Dict[str, Spectrum]:
        pass

    def make_2D_reading(self, t2: np.ndarray, rot_frame: float, repetitions: int = 1,
                        save_frames: bool = False) -> T.Dict[str, Reading2D]:
        pass

    @abc.abstractmethod
    def set_shots(self, shots):
        pass

    def get_background(self):
        return self.background

    def remove_background(self):
        self.background = 0

    @abc.abstractmethod
    def set_background(self, shots):
        pass

    def record_background(self):
        r = self.make_reading()
        self.set_background(r.lines)

    def get_wavelength_array(self, center_wl):
        return np.arange(self.channels)

    def mark_valid_pixel(self):
        raise NotImplementedError

    def delete_valid_pixel(self):
        raise NotImplementedError("Should not be called")



def mm_to_fs(pos_in_mm):
    "converts mm to femtoseconds"
    pos_in_meters = pos_in_mm / 1000.
    pos_sec = pos_in_meters / c
    return pos_sec * 1e15


def fs_to_mm(t_fs):
    pos_m = c * t_fs * 1e-15
    return pos_m * 1000.


def _try_load():
    import json
    try:
        with open("home_pos", 'r') as f:
            h = json.load(f)['home']
        return h
    except FileNotFoundError:
        return 0


@attr.s(auto_attribs=True)
class IDelayLine(IDevice):
    home_pos: float = attr.Factory(_try_load)
    pos_sign: float = 1

    def get_state(self) -> dict:
        return dict(home_pos=self.home_pos)

    @abc.abstractmethod
    def move_mm(self, mm, *args, **kwargs):
        pass

    @abc.abstractmethod
    def get_pos_mm(self):
        pass

    def get_pos_fs(self):
        return self.pos_sign * mm_to_fs(
            (self.get_pos_mm() - self.home_pos) * 2.)

    def move_fs(self, fs, do_wait=False, *args, **kwargs):
        mm = self.pos_sign * fs_to_mm(fs)
        # print('mm', mm+self.home_pos)
        self.move_mm(mm / 2. + self.home_pos, *args, **kwargs)
        if do_wait:
            while self.is_moving():
                time.sleep(0.1)

    @abc.abstractmethod
    def is_moving(self):
        return False

    def def_home(self):
        self.home_pos = self.get_pos_mm()
        self.save_state()

    async def async_move_mm(self, mm, do_wait=False):
        self.move_mm(mm)
        if do_wait:
            while self.is_moving():
                self.pos = self.get_pos_mm()
                await asyncio.sleep(0.1)


@attr.s
class IShutter(IDevice):
    sigShutterToggled: Signal = attr.ib(attr.Factory(Signal))

    @abc.abstractmethod
    def toggle(self):
        pass

    @abc.abstractmethod
    def is_open(self) -> bool:
        pass

    def open(self):
        if self.is_open():
            return
        else:
            self.toggle()

    def close(self):
        if not self.is_open():
            return
        else:
            self.toggle()

    def shutdown(self):
        pass

    @contextlib.contextmanager
    def opened(self):
        self.open()
        yield
        self.close()


@attr.s
class IRotationStage(IDevice):
    sigDegreesChanged: Signal = attr.ib(attr.Factory(Signal))
    sigMovementCompleted: Signal = attr.ib(attr.Factory(Signal))

    @abc.abstractmethod
    def set_degrees(self, deg: float):
        pass

    def set_degrees_and_wait(self, deg: float):
        self.set_degrees(deg)
        while self.is_moving():
            time.sleep(0.1)

    @abc.abstractmethod
    def get_degrees(self) -> float:
        pass

    @abc.abstractmethod
    def is_moving(self):
        pass

    def move_relative(self, x):
        self.set_degrees(x + self.get_degrees())

    async def async_set_degrees(self, deg: float, do_wait=False):
        self.set_degrees(deg)
        while self.is_moving():
            self.sigDegreesChanged.emit(deg)
            await asyncio.sleep(0.3)


@attr.s
class ILissajousScanner(IDevice):
    pos_home: tuple = attr.ib()
    has_zaxis: bool = False

    def init_motor(self):
        pass

    def disable_motor(self):
        pass

    @abc.abstractmethod
    def get_pos_mm(self) -> typing.Tuple[float, float]:
        pass

    @abc.abstractmethod
    def set_pos_mm(self, x=None, y=None):
        pass

    def set_vel_mm(self, xvel=None, yvel=None):
        pass

    @abc.abstractmethod
    def is_moving(self) -> typing.Tuple[bool, bool]:
        pass

    @abc.abstractmethod
    def set_home(self):
        pass

    def set_zpos_mm(self, mm: float):
        raise NotImplementedError

    def get_zpos_mm(self) -> float:
        raise NotImplementedError

    def is_zmoving(self) -> bool:
        raise NotImplementedError


@attr.s
class PulseShaper(IDevice):
    pixel: np.array
    freqs: np.ndarray
    nu0: float

    @abc.abstractmethod
    def set_mask(self, amp, phase):
        pass

    def set_calibration(self, p0):
        self.freqs = np.polyval(p0, self.pixel)


class DAC(abc.ABC):
    @abc.abstractmethod
    def set_power(self, power):
        pass

    @abc.abstractmethod
    def get_power(self) -> float:
        pass

    @abc.abstractmethod
    def upload(self, masks):
        pass

    @property
    @abc.abstractmethod
    def running(self):
        pass


@attr.s(kw_only=True)
class IAOMPulseShaper(PulseShaper):
    dac: DAC
    disp: T.Optional[np.ndarray] = None
    use_brag: bool = False
    ac_freq: float = 75e6
    dac_freq: float = 1.2e9
    t: np.ndarray = attr.ib()
    grating_1: T.Optional[IRotationStage]
    grating_2: T.Optional[IRotationStage]

    @t.default
    def _t_def(self):
        return np.arange(self.pixel) / self.dac_freq

    def set_running(self, running: bool):
        pass

    def set_mask(self, amp, phase):
        return self.dac.set_mask(amp, phase)

    def mask_wfn(self, masks):
        wfn = np.zeros((self.pixel, len(masks)))
        for i, m in enumerate(masks):
            wfn[i, :] = np.cos(2 * np.pi * self.t * self.ac_freq -
                               np.angle(m)) * np.abs(m)
        self.dac.upload(wfn)

    def set_disp_mask(self, mask):
        pass

    def set_mode(self, chopped=True, phase_cycling=False):
        mask1 = np.ones(self.pixel)
        mask2 = np.zeros(self.pixel)
        if self.disp is not None:
            mask1 *= self.disp
        m = [mask1, mask2]
        if phase_cycling:
            mask3 = mask1 * np.exp(1j * np.pi)
            m.append(mask3)
            m.append(mask1)
        if not chopped:
            m = m[0, 2]
        self.mask_wfn(m)

    def set_grating_angle(self, ang1=None, ang2=None):
        if ang1:
            self.grating_2.set_degrees(ang1)
        if ang2:
            self.grating_2.set_degrees(ang2)
