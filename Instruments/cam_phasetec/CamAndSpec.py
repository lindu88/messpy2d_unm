import concurrent
import threading
from math import log
from pathlib import Path
from typing import ClassVar, List, Optional, Tuple, Dict

import attr
import numpy as np
from scipy.stats import trim_mean
from qtpy.QtCore import Slot, Signal
from Config import config
from Instruments.interfaces import ICam
from Instruments.signal_processing import Reading, Spectrum, first, fast_col_mean, Reading2D

from Instruments.cam_phasetec.imaq_nicelib import Cam
from Instruments.cam_phasetec.spec_sp2500i import SP2150i
from typing import List, Optional, Tuple, Dict
from scipy.stats import trim_mean
from math import log


LOG10 = log(10)
PROBE_CENTER = 85
PROBE_CENTER_2 = 50
REF_CENTER = 15
k = 2
PROBE_RANGE = (PROBE_CENTER - k, PROBE_CENTER + k + 1)
PROBE2_RANGE = (PROBE_CENTER_2 - k, PROBE_CENTER_2 + k + 1)
REF_RANGE = (REF_CENTER - k, REF_CENTER + k + 1)

TWO_PROBES = True


@attr.s(auto_attribs=True, kw_only=True)
class PhaseTecCam(ICam):
    spectrograph: SP2150i = attr.ib()
    probe_rows: Tuple[int, int] = attr.ib()
    ref_rows: Tuple[int, int] = attr.ib()
    name: str = 'Phasetec Array'
    shots: int = 50

    if not TWO_PROBES:
        line_names: List[str] = ['Probe', 'Ref', 'max']
        std_names: List[str] = ['Probe', 'Ref', 'Probe/Ref']
        sig_names: List[str] = ['Sig', 'SigNoRef']
    else:
        probe2_rows: Tuple[int, int] = attr.ib()
        line_names: List[str] = ['Probe', 'Probe2', 'Ref', 'max']
        std_names: List[str] = ['Probe', 'Probe2', 'Ref', 'Probe/Ref']
        sig_names: List[str] = ['SigNoRef', 'Sig',  'Sig2NoRef', 'Sig2']

    beta1: Optional[object] = None
    beta2: Optional[object] = None
    channels: int = 128
    ext_channels: int = 0
    changeable_wavelength: bool = True
    changeable_slit: bool = False
    background: Optional[np.ndarray] = attr.ib()
    can_validate_pixel: bool = True
    valid_pixel: Optional[List[np.ndarray]] = None
    _cam: Cam = attr.ib(factory=Cam)

    sigRowsChanged: ClassVar[Signal] = Signal()

    @probe_rows.default
    def _probe_rows_default(self):
        return getattr(config, 'probe2_rows', PROBE_RANGE)

    @probe2_rows.default
    def _probe2_rows_default(self):
        return getattr(config, 'probe2_rows', PROBE2_RANGE)

    @ref_rows.default
    def _ref_rows_default(self):
        return getattr(config, 'ref_rows', REF_RANGE)

    @spectrograph.default
    def _default_spec(self):
        return SP2150i()

    @background.default
    def _back_default(self):
        try:
            return np.load(Path(__file__).parent / 'back.npy')
        except IOError:
            pass
        return None

    def get_state(self):
        d = {
            'shots': self.shots,
            'probe_rows': self.probe_rows,
            'ref_rows': self.ref_rows,
            'probe2_rows': self.probe2_rows
        }
        return d

    def load_state(self):
        super().load_state()
        self.set_shots(self.shots)

    def set_shots(self, shots: int):
        self._cam.set_shots(shots)
        self.shots = shots

    def read_cam(self):
        return self._cam.read_cam()

    def mark_valid_pixel(self,  min_val=2000, max_val=9000):
        arr, ch = self._cam.read_cam()

        pr_range = self.probe_rows
        ref_range = self.ref_rows
        pr2_range = self.probe2_rows

        self.valid_pixel = []
        for (l, u) in [pr_range, ref_range, pr2_range,]:
            sub_arr = arr[l:u, :, :].mean(-1)
            self.valid_pixel += [(min_val < sub_arr) & (sub_arr < max_val)]

    def delete_valid_pixel(self):
        self.valid_pixel = None

    def get_spectra(self, frames=None, **kwargs) -> Tuple[Dict[str, Spectrum], object]:
        arr, ch = self._cam.read_cam()
        if self.background is not None:
            arr = arr - self.background[:, :, None]
        if frames is not None:
            first_frame = first(np.array(ch[0]), 1)
        else:
            first_frame = None

        pr_range = self.probe_rows
        pr2_range = self.probe2_rows
        ref_range = self.ref_rows

        if self.valid_pixel is not None:
            probe = fast_col_mean(arr[pr_range[0]:pr_range[1], ...], self.valid_pixel[0])
            ref = fast_col_mean(arr[ref_range[0]:ref_range[1], ...], self.valid_pixel[1])
            if TWO_PROBES:
                probe2 = fast_col_mean(arr[pr2_range[0]:pr2_range[1], ...], self.valid_pixel[2])
        else:
            probe = np.nanmean(arr[pr_range[0]:pr_range[1], :, :], 0)
            ref = np.nanmean(arr[ref_range[0]:ref_range[1], :, :], 0)
            if TWO_PROBES:
                probe2 = np.nanmean(arr[pr2_range[0]:pr2_range[1], :, :], 0)

        get_max = kwargs.get('get_max', None)
        if get_max:
            probemax = np.nanmax(arr[:, :, :10], 0)
        else:
            probemax = None
        probe = Spectrum.create(probe, probemax, name='Probe1', frames=frames, first_frame=first_frame)
        ref = Spectrum.create(ref, name='Ref', frames=frames, first_frame=first_frame)

        if TWO_PROBES:
            probe2 = Spectrum.create(probe2, name='Probe2', frames=frames, first_frame=first_frame)
        return {i.name: i for i in (probe, probe2, ref)}, ch

    def make_reading(self, frame_data=None) -> Reading:
        d, ch = self.get_spectra(frames=2, get_max=True)
        probe = d['Probe1']
        ref = d['Ref']

        with np.errstate(invalid='ignore', divide='ignore'):
            normed = probe.data / ref.data
            norm_std = 100 * np.nanstd(normed, 1) / np.nanmean(normed, 1)

            n = first(ch[0], 1)
            if (n % 2) == 0:
                f = 1000
            else:
                f = -1000

            pu = trim_mean(normed[:, ::2], 0.2, 1)
            not_pu = trim_mean(normed[:, 1::2], 0.2, 1)

            sig = f * np.log10(pu / not_pu)
            sig2 = d['Probe1'].signal

        # print(sig.shape, ref_mean.shape, norm_std.shape, probe_mean.shape)
        if not TWO_PROBES:
            reading = Reading(lines=np.stack(
                (probe.mean, ref.mean, probe.max)),
                              stds=np.stack((probe.std, ref.std, norm_std)),
                              signals=np.stack((sig, sig2)),
                              valid=True)

        else:
            probe2 = d['Probe2']
            normed2 = probe2.data / ref.data

            pu2 = trim_mean(normed2[:, ::2], 0.2, 1)
            not_pu2 = trim_mean(normed2[:, 1::2], 0.2, 1)
            sig_pr2 = f * np.log10(pu2 / not_pu2)

            pu2 = trim_mean(probe2.data[:, ::2], 0.2, 1)
            not_pu2 = trim_mean(probe2.data[:, 1::2], 0.2, 1)
            sig_pr2_noref = f * np.log10(pu2 / not_pu2)

            if self.beta1 is not None:
                dp = probe.data[:, ::2] - probe.data[:, 1::2]
                dp2 = probe2.data[:, ::2] - probe2.data[:, 1::2]
                dr = np.diff(ref.data[::16, :], axis=1)
                dp = (dp - self.beta1 @ dr)
                dp2 = (dp2 - self.beta2 @ dr)

                sig = f / LOG10 * np.log1p(dp.mean(1) / probe.mean(1))
                sig_pr2 = f / LOG10 * np.log1p(dp2.mean(1) / probe2.mean(1))

            which = 1 if (ch[0][0] > 1) else 0
            reading = Reading(lines=np.stack(
                (probe.mean, probe2.mean, ref.mean, probe.max)),
                              stds=np.stack(
                                  (probe.std, probe2.std, ref.std, norm_std)),
                              signals=np.stack(
                                  (sig2, sig, sig_pr2_noref, sig_pr2)),
                              valid=True)            #
        return reading

    def make_2D_reading(self, t2: np.ndarray, rot_frame: float,
                        repetitions: int = 1, save_frames: bool = False) -> \
            Dict[str, Reading2D]:
        spectra, ch = self.get_spectra(frames=self.shots // repetitions, get_max=False)
        two_d_data = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for name in ('Probe1', 'Probe2'):
                future = executor.submit(Reading2D.from_spectrum, spectra[name], t2, rot_frame, save_frames)
                two_d_data[name] = future
            for name in ('Probe1', 'Probe2'):
                two_d_data[name] = two_d_data[name].result()
        return two_d_data

    def calibrate_ref(self):
        tmp_shots = self.shots
        self._cam.set_shots(10000)
        arr, ch = self._cam.read_cam()
        self._cam.set_shots(tmp_shots)
        if self.background is not None:
            arr = arr - self.background[:, :, None]
        pr_range = self.probe_rows
        ref_range = self.ref_rows
        probe = np.nanmean(arr[pr_range[0]:pr_range[1], :, :], 0)
        dp1 = np.diff(probe, axis=1)
        ref = np.nanmean(arr[ref_range[0]:ref_range[1], :, :], 0)

        dr = np.diff(ref[::16, :], axis=1)
        self.beta1 = np.linalg.lstsq(dp1.T, dr.T)[0]
        self.deltaK1 = 1000 / LOG10 * np.log1p(
            (dp1 - self.beta1 @ dr).mean(1) / probe.mean(1))

        if TWO_PROBES:
            probe2 = np.nanmean(arr[PROBE2_RANGE[0]:PROBE2_RANGE[1], :, :], 0)
            dp2 = np.diff(probe2, axis=1)
            self.beta2 = np.linalg.lstsq(dp2.T, dr.T)[0]
            self.deltaK2 = 1000 / LOG10 * (
                dp2 - self.beta2 @ dr).mean(1) / probe2.mean(1)

    def set_background(self, shots=0):
        arr = self._cam.read_cam()[0]
        back_probe = np.nanmean(arr[:, :, :], 2)
        self.background = back_probe

        fname = Path(__file__).parent / 'back'
        np.save(fname, back_probe)

    def remove_background(self):
        self.background = None

    def get_wavelength_array(self, center_wl):
        center_wl = self.spectrograph.get_wavelength()
        grating = self.spectrograph._last_grating
        disp = 7.69
        if grating == 1:
            disp *= 30/75

        center_ch = 67
        if center_wl < 1000:
            return np.arange(-64, 64, 1)
        else:
            return (np.arange(128) - center_ch) * disp + center_wl



