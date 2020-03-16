import numpy as np
import wrapt
from Instruments.interfaces import ICam, Reading
from Config import config
import attr

from ir_cam import PT_MCT
from spec_sp2500i import SP2500i
from typing import List, Optional, Tuple
from scipy.stats import trim_mean

PROBE_CENTER = 98
REF_CENTER = 34
k = 4
PROBE_RANGE = (PROBE_CENTER-k, PROBE_CENTER+k+1)
REF_RANGE = (REF_CENTER-k, REF_CENTER+k+1)


@attr.s(auto_attribs=True)
class PhaseTecCam(ICam):
    _spec: SP2500i = attr.ib()
    probe_rows: Tuple[float, float] = attr.ib()
    ref_rows: Tuple[float, float] = attr.ib()
    name: str = 'Phasetec Array'
    shots: int = config.shots
    line_names: List[str] = ['Probe', 'Ref', 'max']
    std_names: List[str] = ['Probe', 'Ref', 'Probe/Ref']
    sig_names: List[str] = ['Sig']
    channels: int = 128
    ext_channels: int = 0
    changeable_wavelength: bool = True
    changeable_slit: bool = False
    background: Optional[tuple] = None
    _cam: PT_MCT = attr.ib(factory=PT_MCT)

    @probe_rows.default
    def _probe_rows_default(self):
        if hasattr(config, 'probe_rows'):
            return config.probe_rows
        else:
            return PROBE_RANGE

    @ref_rows.default
    def _ref_rows_default(self):
        if hasattr(config, 'probe_rows'):
            return config.probe_rows
        else:
            return REF_RANGE

    @_spec.default
    def _default_spec(self):
        return SP2500i(comport='COM4')

    def set_shots(self, shots: int):
        self._cam.shots = shots

    def read_cam(self):
        return self._cam.read_cam()

    def make_reading(self):
        arr = self._cam.read_cam()

        if self.background is not None:
            arr = arr - self.background[None, :, :]
        pr_range = self.probe_rows
        ref_range = self.ref_rows
        probe = np.nanmean(arr[:, pr_range[0]:pr_range[1], :], 1)
        probemax = np.nanmax(arr[:, pr_range[0]:pr_range[1], :], 1)
        ref = np.nanmean(arr[:, ref_range[0]:ref_range[1], :], 1)

        probe_mean = np.nanmean(probe, 0)
        probe_std = 100 * np.std(probe, 0) / probe_mean
        probe_max = np.nanmean(probemax, 0)

        ref_mean = np.nanmean(ref, 0)
        ref_std = 100 * np.std(ref, 0) / ref_mean

        with np.errstate(invalid='ignore', divide='ignore'):
            normed = probe / ref
            norm_std = 100 * np.nanstd(normed, 0) / np.nanmean(normed, 0)
            pu = trim_mean(normed.T[:, ::2], 0.1, 1)
            not_pu = trim_mean(normed.T[:, 1::2], 0.1, 1)
            sig = -1000 * np.log10(pu/not_pu)
        # print(sig.shape, ref_mean.shape, norm_std.shape, probe_mean.shape)
        reading = Reading(lines=np.stack((probe_mean, ref_mean, probe_max)),
                          stds=np.stack((probe_std, ref_std, norm_std)),
                          signals=sig[None, :], valid=True)
        return reading

    def get_wavelength(self):
        return self._spec.get_wavelength()

    def set_wavelength(self, wl, timeout):
        return self._spec.set_wavelength(wl, timeout=timeout)

    def set_background(self, shots=0):
        arr = self._cam.read_cam()
        back_probe = np.nanmean(arr[:, :, :], 0)
        self.background = back_probe

    def remove_background(self):
        self.background = None

    def get_wavelength_array(self, center_wl):
        center_wl = self.get_wavelength()
        disp = 7.69
        center_ch = 63
        if center_wl < 1000:
            return np.arange(-64, 64, 1)
        else:
            return (np.arange(128)-center_ch)*disp+center_wl

_ircam = PhaseTecCam()
