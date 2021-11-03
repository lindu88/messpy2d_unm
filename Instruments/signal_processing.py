import math
import typing as T

import attr
import numpy as np
from scipy.constants import c
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


def stats(probe, probe_max=None):
    probe_mean = np.nanmean(probe, 1)
    probe_std = 100 * np.std(probe, 1) / probe_mean
    if probe_max is not None:
        probe_max = np.nanmean(probe_max, 1)
    else:
        probe_max = None
    return probe_mean, probe_std, probe_max


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
    interferogram: np.ndarray
    t2_ps: np.ndarray
    signal_2D: np.ndarray = attr.ib()
    freqs: np.ndarray = attr.ib()
    window: T.Optional[T.Callable] = np.hanning
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
