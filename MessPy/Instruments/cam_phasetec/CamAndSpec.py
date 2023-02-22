import concurrent
import threading
import time
from math import log
from pathlib import Path
from typing import ClassVar, List, Optional, Tuple, Dict

import attr
import numpy as np
from scipy.stats import trim_mean
from qtpy.QtCore import Slot, Signal
from MessPy.Config import config
from MessPy.Instruments.interfaces import ICam
from MessPy.Instruments.signal_processing import Reading, Spectrum, first, fast_col_mean, Reading2D

from MessPy.Instruments.cam_phasetec.imaq_nicelib import Cam
from MessPy.Instruments.cam_phasetec.spec_sp2500i import SP2150i
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
    rows: Dict[str, Tuple[int, int]] = attr.ib()
    name: str = 'Phasetec Array'
    shots: int = 50

    if not TWO_PROBES:
        line_names: List[str] = ['Probe', 'Ref', 'max']
        std_names: List[str] = ['Probe', 'Ref', 'Probe/Ref']
        sig_names: List[str] = ['Sig', 'SigNoRef']
    else:
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
    frame_channel: int = 0
    _cam: Cam = attr.ib(factory=Cam)

    sigRowsChanged: ClassVar[Signal] = Signal()

    @rows.default
    def _rows_default(self):
        return {'Probe': PROBE_RANGE,
                'Ref': REF_RANGE,
                'Probe2': PROBE2_RANGE,
                'back_line': (90, 110)
                }


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
            'rows': self.rows,
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

    def mark_valid_pixel(self,  min_val=300, max_val=12000):
        """"
        Reads the camera and for each row-region, marks pixels which have a value within given range.
        The result is saved in an attribute.
        """
        arr, ch = self._cam.read_cam()

        self.valid_pixel = []
        for (l, u) in self.rows.values():
            sub_arr = arr[l:u, :, :].mean(-1)
            self.valid_pixel += [(min_val < sub_arr) & (sub_arr < max_val)]

    def delete_valid_pixel(self):
        self.valid_pixel = None

    def get_spectra(self, frames=None, **kwargs) -> Tuple[Dict[str, Spectrum], object]:
        import time
        t = time.time()

        arr, ch = self._cam.read_cam(back=self.background, lines=self.rows.values())
        #print(-t + time.time(), self.shots)
        #if self.background is not None:
        #    arr = arr - self.background[:, :, None]
        if frames is not None:
            first_frame = first(np.array(ch[self.frame_channel]), 1)
        else:
            first_frame = None

        pr_range = self.rows['Probe']
        pr2_range = self.rows['Probe2']
        ref_range = self.rows['Ref']
        backline_mean = self.rows['back_line']

        if self.valid_pixel is not None:
            probe = fast_col_mean(arr[pr_range[0]:pr_range[1], ...], self.valid_pixel[0])
            ref = fast_col_mean(arr[ref_range[0]:ref_range[1], ...], self.valid_pixel[1])
            if TWO_PROBES:
                probe2 = fast_col_mean(arr[pr2_range[0]:pr2_range[1], ...], self.valid_pixel[2])
        else:
            probe = self._cam.lines[0]  #- self._cam.lines[-1]
            ref = self._cam.lines[1] #- self._cam.lines[-1]
            #probe = np.nanmean(arr[pr_range[0]:pr_range[1], :, :], 0)
            #ref = np.nanmean(arr[ref_range[0]:ref_range[1], :, :], 0)
            if TWO_PROBES:
                probe2 = self._cam.lines[2] #- self._cam.lines[-1]
                #probe2 = np.nanmean(arr[pr2_range[0]:pr2_range[1], :, :], 0)

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
                f = -1000
            else:
                f = 1000

            pu = trim_mean(normed[:, ::2], 0.2, 1)
            not_pu = trim_mean(normed[:, 1::2], 0.2, 1)

            sig = f * np.log10(pu / not_pu)
            sig_noref = d['Probe1'].signal

        # print(sig.shape, ref_mean.shape, norm_std.shape, probe_mean.shape)
        if not TWO_PROBES:
            reading = Reading(lines=np.stack(
                (probe.mean, ref.mean, probe.max)),
                              stds=np.stack((probe.std, ref.std, norm_std)),
                              signals=np.stack((sig, sig_noref)),
                              valid=True)

        else:
            probe2 = d['Probe2']
            normed2 = probe2.data / ref.data

            if self.beta1 is not None:
                dp = probe.data[:, ::2] - probe.data[:, 1::2]
                dp2 = probe2.data[:, ::2] - probe2.data[:, 1::2]
                dr = ref.data[::8, ::2] - ref.data[::8, 1::2]
                dp = (dp - self.beta1.T @ dr)
                dp2 = (dp2 - self.beta2.T @ dr)

                sig = f / LOG10 * np.log1p(dp.mean(1) / probe.mean)
                sig_pr2 = f / LOG10 * np.log1p(dp2.mean(1) / probe2.mean)
            else:
                pu2 = trim_mean(normed2[:, ::2], 0.2, 1)
                not_pu2 = trim_mean(normed2[:, 1::2], 0.2, 1)
                sig_pr2 = f * np.log10(pu2 / not_pu2)

            pu2 = trim_mean(probe2.data[:, ::2], 0.2, 1)
            not_pu2 = trim_mean(probe2.data[:, 1::2], 0.2, 1)

            sig_pr2_noref = probe2.signal#f * np.log10(pu2 / not_pu2)

            reading = Reading(lines=np.stack(
                (probe.mean, probe2.mean, ref.mean, probe.max)),
                              stds=np.stack(
                                  (probe.std, probe2.std, ref.std, norm_std)),
                              signals=np.stack(
                                  (sig_noref, sig, sig_pr2_noref, sig_pr2)),
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
            two_d_data['Ref'] = spectra['Ref']
        self.two_d_data_ = two_d_data
        return two_d_data

    def calibrate_ref(self):
        tmp_shots = self.shots
        self._cam.set_shots(4000)
        #arr, ch = self._cam.read_cam()
        specs, _ = self.get_spectra()
        self._cam.set_shots(tmp_shots)

        probe = specs['Probe1'].data
        probe2 = specs['Probe2'].data
        ref = specs['Ref'].data

        dp1 = probe[:, ::2] - probe[:, 1::2]
        dp2 = probe2[:, ::2] - probe2[:, 1::2]
        dr = ref[::8, ::2] - ref[::8, 1::2]

        self.beta1 = np.linalg.lstsq(dr.T, dp1.T, rcond=-1)[0]
        self.beta2 = np.linalg.lstsq(dr.T, dp2.T, rcond=-1)[0]
        self.deltaK1 = 1000 / LOG10 * np.log1p(
            (dp1 - self.beta1.T @ dr).mean(1) / probe.mean(1))
        self.deltaK2 = 1000 / LOG10 * (
                dp2 - self.beta2.T @ dr).mean(1) / probe2.mean(1)


    def set_background(self, shots=0):
        if self.background is not None:
            self.background = None
        else:
            arr = self._cam.read_cam(lines=self.rows.values(), back=None)[0]
            #back_probe = np.nanmean(arr[:, :, :], 2)
            self.background = self._cam.lines.mean(2)
            fname = Path(__file__).parent / 'back'
            np.save(fname, self.background)

    def remove_background(self):
        self.background = None

    def get_wavelength_array(self, center_wl):
        center_wl = self.spectrograph.get_wavelength()
        grating = self.spectrograph._last_grating
        disp = 7.8
        if grating == 1:
            disp *= 30/75

        center_ch = 67
        if center_wl < 1000:
            return np.arange(-64, 64, 1)
        else:
            return (np.arange(128) - center_ch) * disp + center_wl
