import pathlib
from threading import Lock

import nidaqmx
import nidaqmx.constants as c
import numpy as np
from nicelib import (load_lib, NiceLib, Sig, RetHandler)


@RetHandler(num_retvals=0)
def ret_errcode(retval, funcargs, niceobj):
    if retval != 0:
        raise ValueError(IMAQ.imgShowError(retval))


class IMAQ(NiceLib):
    _info_ = load_lib('imaq', __package__)
    _ret_ = ret_errcode

    imgShowError = Sig('in', 'buf[200]')
    imgInterfaceOpen = Sig('in', 'out')
    imgSessionOpen = Sig('in', 'out')
    imgCreateBufList = Sig('in', 'out')
    imgSessionConfigure = Sig('in', 'in')
    imgSessionStartAcquisition = Sig('in')
    imgSessionStopAcquisition = Sig('in')
    imgSessionCopyBufferByNumber = Sig('in', 'in', 'in', 'in', 'out', 'out')
    imgSessionTriggerConfigure2 = Sig('in', 'in', 'in', 'in', 'in', 'in')
    imgSessionStatus = Sig('in', 'out', 'out')


from cffi import FFI

ffi: FFI = IMAQ._info._ffi  # typing: FFI


class Cam:
    def __init__(self):
        self.reading_lock = Lock()
        self.init_imaq()
        self.init_nidaqmx()
        self.set_shots(200)

        if (p := (pathlib.Path(__file__).parent / 'back.npy')).exists():
            self.background = np.load(p)
        else:
            self.background = None

    def init_imaq(self):
        self.i = IMAQ.imgInterfaceOpen('img0')
        self.s = IMAQ.imgSessionOpen(self.i)
        IMAQ.imgSessionTriggerConfigure2(self.s, IMAQ.IMG_SIGNAL_EXTERNAL, IMAQ.IMG_EXT_TRIG0,
                                         IMAQ.IMG_TRIG_POLAR_ACTIVEH,
                                         1000, IMAQ.IMG_TRIG_ACTION_CAPTURE)
        self.frames = 0

    def init_nidaqmx(self, first='Chopper'):
        if hasattr(self, 'task'):
            self.task.close()
        task = nidaqmx.Task()
        if first == "Chopper":
            task.ai_channels.add_ai_voltage_chan('Dev1/AI0', min_val=0, max_val=2)
            task.ai_channels.add_ai_voltage_chan('Dev1/AI1', min_val=0, max_val=5)
        else:
            task.ai_channels.add_ai_voltage_chan('Dev1/AI0', name_to_assign_to_channel='Shaper', min_val=0, max_val=1)
            task.ai_channels.add_ai_voltage_chan('Dev1/AI1', name_to_assign_to_channel='Chopper', min_val=0, max_val=5)
        task.timing.cfg_samp_clk_timing(1000, 'PFI0', c.Edge.RISING, sample_mode=c.AcquisitionType.FINITE,
                                        samps_per_chan=20)

        # task.triggers.start_trigger.cfg_anlg_edge_start_trig("APFI0", trigger_level=2.5)
        task.triggers.start_trigger.cfg_dig_edge_start_trig("PFI0")
        task.export_signals.start_trig_output_term = "PFI12"
        self.task = task

    def set_shots(self, shots):
        self.reading_lock.acquire()
        N = shots
        self.task.timing.cfg_samp_clk_timing(1000, 'PFI0', c.Edge.RISING, sample_mode=c.AcquisitionType.FINITE,
                                             samps_per_chan=N)
        self.data = np.empty((128, 128, N), dtype='uint16')

        self.buflist = ffi.new("void *[]", [ffi.NULL] * N)
        self.skiplist = ffi.new("uInt32[]", [0] * N)

        IMAQ.imgSequenceSetup(self.s, N, ffi.cast("void **", self.buflist), self.skiplist, 0, 0)
        self.frames = 0
        self.shots = N
        self.reading_lock.release()

    def set_trigger(self, mode):
        if mode != 'Untriggered':
            self.task.triggers.start_trigger.cfg_anlg_edge_start_trig("PFI0", trigger_level=2.5)
        else:
            pass

    def get_frame_count(self):
        fcount = ffi.new("long[1]")
        IMAQ.imgGetAttribute(self.s, 0x0076 + 0x3FF60000, fcount)
        return fcount[0]

    def read_cam(self):
        self.reading_lock.acquire()
        IMAQ.imgSessionStartAcquisition(self.s)
        self.task.start()
        ba = bytearray(128 * 128 * 2)
        bi = np.frombuffer(ba).view('u2')
        chop = []
        status, buf = IMAQ.imgSessionStatus(self.s)

        for i in range(self.shots):
            IMAQ.imgSessionCopyBufferByNumber(self.s, i + self.frames, ffi.from_buffer(ba), IMAQ.IMG_OVERWRITE_FAIL)
            a = np.swapaxes(bi.reshape(32, 128, 4), 0, 1).reshape(128, 128)
            self.data[:, :, i] = (1 << 14) - a.T
            # hop.append(self.task.read(1)[0])
            # chop.append(self.task.read())

        self.frames += self.shots

        chop = self.task.read(c.READ_ALL_AVAILABLE)
        self.task.stop()
        self.reading_lock.release()
        return self.data, chop

    def remove_background(self):
        self.background = None

    def set_background(self):
        self.background = self.data.mean(2)
        np.save('back.npy', self.background)


if __name__ == "__main__":
    read = 0

    import pyqtgraph as pg

    app = pg.mkQApp()
    timer = pg.Qt.QtCore.QTimer()
    win = pg.PlotWidget()
    l = win.plotItem.plot()
    win.show()

    import time, threading

    cam = Cam()
    cam.read_cam()


    def up():
        t = time.time()
        thr = threading.Thread(target=cam.read_cam)
        # o, ch = cam.read_cam()
        thr.start()
        while thr.is_alive():
            app.processEvents()
        print(time.time() - t)
        l.setData(cam.data[10, 10, :])


    timer.timeout.connect(up)
    timer.start(0)
    timer.setSingleShot(False)
    app.exec_()
    cam.task.close()
