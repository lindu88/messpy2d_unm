import pathlib
from threading import Lock
from typing import Optional

import nidaqmx
import nidaqmx.constants as c
import numpy as np

try:
    from _imaqffi import lib, ffi
except ModuleNotFoundError:
    from ._imaqffi import lib, ffi

class Cam:
    def __init__(self):
        self.reading_lock = Lock()
        self.i, self.s = self.init_imaq()
        self.task = self.init_nidaqmx()
        self.frames = 0
        

        if (p := (pathlib.Path(__file__).parent / 'back.npy')).exists():
            self.background = np.load(p)
        else:
            self.background = None
        self.data = None
        self.line_data = None

    @staticmethod
    def init_imaq():
        IMAQ = lib
        IID = ffi.new("INTERFACE_ID[1]")
        SID = ffi.new("SESSION_ID[1]")
        IMAQ.imgInterfaceOpen(b'img0', IID)
        IMAQ.imgSessionOpen(IID[0], SID)
        s = SID[0]
        IMAQ.imgSessionTriggerConfigure2(s,
                                         IMAQ.IMG_SIGNAL_EXTERNAL,
                                         IMAQ.IMG_EXT_TRIG0,
                                         0,
                                         1000, IMAQ.IMG_TRIG_ACTION_CAPTURE)
        return IID[0], s

    def init_nidaqmx(self, first='Chopper'):
        task = nidaqmx.Task()
        if first == "Chopper":
            task.ai_channels.add_ai_voltage_chan(
                'Dev1/AI0', min_val=0, max_val=2)
            task.ai_channels.add_ai_voltage_chan(
                'Dev1/AI1', min_val=0, max_val=5)
        else:
            task.ai_channels.add_ai_voltage_chan(
                'Dev1/AI0', name_to_assign_to_channel='Shaper', min_val=0, max_val=1)
            task.ai_channels.add_ai_voltage_chan(
                'Dev1/AI1', name_to_assign_to_channel='Chopper', min_val=0, max_val=5)
        task.timing.cfg_samp_clk_timing(1000, 'PFI0', c.Edge.RISING, sample_mode=c.AcquisitionType.FINITE,
                                        samps_per_chan=20)

        # task.triggers.start_trigger.cfg_anlg_edge_start_trig("APFI0", trigger_level=2.5)
        task.triggers.start_trigger.cfg_dig_edge_start_trig("PFI0")
        task.export_signals.start_trig_output_term = "PFI12"
        return task

    def set_shots(self, shots):
        self.reading_lock.acquire()
        IMAQ = lib
        self.task.timing.cfg_samp_clk_timing(1000, 'PFI0', c.Edge.RISING, sample_mode=c.AcquisitionType.FINITE,
                                             samps_per_chan=shots)
        self.data = np.empty((shots, 128, 128), dtype='uint16')

        self.buflist = ffi.new("void *[]", [ffi.NULL] * shots)
        self.skiplist = ffi.new("uInt32[]", [0] * shots)

        IMAQ.imgSequenceSetup(self.s, shots, ffi.cast(
            "void **", self.buflist), self.skiplist, 0, 0)
        self.frames = 0
        self.shots = shots
        self.reading_lock.release()

    def set_trigger(self, mode):
        if mode != 'Untriggered':
            self.task.triggers.start_trigger.cfg_anlg_edge_start_trig(
                "PFI0", trigger_level=2.5)
        else:
            pass

    def get_frame_count(self):
        fcount = ffi.new("long[1]")
        lib.imgGetAttribute(self.s, 0x0076 + 0x3FF60000, fcount)
        return fcount[0]

    def read_cam(self, lines: Optional[list[tuple]] = None, back: Optional[np.ndarray] = None) -> tuple[np.ndarray, np.ndarray]:
        self.reading_lock.acquire()
        lib.imgSessionStartAcquisition(self.s)
        self.task.start()
        rows = 128
        colums = 128
        self.data = np.empty((self.shots, 128, 128), dtype='uint16')
        assert self.data is not None

        if lines is not None:
            self.lines = np.empty((len(lines), 128, self.shots), dtype='float')
            line_num = len(lines)
            line_buf = ffi.from_buffer("float[%d]"%(line_num*128*self.shots), self.lines)
            line_args = []
            for (a, b) in lines:
                line_args += [a, b]
        else:
            line_num = 0
            line_buf = ffi.NULL
            line_args = ffi.NULL

        if self.background is not None and False:
            back = ffi.from_buffer("uInt16[%d]"%(128*128), self.background)
        else:
            back = ffi.NULL
        outp = ffi.from_buffer("uInt16[%d]"%(128*128*self.shots), self.data)
       
        print(lib.read_n_shots(self.shots, self.frames, self.s,
                        outp, line_num, line_args, line_buf, back))
        #for i in range(self.shots):
        #    lib.imgSessionCopyBufferByNumber(
        #        self.s, i + self.frames, bap, lib.IMG_OVERWRITE_FAIL, 
        #        copied_number, copied_index)
        #    a = np.swapaxes(bi.reshape(rows//4, colums, 4),
        #                    0, 1).reshape(rows, colums)
        #    self.data[:, :, i] = MAX_14_BIT - a.T
            # self.background is not None:            #    self.data[:, :, i] -= self.background.astype('uint16')
        #    if lines:
        #        for k, (l, u) in enumerate(lines):
        #            m = np.mean(self.data[l:u, :, i], 0)
        #W            if back is not None:
        #                m = m - back[k]
        #            self.lines[k, :, i] = m

            # hop.append(self.task.read(1)[0])
            # chop.append(self.task.read())       
        
        self.frames += self.shots

        # chop = self.task.in_stream.read(c.READ_ALL_AVAILABLE)
        chop = self.task.read(c.READ_ALL_AVAILABLE)
        self.data = self.data
        self.task.stop()
        self.reading_lock.release()
        return self.data, chop

    def remove_background(self):
        self.background = None

    def set_background(self):
        assert self.data is not None
        self.background = self.data.mean(0).astype(np.uint16)
        np.save('back.npy', self.background)


if __name__ == "__main__":
    read = 0

    import pyqtgraph as pg

    app = pg.mkQApp()
    timer = pg.Qt.QtCore.QTimer()
    win = pg.PlotWidget()
    l = win.plotItem.plot()
    img = pg.ImageItem()
    win.addItem(img)
    win.show()

    import time
    import threading

    cam = Cam()
    cam.set_shots(20)
    cam.read_cam()

    cnt = 0
    import numpy as np

    def up():
        t = time.time()
        thr = threading.Thread(target=cam.read_cam, 
                               args=([(50, 60)],),
                                     )
        # o, ch = cam.read_cam()
        thr.start()
        while thr.is_alive():
            app.processEvents()
        print(time.time() - t)
        img.setImage(cam.data[0])
        global cnt
        #np.save('%d testread' % cnt, cam.data)
        cnt += 1


    timer.timeout.connect(up)
    timer.start(0)
    timer.setSingleShot(False)
    app.exec_()
    cam.task.close()
