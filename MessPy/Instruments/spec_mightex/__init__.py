import ctypes
import ctypes as ct
import os
import time

import attr
from numpy import long
import numpy as np

from MessPy.Instruments.interfaces import ICam, T
from MessPy.Instruments.signal_processing import Reading, Spectrum

dll_path = os.getcwd() + "/x64/MT_Spectrometer_SDK.dll"
sdk = ct.CDLL(dll_path)

class TFrameDataProperty(ctypes.Structure):
    _fields_ = [
        ("DeviceID", ctypes.c_int),
        ("ExposureTime", ctypes.c_int),
        ("TimeStamp", ctypes.c_int),
        ("TriggerOccurred", ctypes.c_int),
        ("TriggerEventCount", ctypes.c_int),
        ("OverSaturated", ctypes.c_int),
        ("LightShieldValue", ctypes.c_int),
    ]

class tFrameRecord(ctypes.Structure):
    _fields_ = [
        ("RawData", ctypes.POINTER(ctypes.c_double)),
        ("CalibData", ctypes.POINTER(ctypes.c_double)),
        ("AbsInten", ctypes.POINTER(ctypes.c_double)),
    ]

def get_dict(frame_record, frames=1, pixels_per_frame=3648):
    result = {}

    for field, _ in frame_record._fields_:
        value = getattr(frame_record, field)

        # Handle NULL pointers
        if value is None or (hasattr(value, "value") and value.value is None):
            result[field] = None
            continue

        # Special handling for your pointer fields
        if field in ['RawData', 'CalibData', 'AbsInten']:
            n = frames * pixels_per_frame
            ArrayType = ctypes.c_double * n
            # cast the pointer to an array of doubles of length n
            arr_ptr = ctypes.cast(value, ctypes.POINTER(ArrayType))
            arr = np.ctypeslib.as_array(arr_ptr.contents)
            result[field] = arr
            continue

        # Fixed size ctypes arrays (unlikely here)
        if hasattr(value, "_length_") and hasattr(value, "_type_"):
            result[field] = np.ctypeslib.as_array(value)

        # Nested structs
        elif hasattr(value, "_fields_"):
            result[field] = get_dict(value, frames=frames, pixels_per_frame=pixels_per_frame)

        # Basic types
        else:
            result[field] = value

    return result

@attr.s(auto_attribs=True)
class MightexSpectrometer(ICam):
    name : str = "Mightex Spec"
    shots: int = 20
    line_names: list = ["Probe"]
    sig_names: list = ["Probe"]
    std_names: list = ["Probe"]
    channels: int = 200
    ext_channels: int = 0
    device_ID : int = None
    chopper: np.ndarray = attr.field(init=False)

    def __attrs_post_init__(self):
        sdk.MTSSE_InitDevice.argTypes = [None]
        sdk.MTSSE_InitDevice.resType = ctypes.c_int
        dev = sdk.MTSSE_InitDevice(None)
        if dev == 0:
            print("No mightex device found\n")
        else:
            print(f"Mightex device has device number {dev}\n")
            self.device_ID = dev

    def set_background(self, shots):
        pass

    def set_shots(self, shots):
        pass

    def get_spectra(self, frames: T.Optional[int]) -> T.Tuple[T.Dict[str, Spectrum], T.Any]:

        frame_record = tFrameRecord()

        #set types
        sdk.MTSSE_GetDeviceSpectrometerFrameData.argTypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.POINTER(tFrameRecord)]
        sdk.MTSSE_GetDeviceSpectrometerFrameData.resType = ctypes.c_int

        sdk.MTSSE_StartFrameGrab.argTypes = [ctypes.c_int]
        sdk.MTSSE_StartFrameGrab.resType = ctypes.c_int

        #grab frames
        #maybe make multiple frame grabs
        sdk.MTSSE_StartFrameGrab(1)

        while sdk.MTSSE_GetDeviceSpectrometerFrameData(self.device_ID, 1, 0, ctypes.byref(frame_record)) == -1:
                #may need to change
                time.sleep(0.010)

        if not frame_record.AbsInten:
            raise RuntimeError("AbsInten pointer is NULL after SDK call")

        data_dict = get_dict(frame_record)
        #TODO: change for better implementation
        spec = Spectrum.create(
            data_dict.get('AbsInten'), name="Probe", frames=frames, first_frame=0
        )
        #TODO: Add physical chopper support
        chop = np.zeros(self.shots, "bool")
        chop[::2] = True

        return {"Probe": spec}, chop

    def make_reading(self) -> Reading:
        reading = self.get_spectra(None)
        data_dict = get_dict(reading)
        return Reading(
            lines=np.mean(data_dict.get('AbsInten')),
            stds=np.zeros_like(data_dict.get('AbsInten')),
            signals=data_dict.get('AbsInten'),
            valid=True,
            full_data=data_dict.get('RawData'),
            shots=self.shots,
        )

    def read_cam(self):
        pass

    def close(self):
        sdk.MTSSE_UnInitDevice.resType = ctypes.c_int
        sdk.MTSSE_UnInitDevice()
        print("closed device\n")

    def set_avg_cnt(self, cnt : int):
        # set avg spec count
        sdk.MTSSE_SetDeviceAverageFrameNum.argTypes = [ctypes.c_int, ctypes.c_int]
        sdk.MTSSE_SetDeviceAverageFrameNum.resType = ctypes.c_int
        sdk.MTSSE_SetDeviceAverageFrameNum(cnt)


if __name__ == "__main__":
    test = MightexSpectrometer()
    print(test.make_reading())