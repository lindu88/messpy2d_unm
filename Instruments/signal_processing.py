import math
from typing import Optional, Callable

import attr
import numpy as np
from scipy.constants import c
from numba import jit, prange

LOG10 = math.log(10)


def THz2cm(THz):
    """
    THz to cm-1
    """
    return c*THz/1e7


def cm2THz(cm):
    """
    cm-1 to THz
    """
    return cm*1e7/c

@jit
def first(arr, val: float) -> int:
    for i, x in enumerate(arr):
        if x > val:
            return i
    return 0


def stats(probe, probe_max=None):
    mean, std, mi, ma = fast_stats2d(probe).T
    probe_mean = mean
    probe_std = 100 * std / probe_mean
    if probe_max is not None:
        probe_max = np.nanmean(probe_max, 1)
    else:
        probe_max = ma
    return probe_mean, probe_std, probe_max


@jit(parallel=True)
def fast_stats2d(arr):
    """
    For a given 2-dimensional array calculate mean, std, min_val and max_val along the second dimension
    in a single pass.
    """
    n = arr.shape[0]
    res = np.zeros((n, 4))
    for i in prange(n):
        res[i, :] = fast_stats(arr[i, :])
    return res

@jit(fastmath=True)
def fast_stats(arr):
    """
    For a given 1-dimensional array calculate mean, std, min_val and max_val in a single pass.
    """
    s = 0
    sq_sum = 0
    n = 0
    min_val = max_val = arr[0]
    for x in arr:
        if not math.isnan(x):
            n += 1
        else:
            continue
        s += x
        sq_sum += x*x
        if x > max_val:
            max_val = x
        elif x < min_val:
            min_val = x
    mean = s/n
    var = (sq_sum - s*s/n) / n
    std = math.sqrt(var)
    return mean, std, min_val, max_val

@jit(fastmath=True)
def fast_signal(arr):
    sig = 0
    mean = 0
    n = arr.shape[0]

    for i in range(0, n, 2):
        sig += (arr[i] - arr[i+1])
        mean += arr[i]

    return 1000/LOG10*sig/mean


@jit(parallel=True)
def fast_signal2d(arr):
    """
    For a given 2-dimensional array calculate mean, std, min_val and max_val along the second dimension
    in a single pass.
    """
    n = arr.shape[0]
    res = np.zeros(n)
    for i in prange(n):
        res[i] = fast_signal(arr[i, :])
    return res


@attr.s(auto_attribs=True)
class Spectrum:
    data: np.ndarray
    mean: np.ndarray
    std: np.ndarray
    max: Optional[np.ndarray]
    name: Optional[str] = None
    frame_data: Optional[np.ndarray] = None
    frames: Optional[int] = None
    signal: Optional[np.ndarray] = None

    @classmethod
    def create(cls, data, data_max=None, name=None, frames=None, first_frame=None):
        mean, std, max = stats(data, data_max)
        signal = None
        if frames is not None:
            frame_data = np.empty((mean.shape[0], frames))

            for i in range(frames):
                frame_data[:, i] = np.nanmean(data[:, i::frames], 1)
            frame_data = np.roll(frame_data, -first_frame, 1)
            if frames == 2:
                signal = 1000 / LOG10 * np.log1p(
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
    interferogram: np.ndarray
    t2_ps: np.ndarray
    signal_2D: np.ndarray = attr.ib()
    freqs: np.ndarray = attr.ib()
    window: Optional[Callable] = np.hanning
    upsample: int = 2
    rot_frame: float = 0

    @classmethod
    def from_spectrum(cls, s: Spectrum, t2_ps, rot_frame, **kwargs) -> 'Reading2D':
        assert (s.frames and s.frames % 4 == 0 and (s.frame_data is not None))
        f = s.frame_data
        f.reshape((f.shape[0], 4, f.shape[1] // 4))
        # 4 Frames for each tau
        sig = 1000 / LOG10 * (f[:, 0, :] - f[:, 1, :] + f[:, 2, :] - f[:, 3, :])
        assert (sig.shape[1] == len(t2_ps))
        return cls(interferogram=sig, t2_ps=t2_ps, rot_frame=rot_frame, **kwargs)

    @signal_2D.default
    def calc_2d(self):
        a = self.interferogram.copy()
        a[:, 0] *= 0.5
        if self.window is not None:
            win = self.window(a.shape[1] * 2)
            a = a * win[None, a.shape[1]:]
        return np.fft.rfft(a, a.shape[1] * self.upsample, 1).real

    @freqs.default
    def calc_freqs(self):
        freqs = np.fft.rfftfreq(len(self.t2_ps) * self.upsample, self.t2_ps[1] - self.t2_ps[0])
        return THz2cm(freqs) + self.rot_frame
