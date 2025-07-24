import ctypes
import ctypes as ct
import os
import time

import attr
from numpy import long
import numpy as np

from MessPy.Instruments.interfaces import ICam, T
from MessPy.Instruments.signal_processing import Reading, Spectrum

dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "x64", "MT_Spectrometer_SDK.dll")
sdk = ctypes.WinDLL(dll_path)

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

def make_array(frame_record, frames=1, pixels=3648):
    out = {}
    n = frames * pixels
    for name, _ in frame_record._fields_:
        ptr = getattr(frame_record, name)
        if name in ['RawData', 'CalibData', 'AbsInten'] and ptr:
            arr = ctypes.cast(ptr, ctypes.POINTER(ctypes.c_double * n)).contents
            out[name] = np.frombuffer(arr, dtype=np.float64)
        else:
            out[name] = None
    return out

@attr.s(auto_attribs=True, kw_only=True)
class MightexSpectrometer(ICam):
    name: str = "Mightex Spec"
    shots: int = 1
    line_names: list = attr.Factory(lambda: ["Probe"])
    sig_names: list = attr.Factory(lambda: ["Probe"])
    std_names: list = attr.Factory(lambda: ["Probe"])
    channels: int = 3648
    center_wl: int = 620
    ext_channels: int = 0
    device_ID: int = None
    chopper: np.ndarray = attr.field(init=False, default=None)

    def __attrs_post_init__(self):
        sdk.MTSSE_InitDevice.argTypes = [None]
        sdk.MTSSE_InitDevice.resType = ctypes.c_int
        dev = sdk.MTSSE_InitDevice(None)

        if dev == 0:
            print("No Mightex device found\n")
        else:
            print(f"Mightex device has device number {dev}\n")
            self.device_ID = dev

    def set_background(self, shots):
        pass

    def get_spectra(self, frames: T.Optional[int]) -> T.Tuple[T.Dict[str, Spectrum], T.Any]:
        frames = frames or self.shots

        # Set SDK call types
        sdk.MTSSE_SetDeviceActiveStatus.argtypes = [ctypes.c_int, ctypes.c_int]
        sdk.MTSSE_SetDeviceActiveStatus.restype = ctypes.c_int

        sdk.MTSSE_SetDeviceWorkMode.argtypes = [ctypes.c_int, ctypes.c_int]
        sdk.MTSSE_SetDeviceWorkMode.restype = ctypes.c_int

        sdk.MTSSE_SetDeviceExposureTime.argtypes = [ctypes.c_int, ctypes.c_int]
        sdk.MTSSE_SetDeviceExposureTime.restype = ctypes.c_int

        sdk.MTSSE_SetDeviceAverageFrameNum.argtypes = [ctypes.c_int, ctypes.c_int]
        sdk.MTSSE_SetDeviceAverageFrameNum.restype = ctypes.c_int

        sdk.MTSSE_SetDeviceSpectrometerAutoDarkStatus.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int]
        sdk.MTSSE_SetDeviceSpectrometerAutoDarkStatus.restype = ctypes.c_int

        sdk.MTSSE_StartFrameGrab.argtypes = [ctypes.c_int]
        sdk.MTSSE_StartFrameGrab.restype = ctypes.c_int

        sdk.MTSSE_GetDeviceSpectrometerFrameData.argtypes = [ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                                             ctypes.POINTER(ctypes.POINTER(tFrameRecord))]
        sdk.MTSSE_GetDeviceSpectrometerFrameData.restype = ctypes.c_int

        """__________________________________________________________________________________________________________________________________________"""

        # Setup
        sdk.MTSSE_SetDeviceActiveStatus(self.device_ID, 1)
        sdk.MTSSE_SetDeviceWorkMode(self.device_ID, 0)
        sdk.MTSSE_SetDeviceExposureTime(self.device_ID, 10000) #exposure time
        sdk.MTSSE_SetDeviceAverageFrameNum(self.device_ID, 1)
        sdk.MTSSE_SetDeviceSpectrometerAutoDarkStatus(self.device_ID, 1, 0)

        all_raw_data = []

        for i in range(frames):
            sdk.MTSSE_StartFrameGrab(1)

            frame_record_ptr = ctypes.POINTER(tFrameRecord)()
            success = sdk.MTSSE_GetDeviceSpectrometerFrameData(self.device_ID, 1, 1, ctypes.byref(frame_record_ptr))
            if success != 1:
                raise RuntimeError(f"Failed to get frame data for frame {i + 1}/{frames}")

            frame_record = frame_record_ptr.contents
            if not frame_record.AbsInten:
                raise RuntimeError(f"RawData pointer is NULL for frame {i + 1}")

            raw_data = make_array(frame_record)['RawData']
            if raw_data.ndim != 1:
                raise ValueError(f"Expected 1D data, got {raw_data.shape}")

            all_raw_data.append(raw_data)

        # Stack to (frames, 3648)
        raw_data_stack = np.stack(all_raw_data, axis=0)

        spec = Spectrum.create(raw_data_stack, name="Probe", frames=frames, first_frame=0)

        chop = np.zeros(frames, dtype=bool)
        chop[::2] = True

        return {"Probe": spec}, chop

    def make_reading(self) -> Reading:
        spectra, chopper = self.get_spectra(frames=self.shots)
        data = spectra["Probe"].data  # shape: (shots, 3648)

        if data.shape != (self.shots, 3648):
            raise ValueError(f"Expected ({self.shots}, 3648), got {data.shape}")

        a = data.T  # shape: (3648, shots)
        b = a.copy()  # placeholder; in real use, would be another type of data
        ratio = a / b  # shape: (3648, shots), all ones if a == b

        full_data = np.stack((a, b, ratio), axis=0)  # shape: (3, 3648, shots)

        tm = full_data.mean(axis=2)  # shape: (3, 3648)
        ts = 100 * full_data.std(axis=2) / tm  # shape: (3, 3648), % standard deviation

        with np.errstate(all="ignore"):
            signal = np.mean(a, axis=1)  # shape: (3648,)
            signal2 = np.zeros_like(signal)  # shape: (3648,)
        signals = np.stack((signal, signal2))  # shape: (2, 3648)

        return Reading(
            lines=tm[:2, :],  # shape: (2, 3648)
            stds=ts,  # shape: (3, 3648)
            signals=signals,  # shape: (2, 3648)
            valid=True,
            full_data=full_data,  # shape: (3, 3648, shots)
            shots=self.shots
        )

    #maybe switch over get_spectra() to read_cam()
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

    def get_wavelength_array(self, center_wl=None):
        if center_wl is None:
            center_wl = self.center_wl  #will need to change

        pixels = self.channels
        x = np.arange(pixels) - pixels // 2  # Center at pixel 1824
        return x * 0.2055921052631579 + center_wl  # pixel dispersion -- will need to change

    def set_shots(self, shots):
        self.shots = shots

if __name__ == "__main__":
    test = MightexSpectrometer()
    test.close()
    print(test.make_reading())
    test.close()

"""
data	(1, 3648)	1 frame of spectral data
a, b	(1, 3648)	single-frame data - a copied to b - supposed to be probe on / probe off i think
ratio	(1, 3648)	element-wise ratio of a / b
tmp	(3, 1, 3648)	stack of a, b, ratio
tm, ts	(3, 3648)	mean and std across shots
signal	(3648,)	dummy signal
signal2 (3648,) dummy signal
signals	(2, 3648)	two dummy signal layers
"""

"""
class Reading:
    Each array has the shape (n_type, pixel), except for full_data which has the shape (n_type, pixel, shots)

    lines: np.ndarray
    stds: np.ndarray
    signals: np.ndarray
    full_data: np.ndarray
    shots: int
    valid: bool
"""