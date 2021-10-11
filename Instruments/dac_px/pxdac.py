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


        @Sig('in', 'in', 'inout')
        def GETBOARDVAL(self, pcc_val):
            data = ffi.new('DWORD*')
            self._autofunc_GETBOARDVAL(pcc_val, ffi.cast('void*', data))
            return data[0]

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

if __name__ == '__main__':
    px = PXDAC
    dac = PXDAC.DAC(1)
    dac.SetDacSampleSizeXD48(2)
    print("Size:",dac.GetDacSampleSizeXD48(1))
    print("Format:", dac.GetDacSampleFormatXD48(1))

    print(dac.get_output_voltage())
    dac.set_output_voltage(ch1=1023, ch2=100)
    print(dac.get_output_voltage())
    dac.SetExternalTriggerEnableXD48(1)
    print("ExtTigger", dac.GetExternalTriggerEnableXD48(1))
    dac.SetTriggerModeXD48(0)
    dac.SetActiveChannelMaskXD48(0x1|0x2)
    b14max = (1<<15)-1
    print(b14max)
    import numpy as np
    mask1 = np.ones(4096*3, dtype=np.int16)
    #mask2 = np.sin(np.arange(4096*3)/16*2*np.pi)*b14max
    mask2 = np.ones(4096*3, dtype=np.int16)   
    mask2 = np.tile(mask2, 1000).reshape(mask2.size, 1000)
    #mask2.ravel("f")
    amps = np.linspace(-b14max, b14max, 1000)
    #amps[::2] = 0
    mask1 = np.tile(mask1, amps.size).reshape(mask1.size, amps.size)    
    mask1 *= amps.astype('int')
    mask1 = mask1.flatten('f')
    mask = np.empty(mask1.size*2, dtype=np.int16)

    
    import matplotlib.pyplot as plt
    #plt.plot(mask1)
    #plt.show()
    
    mask[::2] = mask1
    mask[1::2] = mask1


    #out = np.zeros(masks*12
    #buf = PXDAC._ffi.from_buffer(dual_buf)
    lib = PXDAC._info._ffilib
    #lib.LoadRamBufXD48
    dac.LoadRamBufXD48(0, mask.size*2, mask.ctypes.data, 0)
    dac.BeginRamPlaybackXD48(0,  mask.size*2, 4096*3*2*2)
    #dac.IssueSoftwareTriggerXD48()
    