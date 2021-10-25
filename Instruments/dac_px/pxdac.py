import logging
from typing import Optional

import numpy as np
from nicelib import load_lib, NiceLib, Sig, NiceObject, RetHandler, ret_ignore, ret_return


@RetHandler(num_retvals=0)
def ret_errcode(retval, funcargs, niceobj):

    if retval != 0:
        raise ValueError(PXDAC.GetErrorMessXD48(retval, 1,
                                                niceobj._handles[0]))


class PXDAC(NiceLib):
    _info_ = load_lib('pxdac', __package__)
    _ret_ = ret_errcode


    GetDeviceCountXD48 = Sig()
    GetErrorMessXD48 = Sig('in', 'buf[200]', 'in', 'in', ret=ret_ignore)
    ConnectToDeviceXD48 = Sig('out', 'in')
    GetOutputVoltageRangeVoltsXD48 = Sig('in', 'out', 'in')

    class DAC(NiceObject):
        _init_ = 'ConnectToDeviceXD48'

        DisconnectFromDeviceXD48 = Sig('in')
        InIdleModeXD48 = Sig('in', ret=ret_return)
        InPlaybackModeXD48 = Sig('in', ret=ret_return)

        GetActiveChannelMaskXD48 = Sig('in', 'in', ret=ret_return)
        SetActiveChannelMaskXD48 = Sig('in', 'in')

        GetOutputVoltageCh1XD48 = Sig('in', 'in', ret=ret_return)
        GetOutputVoltageCh2XD48 = Sig('in', 'in', ret=ret_return)
        GetOutputVoltageCh3XD48 = Sig('in', 'in', ret=ret_return)
        GetOutputVoltageCh4XD48 = Sig('in', 'in', ret=ret_return)

        SetOutputVoltageCh1XD48 = Sig('in', 'in')
        SetOutputVoltageCh2XD48 = Sig('in', 'in')
        SetOutputVoltageCh3XD48 = Sig('in', 'in')
        SetOutputVoltageCh4XD48 = Sig('in', 'in')

        SetDacSampleSizeXD48 = Sig('in', 'in')
        GetDacSampleSizeXD48 = Sig('in', 'in', ret=ret_return)

        SetDacSampleFormatXD48 = Sig('in', 'in')
        GetDacSampleFormatXD48 = Sig('in', 'in', ret=ret_return)


        SetExternalTriggerEnableXD48 = Sig('in', 'in')
        GetExternalTriggerEnableXD48 = Sig('in', 'in', ret=ret_return)

        SetTriggerModeXD48 = Sig('in', 'in')
        GetTriggerModeXD48 = Sig('in', 'in', ret=ret_return)

        EndRamPlaybackXD48 = Sig('in')
        BeginRamPlaybackXD48 = Sig('in', 'in', 'in', 'in')
        IsPlaybackInProgressXD48 = Sig('in', ret=ret_return)
        LoadRamBufXD48 = Sig('in', 'in', 'in', 'in', 'in')
        IsTransferInProgressXD48 = Sig('in', ret=ret_return)


        IssueSoftwareTriggerXD48 = Sig('in')

        def get_output_voltage(self):
            vals = (self.GetOutputVoltageCh1XD48(1), self.GetOutputVoltageCh2XD48(1),
                    self.GetOutputVoltageCh3XD48(1), self.GetOutputVoltageCh4XD48(1))
            return list(map(lambda i: PXDAC.GetOutputVoltageRangeVoltsXD48(i, self._handles[0]), vals))

        def set_output_voltage(self, ch1=None, ch2=None, ch3=None, ch4=None):
            def check(x):
                if 0 <= x <= 1023:
                    return x
                else:
                    raise ValueError("Voltage settings have to be between 0 and 1023")
            if ch1 is not None:
                check(ch1)
                self.SetOutputVoltageCh1XD48(ch1)
            if ch2 is not None:
                check(ch2)
                self.SetOutputVoltageCh2XD48(ch2)
            if ch3 is not None:
                self.SetOutputVoltageCh3XD48(check(ch3))
            if ch4 is not None:
                self.SetOutputVoltageCh4XD48(check(ch4))

import sys
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('_')
handler = logging.StreamHandler(sys.stdout)
handler.filter('pxdac')
log.addHandler(handler)

PIXEL = 4096*3 # 12288
MAX_16_Bit = (1 << 13) - 1


def wf(amps, phase,  P, omega0, pixel=np.arange(PIXEL), dac_mHZ=1200, rf_mHZ=75):
    F = np.poly1d(np.polyint(P))
    #F = P.integ()
    phi0 = F(0)
    phase_term = phi0+2*np.pi*F(pixel)/omega0*rf_mHZ/dac_mHZ+phase

    return amps*np.cos(phase_term)

import attr

