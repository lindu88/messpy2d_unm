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
from pathlib import Path

import attr
import numpy as np
from qtpy.QtCore import Signal, QObject  # type: ignore
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
        conf_path = Path(__file__).parent/'config'
        if d:
            with (conf_path / (self.name + '.cfg')).open('w') as f:
                json.dump(d, f, indent=4)

    def load_state(self, exclude: T.Optional[T.List[str]] = None):
        """
        Looks for a .cfg file. If found, uses all values in the json
        as attributes.
        """
        if exclude is None:
            exclude = []
        try:
            conf_path = Path(__file__).parent / 'config'
            with (conf_path / (self.name + '.cfg')).open('r') as f:
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
        raise NotImplementedError

    def set_slit(self, slit: float):
        raise NotImplementedError

    def set_grating(self, idx):
        raise NotImplementedError

    def get_grating(self) -> int:
        raise NotImplementedError


# Defining a minimal interface for each hardware
@attr.s(auto_attribs=True, cmp=False, kw_only=True)
class ICam(IDevice):
    shots: int
    line_names: T.List[str]
    sig_names: T.List[str]
    std_names: T.List[str]
    has_ref: bool = False
    channels: int
    ext_channels: int
    background: object = None
    spectrograph: T.Optional[ISpectrograph] = None

    can_validate_pixel: bool = False

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
    def get_spectra(self, frames: T.Optional[int]) -> T.Tuple[T.Dict[str, Spectrum], T.Any]:
        pass

    def make_2D_reading(self, t2: np.ndarray, rot_frame: float, repetitions: int = 1,
                        save_frames: bool = False) -> T.Dict[str, Reading2D]:
        raise NotImplementedError

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
    beam_passes: int = 2

    def get_state(self) -> dict:
        return dict(home_pos=self.home_pos)

    @abc.abstractmethod
    def move_mm(self, mm: float, *args, **kwargs):
        pass

    @abc.abstractmethod
    def get_pos_mm(self) -> float:
        pass

    def get_pos_fs(self) -> float:
        return self.pos_sign * mm_to_fs(
            (self.get_pos_mm() - self.home_pos) * self.beam_passes)

    def move_fs(self, fs, do_wait=False, *args, **kwargs):
        mm = self.pos_sign * fs_to_mm(fs)
        # print('mm', mm+self.home_pos)
        self.move_mm(mm / self.beam_passes + self.home_pos, *args, **kwargs)
        if do_wait:
            while self.is_moving():
                time.sleep(0.1)

    @abc.abstractmethod
    def is_moving(self) -> bool:
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
    sigShutterToggled: typing.ClassVar[Signal] = Signal(bool)

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
    sigDegreesChanged: typing.ClassVar[Signal] = Signal(float)
    sigMovementCompleted: typing.ClassVar[Signal] = Signal()

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
    pos_home: T.Tuple[float, float] = (0, 0)
    has_zaxis: bool = False

    def init_motor(self):
        pass

    def disable_motor(self):
        pass

    @abc.abstractmethod
    def get_pos_mm(self) -> typing.Tuple[float, float]:
        pass

    @abc.abstractmethod
    def set_pos_mm(self, x: typing.Optional[float] = None, y: typing.Optional[float] = None):
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


@attr.define(kw_only=True)
class IPowerMeter(IDevice):

    @abc.abstractmethod
    def read_power(self) -> float:
        raise NotImplementedError
