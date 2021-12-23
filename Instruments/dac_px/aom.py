from typing import Optional, Literal
from logging import getLogger
from pathlib import Path

import attr
import numpy as np


from .shaper_calculations import double_pulse_mask
from typing import TYPE_CHECKING, Tuple
if TYPE_CHECKING:
    from .pxdac import PXDAC
import matplotlib.pyplot as plt

PIXEL = 4096 * 3  # 12288
MAX_16_Bit = (1 << 13) - 1

log = getLogger(__file__)

def default_dac():
    from .pxdac import PXDAC
    return PXDAC.DAC(1)

from Instruments.interfaces import IDevice
from qtpy.QtCore import Signal

@attr.s(auto_attribs=True)
class AOM(IDevice):
    dac: 'PXDAC.DAC' = attr.Factory(default_dac)
    name: str = "Phasetech AOM"

    amp_fac: float = 1.0
    wave_amp: float = 0.4
    calib: Optional[np.ndarray] = None
    nu: Optional[np.ndarray] = None
    nu0_THz: float = 55
    dac_freq_MHz: float = 1200
    rf_freq_MHz: float = 75
    pixel: np.ndarray = np.arange(PIXEL)

    compensation_phase: Optional[np.ndarray] = None
    phase: Optional[np.ndarray] = np.zeros((PIXEL, 1))
    amp: np.ndarray = np.ones((PIXEL, 1))
    total_phase: Optional[np.ndarray] = np.zeros(PIXEL)
    mask: np.ndarray = np.zeros_like(PIXEL)
    
    chopped: bool = True
    do_dispersion_compensation: bool = True
    phase_cycle: bool = True
    mode: Literal['bragg', 'classic'] = 'bragg'
    
    gvd: float = 0
    tod: float = 0
    fod: float = 0

    sigCalibChanged = Signal(object)
    sigDispersionChanged = Signal(tuple)
    sigModeChanged = Signal(str)

    def __attrs_post_init__(self):
        super(AOM, self).__attrs_post_init__()
        self.setup_dac()

    def get_state(self) -> dict:
        d = {
            'calib': self.calib.tolist() if self.calib is not None else None,
            'gvd': self.gvd,
            'fod': self.fod,
            'tod': self.tod,
            'wave_amp': self.wave_amp,
            'chopped': self.chopped,
            'do_dispersion_compensation': self.do_dispersion_compensation,
            'phase_cycle': self.phase_cycle,
            'mode': self.mode,
            'nu0_THz': self.nu0_THz,
        }
        return d

    def load_state(self):
        super(AOM, self).load_state()

        if self.calib:
            self.set_calib(self.calib)
            self.update_dispersion_compensation()
        self.set_wave_amp(self.wave_amp)

    def setup_dac(self):
        dac = self.dac
        dac.SetDacSampleSizeXD48(2)
        log.info("Size: %s ", dac.GetDacSampleSizeXD48(1))
        log.info("Format: %s", dac.GetDacSampleFormatXD48(1))

        log.info("Output Voltage %s", dac.get_output_voltage())
        dac.set_output_voltage(ch1=200, ch2=1000)
        log.info("Output Voltage %s", dac.get_output_voltage())
        dac.SetExternalTriggerEnableXD48(1)
        log.info("ExtTrigger %s", dac.GetExternalTriggerEnableXD48(1))
        dac.SetTriggerModeXD48(0)
        dac.SetActiveChannelMaskXD48(0x1 | 0x2)
        dac.SetDacSampleSizeXD48(1)

    def update_dispersion_compensation(self):
        """
        Updates the dispersion correction phase from the class attributes.
        """
        x = self.nu - self.nu0_THz
        x *= (2 * np.pi) / 1000 # PHz -> disp params in fs^-n (n=2,3,4)
        coef = np.array([self.gvd, self.tod, self.fod]) / np.array([2, 6, 24])
        print(self.gvd, self.tod, self.fod, self.nu0_THz)
        phase = x ** 2 * coef[0] + x ** 3 * coef[1] + x ** 4 * coef[2]
        self.do_dispersion_compensation = True
        self.compensation_phase = -phase[:, None]
        log.info('Updating dispersion compensation %1.f %.2f %.2e %.2e', self.nu0_THz, self.gvd, self.tod, self.fod)
        self.sigDispersionChanged.emit((self.gvd, self.tod, self.fod))
        self.generate_waveform()

    def set_calib(self, p):
        """
        Sets a new calibration polynomial p.
        """
        self.calib = np.array(p)
        np.save(Path(__file__).parent/'calib_coef.npy', self.calib)
        self.nu = np.polyval(p, self.pixel)
        self.sigCalibChanged.emit(self.calib)
        self.save_state()

    def bragg_wf(self, amp, phase):
        """Calculates a Bragg-correct AOM waveform for given phase and shape"""
        F = np.poly1d(np.polyint(self.calib))
        phase_term = 2 * np.pi * F(self.pixel) / self.nu0_THz * self.rf_freq_MHz / self.dac_freq_MHz
        phase_term = phase + phase_term[:, None]
        return amp * np.cos(phase_term)

    def classic_wf(self, amp, phase):
        """Calculates a uncorrected AOM waveform for given amplitude and shape"""
        f = self.dac_freq_MHz/self.rf_freq_MHz
        return amp * np.cos(self.pixel[:, None] / f * 2 * np.pi + phase)

    def double_pulse(self, taus, rot_frame: float, phase_frames: Literal[1, 2, 4] = 4) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calculates the masks for creating a series a double pulses with phase cycling.
        """
        if self.nu is None:
            raise ValueError("Spectral calibration is required to calculate the masks.")
        phase = np.pi * np.array([(1, 1),
                                  (1, 0),
                                  (0, 1),
                                  (0, 0)])
        phase = phase[:phase_frames, :]
        phase = np.tile(phase, (taus.shape[0], 1))
        phi1 = phase[:, 0]
        phi2 = phase[:, 1]
        taus = taus.repeat(phase_frames)
        masks = double_pulse_mask(self.nu[:, None], rot_frame,
                                  taus[None, :], phi1[None, :], phi2[None, :])
        return np.abs(masks), np.angle(masks)

    def set_amp_and_phase(self, amp=None, phase=None):
        """
        Sets the amplitude and/or the phase of the spectral map.
        Notice that the compensation dispersion phase will be added separately.
        """
        if phase is not None:
            self.phase = phase
        if amp is not None:
            self.amp = amp

    def generate_waveform(self):
        """"
        Actually generates the waveform from set phase and amp. If turned on,
        it will also add the dispersion compensation phase in addition.
        Depending on the `mode` attribute, it will either use a bragg corrected
        waveform or the classic waveform.
        """
        if self.compensation_phase is not None and self.do_dispersion_compensation:
            phase = self.phase - self.compensation_phase
        else:
            phase = self.phase

        self.total_phase = phase

        if self.mode == 'bragg' and self.calib is not None:
            masks = self.bragg_wf(self.amp, self.total_phase)
        else:
            masks = self.classic_wf(self.amp, self.total_phase)

        if self.chopped:
            masks = np.concatenate((0*masks, masks), axis=1)
        if self.phase_cycle:
            masks = np.concatenate((masks, -masks), axis=1)
        self.load_mask(masks)

    def voltage(self, i: int):
        if not (0 <= i < 1023):
            raise ValueError(i)
        self.dac.set_output_voltage(ch1=i)

    def set_wave_amp(self, amp):
        """
        Sets the amplitude of RF-wave. This is archived in two ways. If possible, just the output voltage of the DAC
        is varied. Since this has a lower limit, a set-point below 0.56 is achieved by scaling the array containing
        the waveform, hence it requires a recalculation of the waveform which normally uses the full scale of the DAC.
        """
        if not (0 <= amp <= 1):
            raise ValueError('Amplitude has to be between 0 and 1')
        self.wave_amp = amp
        V = 1.4 * amp
        if V > 0.4:
            k = int((V - 0.4) * 1023)
            self.voltage(k)
            self.amp_fac = 1
        else:
            self.voltage(0)
            f = V / 0.4
            self.amp_fac = f
            self.load_mask()

    def load_mask(self, mask=None):
        if mask is not None:
            self.mask = mask

        if len(self.mask.shape) == 2:
            assert(self.mask.shape[0] == PIXEL)
            self.mask = self.mask.ravel(order='f')

        mask = (self.amp_fac * MAX_16_Bit * self.mask).astype('int16')

        assert (mask.dtype == np.int16)
        assert ((mask.size % PIXEL) == 0)
        print(mask.size // PIXEL)
        self.end_playback()
        mask1 = np.zeros_like(mask)
        mask1[:PIXEL] = MAX_16_Bit
        full_mask = np.zeros(mask.size * 2, dtype=np.int16)
        full_mask[::2] = mask
        full_mask[1::2] = mask1
        self.dac.LoadRamBufXD48(0, full_mask.size * 2, full_mask.ctypes.data, 0)
        self.dac.BeginRamPlaybackXD48(0, full_mask.size * 2, PIXEL * 2 * 2)

    def start_playback(self):
        """Start playback of the current mask"""
        self.dac.BeginRamPlaybackXD48(0, self.mask.size * 2, PIXEL * 2 * 2)

    def end_playback(self):
        """End playback of the current mask"""
        self.dac.EndRamPlaybackXD48()

    def make_calib_mask(self, width=150, separation=350, n_single=15):
        """
        Calculates a calibration mask onto the shaper.
        """
        full_mask = np.cos(np.arange(PIXEL) / 16 * 2 * np.pi)
        pulse_train_mask = np.zeros_like(full_mask)
        single_mask = np.zeros_like(full_mask)
        total = width + separation
        for k, i in enumerate(range(0, full_mask.size, total)):
            pulse_train_mask[i:i + width] = full_mask[i:i + width]
            if k == n_single:
                single_mask[i:i + width] = pulse_train_mask[i:i + width]

        # Three frames: train, single and full
        mask = np.stack((pulse_train_mask, single_mask, full_mask), axis=1)
        return mask

    def load_calib_mask(self, width=150, seperation=350, n_single=15):
        """
        Sets a calibration mask onto the shaper.
        """
        mask = self.make_calib_mask(width, seperation, n_single)
        self.load_mask(mask)

    def load_full_mask(self):
        """Loads a full mask using a frequency of 75 MHz"""
        full_mask = np.cos(np.arange(PIXEL) / 16 * 2 * np.pi)
        self.load_mask(full_mask)


if __name__ == '__main__':
    A = AOM()
    A.load_mask(A.make_calib_mask())