@attr.s(auto_attribs=True)
class AOM:
    amp_fac: float = 1
    calib: Optional[tuple] = None
    nu: Optional[np.ndarray] = None
    nu0_THz: float = 55
    t: np.ndarray = np.arange(PIXEL) / 1.2e9
    compensation_phase: Optional[np.ndarray] = None
    phase: Optional[np.ndarray] = np.zeros_like(PIXEL)
    amp: np.ndarray = np.ones_like(PIXEL)
    total_phase: Optional[np.ndarray] = np.zeros_like(PIXEL)
    chopped: bool = True
    do_disp_comp: bool = True
    phase_cycle: bool = True
    mode: str = 'bragg'
    dac: PXDAC.DAC = PXDAC.DAC(1)

    def __attr_post_init__(self):
        self.setup_dac()

    def setup_dac(self):
        dac = self.dac
        dac.SetDacSampleSizeXD48(2)
        log.info("Size: %s ", dac.GetDacSampleSizeXD48(1))
        log.info("Format: %s", dac.GetDacSampleFormatXD48(1))

        log.info("Output Voltage %s", dac.get_output_voltage())
        dac.set_output_voltage(ch1=200, ch2=1000)
        log.info("Output Voltage %s", dac.get_output_voltage())
        dac.SetExternalTriggerEnableXD48(1)
        log.info("ExtTigger %s", dac.GetExternalTriggerEnableXD48(1))
        dac.SetTriggerModeXD48(0)
        dac.SetActiveChannelMaskXD48(0x1 | 0x2)
        dac.SetDacSampleSizeXD48(1)


    def set_dispersion_correct(self, GVD, TOD, FOD):
        x = self.nu - self.nu0_THz
        x *= (2 * np.pi)
        facs = np.array([GVD, TOD, FOD]) / np.array([2, 6, 24]) / 1000.
        phase = x**2 * facs[0] + x**3 * facs[1] + x**3 * FOD * facs[2]
        self.do_disp_comp = True
        self.compensation_phase = phase
        self.generate_waveform()


    #@Slot(object)
    def set_calib(self, p):
        self.calib = p
        self.nu = np.polyval(p, np.arange(PIXEL))


    def generate_waveform(self, amp=None, phase=None):
        if amp is None:
            amp = self.amp
        else:
            self.amp = amp

        if phase is None:
            phase = self.phase
        else:
            self.phase = phase

        if self.compensation_phase is not None and self.do_disp_comp:
            phase = phase + self.compensation_phase

        self.total_phase = phase

        if self.mode == 'bragg' and self.calib is not None:
            masks = MAX_16_Bit*self.amp_fac*wf(amp, phase, self.calib, self.nu0_THz)
        else:
            masks = MAX_16_Bit*self.amp_fac*amp*np.cos(np.arange(PIXEL)/16*2*np.pi+phase)

        if self.chopped:
            masks = np.concatenate((masks, masks*0))
        if self.phase_cycle:
            masks = np.concatenate((masks, -masks))

        self.load_mask(masks.astype('int16'))


    def voltage(self, i: int):
        if not (0<=i<1023):
            raise ValueError(i)
        self.dac.set_output_voltage(ch1=i)

    def set_wave_amp(self, amp):
        if not (0 < amp <= 1):
            raise ValueError('Amplitude has to be between 0 and 1')
        V = 1.4*amp
        if V > 0.4:
            k = int((V - 0.4)*1023)
            self.voltage(k)
            self.amp_fac = 1
        else:
            self.voltage(0)
            f = V/0.4
            self.amp_fac = f

    def load_mask(self, mask):
        self.mask = mask
        assert((mask.size % PIXEL) == 0)
        self.end_playback()
        mask1 = np.zeros_like(mask)
        mask1[:PIXEL] = MAX_16_Bit
        full_mask = np.zeros(mask.size * 2, dtype=np.int16)
        full_mask[::2] = mask
        full_mask[1::2] = mask1
        self.dac.LoadRamBufXD48(0, full_mask.size * 2, full_mask.ctypes.data, 0)
        self.dac.BeginRamPlaybackXD48(0, full_mask.size * 2,  PIXEL * 2 * 2)

    def start_playback(self):
        self.dac.BeginRamPlaybackXD48(0, self.mask.size * 2, PIXEL * 2 * 2)

    def end_playback(self):
        self.dac.EndRamPlaybackXD48()

    def make_calib_mask(self, width=150, separation=350, n_single=15):
        full_mask = np.cos(np.arange(PIXEL)/16*2*np.pi)*MAX_16_Bit
        pulse_train_mask = np.zeros_like(full_mask)
        single_mask = np.zeros_like(full_mask)
        total = width + separation
        for k, i in enumerate(range(0, full_mask.size, total)):
            pulse_train_mask[i:i+width] = full_mask[i:i+width]
            if k == n_single:
                single_mask[i:i + width] = pulse_train_mask[i:i + width]

        # Three frames: train, single and full
        mask = np.hstack((pulse_train_mask, single_mask, full_mask))
        mask = (self.amp_fac*mask).astype('int16')
        return mask

    def load_calib_mask(self):
        mask = self.make_calib_mask()
        self.load_mask(mask)

    def load_full_mask(self):
        full_mask = np.cos(np.arange(PIXEL) / 16 * 2 * np.pi) * MAX_16_Bit
        self.load_mask(full_mask.astype('int16'))

if __name__ == '__main__':
    A = AOM()
    A.load_mask(A.make_calib_mask())