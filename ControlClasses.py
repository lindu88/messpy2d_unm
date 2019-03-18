import numpy as np
from attr import attrs, attrib, Factory, make_class
from Config import config
import threading
from HwRegistry import _cam, _dl
import Instruments.interfaces as I
from typing import Callable, List

has_second_cam = config.has_second_cam

@attrs
class ReadData:
    shots: int = attrib()
    det_a = attrib()
    det_b = attrib()
    ext = attrib()
    chopper = attrib()

@attrs
class CallBack:
    cb_func : Callable = attrib()
    call_in_thread : bool = attrib(True)
    join_thread : bool = attrib(True)

@attrs
class Signal:
    callbacks: List[CallBack] = attrib(Factory(list))

    def emit(self, *args):
        thr_to_join = []
        for cb in self.callbacks:
            try:
                if not cb.call_in_thread:
                    cb.cb_func(*args)
                else:
                    t = threading.Thread(target=cb.cb_func, args=args)
                    t.run()
                    if cb.join_thread:
                        thr_to_join.append(t)
            except:
                raise
        for t in thr_to_join:
            if t.is_alive():
                t.join()

    def connect(self, cb, do_threaded=True):
        self.callbacks.append(CallBack(cb, do_threaded))

    def disconnect(self, cb):
        cbs = [cb.cb_func for cb in self.callbacks]
        if cb in cbs:
            idx = cbs.find(cb)            
            self.callbacks.pop(idx)
        else:
            raise ValueError("Can't disconnect %s from signal. Not found."%cb)



@attrs
class Cam:
    cam: I.ICam = attrib(_cam)
    shots: int = attrib(config.shots)
    sigShotsChanged: Signal = attrib(Factory(Signal))
    sigReadCompleted: Signal = attrib(Factory(Signal))
    back: tuple = attrib((0, 0))


    def set_shots(self, shots):
        self.shots = shots
        self.cam.set_shots(int(shots))
        config.shots = shots
        self.sigShotsChanged.emit(shots)

    def read_cam(self):
        #_fc.prime_fc(self.shots)
        a,b, chopper, ext = self.cam.read_cam()
        a = a - self.back[0]
        b = b - self.back[1]
        #print(_fc.get_values())
        rd = ReadData(shots=self.shots,
                      det_a=a,
                      det_b=b,
                      ext=ext.T,
                      chopper=chopper)
        self.sigReadCompleted.emit()
        return rd

    def get_bg(self):
        rd = self.read_cam()
        self.back = rd.det_a.mean(0, keepdims=1), rd.det_b.mean(0, keepdims=1)

    def remove_bg(self):
        self.back = (0, 0)


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
        self._dl.home_pos = self._dl.get_pos_mm()
        config['Delay 1 Home Pos.'] = self._dl.get_pos_mm()



arr_factory = Factory(lambda: np.zeros(16))


@attrs
class LastRead:
    cam: Cam = attrib()
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

        self.probe = dr.det_a

        self.probe_mean = self.probe.mean(0)
        self.probe_std = np.nan_to_num(self.probe.std(0) / abs(self.probe_mean) * 100)

        self.reference = dr.det_b
        self.reference_mean = self.reference.mean(0)
        self.reference_std = np.nan_to_num(self.reference.std(0) / abs(self.reference_mean) * 100)

        self.ext_channel_mean = 2 + np.random.rand(1)*0.05
        sign = 1 if dr.chopper[0] else -1
        self.probe_signal = sign*1000*np.log10(self.probe[::2, ...]/self.probe[1::2, ...]).mean(0)
        self.probe_signal = np.nan_to_num(self.probe_signal)
        #self.probe_signal = self.reference_mean

import time

class Controller:
    """Class which controls the main loop."""

    def __init__(self):
        self.cam = Cam()
        self.cam.read_cam()

        if has_second_cam:
            self.cam2 = Cam(cam=_cam2)
            self.cam2.read_cam()
            self.cam.sigShotsChanged.connect(self.cam2.set_shots, do_threaded=False)
        self.cam2 = None
        self.delay_line = Delayline(dl=_dl)

        if config.has_second_dl:
            self.delay_line_second = Delayline(dl=_dl2)
        self.spectrometer = Spectrometer()
        pb, rb = config.probe_back, config.probe_ref
        if pb is None:
            pb = 0
            rb = 0

        self.last_read = LastRead(cam=self.cam,
                                  probe_back=pb,
                                  ref_back=rb)  #type: LastRead
        if config.has_second_cam:
            self.last_read2 = LastRead(cam=self.cam2,
                                  probe_back=0,
                                  ref_back=0)  #type: LastRead

        self.plan = None
        self.pause_plan = False
        self.running_step = False
        self.thread = None

    def loop(self):
        t = time.time()


        if self.plan is None or self.pause_plan:
           # if not self.thread or not self.thread.is_alive():
           #     self.thread = threading.Thread(target=self.last_read.update)
           # else:
           #     pass
           t1 = threading.Thread(target=self.last_read.update)
           t1.start()
           if has_second_cam:
               t2 = threading.Thread(target=self.last_read2.update)
               t2.start()
               t2.join()
           t1.join()




        else:
            # if self.running_step:
            #     if self.thread.is_alive():
            #         return
            #     else:
            #         self.running_step = False
            # else:
            #     self.thread = threading.Thread(target=self.plan.make_step)
            #     self.thread.start()
            #     self.running_step = True
            self.plan.make_step()


        print(time.time()-t)

    def shutdown(self):
        if config.has_second_delaystage:
            _dl2.shutdown()
        _dl.shutdown()
        _cam.shutdown()
        if config.has_second_cam:
            _cam2.shutdown()








