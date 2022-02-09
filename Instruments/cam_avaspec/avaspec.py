import time
from typing import Optional

import attr
import numpy as np
from nicelib import (NiceObject, load_lib, NiceLib,
                     Sig, RetHandler, ret_ignore, ret_return)


@RetHandler(num_retvals=0)
def ret_errcode(retval, funcargs, niceobj):
    if retval != 0:
        raise ValueError(retval)


class Avaspec(NiceLib):
    _info_ = load_lib('avaspec', __package__)
    _ret_ = ret_ignore
    _prefix_ = 'AVS_'
    _use_numpy_ = True
    Init = Sig('in', ret=ret_return)
    UpdateUSBDevices = Sig(ret=ret_return)
    GetList = Sig('in', 'out', 'in')
    Activate = Sig('in', ret=ret_return)
    Done = Sig()

    class Device(NiceObject):
        _init_ = 'Activate'
        PrepareMeasure = Sig('in', 'in')
        GetNumPixels = Sig('in', 'out')
        GetLambda = Sig('in', 'arr[2048]')
        PollScan = Sig('in', ret=ret_return)
        GetScopeData = Sig('in', 'out', 'arr[2048]', ret=ret_errcode)
        UseHighResAdc = Sig('in', 'in')
        # Measure = Sig('in', 'in', 'in')
        # MeasureCallback = Sig('in', '
        # in', 'in')


@attr.define
class MeasurmentSettings:
    start_pixel: int = 0
    stop_pixel: int = 2048
    int_time: float = 0.7  # in ms
    int_delay: int = 0
    n_avg: int = 1
    dark_correct: bool = True
    smooth_pixel: int = 0
    saturation_detection: bool = False
    store_to_ram: int = 20

    """
    typedef struct {
    uint16              m_StartPixel;		   // 2
    uint16              m_StopPixel;           // 2
    float               m_IntegrationTime;     // 4
    uint32              m_IntegrationDelay;    // 4
    uint32              m_NrAverages;		   // 4
    DarkCorrectionType  m_CorDynDark;          // 2
    SmoothingType       m_Smoothing;		   // 3
    uint8               m_SaturationDetection; // 1 
    TriggerType         m_Trigger;			   // 3
    ControlSettingsType m_Control;			   // 16
    } MeasConfigType;"""

    def make_struct(self, ffi):
        print(self.start_pixel)
        mc = Avaspec._ffi.new("MeasConfigType*")
        mc.m_StartPixel = self.start_pixel
        mc.m_StopPixel = self.stop_pixel
        mc.m_IntegrationTime = self.int_time
        mc.m_IntegrationDelay = self.int_delay
        mc.m_NrAverages = self.n_avg
        mc.m_CorDynDark = (self.dark_correct, self.dark_correct * 100)
        mc.m_Smoothing = (self.smooth_pixel, 0)
        mc.m_SaturationDetection = self.saturation_detection
        mc.m_Trigger = (0, 0, 0)
        mc.m_Control = (0, 0, 0, 0, self.store_to_ram)
        return mc


@attr.define
class AvantesSpec:
    sn: str
    device: Avaspec.Device
    measurement_settings: MeasurmentSettings = attr.field(factory=MeasurmentSettings)
    wl: np.ndarray = attr.field()
    data: np.ndarray = attr.field(init=False)
    shots: int = 300
    count: int = 0
    _cb: object = None
    @classmethod
    def take_nth(cls, i=0):
        Avaspec.Init(0)
        num_dev = Avaspec.UpdateUSBDevices()

        if num_dev == 0:
            raise IOError("No Avantes spectrometer found")
        elif i + 1 > num_dev:
            raise ValueError(f"Only {num_dev} spectrometers found. {i}-th was requested")
        ffi = Avaspec._ffi
        info = Avaspec._ffi.new("AvsIdentityType[%d]" % num_dev)
        Avaspec.GetList(ffi.sizeof(info), info)
        sn = ffi.string(info[i].SerialNumber)
        dev = Avaspec.Device(info[i])
        dev.UseHighResAdc(True)
        return cls(sn=sn, device=dev)

    @wl.default
    def wl_default(self):
        return self.device.GetLambda()

    def start_reading(self, shots: int, callback):
        ffi = Avaspec._ffi
        self.shots = shots
        self.measurement_settings.store_to_ram = shots
        self.device.PrepareMeasure(self.measurement_settings.make_struct(ffi))
        hdl = self.device._handles[0]
        if callback is None:
            callback = ffi.NULL
        Avaspec.AVS_MeasureCallback(hdl, callback, -2)
        self.data = np.empty((2048, shots))
        self.count = 0


    def callback_factory(self, fin_cb):
        @Avaspec._ffi.callback("void(long*, int*)")
        def callback(handle, intp):
            self.data[:, self.count] = self.device.GetScopeData()[1]
            self.count += 1
            if self.count == self.shots and fin_cb:
                fin_cb()
        self._cb = callback
        return callback

if __name__ == '__main__':
    spec = AvantesSpec.take_nth(0)
    print(spec.measurement_settings)
    spec.start_reading(200, spec.callback_factory())
    time.sleep(1)
