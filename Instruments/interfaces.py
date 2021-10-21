import typing, abc, time, attr, threading, multiprocessing
import xmlrpc.server as rpc
from enum import auto
import numpy as np
from numpy.lib.mixins import NDArrayOperatorsMixin

T = typing
import asyncio, contextlib

from qtpy.QtWidgets import QWidget
from qtpy.QtCore import Signal, QObject

from scipy.constants import c
import json

import math
from skultrafast.unit_conversions import THz2cm


@attr.s(auto_attribs=True)
class IDevice(abc.ABC):
    name: str

    def init(self):
        self.load_state()

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

    def extra_opts(self):
        pass

    def get_state(self) -> dict:
        return dict()

    def save_state(self):
        d = self.get_state()
        if d:
            with open(self.name + '.cfg', 'w') as f:
                json.dump(d, f)

    def load_state(self):
        try:
            with open(self.name + '.cfg', 'r') as f:
                d = json.load(f)
            for key, val in d:
                setattr(self, key, val)
        except FileNotFoundError:
            return


def stats(probe, probemax=None):
    probe_mean = np.nanmean(probe, 1)
    probe_std = 100 * np.std(probe, 1) / probe_mean
    if probemax is not None:
        probe_max = np.nanmean(probemax, 1)
    else:
        probe_max = None
    return probe_mean, probe_std, probe_max


import math
LOG10 = math.log(10)


@attr.s(auto_attribs=True)
class Spectrum:
    data: np.ndarray
    mean: np.ndarray
    std: np.ndarray
    max: T.Optional[np.ndarray]
    name: T.Optional[str] = None
    frame_data: T.Optional[np.ndarray] = None
    frames: T.Optional[int] = None
    signal: T.Optional[np.ndarray] = None

    @classmethod
    def create(cls, data, data_max=None, name=None, frames=None):
        mean, std, max = stats(data, data_max)
        signal = None
        if frames is not None:
            frame_data = np.empty((mean.shape[0], frames))

            for i in range(frames):
                frame_data[:, i] = np.nanmean(data[:, i::frames], 1)
            if frames == 2:
                signal = -1000 / LOG10 * np.log1p(
                    (frame_data[:, 0] - frame_data[:, 1]) / frame_data[:, 1])

        else:
            frame_data = None

        return cls(data=data,
                   mean=mean,
                   std=std,
                   name=name,
                   max=max,
                   signal=signal,
                   frames=frames,
                   frame_data=frame_data)


@attr.s(auto_attribs=True, cmp=False)
class Reading:
    "Each array has the shape (n_type, pixel)"
    lines: np.ndarray
    stds: np.ndarray
    signals: np.ndarray
    valid: bool


