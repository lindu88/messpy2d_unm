import numpy as np
from attr import attrs, attrib, Factory, make_class
from Config import config
import threading
from Config import _cam, _dl, _dl2


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
        a,b, chopper, ext = _cam.read_cam()

        #print(_fc.get_values())
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
    pos = attrib(0)
    _dl = attrib(object)

    def __attrs_post_init__(self):
        self.pos = self._dl.get_pos_fs()
        self.sigPosChanged.emit(self.pos)

    def set_pos(self, pos_fs, do_wait=True):
        "Set pos in femtoseconds"
        try:
            pos_fs = float(pos_fs)
        except:
            raise
        self._dl.move_fs(pos_fs, do_wait=do_wait)
        self.pos = self._dl.get_pos_fs()
        self.sigPosChanged.emit(self.pos)

    def get_pos(self):
        return self._dl.get_pos_fs()

    def set_speed(self, ps_per_sec):
        self._dl.set_speed(ps_per_sec)

    def set_home(self):
        self._dl.homepos = self._dl.get_pos_mm()
        config['Delay 1 Home Pos.'] = self._dl.get_pos_mm()



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
    chopper = attrib(None)

    def update(self):
        dr = self.cam.read_cam()
        x = np.linspace(-7, 7, 16)

        self.probe = dr.det_a - self.probe_back
        self.probe_mean = self.probe.mean(0)
        self.probe_std = np.nan_to_num(self.probe.std(0) / abs(self.probe_mean) * 100)

        self.reference = dr.det_b - self.ref_back
        self.reference_mean = self.reference.mean(0)
        self.reference_std = np.nan_to_num(self.reference.std(0) / abs(self.reference_mean) * 100)

        self.ext_channel_mean = 2 + np.random.rand(1)*0.05

        self.probe_signal = -1000*np.log10(self.probe[::2, :]/self.probe[1::2, :]).mean(0)
        if dr.chopper[0]:
            self.probe_signal *= -1

import time

class Controller:
    """Class which controls the main loop."""

    def __init__(self):
        self.cam = Cam()
        self.cam.read_cam()
        self.delay_line = Delayline(dl=_dl2)
        self.delay_line_second = Delayline(dl=_dl)
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












