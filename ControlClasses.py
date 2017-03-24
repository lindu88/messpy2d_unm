import numpy as np
from attr import attrs, attrib, Factory, make_class
from Config import config
import threading
from Config import _cam, _dl, _fc


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
    do_threaded = attrib(Factory(list))

    def emit(self, *args):
        for cb, thr in zip(self.callbacks, self.do_threaded):
            try:
                if not thr:
                    cb(*args)
                else:
                    t = threading.Thread(target=cb, args=args)
                    t.run()
            except:
                raise

    def connect(self, cb, thread=True):
        self.callbacks.append(cb)
        self.do_threaded.append(thread)

    def disconnect(self, cb):
        if cb in self.callbacks:
            idx = self.callbacks.find(cb)
            self.callbacks.remove(cb)
            self.do_threaded.pop(idx)
        else:
            raise ValueError("Can't disconnect %s from signal. Not found."%cb)



@attrs
class Cam:
    shots = attrib(200)
    sigShotsChanged = attrib(Factory(Signal))
    num_ch = attrib(16)

    def set_shots(self, shots):
        self.shots = shots

        _cam.set_shots(shots)
        self.sigShotsChanged.emit(shots)

    def read_cam(self):
        #_fc.prime_fc(self.shots)
        _cam.fc = _fc
        a,b, chopper, ext = _cam.read_cam()

        print(_fc.get_values())
        rd = ReadData(shots=self.shots,
                      det_a=a.T,
                      det_b=b.T,
                      ext=ext.T,
                      chopper=chopper)
        return rd

    def get_bg(self):
        pass


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

    pos = attrib(_dl.get_pos_fs())

    def set_pos(self, pos_fs):
        "Set pos in femtoseconds"
        try:
            pos_fs = float(pos_fs)
        except:
            raise
        _dl.move_fs(pos_fs)
        pos_fs = _dl.get_pos_fs()
        self.sigPosChanged.emit(pos_fs)

    def get_pos(self):
        return _dl.get_pos_fs()

    def set_speed(self, ps_per_sec):
        pass



arr_factory = Factory(lambda: np.zeros(16))


@attrs
class LastRead:
    cam = attrib()
    probe = attrib(arr_factory)
    probe_mean = attrib(arr_factory)
    probe_std = attrib(arr_factory)
    reference = attrib(arr_factory)
    reference_mean = attrib(arr_factory)
    reference_std = attrib(arr_factory)
    ext_channel = attrib(arr_factory)
    ext_channel_mean = attrib(arr_factory)
    ext_channel_ref = attrib(arr_factory)
    probe_signal = attrib(arr_factory)
    fringe_count = attrib(None)  # type np.array
    probe_back = attrib(0) # type np.array
    ref_back = attrib(0) # type np.array

    def update(self):
        dr = self.cam.read_cam()
        x = np.linspace(-7, 7, 16)

        self.probe = dr.det_a - self.probe_back
        self.probe_mean = self.probe.mean(0)
        self.probe_std = np.nan_to_num(self.probe.std(0) / abs(self.probe_mean) * 100)

        self.reference = dr.det_b - self.ref_back
        self.reference_mean = self.reference.mean(0)
        self.reference_std = np.nan_to_num(self.reference.std(0) / abs(self.reference_mean) * 100)

        self.ext_channel_mean[1] = 2 + np.random.rand(1)*0.05
        self.probe_signal = np.log10(self.probe_mean/self.reference_mean)

import time

class Controller:
    """Class which controls the main loop."""

    def __init__(self):
        self.cam = Cam()
        self.cam.read_cam()
        self.delay_line = Delayline()
        self.delay_line_second = Delayline()
        self.spectrometer = Spectrometer()
        pb, rb = config.probe_back, config.probe_ref
        if pb is None:
            pb = 0
            rb = 0

        self.last_read = LastRead(cam=self.cam,
                                  probe_back=pb,
                                  ref_back=rb)  #type: LastRead
        self.plan = None
        self.pause_plan = False


    def loop(self):
        t = time.time()
        if self.plan is None or self.pause_plan:
            self.last_read.update()
        else:
            self.plan.make_step()
        print(time.time()-t)