@attr.s(auto_attribs=True, cmp=False)
class Reading2D:
    "Has the shape (pixel, t2)"
    inferogram: np.ndarray
    t2_ps: np.ndarray
    signal_2D: np.ndarray = attr.ib()
    freqs: np.ndarray = attr.ib()
    window : T.Optional[typing.Callable] = np.hanning
    upsample : int = 2
    rot_frame : float = 0

    @classmethod
    def from_spectrum(cls, s: Spectrum, t2_ps, rot_frame, **kwargs) -> 'Reading2D':
        assert(s.frames and s.frames % 4 == 0 and (s.frame_data is not None))
        f = s.frame_data
        f.reshape(f.shape[0], 4, f.shape[1] //4)
        s = 1000/LOG10*(f[:, 0, :] - f[:, 1, :] + f[:, 2, :] - f[:, 3, :])
        assert(s.shape[1] == len(t2_ps))
        return cls(inferogram=s, t2_ps=t2_ps, rot_frame=rot_frame, **kwargs)

    @signal_2D.default
    def calc_2d(self):
        a = self.inferogram.copy()
        a[:, 0] *= 0.5
        if self.window is not None:
            win = self.window(a.shape[1]*2)
            a = a*win[None, a.shape[1]:]
        return np.fft.rfft(a, a.shape[1]*self.upsample, 1).real

    @freqs.default
    def calc_freqs(self):
        freqs = np.fft.rfftfreq(len(self.t2_ps)*self.upsample, self.t2_ps[1]-self.t2_ps[0])
        return THz2cm(freqs) + self.rot_frame






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
    def get_spectra(self) -> T.Dict[str, Spectrum]:
        pass

    def make_2D_reading(self, t2: np.ndarray) -> Reading2D:
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

    def get_wavelength(self) -> float:
        return 0

    def set_wavelength(self, wl: float):
        pass

    def set_slit(self, slit: float):
        pass

    def get_slit(self) -> float:
        return 0

    async def async_make_read(self):

        out = asyncio.Queue()

        def reader():
            out.append(self.make_reading())

        thread = threading.Thread(target=reader)
        thread.start()
        while thread.is_alive():
            await asyncio.sleep(0.01)

        return await out.get()


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
        import json
        self.home_pos = self.get_pos_mm()
        with open("home_pos", 'w') as f:
            json.dump(dict(home=self.home_pos), f)

    def load_home(self):
        import json
        with open("home_pos", 'r') as f:
            self.home_pos = json.load(f)['home']
        print(self.home_pos)

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
        pass

    def get_zpos_mm(self) -> float:
        pass

    def is_zmoving(self) -> bool:
        pass


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


def THz2cm(nu):
    return (nu * 1e10) / c


def cm2THz(nu):
    return c / (nu * 1e10)


def double_pulse_mask(nu: np.ndarray, nu_rf: float, tau: float, phi1: float,
                      phi2: float):
    """
    Return the mask to generate a double pulse

    Parameters
    ----------
    nu : array
        freqs of the shaper pixels in THz
    nu_rf : float
        rotating frame freq of the scanned pulse in THz
    tau : float
        Interpulse distance in ps
    phi1 : float
        Phase shift of the scanned pulse
    phi2 : float
        Phase shift of the fixed pulse
    """
    double = 0.5 * (np.exp(-1j * (nu - nu_rf) * 2 * np.pi * tau) *
                    np.exp(+1j * phi1) + np.exp(1j * phi2))
    return double


def dispersion(nu, nu0, GVD, TOD, FOD):
    x = nu - nu0
    x *= (2 * np.pi)
    facs = np.array([GVD, TOD, FOD]) / np.array([2, 6, 24])
    return x**2 * facs[0] + x**3 * TOD * facs[1] + x**3 * FOD * facs[2]


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


@attr.s
class IAOMPulseShaper(PulseShaper):
    dac: DAC
    disp: T.Optional[np.ndarray]
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
        return dac.set_mask(amp, phase)

    def mask_wfn(self, masks):
        wfn = np.zeros((self.pixel, len(masks)))
        for i, m in enumerate(masks):
            wfn[i, :] = np.cos(2 * np.pi * self.t * self.ac_freq -
                               np.angle(m)) * np.abs(m)
        self.dac.upload(wfn)

    def set_disp_mask(self, mask):
        pass

    def set_two_d_mask(self, tau_max, tau_step, rot_frame, phase_cycling=4):
        taus = np.arange(0, tau_max + 1e-3, tau_step)
        phase = np.array([(1, 0), (1, 1), (0, 1), (0, 0)]) * np.pi
        if phase_cycling == 4:
            phase = np.array([(1, 0), (1, 1), (0, 1), (0, 0)]) * np.pi
            phase = np.repeat(phase, repeats=taus, axis=0)
            phi1 = phase[:, 0]
            phi2 = phase[:, 1]
            taus = taus.repeat(4)
        masks = double_pulse_mask(self.freqs[:, None], rot_frame,
                                  taus[None, :], phi1[None, :], phi2[None, :])

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