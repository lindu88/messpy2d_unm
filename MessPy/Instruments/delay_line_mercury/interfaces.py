import typing, abc, time, attr, threading
import xmlrpc.server as rpc
from enum import auto
import numpy as np
from Signal import Signal
T = typing

@attr.s
class IDevice(abc.ABC):
    name: str = attr.ib()

    def init(self):
        pass

    def shutdown(self):
        pass

    @classmethod
    def create_remote(cls, *args, **kwargs):
        '''Creates an instance and puts it into a 
        xmlrpc server which is started in a seperated thread.
        
        Returns (obj, server, thread)'''
        obj = cls(*args, **kwargs)
        server = rpc.SimpleXMLRPCServer('')
        server.register_instance(obj)
        server.register_introspection_functions()
        thr = threading.Thread(target=server.serve_forever)
        return obj, server, thr



@attr.s(auto_attribs=True, cmp=False)
class Reading:
    "Each array has the shape (n_type, pixel)"
    lines: np.ndarray
    stds: np.ndarray
    signals: np.ndarray
    valid: bool

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
    changeable_wavelength: bool = False
    changeable_slit: bool = False
    center_wl: typing.Optional[float] = None
    slit_width: typing.Optional[float] = None

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
    def set_shots(self, shots):
        pass

    def get_background(self):
        return self.background

    def set_background(self, back):
        self.background = back

    def record_background(self):
        r = self.make_reading()
        self.set_background(r.lines)

    def get_wavelength_array(self, center_wl):
        return np.arange(self.channels)

    def get_wavelength(self) -> float:
        return 0

    def set_wavelength(self, wl: float):
        pass

    def set_slit(self, slit: float):
        pass

    def get_slit(self) -> float:
        return 0

def mm_to_fs(pos_in_mm):
    "converts mm to femtoseconds"
    speed_of_light = 299792458.
    pos_in_meters = pos_in_mm / 1000.
    pos_sec = pos_in_meters / speed_of_light
    return pos_sec * 1e15


def fs_to_mm(t_fs):
    speed_of_light = 299792458.
    pos_m = speed_of_light * t_fs * 1e-15
    return pos_m * 1000.


@attr.s(auto_attribs=True)
class IDelayLine(IDevice):
    home_pos: float = attr.ib(0.)
    pos_sign: float = 1

    @abc.abstractmethod
    def move_mm(self, mm, *args, **kwargs):
        pass

    @abc.abstractmethod
    def get_pos_mm(self):
        pass

    def get_pos_fs(self):
        return self.pos_sign * mm_to_fs((self.get_pos_mm()-self.home_pos)*2.)

    def move_fs(self, fs, do_wait=False, *args, **kwargs):
        mm = self.pos_sign*fs_to_mm(fs)
        #print('mm', mm+self.home_pos)
        self.move_mm(mm/2.+self.home_pos, *args, **kwargs)
        if do_wait:
            while self.is_moving():
                time.sleep(0.1)

    @abc.abstractmethod
    def is_moving(self):
        return False

    def def_home(self):
        self.home_pos = self.get_pos_mm()

    def shutdown(self):
        pass

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

@attr.s
class IRotationStage(abc.ABC):
    sigDegreesChanged: Signal = attr.ib(attr.Factory(Signal))
    sigMovementCompleted: Signal = attr.ib(attr.Factory(Signal))

    @abc.abstractmethod
    def set_degrees(self, deg: float):
        pass

    def set_degrees_and_wait(self, deg: float):
        self.set_degrees(float)
        while self.is_moving():
            time.sleep(0.1)

    @abc.abstractmethod
    def get_degrees(self) -> float:
        pass

    @abc.abstractmethod
    def is_moving(self):
        pass


class ILissajousScanner(IDevice):
    @abc.abstractmethod
    def set_pos_mm(self, x=None, y=None):
        pass

    def set_vel_mm(self, xvel=None, yvel=None):
        pass

    @abc.abstractmethod
    def is_moving(self) -> typing.Tuple[bool, bool]:
        pass
