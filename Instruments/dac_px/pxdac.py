from nicelib import load_lib, NiceLib, Sig, NiceObject, RetHandler, ret_ignore, ret_return
import logging

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
logging.basicConfig(level=logging.INFO)
log = logging.getLogger('pxdac')
handler = logging.StreamHandler(sys.stdout)
handler.filter('pxdac')
log.addHandler(handler)

class AOM:
    def __init__(self):
        dac = PXDAC.DAC(1)
        dac.SetDacSampleSizeXD48(2)
        log.info("Size: %s ", dac.GetDacSampleSizeXD48(1))
        log.info("Format: %s", dac.GetDacSampleFormatXD48(1))
        log.info("Output Voltage %s", dac.get_output_voltage())
        dac.set_output_voltage(ch1=1000, ch2=1000)
        log.info("Output Voltage %s", dac.get_output_voltage())
        dac.SetExternalTriggerEnableXD48(1)
        log.info("ExtTigger %s", dac.GetExternalTriggerEnableXD48(1))
        dac.SetTriggerModeXD48(0)
        dac.SetActiveChannelMaskXD48(0x1 | 0x2)
        self.dac = dac

    def amplitude(self, i: int):
        if (0<i<1023):
            raise ValueError('i')
        self.dac.set_output_voltage(ch1=i)

    def load_mask(self, mask):
        self.mask = mask
        assert(mask.size % (4096*3) == 0)
        self.end_playback()
        self.dac.LoadRamBufXD48(0, mask.size * 2, mask.ctypes.data, 0)
        self.dac.BeginRamPlaybackXD48(0, mask.size * 2, 4096 * 3 * 2 * 2)

    def start_playback(self):
        self.dac.BeginRamPlaybackXD48(0, self.mask.size * 2, 4096 * 3 * 2 * 2)

    def end_playback(self):
        self.dac.EndRamPlaybackXD48()

    def make_calib_mask(self):
        import numpy as np
        #mask1 = np.ones(4096 * 3, dtype=np.int16)
        b14max = (1 << 15) - 1
        fc = (1/16)

        fn = ()
        mask2 = np.cos(np.arange(4096*3)/16*2*np.pi)*b14max
        mask21 = mask2.copy()
        for i in range(0, mask2.size, 500):
            mask21[i+150:i+500] = 0
        i = 6000
        mask22 = np.zeros_like(mask21)
        mask22[i:i+150] = mask2[i:i+150]
        mask2 = np.hstack((mask21, mask22))
        mask1 = np.ones((4096*3), dtype=np.int16)*b14max
        mask1 = np.hstack((mask1, 0*mask1))

        #mask2 = np.ones(4096 * 3, dtype=np.int16)
        #mask2 = np.tile(mask2, 1000).reshape(mask2.size, 1000)
        # mask2.ravel("f")
        #amps = np.linspace(-b14max, b14max, 1000)
        # amps[::2] = 0
        #mask1 = np.tile(mask1, amps.size).reshape(mask1.size, amps.size)
        mask2 = mask2.astype('int')
        #mask1 = mask1.flatten('f')
        mask = np.zeros(mask2.size * 2, dtype=np.int16)
        mask[1::2] = mask1
        mask[::2] = mask2
        return mask

if __name__ == '__main__':
    A = AOM()
    A.load_mask(A.make_calib_mask())
