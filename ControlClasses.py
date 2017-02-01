import numpy as np
from attr import attrs, attrib, Factory, make_class


@attrs
class ReadData:
    shots = attrib()
    det_a = attrib()
    det_b = attrib()
    ext = attrib()
    chopper = attrib()


@attrs
class Signal:
    callbacks = attrib(Factory(list))

    def emit(self, *args):
        for cb in self.callbacks:
            try:
                cb(*args)
            except:
                raise

    def connect(self, cb):
        self.callbacks.append(cb)

    def disconnect(self, cb):
        if cb in self.callbacks:
            self.callbacks.remove(cb)
        else:
            raise ValueError("Can't disconnect %s from signal. Not found."%cb)


@attrs
class Cam:
    shots = attrib(100)
    sigShotsChanged = attrib(Factory(Signal))
    num_ch = attrib(16)

    def set_shots(self, shots):
        self.shots = shots
        self.sigShotsChanged.emit(shots)

    def read_cam(self):
        rand = np.random.randn(self.shots, 16, 3)*0.1
        spec = np.exp(-np.arange(-8, 8)**2/10)+1
        rd = ReadData(shots=self.shots,
                      det_a=spec+rand[:, :, 0],
                      det_b=0.9*spec**2+rand[:, :, 1],
                      ext=rand[3],
                      chopper=(rand[3][9] > 3))
        return rd


@attrs
class Spectrometer:
    wl = attrib(0)
    sigWavelengthChanged = attrib(Factory(Signal))


    def set_wavelength(self, wl):
        self.wl = wl
        self.sigWavelengthChanged.emit(self.wl)

    def get_wavelength(self):
        return self.wl


@attrs
class Delayline():
    sigPosChanged = attrib(Factory(Signal))

    pos = attrib(0)

    def set_pos(self, pos_fs):
        "Set pos in femtoseconds"
        self.pos = pos_fs
        self.sigPosChanged.emit(pos_fs)

    def get_pos(self):
        return self.pos

    def set_speed(self, ps_per_sec):
        pass



arr_factory = Factory(lambda: np.zeros(16))


@attrs
class LastRead:
    cam = attrib()
    probe_mean = attrib(arr_factory)
    probe = attrib(arr_factory)
    probe_ref = attrib(arr_factory)
    reference_mean = attrib(arr_factory)
    probe = attrib(arr_factory)
    reference = attrib(arr_factory)
    ext_channel_mean = attrib(arr_factory)
    probe_signal = attrib(arr_factory)
    fringe_count = attrib(None)  # type np.array


    def update(self):
        dr = self.cam.read_cam()
        x = np.linspace(-7, 7, 16)
        self.probe_mean = dr.det_a.mean(0)
        self.probe_std = np.nan_to_num(dr.det_a.std(0) / abs(self.probe_mean) * 100)
        self.reference_mean = dr.det_b.mean(0)
        self.reference_std = np.nan_to_num(dr.det_b.std(0) / abs(self.reference_mean) * 100)
        self.ext_channel_mean[1] = 2 + np.random.rand(1)*0.05
        self.probe_signal = np.log10(self.probe_mean/self.reference_mean)


class Controller:
    """Class which controls the main loop."""

    def __init__(self):
        self.cam = Cam()
        self.cam.read_cam()
        self.delay_line = Delayline()
        self.delay_line_second = Delayline()
        self.spectrometer = Spectrometer()
        self.last_read = LastRead(cam=self.cam)  #type: LastRead
        self.plan = None
        self.pause_plan = False

    def loop(self):
        if self.plan is None and self.pause_plan:
            self.last_read.update()
        else:
            self.plan.make_step()













